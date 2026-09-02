"""Cards de KPI (st.metric) — apenas apresentação, sem cálculo de indicador."""
from __future__ import annotations

import math
import streamlit as st


def _fmt(value, kind: str) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "sem dado"
    if kind == "pct":
        return f"{value * 100:.1f}%"
    if kind == "int":
        return f"{value:,.0f}".replace(",", ".")
    if kind == "float2":
        return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return str(value)


def kpi_row(items: list[tuple[str, float, str]]) -> None:
    """items: lista de (rótulo, valor, tipo de formatação: 'int'|'pct'|'float2')"""
    cols = st.columns(len(items))
    for col, (label, value, kind) in zip(cols, items):
        col.metric(label, _fmt(value, kind))
