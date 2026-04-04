import pandas as pd
from io import BytesIO
import uuid
import os
from django.conf import settings

from apps.pcp.models.lote import LotePCP
from apps.pcp.services.lote_service import LotePCPService
from apps.pcp.services.utils import (
    consolidar_ripas,
    calcular_roteiro,
    determinar_plano_de_corte,
    gerar_xls_roteiro,
)


def processar_arquivo_dinabox(uploaded_file):
    """
    
    Agora, além de retornar o que sempre retornou, também cria o LotePCP automaticamente.
    
    """
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

    # === Processamento antigo (mantido idêntico) ===
    df = consolidar_ripas(df)
    df['ROTEIRO'] = df.apply(calcular_roteiro, axis=1)
    df['PLANO'] = df.apply(lambda row: determinar_plano_de_corte(row, row['ROTEIRO']), axis=1)

    for col in ['LARGURA_NUM', 'QTD_NUM']:
        if col in df.columns:
            df = df.drop(columns=col)

    for col in ['OBSERVAÇÃO', 'OBS']:
        if col in df.columns:
            df[col] = df[col].str.replace(r' *_(pin|tap|led|curvo|painel|ripa|lamina)_ *', ' ', case=False, regex=True).str.strip()

    # === Geração do XLS (mantida idêntica) ===
    pid = str(uuid.uuid4())[:8]
    nome_saida = f"{pid}_{uploaded_file.name.rsplit('.', 1)[0]}.xls"
    xls_buf = gerar_xls_roteiro(df)
    xls_bytes = xls_buf.getvalue()

    os.makedirs(settings.PCP_OUTPUTS_DIR, exist_ok=True)
    caminho = os.path.join(settings.PCP_OUTPUTS_DIR, nome_saida)
    with open(caminho, 'wb') as f:
        f.write(xls_bytes)

    # === NOVA PARTE: Cria o LotePCP automaticamente (sem quebrar nada) ===
    LotePCPService.criar_lote_a_partir_de_dataframe(
        df=df,
        pid=pid,
        nome_arquivo=uploaded_file.name,
        # ordem_producao pode vir do arquivo no futuro
    )

    return df, xls_bytes, nome_saida, pid