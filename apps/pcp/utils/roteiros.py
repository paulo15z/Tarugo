import pandas as pd

BORDA_COLS = ['BORDA_FACE_FRENTE', 'BORDA_FACE_TRASEIRA', 'BORDA_FACE_LE', 'BORDA_FACE_LD']


def determinar_plano_de_corte(row: pd.Series, roteiro: str) -> str:
    """Determina o plano de corte baseado no roteiro e características da peça"""
    desc = str(row.get('DESCRIÇÃO DA PEÇA', '')).strip().lower()
    obs = (str(row.get('OBSERVAÇÃO', '')) + ' ' + str(row.get('OBS', ''))).strip().lower()
    local = str(row.get('LOCAL', '')).strip().lower()
    material = str(row.get('MATERIAL DA PEÇA', '')).strip().lower()

    if 'PIN' in roteiro:
        return '01'   # PEÇAS COM PINTURA - tudo 3

    if 'lamina' in material or 'lâmina' in material or 'folha' in material or '_lamina_' in obs:
        return '02'   # LÂMINAS OU FOLHAS - tudo 3

    if 'DUP' in roteiro:
        return '05'   # ENGROSSADAS/DUPLADAS - b.o

    if 'PRÉ' in roteiro or 'pré' in desc or 'pre montagem' in obs or 'prem' in obs or '_pre_' in obs:
        return '10'   # PRÉ MONTAGEM - nao sei se o Pré-Montagem do dinabox é funcional

    if 'MCX' in roteiro:
        return '04'   # MONTAGEM DE CAIXAS E GAVETAS - extremo cuidado

    if 'MPE' in roteiro or 'porta' in desc or 'porta' in local or 'frontal' in desc or 'frontal' in local or 'frente' in desc or 'frente' in local:
        return '06'   # PORTAS E FRENTES

    return '11'       # OUTROS


def calcular_roteiro(row: pd.Series) -> str:

    """Calculj o roteiro completo da peça"""
    desc = str(row.get('DESCRIÇÃO DA PEÇA', '')).strip().lower()
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

    if (eh_gaveta or eh_caixa) and not eh_painel and not tem_duplagem: # remover o eh_painel em breve ufa 
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
    if tem_curvo:   #mudar esse nome
        rota.append('XMAR')

    rota.extend(['CQL', 'EXP']) #padrao, tudo tem q verificar e expedir
    return ' > '.join(rota)