import pandas as pd
from io import BytesIO
import xlwt
from collections import Counter
import os
from django.conf import settings
from apps.pcp.models.processamento import ProcessamentoPCP
import uuid
from datetime import datetime


BORDA_COLS = ['BORDA_FACE_FRENTE', 'BORDA_FACE_TRASEIRA', 'BORDA_FACE_LE', 'BORDA_FACE_LD']


def consolidar_ripas(df: pd.DataFrame) -> pd.DataFrame:
    mask_ripa = (
        df['DESCRIÇÃO DA PEÇA'].str.upper().str.contains('RIPA', na=False) |
        df.get('OBSERVAÇÃO', pd.Series(dtype=str)).str.lower().str.contains('_ripa_', na=False) |
        df.get('OBS', pd.Series(dtype=str)).str.lower().str.contains('_ripa_', na=False)
    )

    df_ripas = df[mask_ripa].copy()
    df_resto = df[~mask_ripa].copy()

    #  se não tiver ripa, não mexe
    if df_ripas.empty:
        return df

    #  CONFIG ---------------------------------------------
    ALTURA_CHAPA = 2750.0
    ESPESSURA_SERRA = 4.0
    MARGEM_REFILO = 20.0

    def to_float(val):
        try:
            return float(str(val).replace(',', '.'))
        except:
            return 0.0

    df_ripas['ALTURA_NUM'] = df_ripas['ALTURA DA PEÇA'].apply(to_float)
    df_ripas['LARGURA_NUM'] = df_ripas['LARGURA DA PEÇA'].apply(to_float)
    df_ripas['QTD_NUM'] = df_ripas['QUANTIDADE'].apply(to_float)

    novas_ripas = []

    #  detecta colunas de fita automaticamente
    fita_cols = [col for col in df.columns if 'FITA' in col.upper()]

    grupos = df_ripas.groupby([
        'MATERIAL DA PEÇA',
        'ESPESSURA',
        'ALTURA_NUM',
        'LARGURA_NUM',
        'LOCAL',
        *fita_cols
    ])

    import math

    for name, group in grupos:
        altura_ripa = name[2]
        largura_ripa = name[3]

        total_pecas = int(group['QTD_NUM'].sum())

        if altura_ripa <= 0:
            continue

        #  cálculo de quantas peças cabem em uma tira
        altura_util = ALTURA_CHAPA - MARGEM_REFILO
        altura_por_peca = altura_ripa + ESPESSURA_SERRA

        max_por_tira = int(altura_util // altura_por_peca)

        if max_por_tira <= 0:
            raise ValueError(
                f"Ripa com altura {altura_ripa} maior que a chapa"
            )

        #  quantas tiras precisamos
        qtd_tiras = math.ceil(total_pecas / max_por_tira)

        #  gera UMA LINHA POR TIRA (QTD = 1) nao temos ctz de que o sistema do pcp reconhece essa coluna de quantidade
        for i in range(qtd_tiras):
            nova = group.iloc[0].copy()

            nova['DESCRIÇÃO DA PEÇA'] = "RIPA CORTE"
            nova['ALTURA DA PEÇA'] = str(int(ALTURA_CHAPA)).replace('.', ',')
            nova['LARGURA DA PEÇA'] = str(int(largura_ripa)).replace('.', ',')
            nova['QUANTIDADE'] = "1"

            nova['OBSERVAÇÃO'] = (
                f"TIRA {i+1}/{qtd_tiras} → "
                f"{total_pecas} PCS {int(altura_ripa)}mm"
            )

            #  NÃO mexe nas FITAS → preserva tudo

            novas_ripas.append(nova)

    #  remove completamente as ripas originais
    resultado = pd.concat(
        [df_resto, pd.DataFrame(novas_ripas)],
        ignore_index=True
    )

    return resultado



def determinar_plano_de_corte(row) -> str:
    desc = str(row.get('DESCRIÇÃO DA PEÇA', '')).strip().lower()
    obs = (str(row.get('OBSERVAÇÃO', '')) + ' ' + str(row.get('OBS', ''))).strip().lower()
    local = str(row.get('LOCAL', '')).strip().lower()
    duplagem = str(row.get('DUPLAGEM', '')).strip().lower()
    material = str(row.get('MATERIAL DA PEÇA', '')).strip().lower()

    if '_pin_' in obs or 'pintura' in desc:
        return '01'
    if 'lamina' in material or 'folha' in material or '_lamina_' in obs:
        return '02'
    if 'gaveta' in desc or 'gaveteiro' in desc or 'caixa' in local:
        return '04'
    if duplagem not in ('', 'nan', 'none'):
        return '05'
    if 'porta' in desc or 'frontal' in desc or 'porta' in local:
        return '06'
    if 'pré' in desc or 'pre montagem' in obs or 'prem' in obs:
        return '10'
    return '11'


def calcular_roteiro(row) -> str:
    desc = str(row.get('DESCRIÇÃO DA PEÇA', '')).strip().lower()

    if 'painel para ripas' in desc:
        return 'COR > MAR > CQL > EXP'

    local = str(row.get('LOCAL', '')).strip().lower()
    duplagem = str(row.get('DUPLAGEM', '')).strip().lower()
    furo = str(row.get('FURO', '')).strip().lower()
    obs = (str(row.get('OBSERVAÇÃO', '')) + ' ' + str(row.get('OBS', ''))).strip().lower()

    tem_borda = any(str(row.get(c, '')).strip() not in ('', 'nan') for c in BORDA_COLS) # logica inversa para facilitar a leitura do código do roteiro
    tem_furo = furo not in ('', 'nan', 'none') # verifica se tem furo
    tem_duplagem = duplagem not in ('', 'nan', 'none')                                  # coluca de duplag
    tem_puxador = 'puxador' in desc or 'tampa' in desc                                  # alucinei mas em algum momento vamos usar
    eh_porta = 'porta' in local or 'porta' in desc                                      # verifica se é uma porta
    eh_gaveta = 'gaveta' in desc or 'gaveteiro' in desc or 'gaveta' in local            # verifica se é gaveta
    eh_caixa = 'caixa' in local                                                         # verifica se é caixa (bem porcamente, mas é o que temos)  
    eh_frontal = 'frontal' in local or 'frontal' in desc                                # verifica se é frontal
    eh_tamponamento = 'tamponamento' in local                                           # verifica se é tamponamento (usado para decidir se vai para marcenaria ou não)
    eh_painel = '_painel_' in obs

# uso das tags
    tem_pintura = '_pin_' in obs 
    tem_tapecar = '_tap_' in obs
    tem_eletrica = '_led_' in obs
    tem_curvo = '_curvo_' in obs

    rota = ['COR']

    # 1º: Faz o Engrossamento/Duplagem
    if tem_duplagem:
        rota.append('DUP')

    # 2º: Passa a Borda 
    if tem_borda:
        rota.append('BOR')

    # 3º: Segue o fluxo normal de furação
    if tem_furo:
        rota.append('USI')
        rota.append('FUR')      # vamso em algum momento verificar isso aqui

    # Regra MCX: Só vai para MCX se NÃO tiver duplagem
    if (eh_gaveta or eh_caixa) and not eh_painel and not tem_duplagem:
        rota.append('MCX')

    elif tem_puxador or eh_porta or eh_frontal:
        rota.append('MPE')
        rota.append('MAR')
        
    if eh_painel or (eh_tamponamento and not eh_gaveta):
        rota.append('MAR')

    if tem_pintura:
        rota.append('PIN')
    if tem_tapecar:
        rota.append('TAP')
    if tem_eletrica:
        rota.append('MEL')
    if tem_curvo:
        rota.append('XMAR')

    rota.extend(['CQL', 'EXP'])
    return ' > '.join(rota)


def gerar_xls(df: pd.DataFrame) -> BytesIO:
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Roteiro de Pecas')

    st_header = xlwt.easyxf('font: bold true, colour white, height 200; pattern: pattern solid, fore_colour dark_blue; alignment: horiz centre, vert centre, wrap true; borders: left thin, right thin, top thin, bottom thin;')
    st_header_rot = xlwt.easyxf('font: bold true, colour white, height 200; pattern: pattern solid, fore_colour dark_yellow; alignment: horiz centre, vert centre; borders: left thin, right thin, top thin, bottom thin;')
    st_data = xlwt.easyxf('font: height 180; alignment: horiz centre, vert centre; borders: left thin, right thin, top thin, bottom thin;')
    st_data_alt = xlwt.easyxf('font: height 180; pattern: pattern solid, fore_colour ice_blue; alignment: horiz centre, vert centre; borders: left thin, right thin, top thin, bottom thin;')
    st_rot = xlwt.easyxf('font: bold true, height 180; pattern: pattern solid, fore_colour light_yellow; alignment: horiz centre, vert centre; borders: left thin, right thin, top thin, bottom thin;')

    cols = list(df.columns)
    ws.row(0).height = 600

    for ci, col in enumerate(cols):
        st = st_header_rot if col == 'ROTEIRO' else st_header
        ws.write(0, ci, col, st)
        ws.col(ci).width = 6000 if col in ('ROTEIRO', 'PLANO') else 4000

    for ri, (_, row) in enumerate(df.iterrows(), 1):
        st_base = st_data_alt if ri % 2 == 0 else st_data
        for ci, col in enumerate(cols):
            val = str(row.get(col, '')).replace('nan', '').strip()
            ws.write(ri, ci, val, st_rot if col in ('ROTEIRO', 'PLANO') else st_base)

    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


def processar_arquivo_dinabox(uploaded_file):
    ext = uploaded_file.name.rsplit('.', 1)[-1].lower()

    if ext == 'csv':
        raw = uploaded_file.read()
        text = None
        for enc in ('utf-8-sig', 'utf-8', 'cp1252', 'latin-1'):
            try:
                text = raw.decode(enc)
                break
            except:
                continue
        if text is None:
            raise ValueError("Não foi possível decodificar o CSV")

        linhas = text.splitlines()
        corpo = [l.rstrip(';') for l in linhas if not (l.startswith('[') and '[LISTA]' not in l and '[/LISTA]' not in l)]
        df = pd.read_csv(BytesIO('\n'.join(corpo).encode()), sep=';', dtype=str).fillna('')
    else:
        df = pd.read_excel(uploaded_file, dtype=str, engine='openpyxl' if ext == 'xlsx' else 'xlrd').fillna('')

    df.columns = [c.strip() for c in df.columns]
    df = df[[c for c in df.columns if c]]

    if 'NOME DO CLIENTE' in df.columns:
        df = df[~df['NOME DO CLIENTE'].str.strip().isin(['RODAPÉ', ''])]

    obrigatorias = ['LOCAL', 'FURO', 'DUPLAGEM', 'DESCRIÇÃO DA PEÇA']
    faltando = [c for c in obrigatorias if c not in df.columns]
    if faltando:
        raise ValueError(f"Colunas obrigatórias não encontradas: {', '.join(faltando)}")

    df = consolidar_ripas(df)
    df['ROTEIRO'] = df.apply(calcular_roteiro, axis=1)
    df['PLANO'] = df.apply(determinar_plano_de_corte, axis=1)

    for col in ['LARGURA_NUM', 'QTD_NUM']:
        if col in df.columns:
            df = df.drop(columns=col)

    for col in ['OBSERVAÇÃO', 'OBS']:
        if col in df.columns:
            df[col] = df[col].str.replace(r' *_(pin|tap|led|curvo|painel|ripa|lamina)_ *', ' ', case=False, regex=True).str.strip()

    pid = str(uuid.uuid4())[:8]
    nome_saida = f"{pid}_{uploaded_file.name.rsplit('.', 1)[0]}.xls"

    xls_buf = gerar_xls(df)
    xls_bytes = xls_buf.getvalue()

    os.makedirs(settings.PCP_OUTPUTS_DIR, exist_ok=True)
    caminho = os.path.join(settings.PCP_OUTPUTS_DIR, nome_saida)

    with open(caminho, 'wb') as f:
        f.write(xls_bytes)

    return df, xls_bytes, nome_saida, pid
