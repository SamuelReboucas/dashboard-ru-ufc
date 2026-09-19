"""
Dashboard executivo do Restaurante Universitário.

Execução:
    streamlit run app/streamlit_app.py

Pré-requisito: rodar `python -m src.pipeline` pelo menos uma vez para gerar
data/processed/*.csv, data/powerbi/*.csv e outputs/relatorio_qualidade.csv.

Estrutura em 4 abas, alinhada à especificação oficial do Painel Estratégico
da Nutrição (docs/especificacao_visual_powerbi.md): Visão Geral, Qualidade,
Produção e Eficiência — mais uma aba de Gestão (fora do escopo do documento
da gestão, mas mantida por já existir e ser útil).
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import streamlit as st

from src import metrics
from src import metrics_powerbi
from src.config import load_mappings
from app.components.data_loader import load_all, load_all_powerbi, load_metadata, load_quality_report
from app.components.filters import render_sidebar_filters
from app.components.kpi_cards import kpi_row
from app.components.charts import line_chart, bar_chart, ranking_chart

st.set_page_config(page_title="Painel Estratégico da Nutrição — RU", layout="wide", page_icon="🍽️")

RU_LABELS = load_mappings()["ru_canonico"]  # {"P1": "Pici 1", ...}


def _ru_label(code: str) -> str:
    return RU_LABELS.get(code, code)


def main() -> None:
    st.title("🍽️ Painel Estratégico da Nutrição — Restaurante Universitário")

    data = load_all()
    data_pbi = load_all_powerbi()
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

    # ---- Filtros -----------------------------------------------------
    tipos_preparacao = []
    if not data_pbi["producao"].empty:
        tipos_preparacao = data_pbi["producao"]["tipo_preparacao"].dropna().unique().tolist()
    filtros = render_sidebar_filters(data["detalhe"], tipos_preparacao=tipos_preparacao)

    # filtros para as métricas do MVP original (não conhecem tipo_preparacao)
    filtros_mvp = {k: v for k, v in filtros.items() if k != "tipo_preparacao"}
    # filtros para as métricas oficiais (fact_producao/satisfacao/temperatura)
    filtros_pbi = {k: v for k, v in filtros.items() if k in ("ru", "refeicao", "tipo_preparacao", "data_ini", "data_fim")}
    # satisfação oficial: tipo_preparacao só está disponível em 100% das
    # linhas (ver achado da chave composta); os demais filtros valem igual
    filtros_pbi_satisfacao = filtros_pbi

    producao_vazia = data_pbi["producao"].empty
    satisfacao_vazia = data_pbi["satisfacao"].empty
    temperatura_vazia = data_pbi["temperatura"].empty
    sem_camada_oficial = producao_vazia and satisfacao_vazia and temperatura_vazia

    tabs = st.tabs(["Visão Geral", "Qualidade", "Produção e Eficiência", "Gestão"])

    # ======================================================================
    # PÁGINA 1 — VISÃO GERAL
    # ======================================================================
    with tabs[0]:
        st.subheader("Visão Geral")

        realizadas = metrics.refeicoes_realizadas(data["detalhe"], **filtros_mvp)["refeicoes_realizadas"].iloc[0]
        pct_exec = metrics.pct_execucao(data["detalhe"], **filtros_mvp)["pct_execucao"].iloc[0]

        mensal = metrics.evolucao_refeicoes(data["detalhe"], freq="ME", **filtros_mvp)
        media_mensal = mensal["comensais_real"].mean() if not mensal.empty else None

        kpi_row([
            ("Total de Refeições", realizadas, "int"),
            ("Média Mensal", media_mensal, "int"),
            ("% Execução (real/previsto)", pct_exec, "pct"),
        ])
        st.caption(
            "⚠ \"% Execução\" usa a maior previsão de prato entre as opções da "
            "refeição (proxy) — não há, na fonte, um campo de previsto total "
            "oficial. \"Média Mensal\" inclui meses parciais no início/fim do "
            "período de dados disponível. Ver `docs/indicadores.md`."
        )

        evol = metrics.evolucao_refeicoes(data["detalhe"], **filtros_mvp)
        if not evol.empty:
            st.plotly_chart(
                line_chart(evol, "data", "comensais_real", "Evolução temporal de refeições realizadas", "Refeições"),
                use_container_width=True,
            )

        por_ru = metrics.refeicoes_realizadas(data["detalhe"], group_by=["ru"], **filtros_mvp)
        por_ru["RU"] = por_ru["ru"].map(_ru_label)
        st.plotly_chart(
            bar_chart(por_ru, "RU", "refeicoes_realizadas", "Comparação entre unidades", "Refeições"),
            use_container_width=True,
        )

    # ======================================================================
    # PÁGINA 2 — QUALIDADE
    # ======================================================================
    with tabs[1]:
        st.subheader("Qualidade")

        if sem_camada_oficial:
            st.info(
                "Camada `data/powerbi/` não encontrada — os indicadores oficiais "
                "de Resto-Ingesta, ISC e Conformidade Térmica não podem ser "
                "calculados. Rode `python -m src.pipeline` e garanta que "
                "`data/powerbi/*.csv` esteja no repositório publicado."
            )
        else:
            st.caption(
                "⚠ Indicadores oficiais, definidos com a Nutrição (mesmo modelo "
                "usado no Power BI). Não confundir `Resto-Ingesta (oficial)` "
                "com o `Rejeito` de pré-preparo mostrado mais abaixo — são "
                "conceitos diferentes (ver docs/aderencia_orientacoes_gestao.md)."
            )

            resto = metrics_powerbi.resto_ingesta(data_pbi["producao"], **filtros_pbi) if not producao_vazia else None
            isc = metrics_powerbi.isc_agregado(data_pbi["satisfacao"], **filtros_pbi_satisfacao) if not satisfacao_vazia else None
            conf = metrics_powerbi.conformidade_termica(data_pbi["temperatura"], **filtros_pbi) if not temperatura_vazia else None

            kpi_row([
                ("Resto-Ingesta (kg)", resto["resto_ingesta_kg"].iloc[0] if resto is not None else None, "int"),
                ("% Resto-Ingesta", resto["pct_resto_ingesta"].iloc[0] / 100 if resto is not None else None, "pct"),
                ("ISC Agregado (0-10)", isc["isc_agregado"].iloc[0] if isc is not None else None, "float2"),
                ("Total de Respostas", isc["total_respostas"].iloc[0] if isc is not None else None, "int"),
            ])
            kpi_row([
                ("% Conformidade Temperatura", conf["pct_conformidade"].iloc[0] if conf is not None else None, "pct"),
                ("% Cobertura da Classificação", conf["pct_cobertura"].iloc[0] if conf is not None else None, "pct"),
                ("Medições Fora do Padrão", conf["medicoes_fora_padrao"].iloc[0] if conf is not None else None, "int"),
            ])
            if conf is not None:
                st.caption(
                    "% Conformidade considera só medições avaliadas (com classe "
                    "térmica conhecida); % Cobertura mostra quanto das medições "
                    "válidas isso representa — ler os dois números juntos."
                )

            c1, c2 = st.columns(2)
            with c1:
                if isc is not None:
                    dist_isc = pd.DataFrame({
                        "Nível": ["Ótimo", "Regular", "Ruim"],
                        "Percentual": [isc["pct_otimo"].iloc[0], isc["pct_regular"].iloc[0], isc["pct_ruim"].iloc[0]],
                    })
                    st.plotly_chart(
                        bar_chart(dist_isc, "Nível", "Percentual", "Distribuição de satisfação (Ótimo/Regular/Ruim)", "% das respostas"),
                        use_container_width=True,
                    )
            with c2:
                if resto is not None:
                    resto_ru = metrics_powerbi.resto_ingesta(data_pbi["producao"], group_by=["ru"], **filtros_pbi)
                    resto_ru["RU"] = resto_ru["ru"].map(_ru_label)
                    st.plotly_chart(
                        bar_chart(resto_ru, "RU", "pct_resto_ingesta", "% Resto-Ingesta por RU", "%"),
                        use_container_width=True,
                    )
                    st.caption(
                        "Cada barra é independente (Resto-Ingesta daquele RU ÷ "
                        "Quantidade Distribuída daquele RU) — não somam 100% "
                        "entre si, e não devem ser somadas."
                    )

            if not temperatura_vazia:
                dist_status = metrics_powerbi.distribuicao_status_temperatura(data_pbi["temperatura"], **filtros_pbi)
                st.plotly_chart(
                    bar_chart(dist_status, "status", "quantidade", "Distribuição por status de temperatura", "Medições"),
                    use_container_width=True,
                )

        st.divider()
        st.markdown("##### Avaliação sensorial (qualidade técnica interna)")
        st.caption(
            "⚠ Diferente do ISC acima: esta avaliação é feita por um "
            "integrante da equipe (QC interno), não pelo comensal — não é "
            "'satisfação do cliente'. Ver docs/aderencia_orientacoes_gestao.md."
        )
        sensorial_ru = metrics.avaliacao_sensorial_media(data["sensorial"], group_by=["ru"], **filtros_mvp)
        sensorial_ru["RU"] = sensorial_ru["ru"].map(_ru_label)
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(
                bar_chart(sensorial_ru, "RU", "avaliacao_sensorial_media", "Avaliação sensorial média por RU", "Nota (0-5)"),
                use_container_width=True,
            )
        with c2:
            piores = metrics.top_piores_preparacoes(data["sensorial"], n=5, **filtros_mvp)
            if not piores.empty:
                st.plotly_chart(
                    ranking_chart(piores, "nota_media", "preparacao", "Top 5 preparações com pior avaliação"),
                    use_container_width=True,
                )
            else:
                st.info("Sem preparações com avaliações suficientes (mínimo 3) no recorte selecionado.")

    # ======================================================================
    # PÁGINA 3 — PRODUÇÃO E EFICIÊNCIA
    # ======================================================================
    with tabs[2]:
        st.subheader("Produção e Eficiência")

        rejeito = metrics.rejeito_total(data["detalhe"], **filtros_mvp)["rejeito_total"].iloc[0]
        per_capita_kpi = metrics.desperdicio_per_capita(data["detalhe"], **filtros_mvp)["desperdicio_per_capita"].iloc[0]
        ia = metrics.indice_aceitabilidade(data["detalhe"], **filtros_mvp)["indice_aceitabilidade"].iloc[0]

        kpi_row([
            ("Rejeito de pré-preparo (kg)", rejeito, "int"),
            ("Desperdício per capita (kg)", per_capita_kpi, "float2"),
            ("Índice de aceitabilidade", ia, "pct"),
        ])
        st.caption(
            "⚠ \"Rejeito de pré-preparo\" = peso bruto − peso líquido (perda "
            "antes de servir) — diferente do \"Resto-Ingesta\" oficial da aba "
            "Qualidade (que mede o que sobra depois de servido)."
        )

        per_capita_ru = metrics.desperdicio_per_capita(data["detalhe"], group_by=["ru"], **filtros_mvp)
        per_capita_ru["RU"] = per_capita_ru["ru"].map(_ru_label)
        st.plotly_chart(
            bar_chart(per_capita_ru, "RU", "desperdicio_per_capita", "Desperdício per capita por RU", "kg/comensal"),
            use_container_width=True,
        )

        if not producao_vazia:
            st.divider()
            st.markdown("##### Per Capita oficial (por preparação)")
            per_capita_tipo = metrics_powerbi.per_capita_por_tipo(data_pbi["producao"], **filtros_pbi)
            per_capita_tipo = per_capita_tipo.sort_values("per_capita_g_comensal", ascending=False).head(10)
            st.plotly_chart(
                ranking_chart(per_capita_tipo, "per_capita_g_comensal", "tipo_preparacao", "Per Capita por tipo de preparação (g/comensal)"),
                use_container_width=True,
            )
            st.caption(
                "Não existe um card único de 'Per Capita Geral' — misturar "
                "preparações diferentes (ex.: Suco e Salada) num só número "
                "não tem interpretação gerencial única."
            )

    # ======================================================================
    # PÁGINA 4 — GESTÃO (fora do escopo do documento da gestão, mantida)
    # ======================================================================
    with tabs[3]:
        st.subheader("Gestão")
        st.caption(
            "Fora do escopo do Painel Estratégico da Nutrição — mantida aqui "
            "por já existir desde o MVP original."
        )

        atend = metrics.atendimentos_resolvidos(data["atendimentos"], **filtros_mvp)
        manut = metrics.manutencao_resolvida(data["manutencao"], **filtros_mvp)
        kpi_row([
            ("Atendimentos no período", atend["total"].iloc[0] if len(atend) else None, "int"),
            ("% Atendimentos resolvidos", atend["pct_resolvido"].iloc[0] if len(atend) else None, "pct"),
            ("% OS de manutenção resolvidas", manut["pct_resolvido"].iloc[0] if len(manut) else None, "pct"),
        ])

        manut_tipo = metrics.manutencao_resolvida(data["manutencao"], group_by=["tipo"], **filtros_mvp)
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
