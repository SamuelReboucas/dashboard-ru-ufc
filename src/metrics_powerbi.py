"""
Métricas dos indicadores "oficiais" definidos com a Nutrição, que hoje só
existiam no modelo Power BI (src/powerbi_export.py) — este módulo expõe as
mesmas fórmulas, já validadas, para uso no dashboard Streamlit.

Não reaproveita nem duplica lógica de limpeza: lê diretamente os CSVs de
data/powerbi/ (mesma fonte usada pelo Power BI), que já saem tratados do
pipeline (python -m src.pipeline). Nenhuma fórmula nova é inventada aqui —
tudo replica exatamente o que está documentado em docs/medidas_powerbi.md
e já foi testado em tests/test_powerbi_export.py.

Fórmulas replicadas (com a mesma ressalva de granularidade do Per Capita,
já resolvida via deduplicação por RU+Data+Refeição):
  Resto-Ingesta (kg)  = SUM(resto_ingesta_kg)
  % Resto-Ingesta      = SUM(resto_ingesta_kg) / SUM(quantidade_distribuida) * 100
  Per Capita           = SUM(consumo_real) * 1000 / SUM(comensais_real deduplicado)
  ISC Agregado         = (SUM(otimo)*10 + SUM(regular)*5 + SUM(ruim)*1) / SUM(total_respostas correto)
  % Conformidade       = conformes / avaliadas (nunca inclui SEM_MEDICAO/SEM_CLASSIFICACAO/MEDICAO_INVALIDA)
  % Cobertura          = avaliadas / válidas
"""
from __future__ import annotations

from datetime import date
import numpy as np
import pandas as pd


def apply_filters(
    df: pd.DataFrame,
    ru: list[str] | None = None,
    refeicao: list[str] | None = None,
    tipo_preparacao: list[str] | None = None,
    data_ini: date | None = None,
    data_fim: date | None = None,
) -> pd.DataFrame:
    """Mesmo padrão de filtro já usado em src/metrics.py, com o acréscimo
    de `tipo_preparacao` (novidade da camada Power BI)."""
    out = df
    if ru and "ru" in out.columns:
        out = out[out["ru"].isin(ru)]
    if refeicao and "refeicao" in out.columns:
        out = out[out["refeicao"].isin(refeicao)]
    if tipo_preparacao and "tipo_preparacao" in out.columns:
        out = out[out["tipo_preparacao"].isin(tipo_preparacao)]
    if data_ini is not None and "data" in out.columns:
        out = out[out["data"] >= pd.Timestamp(data_ini)]
    if data_fim is not None and "data" in out.columns:
        out = out[out["data"] <= pd.Timestamp(data_fim)]
    return out


# ---------------------------------------------------------------------------
# Resto-Ingesta (fact_producao)
# ---------------------------------------------------------------------------


def resto_ingesta(df_producao: pd.DataFrame, group_by: list[str] | None = None, **filtros) -> pd.DataFrame:
    """Resto-Ingesta oficial (kg) e % Resto-Ingesta, validados contra a
    regra confirmada com a Nutrição (ver docs/aderencia_orientacoes_gestao.md,
    seção 3-A). Diferente do `rejeito_total` do MVP original (que é proxy de
    perda de pré-preparo, peso_bruto-peso_liq) — este é o indicador oficial."""
    df = apply_filters(df_producao, **filtros)
    if group_by:
        g = df.groupby(group_by, dropna=False).agg(
            resto_ingesta_kg=("resto_ingesta_kg", "sum"),
            quantidade_distribuida=("quantidade_distribuida", "sum"),
        )
        g["pct_resto_ingesta"] = (g["resto_ingesta_kg"] / g["quantidade_distribuida"].replace(0, np.nan)) * 100
        return g.reset_index()
    resto = df["resto_ingesta_kg"].sum()
    dist = df["quantidade_distribuida"].sum()
    return pd.DataFrame({
        "resto_ingesta_kg": [resto],
        "quantidade_distribuida": [dist],
        "pct_resto_ingesta": [(resto / dist * 100) if dist else np.nan],
    })


# ---------------------------------------------------------------------------
# Per Capita (fact_producao) — com deduplicação de comensais_real
# ---------------------------------------------------------------------------


def per_capita_por_preparacao(df_producao: pd.DataFrame, n: int = 10, **filtros) -> pd.DataFrame:
    """Per Capita (g/comensal) por preparação específica, com a
    deduplicação de `comensais_real` por RU+Data+Refeição já validada em
    `src.powerbi_export.per_capita_agregado_por_preparacao` (mesma lógica,
    reaproveitada aqui). Nunca soma `comensais_real` direto por linha de
    preparação — isso inflaria o denominador pelo nº de pratos do dia."""
    df = apply_filters(df_producao, **filtros)

    def _calc(g: pd.DataFrame) -> pd.Series:
        consumo_total = g["consumo_real"].sum()
        comensais_dedup = g.drop_duplicates(subset=["ru", "data", "refeicao"])["comensais_real"]
        comensais_total = comensais_dedup.sum()
        per_capita = (consumo_total * 1000 / comensais_total) if comensais_total else np.nan
        return pd.Series({"per_capita_g_comensal": per_capita, "n_registros": len(g)})

    resultado = df.groupby(["tipo_preparacao", "preparacao"], dropna=False).apply(_calc).reset_index()
    resultado = resultado[resultado["n_registros"] >= 3]  # evita destacar 1 registro isolado
    return resultado.sort_values("per_capita_g_comensal", ascending=False).head(n)


def per_capita_por_tipo(df_producao: pd.DataFrame, **filtros) -> pd.DataFrame:
    """Mesma lógica, agrupando só por `tipo_preparacao` (visão mais geral,
    usada no card resumo)."""
    df = apply_filters(df_producao, **filtros)

    def _calc(g: pd.DataFrame) -> pd.Series:
        consumo_total = g["consumo_real"].sum()
        comensais_dedup = g.drop_duplicates(subset=["ru", "data", "refeicao"])["comensais_real"]
        comensais_total = comensais_dedup.sum()
        per_capita = (consumo_total * 1000 / comensais_total) if comensais_total else np.nan
        return pd.Series({"per_capita_g_comensal": per_capita})

    return df.groupby("tipo_preparacao", dropna=False).apply(_calc).reset_index()


# ---------------------------------------------------------------------------
# ISC Agregado (fact_satisfacao) — corrigido (achado da construção manual)
# ---------------------------------------------------------------------------


def isc_agregado(df_satisfacao: pd.DataFrame, group_by: list[str] | None = None, **filtros) -> pd.DataFrame:
    """ISC Agregado com a correção validada durante a construção manual do
    Power BI: o denominador é `Total Ótimo + Total Regular + Total Ruim`
    (recalculado a partir das próprias contagens), nunca `SUM(total_respostas)`
    — essa coluna pré-calculada fica nula em 26 linhas onde `otimo` tem
    valor real mas `regular`/`ruim` vieram vazios na fonte, o que subconta
    o denominador e infla o ISC (achado real: 9,63 em vez de 9,36).
    Ver docs/medidas_powerbi.md, seção "Satisfação / ISC"."""
    filtros_sem_tipo_prep = {k: v for k, v in filtros.items() if k != "tipo_preparacao"}
    df = apply_filters(df_satisfacao, **filtros_sem_tipo_prep)
    # tipo_preparacao é aplicado à parte pois pode estar ausente em parte
    # das linhas de satisfação (achado documentado) sem que isso invalide
    # a linha para os demais filtros
    if filtros.get("tipo_preparacao"):
        df = df[df["tipo_preparacao"].isin(filtros["tipo_preparacao"])]

    if group_by:
        g = df.groupby(group_by, dropna=False).agg(
            total_otimo=("otimo", "sum"),
            total_regular=("regular", "sum"),
            total_ruim=("ruim", "sum"),
        )
        g["total_respostas"] = g["total_otimo"] + g["total_regular"] + g["total_ruim"]
        g["isc_agregado"] = (
            g["total_otimo"] * 10 + g["total_regular"] * 5 + g["total_ruim"] * 1
        ) / g["total_respostas"].replace(0, np.nan)
        g["pct_otimo"] = g["total_otimo"] / g["total_respostas"].replace(0, np.nan)
        g["pct_regular"] = g["total_regular"] / g["total_respostas"].replace(0, np.nan)
        g["pct_ruim"] = g["total_ruim"] / g["total_respostas"].replace(0, np.nan)
        return g.reset_index()

    otimo, regular, ruim = df["otimo"].sum(), df["regular"].sum(), df["ruim"].sum()
    total = otimo + regular + ruim
    isc = (otimo * 10 + regular * 5 + ruim * 1) / total if total else np.nan
    return pd.DataFrame({
        "total_otimo": [otimo], "total_regular": [regular], "total_ruim": [ruim],
        "total_respostas": [total], "isc_agregado": [isc],
        "pct_otimo": [otimo / total if total else np.nan],
        "pct_regular": [regular / total if total else np.nan],
        "pct_ruim": [ruim / total if total else np.nan],
    })


# ---------------------------------------------------------------------------
# Conformidade Térmica (fact_temperatura)
# ---------------------------------------------------------------------------


def conformidade_termica(df_temperatura: pd.DataFrame, group_by: list[str] | None = None, **filtros) -> pd.DataFrame:
    """% Conformidade (só entre medições avaliadas: CONFORME/NAO_CONFORME)
    e % Cobertura da Classificação (avaliadas / válidas). Nunca inclui
    SEM_MEDICAO, SEM_CLASSIFICACAO nem MEDICAO_INVALIDA no denominador de
    conformidade — regra oficial da Nutrição, ver docs/medidas_powerbi.md."""
    df = apply_filters(df_temperatura, **filtros)

    def _calc(g: pd.DataFrame) -> pd.Series:
        validas = (g["temperatura_valida"] == True).sum()  # noqa: E712
        avaliadas = g["status_temperatura"].isin(["CONFORME", "NAO_CONFORME"]).sum()
        conformes = (g["status_temperatura"] == "CONFORME").sum()
        fora_padrao = (g["status_temperatura"] == "NAO_CONFORME").sum()
        return pd.Series({
            "medicoes_validas": validas,
            "medicoes_avaliadas": avaliadas,
            "medicoes_conformes": conformes,
            "medicoes_fora_padrao": fora_padrao,
            "pct_conformidade": (conformes / avaliadas) if avaliadas else np.nan,
            "pct_cobertura": (avaliadas / validas) if validas else np.nan,
        })

    if group_by:
        return df.groupby(group_by, dropna=False).apply(_calc).reset_index()
    return _calc(df).to_frame().T.reset_index(drop=True)


def distribuicao_status_temperatura(df_temperatura: pd.DataFrame, **filtros) -> pd.DataFrame:
    """Contagem por status (para gráfico de barras/pizza)."""
    df = apply_filters(df_temperatura, **filtros)
    return df["status_temperatura"].value_counts().rename_axis("status").reset_index(name="quantidade")
