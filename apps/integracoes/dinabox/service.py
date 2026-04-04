# apps/integracoes/dinabox/service.py
from io import BytesIO
import pandas as pd
from pydantic import BaseModel, Field

class DinaboxFile(BaseModel):
    """Valida o input para o parser do Dinabox."""
    raw_file: bytes
    filename: str = Field(..., min_length=1)

class DinaboxService:
    """
    Serviço central para lidar com a importação e parsing de arquivos do Dinabox.
    Objetivo: Substituir a lógica espalhada em `pcp/utils/parsers.py`.
    """
    @staticmethod
    def parse_to_dataframe(raw_file: bytes, filename: str) -> pd.DataFrame:
        """
        Recebe os bytes de um arquivo e seu nome, e retorna um DataFrame Pandas limpo e validado.
        Este método consolida a lógica de `ler_arquivo_dinabox`.
        """
        # Validação de entrada com Pydantic
        file_data = DinaboxFile(raw_file=raw_file, filename=filename)
        
        ext = file_data.filename.rsplit(".", 1)[-1].lower()

        if ext == 'csv':
            text = None
            for enc in ('utf-8-sig', 'utf-8', 'cp1252', 'latin-1'):
                try:
                    text = file_data.raw_file.decode(enc)
                    break
                except UnicodeDecodeError:
                    continue
            
            if text is None:
                raise ValueError("Não foi possível decodificar o arquivo CSV. Verifique o encoding.")

            # Remove o cabeçalho e rodapé específicos do Dinabox
            linhas = text.splitlines()
            corpo = [l.rstrip(';') for l in linhas if not (l.startswith('[') and '[LISTA]' not in l and '[/LISTA]' not in l)]
            df = pd.read_csv(BytesIO('\n'.join(corpo).encode('utf-8')), sep=';', dtype=str).fillna('')
        else:
            # Suporta tanto XLS (xlrd) quanto XLSX (openpyxl)
            df = pd.read_excel(BytesIO(file_data.raw_file), dtype=str).fillna('')

        # --- Limpeza e Padronização do DataFrame ---
        
        # 1. Nomes de colunas
        df.columns = [c.strip() for c in df.columns]
        df = df[[c for c in df.columns if c]] # Remove colunas vazias

        # 2. Remove rodapé do relatório
        if 'NOME DO CLIENTE' in df.columns:
            df = df[~df['NOME DO CLIENTE'].astype(str).str.strip().isin(['RODAPÉ', 'RODAPE', ''])]

        # 3. Limpa espaços em branco de todas as colunas de texto
        for col in df.columns:
            if pd.api.types.is_object_dtype(df[col]):
                df[col] = df[col].astype(str).str.strip()

        # 4. Validação de colunas obrigatórias para o PCP
        obrigatorias = ['LOCAL', 'FURO', 'DUPLAGEM', 'DESCRIÇÃO DA PEÇA']
        faltando = [c for c in obrigatorias if c not in df.columns]
        if faltando:
            raise ValueError(f"Colunas obrigatórias do Dinabox não encontradas no arquivo: {', '.join(faltando)}")

        return df
