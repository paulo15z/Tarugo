# apps/pcp/utils/parsers.py
from io import BytesIO
import pandas as pd


def ler_arquivo_dinabox(raw_file: bytes, filename: str) -> pd.DataFrame:
    """Parser simples e robusto - versão que já estava funcionando + pequenas correções"""
    ext = filename.rsplit('.', 1)[-1].lower()

    if ext == 'csv':
        raw = raw_file
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
        df = pd.read_excel(BytesIO(raw_file), dtype=str).fillna('')

    # Limpeza básica de colunas
    df.columns = [c.strip() for c in df.columns]
    df = df[[c for c in df.columns if c]]

    # Remove rodapé
    if 'NOME DO CLIENTE' in df.columns:
        df = df[~df['NOME DO CLIENTE'].astype(str).str.strip().isin(['RODAPÉ', 'RODAPE', ''])]

    # Remove espaços iniciais/finais em todas as colunas de texto
    for col in df.columns:
        if pd.api.types.is_object_dtype(df[col]):
            df[col] = df[col].astype(str).str.strip()

    # Verifica colunas obrigatórias (aceita variações)
    obrigatorias = ['LOCAL', 'FURO', 'DUPLAGEM', 'DESCRIÇÃO DA PEÇA']
    faltando = [c for c in obrigatorias if c not in df.columns]
    if faltando:
        raise ValueError(f"Colunas obrigatórias não encontradas: {', '.join(faltando)}")

    return df