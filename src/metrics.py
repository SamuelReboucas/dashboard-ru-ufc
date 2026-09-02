"""
Funções de indicador (KPI) do MVP do dashboard RU.

Cada função:
  - recebe uma tabela fato (já limpa por src/transform.py) e filtros opcionais;
  - documenta no docstring: definição, fórmula, fonte, campos e filtros;
  - devolve um pandas.DataFrame agregado (nunca um número "solto" sem contexto),
    para poder alimentar tanto um card quanto um gráfico.

Ver docs/indicadores.md para a versão narrativa (não técnica) de cada KPI.
"""
from __future__ import annotations

from datetime import date
import pandas as pd
import numpy as np


# ---------------------------------------------------------------------------
# Filtro genérico — usado por todas as métricas
# ---------------------------------------------------------------------------


def apply_filters(
    df: pd.DataFrame,
    ru: list[str] | None = None,
    refeicao: list[str] | None = None,
    data_ini: date | None = None,
    data_fim: date | None = None,
) -> pd.DataFrame:
    """Filtra por RU, tipo de refeição e período. `ru`/`refeicao` aceitam
    listas (multi-seleção do dashboard); None = sem filtro."""
    out = df
    if ru and "ru" in out.columns:
        out = out[out["ru"].isin(ru)]
    if refeicao and "refeicao" in out.columns:
        out = out[out["refeicao"].isin(refeicao)]
    if data_ini is not None and "data" in out.columns:
        out = out[out["data"] >= pd.Timestamp(data_ini)]
    if data_fim is not None and "data" in out.columns:
        out = out[out["data"] <= pd.Timestamp(data_fim)]
    return out


def _groupby_or_total(df: pd.DataFrame, group_by: list[str] | None) -> pd.core.groupby.DataFrameGroupBy | None:
    if not group_by:
        return None
    return df.groupby(group_by, dropna=False)


def _meal_level(df_detalhe: pd.DataFrame) -> pd.DataFrame:
    """Colapsa a tabela de detalhe (grão = preparação) para o grão de
    refeição (RU + data + refeição).

    ACHADO DO SMOKE TEST (ver docs/implementacao_mvp.md): `comensais_real`
    vem **repetido em todas as linhas de preparação da mesma refeição**
    (é uma contagem de cabeça única por refeição, não por prato). Somar essa
    coluna direto na tabela de detalhe multiplica o resultado pelo número de
    pratos do dia — por isso todo indicador de "refeições" precisa passar
    por este colapso antes de agregar.

    `comensais` (previsto), ao contrário, varia por prato (é uma previsão de
    quantas pessoas escolheriam aquele prato específico, não um total da
    refeição). Não existe, nas abas de detalhe, um campo de "previsto total
    da refeição" equivalente ao `comensais_real`. Usamos o MAIOR valor de
    `comensais` entre os pratos daquela refeição como proxy do previsto total
    (tipicamente a proteína principal, que é o melhor preditor do total de
    comensais). Isso é uma aproximação documentada, não um valor exato.
    """
    return (
        df_detalhe.groupby(["ru", "data", "refeicao"], dropna=False)
        .agg(comensais_real=("comensais_real", "max"), comensais_previsto=("comensais", "max"))
        .reset_index()
    )


# ---------------------------------------------------------------------------
# A. Panorama
# ---------------------------------------------------------------------------


def refeicoes_realizadas(df_detalhe: pd.DataFrame, group_by: list[str] | None = None, **filtros) -> pd.DataFrame:
    """Refeições realizadas (nº de comensais atendidos).

    Fórmula: SUM(comensais_real), calculado no grão de REFEIÇÃO (RU+data+
    refeição) — ver `_meal_level`. `comensais_real` chega duplicado em todas
    as linhas de preparação da mesma refeição; somar sem colapsar antes
    infla o resultado pelo nº de pratos do dia.
    Fonte: fact_detalhe (P1D/P2D/BD/LD/PO2), campo `comensais_real`
    Filtros: ru, refeicao, data_ini, data_fim
    """
    df = apply_filters(df_detalhe, **filtros)
    meal = _meal_level(df)
    group_cols = [c for c in (group_by or []) if c in meal.columns]
    if group_cols:
        return meal.groupby(group_cols, dropna=False)["comensais_real"].sum().reset_index(
            name="refeicoes_realizadas"
        )
    return pd.DataFrame({"refeicoes_realizadas": [meal["comensais_real"].sum()]})


def refeicoes_previstas(df_detalhe: pd.DataFrame, group_by: list[str] | None = None, **filtros) -> pd.DataFrame:
    """Refeições previstas (estimativa de comensais).

    Fórmula: SUM(comensais_previsto), no grão de refeição — `comensais_previsto`
    é o MAIOR valor de `comensais` entre os pratos daquela refeição (proxy;
    ver docstring de `_meal_level` para a limitação completa).
    Fonte: fact_detalhe, campo `comensais`
    Filtros: ru, refeicao, data_ini, data_fim
    """
    df = apply_filters(df_detalhe, **filtros)
    meal = _meal_level(df)
    group_cols = [c for c in (group_by or []) if c in meal.columns]
    if group_cols:
        return meal.groupby(group_cols, dropna=False)["comensais_previsto"].sum().reset_index(
            name="refeicoes_previstas"
        )
    return pd.DataFrame({"refeicoes_previstas": [meal["comensais_previsto"].sum()]})


def pct_execucao(df_detalhe: pd.DataFrame, group_by: list[str] | None = None, **filtros) -> pd.DataFrame:
    """Percentual de execução (Realizado / Previsto).

    Fórmula: SUM(comensais_real) / SUM(comensais_previsto), no grão de
    refeição (ver `_meal_level`).
    Fonte: fact_detalhe, campos `comensais_real` e `comensais`
    Filtros: ru, refeicao, data_ini, data_fim
    Premissa: quando SUM(comensais_previsto) = 0 o resultado é NaN (evita
    divisão por zero); o dashboard deve exibir "sem dado" nesse caso.
    LIMITAÇÃO: `comensais_previsto` é uma aproximação (maior previsão de
    prato da refeição), não um "previsto total" oficial — tratar como
    indicador direcional, não como número de precisão orçamentária.
    """
    df = apply_filters(df_detalhe, **filtros)
    meal = _meal_level(df)
    group_cols = [c for c in (group_by or []) if c in meal.columns]
    if group_cols:
        g = meal.groupby(group_cols, dropna=False).agg(
            comensais_real=("comensais_real", "sum"), comensais_previsto=("comensais_previsto", "sum")
        )
        g["pct_execucao"] = g["comensais_real"] / g["comensais_previsto"].replace(0, np.nan)
        return g.reset_index()
    real = meal["comensais_real"].sum()
    prev = meal["comensais_previsto"].sum()
    return pd.DataFrame({"pct_execucao": [real / prev if prev else np.nan]})


def evolucao_refeicoes(df_detalhe: pd.DataFrame, freq: str = "D", **filtros) -> pd.DataFrame:
    """Série temporal de refeições realizadas.

    Fórmula: SUM(comensais_real) agrupado por período (`freq`; padrão diário,
    aceita códigos de frequência do pandas, ex.: "D", "W", "ME" para mensal),
    calculado no grão de refeição (ver `_meal_level`).
    Fonte: fact_detalhe
    Filtros: ru, refeicao, data_ini, data_fim
    """
    df = apply_filters(df_detalhe, **filtros)
    meal = _meal_level(df)
    serie = meal.set_index("data").resample(freq)["comensais_real"].sum()
    return serie.reset_index()


# ---------------------------------------------------------------------------
# B. Desperdício e eficiência
# ---------------------------------------------------------------------------


def rejeito_total(df_detalhe: pd.DataFrame, group_by: list[str] | None = None, **filtros) -> pd.DataFrame:
    """Rejeito estimado (peso não aproveitado na preparação).

    Fórmula: SUM(peso_bruto - peso_liq)
    Fonte: fact_detalhe, campos `peso_bruto` (peso recebido) e `peso_liq`
    (peso líquido preparado/servido)
    Filtros: ru, refeicao, data_ini, data_fim
    LIMITAÇÃO DOCUMENTADA: as abas de detalhe não têm uma coluna explícita
    "Rejeito" (essa existe só nas abas consolidadas P1/P2/B/L/PO, descartadas
    por alta taxa de erro — ver docs/auditoria_dados.md). Usamos
    peso_bruto - peso_liq como proxy. Validar com a nutricionista do RU antes
    de publicar externamente.
    """
    df = apply_filters(df_detalhe, **filtros)
    df = df.assign(rejeito=df["peso_bruto"] - df["peso_liq"])
    if group_by:
        return df.groupby(group_by, dropna=False)["rejeito"].sum().reset_index(name="rejeito_total")
    return pd.DataFrame({"rejeito_total": [df["rejeito"].sum()]})


def desperdicio_per_capita(df_detalhe: pd.DataFrame, group_by: list[str] | None = None, **filtros) -> pd.DataFrame:
    """Desperdício per capita (kg por comensal).

    Fórmula: SUM(sobra_limpa + sobra_suja) [grão de preparação, aditivo] /
    SUM(comensais_real) [grão de refeição — ver `_meal_level`]
    Fonte: fact_detalhe, campos `sobra_limpa`, `sobra_suja`, `comensais_real`
    Filtros: ru, refeicao, data_ini, data_fim
    LIMITAÇÃO: assim como em `refeicoes_realizadas`, `comensais_real` precisa
    ser colapsado ao grão de refeição antes de somar — do contrário o
    denominador é multiplicado pelo nº de pratos do dia (achado do smoke
    test, ver docs/implementacao_mvp.md). `sobra_limpa`/`sobra_suja` já são
    legitimamente por prato, então continuam somadas direto.
    """
    df = apply_filters(df_detalhe, **filtros)
    df = df.assign(sobra_total=df["sobra_limpa"].fillna(0) + df["sobra_suja"].fillna(0))
    meal = _meal_level(df)

    if group_by:
        sobra_g = df.groupby(group_by, dropna=False)["sobra_total"].sum()
        comensais_g = meal.groupby(group_by, dropna=False)["comensais_real"].sum()
        out = (sobra_g / comensais_g.replace(0, np.nan)).reset_index(name="desperdicio_per_capita")
        return out

    sobra_total = df["sobra_total"].sum()
    comensais_real_total = meal["comensais_real"].sum()
    return pd.DataFrame(
        {"desperdicio_per_capita": [sobra_total / comensais_real_total if comensais_real_total else np.nan]}
    )


def indice_aceitabilidade(df_detalhe: pd.DataFrame, group_by: list[str] | None = None, **filtros) -> pd.DataFrame:
    """Índice de Aceitabilidade / Resto-Ingesta (quanto do prato foi consumido).

    Fórmula: 1 - (SUM(sobra_suja) / SUM(peso_liq))
    Fonte: fact_detalhe, campos `sobra_suja` (resto no prato) e `peso_liq`
    (peso líquido servido)
    Filtros: ru, refeicao, data_ini, data_fim
    Premissa: quanto mais próximo de 1 (100%), menor o resto-ingesta (melhor
    aceitação do cardápio).
    """
    df = apply_filters(df_detalhe, **filtros)
    if group_by:
        g = df.groupby(group_by, dropna=False).agg(
            sobra_suja=("sobra_suja", "sum"), peso_liq=("peso_liq", "sum")
        )
        g["indice_aceitabilidade"] = 1 - (g["sobra_suja"] / g["peso_liq"].replace(0, np.nan))
        return g.reset_index()
    sobra_suja = df["sobra_suja"].sum()
    peso_liq = df["peso_liq"].sum()
    return pd.DataFrame(
        {"indice_aceitabilidade": [1 - (sobra_suja / peso_liq) if peso_liq else np.nan]}
    )


# ---------------------------------------------------------------------------
# C. Qualidade / satisfação
# ---------------------------------------------------------------------------


def avaliacao_sensorial_media(df_sensorial: pd.DataFrame, group_by: list[str] | None = None, **filtros) -> pd.DataFrame:
    """Nota sensorial média (escala 0-5).

    Fórmula: AVG(global)
    Fonte: fact_sensorial, campo `global` (nota consolidada aparência/textura/
    sabor/odor daquela avaliação)
    Filtros: ru, refeicao, data_ini, data_fim
    """
    df = apply_filters(df_sensorial, **filtros)
    if group_by:
        return df.groupby(group_by, dropna=False)["global"].mean().reset_index(
            name="avaliacao_sensorial_media"
        )
    return pd.DataFrame({"avaliacao_sensorial_media": [df["global"].mean()]})


def isc_medio(df_isc: pd.DataFrame, group_by: list[str] | None = None, **filtros) -> pd.DataFrame:
    """ISC médio (Índice de Satisfação do Cliente, escala 0-10).

    Fórmula: AVG(isc) — usamos o valor de ISC já calculado na fonte, por
    preparação/dia/RU (ver docs/fontes_oficiais.md); o pipeline não reconstrói
    a ponderação original, apenas agrega por média simples no período/recorte
    selecionado.
    Fonte: fact_isc (abas ISC alm / ISC jan / ISC Café), campo `isc`
    Filtros: ru, refeicao, data_ini, data_fim
    """
    df = apply_filters(df_isc, **filtros)
    if group_by:
        return df.groupby(group_by, dropna=False)["isc"].mean().reset_index(name="isc_medio")
    return pd.DataFrame({"isc_medio": [df["isc"].mean()]})


def top_piores_preparacoes(df_sensorial: pd.DataFrame, n: int = 5, **filtros) -> pd.DataFrame:
    """Ranking das preparações com pior avaliação sensorial no recorte.

    Fórmula: AVG(global) agrupado por preparação, ordenado ascendente
    Fonte: fact_sensorial, campos `preparacao`, `global`
    Filtros: ru, refeicao, data_ini, data_fim
    Premissa: preparações com menos de 3 avaliações no recorte são excluídas
    do ranking (evita destacar 1 avaliação isolada como "pior prato").
    """
    df = apply_filters(df_sensorial, **filtros)
    g = df.groupby("preparacao")["global"].agg(["mean", "count"]).reset_index()
    g = g[g["count"] >= 3]
    g = g.sort_values("mean", ascending=True).head(n)
    return g.rename(columns={"mean": "nota_media", "count": "n_avaliacoes"})


# ---------------------------------------------------------------------------
# D. Gestão
# ---------------------------------------------------------------------------


def atendimentos_resolvidos(df_atendimentos: pd.DataFrame, group_by: list[str] | None = None, **filtros) -> pd.DataFrame:
    """Atendimentos e percentual resolvido.

    Fórmula: COUNT(*) e SUM(resolvido_flag) / COUNT(*)
    Fonte: fact_gestao_atendimentos (agregado, sem dado pessoal — ver
    docs/auditoria_dados.md, seção "Dados que não podem ser publicados")
    Filtros: ru, data_ini, data_fim (não há filtro de refeição neste domínio)
    """
    df = apply_filters(df_atendimentos, **{k: v for k, v in filtros.items() if k != "refeicao"})
    if group_by:
        g = df.groupby(group_by, dropna=False).agg(
            total=("resolvido_flag", "size"), resolvidos=("resolvido_flag", "sum")
        )
        g["pct_resolvido"] = g["resolvidos"] / g["total"]
        return g.reset_index()
    total = len(df)
    resolvidos = df["resolvido_flag"].sum()
    return pd.DataFrame(
        {"total": [total], "resolvidos": [resolvidos], "pct_resolvido": [resolvidos / total if total else np.nan]}
    )


def manutencao_resolvida(df_manutencao: pd.DataFrame, group_by: list[str] | None = None, **filtros) -> pd.DataFrame:
    """Ordens de serviço (infraestrutura + TI) e percentual resolvido.

    Fórmula: COUNT(*) e SUM(resolvido_flag) / COUNT(*)
    Fonte: fact_gestao_manutencao (UFC-INFRA + OS - STI combinadas)
    Filtros: ru, data_ini, data_fim (campo adicional `tipo`: Infraestrutura/TI)
    """
    df = apply_filters(df_manutencao, **{k: v for k, v in filtros.items() if k != "refeicao"})
    cols = group_by or []
    if cols:
        g = df.groupby(cols, dropna=False).agg(
            total=("resolvido_flag", "size"), resolvidos=("resolvido_flag", "sum")
        )
        g["pct_resolvido"] = g["resolvidos"] / g["total"]
        return g.reset_index()
    total = len(df)
    resolvidos = df["resolvido_flag"].sum()
    return pd.DataFrame(
        {"total": [total], "resolvidos": [resolvidos], "pct_resolvido": [resolvidos / total if total else np.nan]}
    )
