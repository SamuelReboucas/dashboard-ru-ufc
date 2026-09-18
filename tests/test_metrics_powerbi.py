"""Testes de src/metrics_powerbi.py — mesma rigor de src/metrics.py."""
import numpy as np
import pandas as pd
import pytest

from src.metrics_powerbi import (
    apply_filters,
    resto_ingesta,
    per_capita_por_preparacao,
    per_capita_por_tipo,
    isc_agregado,
    conformidade_termica,
    distribuicao_status_temperatura,
)


@pytest.fixture
def fact_producao():
    return pd.DataFrame([
        {"ru": "P1", "data": pd.Timestamp("2026-01-05"), "refeicao": "Almoço",
         "tipo_preparacao": "PB", "preparacao": "Frango",
         "resto_ingesta_kg": 2.0, "quantidade_distribuida": 85.0,
         "consumo_real": 83.0, "comensais_real": 300},
        {"ru": "P1", "data": pd.Timestamp("2026-01-05"), "refeicao": "Almoço",
         "tipo_preparacao": "Salada", "preparacao": "Alface",
         "resto_ingesta_kg": 0.5, "quantidade_distribuida": 17.0,
         "consumo_real": 16.5, "comensais_real": 300},
        {"ru": "P1", "data": pd.Timestamp("2026-01-06"), "refeicao": "Almoço",
         "tipo_preparacao": "PB", "preparacao": "Carne",
         "resto_ingesta_kg": 4.0, "quantidade_distribuida": 72.0,
         "consumo_real": 68.0, "comensais_real": 200},
        {"ru": "B", "data": pd.Timestamp("2026-01-05"), "refeicao": "Jantar",
         "tipo_preparacao": "PB", "preparacao": "Frango",
         "resto_ingesta_kg": 3.0, "quantidade_distribuida": 90.0,
         "consumo_real": 87.0, "comensais_real": 400},
    ])


@pytest.fixture
def fact_satisfacao():
    return pd.DataFrame([
        {"ru": "P1", "data": pd.Timestamp("2026-01-05"), "refeicao": "Almoço",
         "tipo_preparacao": "PB", "otimo": 100, "regular": 20, "ruim": 5},
        {"ru": "P1", "data": pd.Timestamp("2026-01-06"), "refeicao": "Almoço",
         "tipo_preparacao": "PB", "otimo": 50, "regular": None, "ruim": None},  # linha parcial (achado real)
        {"ru": "B", "data": pd.Timestamp("2026-01-05"), "refeicao": "Jantar",
         "tipo_preparacao": "Salada", "otimo": 30, "regular": 8, "ruim": 2},
    ])


@pytest.fixture
def fact_temperatura():
    return pd.DataFrame([
        {"ru": "P1", "data": pd.Timestamp("2026-01-05"), "refeicao": "Almoço",
         "temperatura_valida": True, "status_temperatura": "CONFORME"},
        {"ru": "P1", "data": pd.Timestamp("2026-01-05"), "refeicao": "Almoço",
         "temperatura_valida": True, "status_temperatura": "NAO_CONFORME"},
        {"ru": "P1", "data": pd.Timestamp("2026-01-06"), "refeicao": "Almoço",
         "temperatura_valida": True, "status_temperatura": "SEM_CLASSIFICACAO"},
        {"ru": "B", "data": pd.Timestamp("2026-01-05"), "refeicao": "Jantar",
         "temperatura_valida": False, "status_temperatura": "SEM_MEDICAO"},
        {"ru": "B", "data": pd.Timestamp("2026-01-06"), "refeicao": "Jantar",
         "temperatura_valida": True, "status_temperatura": "MEDICAO_INVALIDA"},
    ])


# ---------------------------------------------------------------------------
# Resto-Ingesta
# ---------------------------------------------------------------------------


def test_resto_ingesta_total(fact_producao):
    r = resto_ingesta(fact_producao)
    assert r["resto_ingesta_kg"].iloc[0] == pytest.approx(2.0 + 0.5 + 4.0 + 3.0)
    assert r["quantidade_distribuida"].iloc[0] == pytest.approx(85 + 17 + 72 + 90)


def test_resto_ingesta_pct_e_razao_de_somas(fact_producao):
    r = resto_ingesta(fact_producao, ru=["P1"])
    resto = 2.0 + 0.5 + 4.0
    dist = 85 + 17 + 72
    assert r["pct_resto_ingesta"].iloc[0] == pytest.approx(resto / dist * 100)


def test_resto_ingesta_agrupado_por_ru(fact_producao):
    r = resto_ingesta(fact_producao, group_by=["ru"]).set_index("ru")
    assert r.loc["B", "resto_ingesta_kg"] == pytest.approx(3.0)


# ---------------------------------------------------------------------------
# Per Capita — dedup obrigatória
# ---------------------------------------------------------------------------


def test_per_capita_por_tipo_deduplica_comensais(fact_producao):
    """PB tem 2 linhas em datas diferentes (Frango 05/01, Carne 06/01) —
    comensais deve somar 300+200=500, não inflar por repetição de linha."""
    r = per_capita_por_tipo(fact_producao, ru=["P1"], refeicao=["Almoço"])
    pb = r[r["tipo_preparacao"] == "PB"].iloc[0]
    esperado = (83.0 + 68.0) * 1000 / (300 + 200)
    assert pb["per_capita_g_comensal"] == pytest.approx(esperado)


def test_per_capita_por_preparacao_exige_minimo_3_registros(fact_producao):
    r = per_capita_por_preparacao(fact_producao, n=10)
    # nenhuma preparação do fixture tem 3+ registros -> resultado vazio
    assert len(r) == 0


def test_per_capita_por_preparacao_com_dados_suficientes():
    linhas = []
    for i, (data, consumo, comensais) in enumerate([
        ("2026-01-05", 80.0, 300), ("2026-01-06", 80.0, 300), ("2026-01-07", 80.0, 300)
    ]):
        linhas.append({"ru": "P1", "data": pd.Timestamp(data), "refeicao": "Almoço",
                        "tipo_preparacao": "PB", "preparacao": "Frango",
                        "consumo_real": consumo, "comensais_real": comensais})
    df = pd.DataFrame(linhas)
    r = per_capita_por_preparacao(df, n=5)
    assert len(r) == 1
    assert r.iloc[0]["per_capita_g_comensal"] == pytest.approx(80.0 * 1000 / 300)


# ---------------------------------------------------------------------------
# ISC Agregado — corrigido
# ---------------------------------------------------------------------------


def test_isc_agregado_usa_denominador_recalculado_nao_coluna_pronta(fact_satisfacao):
    """A linha parcial (otimo=50, regular/ruim nulos) deve ENTRAR no
    numerador (otimo) e no denominador (soma das 3 colunas, tratando nulo
    como 0) — não pode ficar de fora do denominador como no bug original."""
    r = isc_agregado(fact_satisfacao, ru=["P1"])
    otimo_total = 100 + 50
    regular_total = 20  # (regular nulo na 2a linha -> soma ignora, não conta como erro)
    ruim_total = 5
    total = otimo_total + regular_total + ruim_total
    esperado = (otimo_total * 10 + regular_total * 5 + ruim_total * 1) / total
    assert r["isc_agregado"].iloc[0] == pytest.approx(esperado)
    assert r["total_respostas"].iloc[0] == total


def test_isc_agregado_nao_e_igual_a_average_isc_linha(fact_satisfacao):
    """Trava a regressão do bug real: garante que o cálculo não é uma
    média simples de um campo por linha, e sim razão de somas."""
    r = isc_agregado(fact_satisfacao, ru=["P1"])
    isc_por_linha = [(100*10+20*5+5*1)/125, (50*10)/50]  # médias por linha, se calculadas erradas
    media_ingenua = sum(isc_por_linha) / len(isc_por_linha)
    assert r["isc_agregado"].iloc[0] != pytest.approx(media_ingenua)


def test_isc_distribuicao_percentuais_somam_100(fact_satisfacao):
    r = isc_agregado(fact_satisfacao)
    soma_pct = r["pct_otimo"].iloc[0] + r["pct_regular"].iloc[0] + r["pct_ruim"].iloc[0]
    assert soma_pct == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# Conformidade Térmica
# ---------------------------------------------------------------------------


def test_conformidade_termica_denominador_correto(fact_temperatura):
    """5 linhas: 1 CONFORME, 1 NAO_CONFORME, 1 SEM_CLASSIFICACAO,
    1 SEM_MEDICAO, 1 MEDICAO_INVALIDA. Avaliadas = 2 (só conforme+não
    conforme). % Conformidade = 1/2 = 50%, nunca 1/5."""
    r = conformidade_termica(fact_temperatura)
    assert r["medicoes_avaliadas"].iloc[0] == 2
    assert r["medicoes_conformes"].iloc[0] == 1
    assert r["pct_conformidade"].iloc[0] == pytest.approx(0.5)


def test_conformidade_termica_cobertura(fact_temperatura):
    """Válidas = 4 (todas exceto a SEM_MEDICAO); avaliadas = 2.
    Cobertura = 2/4 = 50%."""
    r = conformidade_termica(fact_temperatura)
    assert r["medicoes_validas"].iloc[0] == 4
    assert r["pct_cobertura"].iloc[0] == pytest.approx(0.5)


def test_conformidade_termica_medicao_invalida_nunca_conta_como_nao_conforme(fact_temperatura):
    r = conformidade_termica(fact_temperatura)
    # se MEDICAO_INVALIDA contasse como não-conforme, teria 2 não-conformes, não 1
    assert r["medicoes_fora_padrao"].iloc[0] == 1


def test_distribuicao_status_temperatura(fact_temperatura):
    r = distribuicao_status_temperatura(fact_temperatura)
    assert set(r["status"]) == {"CONFORME", "NAO_CONFORME", "SEM_CLASSIFICACAO", "SEM_MEDICAO", "MEDICAO_INVALIDA"}


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v"]))
