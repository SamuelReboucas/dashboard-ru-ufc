"""
Carrega os dados processados para uso no Streamlit. Não contém regra de
negócio nem lógica de anonimização — só leitura, resolução de camada e cache.

Resolução de camada (ver src/config.resolve_fact_path):
  1. data/processed/        (camada privada, completa — só existe localmente,
     após rodar `python -m src.pipeline` com o Excel em data/raw/)
  2. data/processed_public/ (camada pública, sem PII — é a única que existe
     no Streamlit Community Cloud, pois é a única versionada no Git)
"""
from __future__ import annotations

import json

import pandas as pd
import streamlit as st

from src.config import FACT_PATHS, resolve_fact_path, resolve_metadata_path, QUALIDADE_REPORT_PATH

DATE_COLS_BY_KEY = {
    "detalhe": ["data"],
    "sensorial": ["data"],
    "isc": ["data"],
    "atendimentos": ["data"],
    "manutencao": ["data", "data_resolucao"],
}


@st.cache_data(show_spinner=False)
def load_fact(key: str) -> pd.DataFrame:
    path = resolve_fact_path(key)
    if path is None:
        return pd.DataFrame()
    return pd.read_csv(path, parse_dates=DATE_COLS_BY_KEY.get(key, []))


@st.cache_data(show_spinner=False)
def load_metadata() -> dict:
    path = resolve_metadata_path()
    if path is None:
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data(show_spinner=False)
def load_quality_report() -> pd.DataFrame:
    if not QUALIDADE_REPORT_PATH.exists():
        return pd.DataFrame()
    return pd.read_csv(QUALIDADE_REPORT_PATH)


def load_all() -> dict[str, pd.DataFrame]:
    return {key: load_fact(key) for key in FACT_PATHS}
