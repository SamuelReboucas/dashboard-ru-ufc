"""Filtros globais (sidebar): período, RU, refeição."""
from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from src.config import load_mappings


def render_sidebar_filters(fact_detalhe: pd.DataFrame, tipos_preparacao: list[str] | None = None) -> dict:
    mp = load_mappings()
    ru_labels = mp["ru_canonico"]  # {"P1": "Pici 1", ...}
    refeicoes = ["Café", "Almoço", "Jantar"]

    st.sidebar.header("Filtros")

    if not fact_detalhe.empty and fact_detalhe["data"].notna().any():
        data_min = fact_detalhe["data"].min().date()
        data_max = fact_detalhe["data"].max().date()
    else:
        data_min, data_max = date(2026, 1, 1), date.today()

    periodo = st.sidebar.date_input(
        "Período",
        value=(data_min, data_max),
        min_value=data_min,
        max_value=data_max,
    )
    if isinstance(periodo, tuple) and len(periodo) == 2:
        data_ini, data_fim = periodo
    else:
        data_ini, data_fim = data_min, data_max

    ru_selecionados_labels = st.sidebar.multiselect(
        "Restaurante Universitário (RU)",
        options=list(ru_labels.values()),
        default=list(ru_labels.values()),
    )
    label_to_code = {v: k for k, v in ru_labels.items()}
    ru_selecionados = [label_to_code[l] for l in ru_selecionados_labels] or None

    refeicao_selecionada = st.sidebar.multiselect(
        "Refeição", options=refeicoes, default=refeicoes
    ) or None

    tipo_preparacao_selecionado = None
    if tipos_preparacao:
        tipo_preparacao_selecionado = st.sidebar.multiselect(
            "Tipo de preparação",
            options=sorted(tipos_preparacao),
            default=[],
            help=(
                "Filtra a aba 'Indicadores Oficiais' e a página 'Produção e "
                "Eficiência' (Resto-Ingesta, Per Capita, Conformidade). Não "
                "afeta as abas do MVP original, que usam outra fonte de dado "
                "sem essa dimensão. Vazio = todos os tipos."
            ),
        ) or None

    return {
        "ru": ru_selecionados,
        "refeicao": refeicao_selecionada,
        "data_ini": data_ini,
        "data_fim": data_fim,
        "tipo_preparacao": tipo_preparacao_selecionado,
    }
