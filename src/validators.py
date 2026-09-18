"""
Camada de validação de qualidade de dados.

Roda sobre os DataFrames "crus" (pré-filtro) vindos de src/extract.py e usa os
mesmos normalizadores de src/transform.py, para que o relatório de qualidade
reflita exatamente o que seria descartado/ajustado na etapa de transformação.

Saída: outputs/relatorio_qualidade.csv com colunas
regra | quantidade | severidade | fonte | exemplo
"""
from __future__ import annotations

import pandas as pd
import numpy as np

from src.config import load_mappings
from src.transform import (
    normalize_ru,
    normalize_refeicao,
    to_numeric_safe,
    to_date_safe,
)


def _out_of_valid_range_mask(date_dt: pd.Series) -> pd.Series:
    mp = load_mappings()
    lo = pd.Timestamp(mp["data_min_valida"])
    hi = pd.Timestamp(mp["data_max_valida"])
    return date_dt.notna() & ~date_dt.between(lo, hi)


def _row(regra: str, quantidade: int, severidade: str, fonte: str, exemplo) -> dict:
    return {
        "regra": regra,
        "quantidade": int(quantidade),
        "severidade": severidade,
        "fonte": fonte,
        "exemplo": "" if exemplo is None else str(exemplo)[:120],
    }


def _first_example(series: pd.Series, mask: pd.Series):
    vals = series[mask]
    return vals.iloc[0] if len(vals) else None


# ---------------------------------------------------------------------------
# Regras por fonte
# ---------------------------------------------------------------------------


def check_detalhe(df_raw: pd.DataFrame, fonte="detalhe (P1D/P2D/BD/LD/PO2)") -> list[dict]:
    rows = []
    df = df_raw.copy()

    data_dt = to_date_safe(df["data"])
    invalid_date_mask = data_dt.isna() & df["data"].notna()
    rows.append(_row("data_invalida", invalid_date_mask.sum(), "alta", fonte,
                      _first_example(df["data"], invalid_date_mask)))

    refeicao_norm = normalize_refeicao(df["refeicao"])
    invalid_meal_mask = refeicao_norm.isna() & df["refeicao"].notna()
    rows.append(_row("refeicao_desconhecida", invalid_meal_mask.sum(), "media", fonte,
                      _first_example(df["refeicao"], invalid_meal_mask)))

    fora_periodo_mask = _out_of_valid_range_mask(data_dt)
    rows.append(_row("data_fora_do_periodo_valido", fora_periodo_mask.sum(), "alta", fonte,
                      _first_example(df["data"], fora_periodo_mask)))

    key_cols = ["ru", "data", "refeicao", "prep"]
    dup_mask = df.duplicated(subset=key_cols, keep="first")
    rows.append(_row("duplicidade_linha", dup_mask.sum(), "baixa", fonte,
                      df.loc[dup_mask, key_cols].iloc[0].to_dict() if dup_mask.any() else None))

    comensais_real = to_numeric_safe(df["comensais_real"])
    peso_bruto = to_numeric_safe(df["peso_bruto"])
    sobra_limpa = to_numeric_safe(df["sobra_limpa"])
    sobra_suja = to_numeric_safe(df["sobra_suja"])

    neg_mask = (comensais_real < 0) | (peso_bruto < 0) | (sobra_limpa < 0) | (sobra_suja < 0)
    rows.append(_row("negativo_impossivel", neg_mask.fillna(False).sum(), "alta", fonte,
                      "valor negativo em comensais/peso/sobra"))

    zero_div_mask = (comensais_real == 0) & ((sobra_limpa > 0) | (sobra_suja > 0))
    rows.append(_row("divisao_por_zero_per_capita", zero_div_mask.fillna(False).sum(), "media", fonte,
                      "comensais_real=0 com sobra>0 (per capita indefinido)"))

    comensais = to_numeric_safe(df["comensais"])
    ratio = comensais_real / comensais.replace(0, np.nan)
    fora_intervalo_mask = (ratio < 0.1) | (ratio > 5)
    rows.append(_row("inconsistencia_previsto_realizado", fora_intervalo_mask.fillna(False).sum(),
                      "media", fonte,
                      "comensais_real muito distante de comensais previstos "
                      "(comparação feita no grão de preparação; ver limitação "
                      "documentada em docs/indicadores.md — comensais varia por prato, "
                      "comensais_real é único por refeição)"))

    ausencia_fonte_mask = df["prep"].isna() & (comensais_real.notna() & (comensais_real != 0))
    rows.append(_row("ausencia_de_fonte_prep", ausencia_fonte_mask.fillna(False).sum(), "media", fonte,
                      "linha com consumo real mas sem identificação da preparação"))

    return rows


def check_isc(df_raw: pd.DataFrame, fonte="ISC alm/jan/Café") -> list[dict]:
    rows = []
    if df_raw.empty:
        return rows
    df = df_raw.copy()

    data_dt = to_date_safe(df["data"])
    invalid_date_mask = data_dt.isna() & df["data"].notna()
    rows.append(_row("data_invalida", invalid_date_mask.sum(), "alta", fonte,
                      _first_example(df["data"], invalid_date_mask)))

    fora_periodo_mask = _out_of_valid_range_mask(data_dt)
    rows.append(_row("data_fora_do_periodo_valido", fora_periodo_mask.sum(), "alta", fonte,
                      _first_example(df["data"], fora_periodo_mask)))

    key_cols = ["ru", "data", "refeicao", "preparacao"]
    dup_mask = df.duplicated(subset=key_cols, keep="first")
    rows.append(_row("duplicidade_linha", dup_mask.sum(), "baixa", fonte, None))

    isc_num = to_numeric_safe(df["isc"])
    fora_intervalo_mask = (isc_num < 0) | (isc_num > 10)
    rows.append(_row("isc_fora_intervalo_0_10", fora_intervalo_mask.fillna(False).sum(), "media", fonte,
                      "valor de ISC fora da escala 0-10"))

    return rows


def check_sensorial(df_raw: pd.DataFrame, fonte="Av. Sensorial") -> list[dict]:
    rows = []
    df = df_raw.copy()

    data_dt = to_date_safe(df["data"])
    invalid_date_mask = data_dt.isna() & df["data"].notna()
    rows.append(_row("data_invalida", invalid_date_mask.sum(), "alta", fonte,
                      _first_example(df["data"], invalid_date_mask)))

    fora_periodo_mask = _out_of_valid_range_mask(data_dt)
    rows.append(_row("data_fora_do_periodo_valido", fora_periodo_mask.sum(), "alta", fonte,
                      _first_example(df["data"], fora_periodo_mask)))

    ru_norm = normalize_ru(df["refeitorio"])
    ru_desconhecido_mask = ru_norm.isna() & df["refeitorio"].notna()
    rows.append(_row("ru_desconhecido", ru_desconhecido_mask.sum(), "alta", fonte,
                      _first_example(df["refeitorio"], ru_desconhecido_mask)))

    key_cols = ["refeitorio", "data", "refeicao", "preparacao", "avaliador"]
    dup_mask = df.duplicated(subset=key_cols, keep="first")
    rows.append(_row("duplicidade_linha", dup_mask.sum(), "baixa", fonte, None))

    global_num = to_numeric_safe(df["global"])
    fora_intervalo_mask = (global_num < 0) | (global_num > 5)
    rows.append(_row("nota_sensorial_fora_intervalo_0_5", fora_intervalo_mask.fillna(False).sum(),
                      "media", fonte, "nota Global fora da escala 0-5"))

    return rows


def check_gestao(df_raw: pd.DataFrame, ru_col: str, fonte: str) -> list[dict]:
    rows = []
    df = df_raw.copy()
    if "data" not in df.columns or df.empty:
        return rows

    data_dt = to_date_safe(df["data"])
    invalid_date_mask = data_dt.isna() & df["data"].notna()
    rows.append(_row("data_invalida", invalid_date_mask.sum(), "alta", fonte,
                      _first_example(df["data"], invalid_date_mask)))

    fora_periodo_mask = _out_of_valid_range_mask(data_dt)
    rows.append(_row("data_fora_do_periodo_valido", fora_periodo_mask.sum(), "media", fonte,
                      _first_example(df["data"], fora_periodo_mask)))

    if ru_col in df.columns:
        ru_norm = normalize_ru(df[ru_col])
        ru_desconhecido_mask = ru_norm.isna() & df[ru_col].notna()
        rows.append(_row("ru_desconhecido", ru_desconhecido_mask.sum(), "media", fonte,
                          _first_example(df[ru_col], ru_desconhecido_mask)))

    dup_mask = df.duplicated(keep="first")
    rows.append(_row("duplicidade_linha", dup_mask.sum(), "baixa", fonte, None))

    return rows


def check_temperatura(df_raw: pd.DataFrame, fonte="detalhe (P1D/P2D/BD/LD/PO2)") -> list[dict]:
    """Achado desta etapa: 4 leituras de `Temp (°C)` fisicamente
    implausíveis (fora de -5°C a 100°C, ex.: "614°C"), quase certamente
    erro de digitação. Critério técnico: mesma faixa usada em
    `src/powerbi_export.TEMPERATURA_FISICA_MIN/MAX` — reaproveitada aqui,
    não duplicada, para que as duas checagens nunca divirjam."""
    from src.powerbi_export import clean_temperatura, is_temperatura_plausivel

    rows = []
    if "temp_c" not in df_raw.columns:
        return rows
    df = df_raw.copy()
    temp_limpa = df["temp_c"].map(clean_temperatura)
    implausivel_mask = temp_limpa.notna() & ~is_temperatura_plausivel(temp_limpa)
    exemplo = None
    if implausivel_mask.any():
        idx = df.loc[implausivel_mask].index[0]
        exemplo = (f"ru={df.at[idx,'ru']} data={df.at[idx,'data']} "
                   f"prep={df.at[idx,'prep']} valor_bruto={df.at[idx,'temp_c']} "
                   f"valor_limpo={temp_limpa.at[idx]}")
    rows.append(_row("temperatura_fora_da_faixa_fisica", implausivel_mask.sum(), "media", fonte, exemplo))
    return rows


def build_quality_report(raw: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows: list[dict] = []
    rows += check_detalhe(raw["detalhe"])
    rows += check_temperatura(raw["detalhe"])
    rows += check_isc(raw["isc"])
    rows += check_sensorial(raw["sensorial"])
    rows += check_gestao(raw["atendimentos"], ru_col="ru", fonte="Atendimentos Especializado")
    rows += check_gestao(raw["manutencao"], ru_col="ru_texto", fonte="UFC-INFRA / OS - STI")

    df = pd.DataFrame(rows, columns=["regra", "quantidade", "severidade", "fonte", "exemplo"])
    df = df.sort_values(["severidade", "quantidade"], ascending=[True, False]).reset_index(drop=True)
    return df
