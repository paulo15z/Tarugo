import pandas as pd
from collections import Counter
import math
from typing import Any
from io import BytesIO
import xlwt

BORDA_COLS = ['BORDA_FACE_FRENTE', 'BORDA_FACE_TRASEIRA', 'BORDA_FACE_LE', 'BORDA_FACE_LD']


def _formatar_ripa_para_erro(row, altura_ripa: float, altura_chapa: float) -> str:
    """Monta uma mensagem clara para identificar a ripa que falhou."""
    id_peca = str(row.get('ID DA PEÇA', '')).strip() or 'sem ID'
    descricao = str(row.get('DESCRIÇÃO DA PEÇA', '')).strip() or 'sem descrição'
    local = str(row.get('LOCAL', '')).strip() or 'sem local'
    return (
        f"Ripa inválida para consolidação: ID {id_peca} | {descricao} | {local} | "
        f"altura {altura_ripa:.1f}mm > chapa {altura_chapa:.1f}mm. "
        "Esta validação usa apenas a altura bruta da chapa; "
        "refilo e serra ficam para o cut planning."
    )


def consolidar_ripas(df: pd.DataFrame) -> pd.DataFrame:
    """Mantém exatamente o comportamento original (apenas extraído)"""
    mask_porta = (
        df['LOCAL'].astype(str).str.upper().str.contains('PORTA', na=False)
    )
    mask_ripa = (
        df['DESCRIÇÃO DA PEÇA'].str.upper().str.contains('RIPA', na=False) |
        df.get('OBSERVAÇÃO', pd.Series(dtype=str)).str.lower().str.contains('_ripa_', na=False) |
        df.get('OBS', pd.Series(dtype=str)).str.lower().str.contains('_ripa_', na=False)
    )
    mask_ripa = mask_ripa & ~mask_porta

    df_ripas = df[mask_ripa].copy()
    df_resto = df[~mask_ripa].copy()

    if df_ripas.empty:
        return df

    ALTURA_CHAPA = 2750.0

    def to_float(val):
        try:
            return float(str(val).replace(',', '.'))
        except:
            return 0.0

    df_ripas['ALTURA_NUM'] = df_ripas['ALTURA DA PEÇA'].apply(to_float)
    df_ripas['LARGURA_NUM'] = df_ripas['LARGURA DA PEÇA'].apply(to_float)
    df_ripas['QTD_NUM'] = df_ripas['QUANTIDADE'].apply(to_float)

    novas_ripas = []
    fita_cols = [col for col in df.columns if 'FITA' in col.upper()]

    grupos = df_ripas.groupby([
        'MATERIAL DA PEÇA',
        'ESPESSURA',
        'ALTURA_NUM',
        'LARGURA_NUM',
        'LOCAL',
        *fita_cols
    ])

    for name, group in grupos:
        altura_ripa = name[2]
        largura_ripa = name[3]
        total_pecas = int(group['QTD_NUM'].sum())

        if altura_ripa <= 0:
            continue

        # O cut planning já considera refilo e serra; aqui usamos só a altura bruta.
        max_por_tira = int(ALTURA_CHAPA // altura_ripa)

        if max_por_tira <= 0:
            raise ValueError(
                _formatar_ripa_para_erro(group.iloc[0], altura_ripa, ALTURA_CHAPA)
            )

        qtd_tiras = math.ceil(total_pecas / max_por_tira)

        for i in range(qtd_tiras):
            nova = group.iloc[0].copy()
            nova['DESCRIÇÃO DA PEÇA'] = "RIPA CORTE"
            nova['ALTURA DA PEÇA'] = str(int(ALTURA_CHAPA)).replace('.', ',')
            nova['LARGURA DA PEÇA'] = str(int(largura_ripa)).replace('.', ',')
            nova['QUANTIDADE'] = "1"
            nova['OBSERVAÇÃO'] = f"TIRA {i+1}/{qtd_tiras} → {total_pecas} PCS {int(altura_ripa)}mm"
            novas_ripas.append(nova)

    resultado = pd.concat([df_resto, pd.DataFrame(novas_ripas)], ignore_index=True)
    resultado = resultado.drop(columns=['ALTURA_NUM', 'LARGURA_NUM', 'QTD_NUM'], errors='ignore')
    return resultado


def determinar_plano_de_corte(row, roteiro: str) -> str:
    """Mantem a logica de plano priorizando tags estruturadas do Dinabox."""
    desc = str(row.get('DESCRI??O DA PE?A', '')).strip().lower()
    obs = (str(row.get('OBSERVA??O', '')) + ' ' + str(row.get('OBS', ''))).strip().lower()
    local = str(row.get('LOCAL', '')).strip().lower()
    material = str(row.get('MATERIAL DA PE?A', '')).strip().lower()

    tag_ripa = '_ripa_' in obs
    tag_painel = '_painel_' in obs
    tag_passagem = '_passagem_' in obs
    tag_lamina = '_lamina_' in obs
    tag_pintura = '_pin_' in obs or 'PIN' in roteiro
    tag_pre_montagem = '_pre_' in obs or '_pr?_' in obs or 'PR?' in roteiro

    if tag_pintura:
        return '01'
    if tag_lamina or 'lamina' in material or 'l?mina' in material or 'folha' in material:
        return '02'
    if tag_ripa:
        return '03'
    if tag_painel or tag_passagem:
        return '07'
    if 'DUP' in roteiro:
        return '05'
    if tag_pre_montagem or 'pre montagem' in obs or 'prem' in obs:
        return '10'
    if 'MCX' in roteiro:
        return '04'
    if 'MPE' in roteiro:
        return '06'
    if 'porta' in desc or 'porta' in local or 'frontal' in desc or 'frontal' in local or 'frente' in desc or 'frente' in local:
        return '06'
    return '11'


def calcular_roteiro(row) -> str:
    """calculo de roteiro baseado no csv q o dinabox exporta. Vale verificar se adicionar TODOS os campos disponiveis traria algum beneficio ou so complexidade"""
    desc = str(row.get('DESCRIÇÃO DA PEÇA', '')).strip().lower()
    local = str(row.get('LOCAL', '')).strip().lower()
    duplagem = str(row.get('DUPLAGEM', '')).strip().lower()
    furo = str(row.get('FURO', '')).strip().lower()
    obs = (str(row.get('OBSERVAÇÃO', '')) + ' ' + str(row.get('OBS', ''))).strip().lower()

    tem_borda = any(str(row.get(c, '')).strip() not in ('', 'nan') for c in BORDA_COLS)
    tem_furo = furo not in ('', 'nan', 'none')
    tem_duplagem = duplagem not in ('', 'nan', 'none')
    tem_puxador = 'puxador' in desc or 'tampa' in desc
    eh_ripa = 'ripa' in desc or 'ripa' in local or '_ripa_' in obs
    eh_porta = 'porta' in local or 'porta' in desc
    eh_gaveta = 'gaveta' in desc or 'gaveteiro' in desc or 'gaveta' in local
    eh_caixa = 'caixa' in local
    eh_frontal = 'frontal' in local or 'frontal' in desc
    eh_tamponamento = 'tamponamento' in local
    eh_painel = '_painel_' in obs

    tem_pintura = '_pin_' in obs
    tem_tapecar = '_tap_' in obs
    tem_eletrica = '_led_' in obs
    tem_curvo = '_curvo_' in obs

    rota = ['COR']
    if tem_duplagem and not eh_ripa:
        rota.append('DUP')
    if tem_borda:
        rota.append('BOR')
        if eh_ripa:
            rota.append('MAR')
            rota.append('XBOR')
    if tem_furo:
        rota.append('USI')
        rota.append('FUR')
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

    rota_final = []
    for etapa in rota:
        if etapa not in rota_final:
            rota_final.append(etapa)

    return ' > '.join(rota_final)

def gerar_xls_roteiro(df: pd.DataFrame) -> BytesIO:
    """ gera arquivo XLS formatado com estilos """

    
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Roteiro de Pecas')

    st_header = xlwt.easyxf(
        'font: bold true, colour white, height 200; '
        'pattern: pattern solid, fore_colour dark_blue; '
        'alignment: horiz centre, vert centre, wrap true; '
        'borders: left thin, right thin, top thin, bottom thin;'
    )
    st_header_rot = xlwt.easyxf(
        'font: bold true, colour white, height 200; '
        'pattern: pattern solid, fore_colour dark_yellow; '
        'alignment: horiz centre, vert centre; '
        'borders: left thin, right thin, top thin, bottom thin;'
    )
    st_data = xlwt.easyxf(
        'font: height 180; alignment: horiz centre, vert centre; '
        'borders: left thin, right thin, top thin, bottom thin;'
    )
    st_data_alt = xlwt.easyxf(
        'font: height 180; pattern: pattern solid, fore_colour ice_blue; '
        'alignment: horiz centre, vert centre; '
        'borders: left thin, right thin, top thin, bottom thin;'
    )
    st_rot = xlwt.easyxf(
        'font: bold true, height 180; pattern: pattern solid, fore_colour light_yellow; '
        'alignment: horiz centre, vert centre; '
        'borders: left thin, right thin, top thin, bottom thin;'
    )

    cols = list(df.columns)
    ws.row(0).height = 600

    for ci, col in enumerate(cols):
        st = st_header_rot if col in ('ROTEIRO', 'PLANO') else st_header
        ws.write(0, ci, col, st)
        ws.col(ci).width = 6000 if col in ('ROTEIRO', 'PLANO') else 4000

    for ri, (_, row) in enumerate(df.iterrows(), 1):
        st_base = st_data_alt if ri % 2 == 0 else st_data
        for ci, col in enumerate(cols):
            val = str(row.get(col, '')).replace('nan', '').strip()
            style = st_rot if col in ('ROTEIRO', 'PLANO') else st_base
            ws.write(ri, ci, val, style)

    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf
