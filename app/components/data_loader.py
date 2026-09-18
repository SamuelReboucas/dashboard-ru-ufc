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

from src.config import (
    FACT_PATHS, resolve_fact_path, resolve_metadata_path, QUALIDADE_REPORT_PATH,
    FACT_PRODUCAO_PATH, FACT_SATISFACAO_PATH, FACT_TEMPERATURA_PATH, FACT_REFEICOES_PATH,
)

DATE_COLS_BY_KEY = {
    "detalhe": ["data"],
    "sensorial": ["data"],
    "isc": ["data"],
    "atendimentos": ["data"],
    "manutencao": ["data", "data_resolucao"],
}

# Tabelas do modelo Power BI (data/powerbi/) — indicadores oficiais definidos
# com a Nutrição (Resto-Ingesta, Per Capita, ISC Agregado, Conformidade
# Térmica). Camada opcional: se o arquivo não existir (deploy ainda sem essa
# camada), a aba correspondente no Streamlit avisa e não quebra o resto do
# dashboard — ver `load_powerbi_fact`.
POWERBI_FACT_PATHS = {
    "producao": FACT_PRODUCAO_PATH,
    "satisfacao": FACT_SATISFACAO_PATH,
    "temperatura": FACT_TEMPERATURA_PATH,
    "refeicoes": FACT_REFEICOES_PATH,
}
POWERBI_DATE_COLS = {
    "producao": ["data"],
    "satisfacao": ["data"],
    "temperatura": ["data"],
    "refeicoes": ["data"],
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


@st.cache_data(show_spinner=False)
def load_powerbi_fact(key: str) -> pd.DataFrame:
    """Lê uma tabela fato do modelo Power BI (data/powerbi/). Retorna
    DataFrame vazio se o arquivo não existir — permite que o dashboard
    continue funcionando normalmente (com um aviso na aba correspondente)
    mesmo antes dessa camada ser publicada no repositório."""
    path = POWERBI_FACT_PATHS.get(key)
    if path is None or not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, parse_dates=POWERBI_DATE_COLS.get(key, []))


def load_all_powerbi() -> dict[str, pd.DataFrame]:
    return {key: load_powerbi_fact(key) for key in POWERBI_FACT_PATHS}
