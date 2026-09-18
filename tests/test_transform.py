"""
Testes de src/transform.py.

Cobrem, com dados sintéticos (sem depender do Excel real), os pontos que
falharam de verdade durante a implementação: alias LAB->Labomar ausente,
datas brasileiras interpretadas sem dayfirst, e limpeza de erros de fórmula.
"""
import numpy as np
import pandas as pd
import pytest

from src.transform import (
    normalize_ru,
    normalize_refeicao,
    to_numeric_safe,
    to_date_safe,
    build_fact_detalhe,
    build_fact_gestao_manutencao,
    build_public_layer,
    PII_COLUMNS_BY_FACT,
    is_realizado_detalhe,
    is_realizado_isc,
    max_data_realizada,
    _within_valid_range,
)


# ---------------------------------------------------------------------------
# normalize_ru
# ---------------------------------------------------------------------------


def test_normalize_ru_reconhece_siglas_e_nomes_completos():
    entrada = pd.Series(["P1", "Pici 1", "BENFICA", "Porangabussu", "PORANGA"])
    saida = normalize_ru(entrada)
    assert list(saida) == ["P1", "P1", "B", "PO", "PO"]


def test_normalize_ru_alias_lab_para_labomar():
    """Regressão: 'LAB' não estava mapeado em ru_aliases e fazia 6 registros
    de Atendimentos Especializado caírem como ru_desconhecido (achado real
    do relatório de qualidade)."""
    entrada = pd.Series(["LAB", "Labomar", "L"])
    saida = normalize_ru(entrada)
    assert list(saida) == ["L", "L", "L"]


def test_normalize_ru_valor_desconhecido_vira_nan():
    entrada = pd.Series(["SENUT", "Cozinha Central", None])
    saida = normalize_ru(entrada)
    assert saida.isna().all()


def test_normalize_ru_e_insensivel_a_acento_e_caixa():
    entrada = pd.Series(["porangabussu", "PORANGABUSSU", "PoRaNgAbUsSu"])
    saida = normalize_ru(entrada)
    assert (saida == "PO").all()


# ---------------------------------------------------------------------------
# normalize_refeicao
# ---------------------------------------------------------------------------


def test_normalize_refeicao_variacoes_de_acento_e_caixa():
    entrada = pd.Series(["ALMOÇO", "Almoco", "café", "JANTAR"])
    saida = normalize_refeicao(entrada)
    assert list(saida) == ["Almoço", "Almoço", "Café", "Jantar"]


def test_normalize_refeicao_desconhecida_vira_nan():
    entrada = pd.Series(["Ceia", "Lanche", None])
    saida = normalize_refeicao(entrada)
    assert saida.isna().all()


# ---------------------------------------------------------------------------
# to_date_safe — regressão do bug de dayfirst
# ---------------------------------------------------------------------------


def test_to_date_safe_interpreta_formato_brasileiro_dayfirst():
    """Regressão: sem dayfirst=True, '13/01/2026' (13 de janeiro) virava NaT
    porque o pandas tentava interpretar '13' como mês (formato americano)."""
    entrada = pd.Series(["13/01/2026", "05/12/2026", "01/02/2026"])
    saida = to_date_safe(entrada)
    assert saida.isna().sum() == 0
    assert saida.iloc[0] == pd.Timestamp("2026-01-13")
    assert saida.iloc[1] == pd.Timestamp("2026-12-05")
    assert saida.iloc[2] == pd.Timestamp("2026-02-01")


def test_to_date_safe_datas_ja_datetime_nao_sao_afetadas_por_dayfirst():
    entrada = pd.Series([pd.Timestamp("2026-03-10"), pd.Timestamp("2026-11-20")])
    saida = to_date_safe(entrada)
    assert list(saida) == list(entrada)


def test_to_date_safe_valor_invalido_vira_nat():
    entrada = pd.Series(["#REF!", "não é data", "23/202/2026", None])
    saida = to_date_safe(entrada)
    assert saida.isna().all()


# ---------------------------------------------------------------------------
# to_numeric_safe
# ---------------------------------------------------------------------------


def test_to_numeric_safe_trata_erros_de_formula_como_nan():
    entrada = pd.Series(["#DIV/0!", "#N/A", "#VALUE!", "10.5", "", None, 42])
    saida = to_numeric_safe(entrada)
    # "#DIV/0!", "#N/A", "#VALUE!", "" e None -> NaN (5 no total)
    assert saida.isna().sum() == 5
    assert saida.iloc[3] == 10.5
    assert saida.iloc[6] == 42


def test_to_numeric_safe_nunca_transforma_erro_em_zero():
    """Requisito de negócio: erro de fórmula é ausência de dado, não zero —
    tratar como zero inflaria/distorceria somas de desperdício."""
    entrada = pd.Series(["#DIV/0!"])
    saida = to_numeric_safe(entrada)
    assert saida.isna().iloc[0]
    assert not (saida.fillna(-1) == 0).iloc[0]


# ---------------------------------------------------------------------------
# _within_valid_range
# ---------------------------------------------------------------------------


def test_within_valid_range_marca_datas_fora_da_janela_do_projeto():
    datas = pd.to_datetime(pd.Series(["2026-05-01", "2027-03-24", "2024-01-01"]))
    mask = _within_valid_range(datas)
    assert list(mask) == [True, False, False]


# ---------------------------------------------------------------------------
# build_fact_detalhe — integração da limpeza completa
# ---------------------------------------------------------------------------


def _raw_detalhe_row(**overrides):
    base = {
        "ru": "P1",
        "refeicao": "Almoço",
        "mes": "01",
        "data": "05/01/2026",
        "prep": "PB",
        "cardapio": "Frango",
        "temp_c": 70,
        "peso_bruto": 100.0,
        "repos": None,
        "qtd1": None,
        "tam1": None,
        "qtd2": None,
        "tam2": None,
        "peso_liq": 90.0,
        "pce": None,
        "pc_pct": 0.5,
        "previsao": 100,
        "peso_previsto": 50.0,
        "controle_cubas": None,
        "comensais": 200,
        "ajustes": None,
        "sobra_limpa": 5.0,
        "sobra_suja": 2.0,
        "consumo_real": 90.0,
        "pc_pres": 0.45,
        "comensais_real": 180,
        "bom": 10,
        "regular": 2,
        "ruim": 0,
        "sheet_origem": "P1D",
    }
    base.update(overrides)
    return base


def test_build_fact_detalhe_remove_linhas_sem_data_valida():
    df_raw = pd.DataFrame([
        _raw_detalhe_row(),
        _raw_detalhe_row(data=None, prep="Vazio"),          # linha-template sem data
        _raw_detalhe_row(data="#REF!", prep="ErroRef"),     # erro de fórmula na data
    ])
    result = build_fact_detalhe(df_raw)
    assert len(result) == 1
    assert result.iloc[0]["prep"] == "PB"


def test_build_fact_detalhe_remove_duplicatas_exatas_por_chave():
    df_raw = pd.DataFrame([_raw_detalhe_row(), _raw_detalhe_row()])  # linha idêntica 2x
    result = build_fact_detalhe(df_raw)
    assert len(result) == 1


def test_build_fact_detalhe_trata_negativo_impossivel_como_nan():
    df_raw = pd.DataFrame([_raw_detalhe_row(comensais_real=-5)])
    result = build_fact_detalhe(df_raw)
    assert pd.isna(result.iloc[0]["comensais_real"])


def test_build_fact_detalhe_normaliza_refeicao_e_datas_brasileiras():
    df_raw = pd.DataFrame([_raw_detalhe_row(refeicao="ALMOÇO", data="05/01/2026")])
    result = build_fact_detalhe(df_raw)
    assert result.iloc[0]["refeicao"] == "Almoço"
    assert result.iloc[0]["data"] == pd.Timestamp("2026-01-05")


# ---------------------------------------------------------------------------
# build_fact_gestao_manutencao — mapeamento de RU por texto livre + range de datas
# ---------------------------------------------------------------------------


def test_build_fact_gestao_manutencao_mapeia_local_para_ru_canonico():
    df_raw = pd.DataFrame([
        {"data": "10/02/2026", "ru_texto": "Benfica", "resolvido": "Sim",
         "data_resolucao": "12/02/2026", "tipo": "Infraestrutura", "sheet_origem": "UFC-INFRA"},
        {"data": "11/02/2026", "ru_texto": "SENUT", "resolvido": "Não",
         "data_resolucao": None, "tipo": "Infraestrutura", "sheet_origem": "UFC-INFRA"},
    ])
    result = build_fact_gestao_manutencao(df_raw)
    assert result.loc[result["ru_texto"] == "Benfica", "ru"].iloc[0] == "B"
    assert pd.isna(result.loc[result["ru_texto"] == "SENUT", "ru"].iloc[0])


def test_build_fact_gestao_manutencao_descarta_data_fora_do_periodo_valido():
    """Regressão: um registro real com ano '2027' (típico erro de digitação)
    distorcia a 'data de última atualização' exibida no dashboard."""
    df_raw = pd.DataFrame([
        {"data": "24/03/2027", "ru_texto": "Porangabussu", "resolvido": "Não",
         "data_resolucao": None, "tipo": "Infraestrutura", "sheet_origem": "UFC-INFRA"},
        {"data": "24/03/2026", "ru_texto": "Porangabussu", "resolvido": "Sim",
         "data_resolucao": "25/03/2026", "tipo": "Infraestrutura", "sheet_origem": "UFC-INFRA"},
    ])
    result = build_fact_gestao_manutencao(df_raw)
    assert len(result) == 1
    assert result.iloc[0]["data"] == pd.Timestamp("2026-03-24")


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v"]))


# ---------------------------------------------------------------------------
# build_public_layer — camada segura para publicação (GitHub / deploy)
# ---------------------------------------------------------------------------


def test_build_public_layer_remove_avaliador_de_sensorial():
    fact = {
        "sensorial": pd.DataFrame([
            {"ru": "P1", "data": pd.Timestamp("2026-01-05"), "avaliador": "Fulana da Silva", "global": 4.0}
        ]),
        "detalhe": pd.DataFrame([{"ru": "P1", "comensais_real": 100}]),
    }
    public = build_public_layer(fact)
    assert "avaliador" not in public["sensorial"].columns
    assert "Fulana da Silva" not in public["sensorial"].to_string()


def test_build_public_layer_preserva_grao_e_demais_colunas():
    """A camada pública não deve mudar o número de linhas nem os valores das
    métricas — só remove a(s) coluna(s) de PII (ver PII_COLUMNS_BY_FACT)."""
    fact = {
        "sensorial": pd.DataFrame([
            {"ru": "P1", "avaliador": "A", "global": 4.0},
            {"ru": "P1", "avaliador": "B", "global": 2.0},
        ]),
    }
    public = build_public_layer(fact)
    assert len(public["sensorial"]) == len(fact["sensorial"])
    assert public["sensorial"]["global"].tolist() == fact["sensorial"]["global"].tolist()


def test_build_public_layer_nao_altera_tabelas_sem_pii_cadastrada():
    fact = {"detalhe": pd.DataFrame([{"ru": "P1", "comensais_real": 100, "peso_bruto": 50.0}])}
    public = build_public_layer(fact)
    pd.testing.assert_frame_equal(public["detalhe"], fact["detalhe"])


def test_pii_columns_by_fact_so_lista_sensorial():
    """Documenta a auditoria: das 5 tabelas fato do MVP, só `sensorial` tem
    coluna de PII (nome de avaliador) — ver docs/auditoria_dados.md."""
    assert set(PII_COLUMNS_BY_FACT.keys()) == {"sensorial"}
    assert PII_COLUMNS_BY_FACT["sensorial"] == ["avaliador"]


# ---------------------------------------------------------------------------
# max_data_realizada — "dados atualizados até" ignora linhas de calendário
# futuro pré-preenchidas (achado desta revisão)
# ---------------------------------------------------------------------------


def test_is_realizado_detalhe_marca_peso_liq_zero_como_nao_realizado():
    df = pd.DataFrame({"peso_liq": [50.0, 0.0, None, 10.5]})
    assert list(is_realizado_detalhe(df)) == [True, False, False, True]


def test_is_realizado_isc_marca_todas_contagens_nulas_como_nao_realizado():
    df = pd.DataFrame({
        "otimo": [10, None, None],
        "regular": [2, None, 5],
        "ruim": [1, None, None],
    })
    assert list(is_realizado_isc(df)) == [True, False, True]


def test_max_data_realizada_ignora_linhas_de_planejamento_futuro_em_detalhe():
    """Reproduz o achado real: linhas com data futura e peso_liq=0 (template
    de calendário) não devem definir 'dados atualizados até'."""
    fact = {
        "detalhe": pd.DataFrame([
            {"data": pd.Timestamp("2026-09-02"), "peso_liq": 50.0},
            {"data": pd.Timestamp("2026-09-04"), "peso_liq": 0.0},  # placeholder futuro
            {"data": pd.Timestamp("2026-09-07"), "peso_liq": 0.0},  # placeholder futuro
        ]),
    }
    resultado = max_data_realizada(fact)
    assert resultado == pd.Timestamp("2026-09-02")


def test_max_data_realizada_ignora_linhas_de_planejamento_futuro_em_isc():
    fact = {
        "isc": pd.DataFrame([
            {"data": pd.Timestamp("2026-09-01"), "otimo": 20, "regular": 5, "ruim": 1},
            {"data": pd.Timestamp("2026-09-04"), "otimo": None, "regular": None, "ruim": None},  # placeholder
        ]),
    }
    resultado = max_data_realizada(fact)
    assert resultado == pd.Timestamp("2026-09-01")


def test_max_data_realizada_usa_max_simples_para_tabelas_sem_criterio_especial():
    fact = {
        "sensorial": pd.DataFrame([
            {"data": pd.Timestamp("2026-09-01"), "global": 4.0},
            {"data": pd.Timestamp("2026-09-02"), "global": None},  # sem criterio: entra no MAX mesmo assim
        ]),
    }
    resultado = max_data_realizada(fact)
    assert resultado == pd.Timestamp("2026-09-02")


def test_max_data_realizada_combina_o_maximo_entre_varias_tabelas():
    fact = {
        "detalhe": pd.DataFrame([
            {"data": pd.Timestamp("2026-09-02"), "peso_liq": 50.0},
            {"data": pd.Timestamp("2026-09-04"), "peso_liq": 0.0},
        ]),
        "isc": pd.DataFrame([
            {"data": pd.Timestamp("2026-09-03"), "otimo": 10, "regular": 1, "ruim": 0},
        ]),
    }
    resultado = max_data_realizada(fact)
    assert resultado == pd.Timestamp("2026-09-03")  # isc realizado supera detalhe realizado


def test_max_data_realizada_retorna_none_sem_nenhum_dado():
    resultado = max_data_realizada({"detalhe": pd.DataFrame(columns=["data", "peso_liq"])})
    assert resultado is None
