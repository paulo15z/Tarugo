import pandas as pd

from apps.pcp.services.pcp_service import consolidar_ripas


def _montar_df_basico(*, ripas: list[dict], resto: list[dict]) -> pd.DataFrame:
    """
    Monta um DataFrame minimalista para testar ``consolidar_ripas``.

    Args:
        ripas (list[dict]): Linhas que representam peças de ripa.
        resto (list[dict]): Linhas que representam peças que não são ripas.

    Returns:
        pd.DataFrame: DataFrame combinado.
    """
    dados = []
    dados.extend(ripas)
    dados.extend(resto)
    return pd.DataFrame(dados)


def test_consolidar_ripas_empilha_altura_mantem_largura() -> None:
    """
    Caso esperado: agrupar ripas pelo mesmo conjunto e empilhar na altura do painel.

    Confere que a largura não é somada e que a altura do painel é recalculada:
    altura_painel = (altura_ripa * qtd) + (qtd * ESPESSURA_SERRA) + MARGEM_REFILO
    """
    df = _montar_df_basico(
        ripas=[
            {
                "DESCRIÇÃO DA PEÇA": "RIPA LATERAL",
                "MATERIAL DA PEÇA": "MDF",
                "ESPESSURA": "15",
                "ALTURA DA PEÇA": "1000",
                "LOCAL": "CABINE",
                "LARGURA DA PEÇA": "50",
                "QUANTIDADE": "2",
                "OBSERVAÇÃO": "",
                "OBS": "",
                "BORDA_FACE_FRENTE": "X",
                "BORDA_FACE_TRASEIRA": "X",
                "BORDA_FACE_LE": "X",
                "BORDA_FACE_LD": "X",
            }
        ],
        resto=[
            {
                "DESCRIÇÃO DA PEÇA": "OUTRA PEÇA",
                "MATERIAL DA PEÇA": "MDF",
                "ESPESSURA": "15",
                "ALTURA DA PEÇA": "1200",
                "LOCAL": "CABINE",
                "LARGURA DA PEÇA": "60",
                "QUANTIDADE": "1",
                "OBSERVAÇÃO": "",
                "OBS": "",
                "BORDA_FACE_FRENTE": "X",
                "BORDA_FACE_TRASEIRA": "X",
                "BORDA_FACE_LE": "X",
                "BORDA_FACE_LD": "X",
            }
        ],
    )

    out = consolidar_ripas(df)

    assert len(out) == 2
    painel = out[out["DESCRIÇÃO DA PEÇA"].str.contains("PAINEL PARA RIPAS")].iloc[0]

    # Largura deve permanecer igual à largura da ripa.
    assert painel["LARGURA DA PEÇA"] == "50"
    # Altura do painel deve refletir a nova regra.
    assert painel["ALTURA DA PEÇA"] == "2028,0"
    assert painel["QUANTIDADE"] == "1"
    # Instrução do marceneiro deve passar "altura correta".
    assert "2×1000mm" in str(painel["OBSERVAÇÃO"])
    # Borda do painel (painel consolidado) deve ser limpa.
    assert painel["BORDA_FACE_FRENTE"] == ""
    assert painel["BORDA_FACE_TRASEIRA"] == ""


def test_consolidar_ripas_sem_ripas_retornar_df_original() -> None:
    """
    Edge case: se não houver linhas de ripa, ``consolidar_ripas`` deve retornar o df original.
    """
    df = pd.DataFrame(
        [
            {
                "DESCRIÇÃO DA PEÇA": "OUTRA PEÇA",
                "MATERIAL DA PEÇA": "MDF",
                "ESPESSURA": "15",
                "ALTURA DA PEÇA": "1200",
                "LOCAL": "CABINE",
                "LARGURA DA PEÇA": "60",
                "QUANTIDADE": "1",
                "OBSERVAÇÃO": "",
                "OBS": "",
            }
        ]
    )
    out = consolidar_ripas(df)
    assert out.equals(df)


def test_consolidar_ripas_quantidade_invalida_nao_crasha() -> None:
    """
    Failure case: quantidade inválida (não numérica) deve ser tratada via ``to_float`` -> 0.0,
    evitando quebra do processamento.
    """
    df = _montar_df_basico(
        ripas=[
            {
                "DESCRIÇÃO DA PEÇA": "RIPA",
                "MATERIAL DA PEÇA": "MDF",
                "ESPESSURA": "15",
                "ALTURA DA PEÇA": "1000",
                "LOCAL": "CABINE",
                "LARGURA DA PEÇA": "50",
                "QUANTIDADE": "abc",
                "OBSERVAÇÃO": "",
                "OBS": "",
            }
        ],
        resto=[],
    )

    out = consolidar_ripas(df)
    assert len(out) == 1

    painel = out.iloc[0]
    assert "PAINEL PARA RIPAS" in str(painel["DESCRIÇÃO DA PEÇA"])
    # qtd = 0 => altura_painel = 0 + 0 + MARGEM_REFILO (20.0)
    assert painel["ALTURA DA PEÇA"] == "20,0"
    assert painel["QUANTIDADE"] == "1"

