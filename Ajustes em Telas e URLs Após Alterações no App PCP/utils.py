import pandas as pd
from collections import Counter
import math
from typing import Any
from io import BytesIO
import xlwt

BORDA_COLS = ['BORDA_FACE_FRENTE', 'BORDA_FACE_TRASEIRA', 'BORDA_FACE_LE', 'BORDA_FACE_LD']


def consolidar_ripas(df: pd.DataFrame) -> pd.DataFrame:
    """Mantém exatamente o comportamento original (apenas extraído)"""
    mask_ripa = (
        df['DESCRIÇÃO DA PEÇA'].str.upper().str.contains('RIPA', na=False) |
        df.get('OBSERVAÇÃO', pd.Series(dtype=str)).str.lower().str.contains('_ripa_', na=False) |
        df.get('OBS', pd.Series(dtype=str)).str.lower().str.contains('_ripa_', na=False)
    )

    df_ripas = df[mask_ripa].copy()
    df_resto = df[~mask_ripa].copy()

    if df_ripas.empty:
        return df

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

        altura_util = ALTURA_CHAPA - MARGEM_REFILO
        altura_por_peca = altura_ripa + ESPESSURA_SERRA
        max_por_tira = int(altura_util // altura_por_peca)

        if max_por_tira <= 0:
            raise ValueError(f"Ripa com altura {altura_ripa} maior que a chapa")

        qtd_tiras = math.ceil(total_pecas / max_por_tira)

        for i in range(qtd_tiras):
            nova = group.iloc[0].copy()
            nova['DESCRIÇÃO DA PEÇA'] = "RIPA CORTE"
            nova['ALTURA DA PEÇA'] = str(int(ALTURA_CHAPA)).replace('.', ',')
            nova['LARGURA DA PEÇA'] = str(int(largura_ripa)).replace('.', ',')
            nova['QUANTIDADE'] = "1"
            nova['OBSERVAÇÃO'] = f"TIRA {i+1}/{qtd_tiras} → {total_pecas} PCS {int(altura_ripa)}mm"
            novas_ripas.append(nova)

    return pd.concat([df_resto, pd.DataFrame(novas_ripas)], ignore_index=True)


def determinar_plano_de_corte(row, roteiro: str) -> str:
    """Mantém exatamente a lógica original"""
    desc = str(row.get('DESCRIÇÃO DA PEÇA', '')).strip().lower()
    obs = (str(row.get('OBSERVAÇÃO', '')) + ' ' + str(row.get('OBS', ''))).strip().lower()
    local = str(row.get('LOCAL', '')).strip().lower()
    material = str(row.get('MATERIAL DA PEÇA', '')).strip().lower()

    if 'PIN' in roteiro:
        return '01'
    if 'lamina' in material or 'lâmina' in material or 'folha' in material or '_lamina_' in obs:
        return '02'
    if 'DUP' in roteiro:
        return '05'
    if 'PRÉ' in roteiro or 'pré' in desc or 'pre montagem' in obs or 'prem' in obs or '_pré_' in obs:
        return '10'
    if 'MCX' in roteiro:
        return '04'
    if 'MPE' in roteiro or 'porta' in desc or 'porta' in local or 'frontal' in desc or 'frontal' in local or 'frente' in desc or 'frente' in local:
        return '06'
    return '11'


def calcular_roteiro(row) -> str:
    """Mantém exatamente a lógica original"""
    desc = str(row.get('DESCRIÇÃO DA PEÇA', '')).strip().lower()
    if 'painel para ripas' in desc:
        return 'COR > MAR > CQL > EXP'

    local = str(row.get('LOCAL', '')).strip().lower()
    duplagem = str(row.get('DUPLAGEM', '')).strip().lower()
    furo = str(row.get('FURO', '')).strip().lower()
    obs = (str(row.get('OBSERVAÇÃO', '')) + ' ' + str(row.get('OBS', ''))).strip().lower()

    tem_borda = any(str(row.get(c, '')).strip() not in ('', 'nan') for c in BORDA_COLS)
    tem_furo = furo not in ('', 'nan', 'none')
    tem_duplagem = duplagem not in ('', 'nan', 'none')
    tem_puxador = 'puxador' in desc or 'tampa' in desc
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
    if tem_duplagem:
        rota.append('DUP')
    if tem_borda:
        rota.append('BOR')
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
    return ' > '.join(rota)

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