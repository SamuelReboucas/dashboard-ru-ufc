"""
Testes de src/metrics.py com dados sintéticos representativos do formato
real das tabelas fato (após transform.py).

Cobre especificamente a regressão encontrada no smoke test: `comensais_real`
vem repetido em toda linha de preparação da mesma refeição, e somar direto
(sem colapsar ao grão de refeição) inflava "refeições realizadas" em ~11x.
"""
import numpy as np
import pandas as pd
import pytest

from src import metrics


# ---------------------------------------------------------------------------
# Fixture: tabela de detalhe sintética, no formato real (grão = preparação)
# ---------------------------------------------------------------------------


@pytest.fixture
def fact_detalhe():
    """2 refeições (P1/Almoço/05-01 e P1/Almoço/06-01), cada uma com 3 pratos.
    `comensais_real` é intencionalmente igual entre os pratos da mesma
    refeição (replica o dado real); `comensais` varia por prato."""
    rows = []
    for data, comensais_real, previsoes, sobras_limpa, sobras_suja, pesos_bruto, pesos_liq in [
        ("2026-01-05", 300, [100, 150, 90], [5, 4, 3], [1, 2, 1], [50, 60, 40], [45, 55, 38]),
        ("2026-01-06", 200, [80, 120, 70], [2, 3, 2], [0, 1, 0], [40, 50, 30], [38, 47, 29]),
    ]:
        for i, prep in enumerate(["PB", "PV", "VEG"]):
            rows.append({
                "ru": "P1",
                "data": pd.Timestamp(data),
                "refeicao": "Almoço",
                "prep": prep,
                "comensais": previsoes[i],
                "comensais_real": comensais_real,
                "sobra_limpa": sobras_limpa[i],
                "sobra_suja": sobras_suja[i],
                "peso_bruto": pesos_bruto[i],
                "peso_liq": pesos_liq[i],
            })
    # 1 refeição de outro RU, para testar group_by/filtros
    rows.append({
        "ru": "B", "data": pd.Timestamp("2026-01-05"), "refeicao": "Jantar", "prep": "PB",
        "comensais": 50, "comensais_real": 400, "sobra_limpa": 10, "sobra_suja": 5,
        "peso_bruto": 100, "peso_liq": 90,
    })
    return pd.DataFrame(rows)


@pytest.fixture
def fact_sensorial():
    return pd.DataFrame([
        {"ru": "P1", "data": pd.Timestamp("2026-01-05"), "refeicao": "Almoço", "preparacao": "PB",
         "global": 4.0, "avaliador": "A"},
        {"ru": "P1", "data": pd.Timestamp("2026-01-05"), "refeicao": "Almoço", "preparacao": "PB",
         "global": 3.0, "avaliador": "B"},
        {"ru": "P1", "data": pd.Timestamp("2026-01-05"), "refeicao": "Almoço", "preparacao": "PB",
         "global": 5.0, "avaliador": "C"},
        {"ru": "P1", "data": pd.Timestamp("2026-01-06"), "refeicao": "Almoço", "preparacao": "Salada Ruim",
         "global": 1.0, "avaliador": "A"},
        {"ru": "P1", "data": pd.Timestamp("2026-01-06"), "refeicao": "Almoço", "preparacao": "Salada Ruim",
         "global": 1.0, "avaliador": "B"},
        {"ru": "P1", "data": pd.Timestamp("2026-01-06"), "refeicao": "Almoço", "preparacao": "Salada Ruim",
         "global": 1.0, "avaliador": "C"},
        # preparação com só 1 avaliação — não deve entrar no ranking (mínimo 3)
        {"ru": "P1", "data": pd.Timestamp("2026-01-06"), "refeicao": "Almoço", "preparacao": "Isolada",
         "global": 0.5, "avaliador": "A"},
    ])


@pytest.fixture
def fact_isc():
    return pd.DataFrame([
        {"ru": "P1", "data": pd.Timestamp("2026-01-05"), "refeicao": "Almoço", "isc": 8.0},
        {"ru": "P1", "data": pd.Timestamp("2026-01-06"), "refeicao": "Almoço", "isc": 6.0},
        {"ru": "B", "data": pd.Timestamp("2026-01-05"), "refeicao": "Jantar", "isc": 9.0},
    ])


@pytest.fixture
def fact_atendimentos():
    return pd.DataFrame([
        {"ru": "P1", "data": pd.Timestamp("2026-01-05"), "resolvido_flag": True},
        {"ru": "P1", "data": pd.Timestamp("2026-01-06"), "resolvido_flag": False},
        {"ru": "B", "data": pd.Timestamp("2026-01-05"), "resolvido_flag": True},
    ])


# ---------------------------------------------------------------------------
# Panorama
# ---------------------------------------------------------------------------


def test_refeicoes_realizadas_nao_infla_pelo_numero_de_pratos(fact_detalhe):
    """Regressão central do smoke test: sem colapsar ao grão de refeição, a
    soma de comensais_real ficava ~11x maior que o real."""
    result = metrics.refeicoes_realizadas(fact_detalhe, ru=["P1"], refeicao=["Almoço"])
    # 2 refeições de P1/Almoço: 300 (05/01) + 200 (06/01) = 500 — NÃO 300*3+200*3=1500
    assert result["refeicoes_realizadas"].iloc[0] == 500


def test_refeicoes_realizadas_filtra_por_ru(fact_detalhe):
    result = metrics.refeicoes_realizadas(fact_detalhe, ru=["B"])
    assert result["refeicoes_realizadas"].iloc[0] == 400


def test_refeicoes_realizadas_agrupa_por_ru(fact_detalhe):
    result = metrics.refeicoes_realizadas(fact_detalhe, group_by=["ru"])
    result = result.set_index("ru")
    assert result.loc["P1", "refeicoes_realizadas"] == 500
    assert result.loc["B", "refeicoes_realizadas"] == 400


def test_refeicoes_previstas_usa_maior_previsao_por_refeicao(fact_detalhe):
    """comensais_previsto = MAX(comensais) por refeição (proxy documentado em
    metrics._meal_level), não SUM — pratos são opções, não somam headcount."""
    result = metrics.refeicoes_previstas(fact_detalhe, ru=["P1"], refeicao=["Almoço"])
    # 05/01: max(100,150,90)=150 | 06/01: max(80,120,70)=120 -> soma=270
    assert result["refeicoes_previstas"].iloc[0] == 270


def test_pct_execucao_calcula_razao_real_sobre_previsto(fact_detalhe):
    result = metrics.pct_execucao(fact_detalhe, ru=["P1"], refeicao=["Almoço"])
    # real=500, previsto=270 -> 500/270
    assert result["pct_execucao"].iloc[0] == pytest.approx(500 / 270)


def test_pct_execucao_retorna_nan_quando_previsto_e_zero():
    df = pd.DataFrame([
        {"ru": "P1", "data": pd.Timestamp("2026-01-05"), "refeicao": "Almoço",
         "comensais": 0, "comensais_real": 100, "prep": "PB",
         "sobra_limpa": 0, "sobra_suja": 0, "peso_bruto": 0, "peso_liq": 0},
    ])
    result = metrics.pct_execucao(df)
    assert np.isnan(result["pct_execucao"].iloc[0])


def test_evolucao_refeicoes_serie_diaria_no_grao_correto(fact_detalhe):
    result = metrics.evolucao_refeicoes(fact_detalhe, ru=["P1"], refeicao=["Almoço"])
    result = result.set_index("data")["comensais_real"]
    assert result.loc[pd.Timestamp("2026-01-05")] == 300
    assert result.loc[pd.Timestamp("2026-01-06")] == 200


def test_apply_filters_por_periodo(fact_detalhe):
    result = metrics.apply_filters(fact_detalhe, data_ini=pd.Timestamp("2026-01-06").date())
    assert result["data"].min() == pd.Timestamp("2026-01-06")


# ---------------------------------------------------------------------------
# Desperdício
# ---------------------------------------------------------------------------


def test_desperdicio_per_capita(fact_detalhe):
    """(sobra_limpa+sobra_suja) somadas nos pratos / comensais_real da refeição."""
    result = metrics.desperdicio_per_capita(fact_detalhe, ru=["P1"], refeicao=["Almoço"])
    sobra_total = (5 + 4 + 3 + 1 + 2 + 1) + (2 + 3 + 2 + 0 + 1 + 0)  # limpa+suja das 2 refeições
    comensais_real_total = 300 + 200
    assert result["desperdicio_per_capita"].iloc[0] == pytest.approx(sobra_total / comensais_real_total)


def test_rejeito_total_soma_peso_bruto_menos_liquido(fact_detalhe):
    result = metrics.rejeito_total(fact_detalhe, ru=["P1"], refeicao=["Almoço"])
    bruto = 50 + 60 + 40 + 40 + 50 + 30
    liq = 45 + 55 + 38 + 38 + 47 + 29
    assert result["rejeito_total"].iloc[0] == pytest.approx(bruto - liq)


def test_indice_aceitabilidade_formula(fact_detalhe):
    result = metrics.indice_aceitabilidade(fact_detalhe, ru=["P1"], refeicao=["Almoço"])
    sobra_suja = (1 + 2 + 1) + (0 + 1 + 0)
    peso_liq = (45 + 55 + 38) + (38 + 47 + 29)
    esperado = 1 - (sobra_suja / peso_liq)
    assert result["indice_aceitabilidade"].iloc[0] == pytest.approx(esperado)


def test_desperdicio_per_capita_agrupado_por_ru(fact_detalhe):
    result = metrics.desperdicio_per_capita(fact_detalhe, group_by=["ru"]).set_index("ru")
    sobra_b = 10 + 5
    assert result.loc["B", "desperdicio_per_capita"] == pytest.approx(sobra_b / 400)


# ---------------------------------------------------------------------------
# Qualidade / satisfação
# ---------------------------------------------------------------------------


def test_avaliacao_sensorial_media(fact_sensorial):
    result = metrics.avaliacao_sensorial_media(fact_sensorial, ru=["P1"], data_ini=None, data_fim=None)
    # média de todas as notas do fixture (7 avaliações)
    esperado = fact_sensorial["global"].mean()
    assert result["avaliacao_sensorial_media"].iloc[0] == pytest.approx(esperado)


def test_isc_medio(fact_isc):
    result = metrics.isc_medio(fact_isc, ru=["P1"])
    assert result["isc_medio"].iloc[0] == pytest.approx((8.0 + 6.0) / 2)


def test_isc_medio_agrupado_por_ru(fact_isc):
    result = metrics.isc_medio(fact_isc, group_by=["ru"]).set_index("ru")
    assert result.loc["B", "isc_medio"] == pytest.approx(9.0)


def test_top_piores_preparacoes_exige_minimo_3_avaliacoes(fact_sensorial):
    result = metrics.top_piores_preparacoes(fact_sensorial, n=5)
    # "Isolada" tem só 1 avaliação e não deve aparecer no ranking
    assert "Isolada" not in result["preparacao"].values
    assert result.iloc[0]["preparacao"] == "Salada Ruim"  # pior média (1.0)


def test_top_piores_preparacoes_ordena_ascendente(fact_sensorial):
    result = metrics.top_piores_preparacoes(fact_sensorial, n=5)
    notas = result["nota_media"].tolist()
    assert notas == sorted(notas)


# ---------------------------------------------------------------------------
# Gestão
# ---------------------------------------------------------------------------


def test_atendimentos_resolvidos_percentual(fact_atendimentos):
    result = metrics.atendimentos_resolvidos(fact_atendimentos)
    assert result["total"].iloc[0] == 3
    assert result["resolvidos"].iloc[0] == 2
    assert result["pct_resolvido"].iloc[0] == pytest.approx(2 / 3)


def test_atendimentos_resolvidos_filtra_por_ru(fact_atendimentos):
    result = metrics.atendimentos_resolvidos(fact_atendimentos, ru=["P1"])
    assert result["total"].iloc[0] == 2
    assert result["resolvidos"].iloc[0] == 1


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v"]))
