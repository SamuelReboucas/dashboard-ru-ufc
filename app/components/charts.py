"""Wrappers Plotly — só apresentação, recebem DataFrame já agregado por
src/metrics.py."""
from __future__ import annotations

import pandas as pd
import plotly.express as px

TEMPLATE = "plotly_white"


def line_chart(df: pd.DataFrame, x: str, y: str, title: str, y_label: str | None = None):
    fig = px.line(df, x=x, y=y, markers=True, template=TEMPLATE, title=title)
    fig.update_layout(yaxis_title=y_label or y, xaxis_title="", margin=dict(t=50, l=10, r=10, b=10))
    return fig


def bar_chart(df: pd.DataFrame, x: str, y: str, title: str, y_label: str | None = None, color: str | None = None):
    fig = px.bar(df, x=x, y=y, color=color, template=TEMPLATE, title=title, text_auto=".2s")
    fig.update_layout(yaxis_title=y_label or y, xaxis_title="", margin=dict(t=50, l=10, r=10, b=10))
    return fig


def ranking_chart(df: pd.DataFrame, x: str, y: str, title: str):
    fig = px.bar(
        df.sort_values(x), x=x, y=y, orientation="h", template=TEMPLATE, title=title, text_auto=".2f"
    )
    fig.update_layout(margin=dict(t=50, l=10, r=10, b=10))
    return fig
