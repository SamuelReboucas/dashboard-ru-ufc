"""
Dashboard executivo do Restaurante Universitário — MVP v1.

Execução:
    streamlit run app/streamlit_app.py

Pré-requisito: rodar `python -m src.pipeline` pelo menos uma vez para gerar
data/processed/*.csv e outputs/relatorio_qualidade.csv.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Garante que a raiz do projeto esteja no sys.path, para `from src...` funcionar
# independentemente de onde o `streamlit run` é chamado.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import streamlit as st

from src import metrics
from src.config import load_mappings
from app.components.data_loader import load_all, load_metadata, load_quality_report
from app.components.filters import render_sidebar_filters
from app.components.kpi_cards import kpi_row
from app.components.charts import line_chart, bar_chart, ranking_chart

st.set_page_config(page_title="Painel RU — MVP", layout="wide", page_icon="🍽️")

RU_LABELS = load_mappings()["ru_canonico"]  # {"P1": "Pici 1", ...}


def _ru_label(code: str) -> str:
    return RU_LABELS.get(code, code)


def main() -> None:
    st.title("🍽️ Painel do Restaurante Universitário — MVP v1")

    data = load_all()
    meta = load_metadata()
    quality = load_quality_report()

    if data["detalhe"].empty:
        st.error(
            "Nenhum dado processado encontrado. Rode `python -m src.pipeline` "
            "com o Excel em `data/raw/` antes de abrir o dashboard."
        )
        st.stop()

    # ---- Cabeçalho: atualização e alertas de qualidade -----------------
    col_a, col_b = st.columns([3, 1])
    with col_a:
        data_atualizacao = meta.get("dados_atualizados_ate")
        if data_atualizacao:
            data_fmt = pd.to_datetime(data_atualizacao).strftime("%d/%m/%Y")
            st.caption(f"📅 **Dados atualizados até:** {data_fmt}")
    with col_b:
        n_alertas = meta.get("n_alertas_qualidade", 0)
        if n_alertas:
            st.warning(f"⚠ Existem {n_alertas} alertas de qualidade dos dados")
        else:
            st.success("✅ Sem alertas críticos de qualidade")

    with st.expander("Ver relatório de qualidade dos dados"):
        if quality.empty:
            st.write("Relatório de qualidade não encontrado.")
        else:
            st.dataframe(quality, use_container_width=True, hide_index=True)

    # ---- Filtros ---------------------------------------------------------
    filtros = render_sidebar_filters(data["detalhe"])

    tabs = st.tabs(["Visão Geral", "Panorama", "Desperdício e Eficiência", "Qualidade / Satisfação", "Gestão"])

    # ================= VISÃO GERAL ========================================
    with tabs[0]:
        st.subheader("KPIs principais do período selecionado")

        realizadas = metrics.refeicoes_realizadas(data["detalhe"], **filtros)["refeicoes_realizadas"].iloc[0]
        pct_exec = metrics.pct_execucao(data["detalhe"], **filtros)["pct_execucao"].iloc[0]
        per_capita = metrics.desperdicio_per_capita(data["detalhe"], **filtros)["desperdicio_per_capita"].iloc[0]
        sensorial = metrics.avaliacao_sensorial_media(data["sensorial"], **filtros)["avaliacao_sensorial_media"].iloc[0]
        isc = metrics.isc_medio(data["isc"], **filtros)["isc_medio"].iloc[0]
        atend = metrics.atendimentos_resolvidos(data["atendimentos"], **filtros)

        kpi_row([
            ("Refeições realizadas", realizadas, "int"),
            ("% Execução (real/previsto)", pct_exec, "pct"),
            ("Desperdício per capita (kg)", per_capita, "float2"),
        ])
        kpi_row([
            ("Avaliação sensorial média (0-5)", sensorial, "float2"),
            ("ISC médio (0-10)", isc, "float2"),
            ("% Atendimentos resolvidos", atend["pct_resolvido"].iloc[0] if len(atend) else None, "pct"),
        ])

        evol = metrics.evolucao_refeicoes(data["detalhe"], **filtros)
        if not evol.empty:
            st.plotly_chart(
                line_chart(evol, "data", "comensais_real", "Evolução de refeições realizadas", "Refeições"),
                use_container_width=True,
            )

    # ================= PANORAMA ===========================================
    with tabs[1]:
        st.subheader("Panorama — volume e previsto x realizado")
        st.caption(
            "⚠ \"Previsto\" usa a maior previsão de prato entre as opções da "
            "refeição (proxy) — não há, na fonte, um campo de previsto "
            "total oficial. Ver `docs/indicadores.md`."
        )

        por_ru = metrics.refeicoes_realizadas(data["detalhe"], group_by=["ru"], **filtros)
        por_ru["RU"] = por_ru["ru"].map(_ru_label)
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(
                bar_chart(por_ru, "RU", "refeicoes_realizadas", "Refeições realizadas por RU", "Refeições"),
                use_container_width=True,
            )
        with c2:
            pct_ru = metrics.pct_execucao(data["detalhe"], group_by=["ru"], **filtros)
            pct_ru["RU"] = pct_ru["ru"].map(_ru_label)
            st.plotly_chart(
                bar_chart(pct_ru, "RU", "pct_execucao", "% Execução por RU", "% Execução"),
                use_container_width=True,
            )

        evol_ru = data["detalhe"].copy()
        evol = metrics.evolucao_refeicoes(data["detalhe"], **filtros)
        if not evol.empty:
            st.plotly_chart(
                line_chart(evol, "data", "comensais_real", "Evolução diária de refeições realizadas", "Refeições"),
                use_container_width=True,
            )

    # ================= DESPERDÍCIO ========================================
    with tabs[2]:
        st.subheader("Desperdício e eficiência")
        st.caption(
            "⚠ Rejeito calculado como *peso bruto - peso líquido* (proxy) — "
            "não há campo explícito de rejeito nas abas de detalhe. "
            "Ver `docs/indicadores.md`."
        )

        rejeito = metrics.rejeito_total(data["detalhe"], **filtros)["rejeito_total"].iloc[0]
        per_capita_kpi = metrics.desperdicio_per_capita(data["detalhe"], **filtros)["desperdicio_per_capita"].iloc[0]
        ia = metrics.indice_aceitabilidade(data["detalhe"], **filtros)["indice_aceitabilidade"].iloc[0]
        kpi_row([
            ("Rejeito total (kg)", rejeito, "int"),
            ("Desperdício per capita (kg)", per_capita_kpi, "float2"),
            ("Índice de aceitabilidade", ia, "pct"),
        ])

        per_capita_ru = metrics.desperdicio_per_capita(data["detalhe"], group_by=["ru"], **filtros)
        per_capita_ru["RU"] = per_capita_ru["ru"].map(_ru_label)
        st.plotly_chart(
            bar_chart(per_capita_ru, "RU", "desperdicio_per_capita", "Desperdício per capita por RU", "kg/comensal"),
            use_container_width=True,
        )

    # ================= QUALIDADE ==========================================
    with tabs[3]:
        st.subheader("Qualidade / satisfação")

        sensorial_ru = metrics.avaliacao_sensorial_media(data["sensorial"], group_by=["ru"], **filtros)
        sensorial_ru["RU"] = sensorial_ru["ru"].map(_ru_label)
        isc_ru = metrics.isc_medio(data["isc"], group_by=["ru"], **filtros)
        isc_ru["RU"] = isc_ru["ru"].map(_ru_label)

        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(
                bar_chart(sensorial_ru, "RU", "avaliacao_sensorial_media", "Avaliação sensorial média por RU", "Nota (0-5)"),
                use_container_width=True,
            )
        with c2:
            st.plotly_chart(
                bar_chart(isc_ru, "RU", "isc_medio", "ISC médio por RU", "ISC (0-10)"),
                use_container_width=True,
            )

        piores = metrics.top_piores_preparacoes(data["sensorial"], n=5, **filtros)
        if not piores.empty:
            st.plotly_chart(
                ranking_chart(piores, "nota_media", "preparacao", "Top 5 preparações com pior avaliação"),
                use_container_width=True,
            )
        else:
            st.info("Sem preparações com avaliações suficientes (mínimo 3) no recorte selecionado.")

    # ================= GESTÃO =============================================
    with tabs[4]:
        st.subheader("Gestão")

        atend = metrics.atendimentos_resolvidos(data["atendimentos"], **filtros)
        manut = metrics.manutencao_resolvida(data["manutencao"], **filtros)
        kpi_row([
            ("Atendimentos no período", atend["total"].iloc[0] if len(atend) else None, "int"),
            ("% Atendimentos resolvidos", atend["pct_resolvido"].iloc[0] if len(atend) else None, "pct"),
            ("% OS de manutenção resolvidas", manut["pct_resolvido"].iloc[0] if len(manut) else None, "pct"),
        ])

        manut_tipo = metrics.manutencao_resolvida(data["manutencao"], group_by=["tipo"], **filtros)
        if not manut_tipo.empty:
            st.plotly_chart(
                bar_chart(manut_tipo, "tipo", "total", "OS de manutenção por tipo", "Quantidade"),
                use_container_width=True,
            )
        st.caption(
            "Dados de Atendimentos Especializado exibidos apenas de forma agregada — "
            "nomes, CPF e texto livre de relatos nunca são carregados nesta camada "
            "(ver docs/auditoria_dados.md, seção Privacidade)."
        )


if __name__ == "__main__":
    main()
