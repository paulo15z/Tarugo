# apps/pcp/services/processamento_service.py
from io import BytesIO
import uuid

import pandas as pd

from django.core.files.base import ContentFile

from pydantic import ValidationError

from apps.pcp.models.processamento import ProcessamentoPCP
from apps.pcp.services.schemas import PCPProcessRequest   # ← corrigido

# Utils
from apps.pcp.utils.parsers import ler_arquivo_dinabox
from apps.pcp.utils.ripas import consolidar_ripas
from apps.pcp.utils.roteiros import calcular_roteiro, determinar_plano_de_corte
from apps.pcp.utils.excel import gerar_xls_roteiro


class ProcessamentoPCPService:

    @staticmethod
    def gerar_coluna_r(df: pd.DataFrame, lote: int) -> pd.DataFrame:
        """Coluna R = lote-plano (ex: 305-06)"""
        df = df.copy()
        df['PLANO'] = df['PLANO'].astype(str).str.strip()
        df['R'] = df['PLANO'].apply(lambda plano: f"{lote}-{plano}")
        return df

    @staticmethod
    def processar_arquivo(uploaded_file, lote: int):
        try:
            input_data = PCPProcessRequest(          # ← corrigido
                lote=lote,
                filename=uploaded_file.name,
                file_bytes=uploaded_file.read()
            )
        except ValidationError as e:
            raise ValueError(f"Erro de validação: {e}") from e

        # 1. Ler arquivo
        df = ler_arquivo_dinabox(input_data.file_bytes, input_data.filename)

        # 2. Processamento
        df = consolidar_ripas(df)
        df['ROTEIRO'] = df.apply(calcular_roteiro, axis=1)
        df['PLANO'] = df.apply(
            lambda row: determinar_plano_de_corte(row, row.get('ROTEIRO', '')), 
            axis=1
        )

        # 3. Gerar coluna R
        df = ProcessamentoPCPService.gerar_coluna_r(df, lote=input_data.lote)

        # 4. Limpeza
        for col in ['LARGURA_NUM', 'QTD_NUM']:
            if col in df.columns:
                df = df.drop(columns=[col], errors='ignore')

        for col in ['OBSERVAÇÃO', 'OBS']:
            if col in df.columns:
                df[col] = (
                    df[col]
                    .astype(str)
                    .str.replace(r' *_(pin|tap|led|curvo|painel|ripa|lamina)_ *', ' ', case=False, regex=True)
                    .str.strip()
                )

        if 'DUPLAGEM' in df.columns:
            df['DUPLAGEM'] = df['DUPLAGEM'].astype(str).str.lower().str.strip()
            mask = df['DUPLAGEM'].str.contains('duplagem', na=False)
            if mask.any():
                df.loc[mask, 'OBSERVAÇÃO'] = df.loc[mask, 'OBSERVAÇÃO'].fillna('') + ' _dup_ '

        # 5. Gerar XLS
        xls_buf = gerar_xls_roteiro(df)
        xls_bytes = xls_buf.getvalue()

        # 6. Salvar
        pid = str(uuid.uuid4())[:8]
        nome_saida = f"{pid}_Lote-{lote}_{uploaded_file.name.rsplit('.', 1)[0]}.xls"

        processamento = ProcessamentoPCP.objects.create(
            id=pid,
            nome_arquivo=uploaded_file.name,
            lote=lote,
            total_pecas=len(df),
        )

        arquivo_content = ContentFile(xls_bytes, name=nome_saida)
        processamento.arquivo_saida.save(nome_saida, arquivo_content, save=True)

        # 7. Resposta
        cols_previa = ['R', 'DESCRIÇÃO DA PEÇA', 'LOCAL', 'PLANO', 'ROTEIRO']
        if 'OBSERVAÇÃO' in df.columns:
            cols_previa.insert(3, 'OBSERVAÇÃO')

        previa = df[cols_previa].head(50).fillna('').to_dict(orient='records')

        resumo_df = df['ROTEIRO'].fillna('SEM ROTEIRO').astype(str).value_counts().reset_index()
        resumo_df.columns = ['roteiro', 'qtd']
        resumo = resumo_df.to_dict(orient='records')

        return {
            'pid': pid,
            'lote': lote,
            'total_pecas': len(df),
            'previa': previa,
            'resumo': resumo,
            'nome_saida': nome_saida,
        }