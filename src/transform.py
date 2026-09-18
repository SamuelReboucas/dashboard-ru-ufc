"""
Camada de transformação.

Recebe os DataFrames crus de src/extract.py e devolve tabelas "fato" limpas
e padronizadas, prontas para src/metrics.py. Toda regra de normalização usa
config/mappings.yaml — nada de aliases hardcoded aqui.
"""
from __future__ import annotations

import unicodedata
import pandas as pd
import numpy as np

from src.config import load_mappings

_mp = None


def _mappings() -> dict:
    global _mp
    if _mp is None:
        _mp = load_mappings()
    return _mp


def _strip_accents(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn"
    )


def _norm_key(value) -> str:
    if value is None:
        return ""
    return _strip_accents(str(value)).strip().upper()


# ---------------------------------------------------------------------------
# Normalizadores genéricos
# ---------------------------------------------------------------------------


def normalize_ru(series: pd.Series) -> pd.Series:
    """Mapeia texto livre de RU (nome completo, sigla, variações de acento)
    para o código canônico (P1, P2, B, L, PO). Valores não reconhecidos viram
    NaN — tratados depois pelo validador `ru_desconhecido`."""
    aliases = _mappings()["ru_aliases"]
    return series.map(lambda v: aliases.get(_norm_key(v), np.nan))


def normalize_refeicao(series: pd.Series) -> pd.Series:
    """Padroniza Café/Almoço/Jantar a partir de variações de acento/caixa."""
    aliases = _mappings()["refeicao_aliases"]
    return series.map(lambda v: aliases.get(_norm_key(v), np.nan))


def to_numeric_safe(series: pd.Series) -> pd.Series:
    """Converte para número, tratando erros de fórmula do Excel e strings
    vazias como ausência de dado (NaN) — nunca como zero."""
    erros = set(_mappings()["valores_erro"])

    def _clean(v):
        if v is None:
            return np.nan
        if isinstance(v, str):
            s = v.strip()
            if s == "" or s in erros or s.startswith("#"):
                return np.nan
        return v

    cleaned = series.map(_clean)
    return pd.to_numeric(cleaned, errors="coerce")


def to_date_safe(series: pd.Series) -> pd.Series:
    """Converte para datetime; qualquer valor não interpretável (incluindo
    erros de fórmula tipo #REF!) vira NaT.

    `dayfirst=True` é obrigatório aqui: parte das abas (ex.: UFC-INFRA) grava
    a data como texto no formato brasileiro dd/mm/aaaa (ex.: "13/01/2026").
    Sem esse parâmetro, o pandas assume mês primeiro (padrão americano) e
    descarta como inválida qualquer data com dia > 12. Datas que já chegam
    como objeto datetime (a maioria, vinda do Excel) não são afetadas por
    este parâmetro.
    """
    return pd.to_datetime(series, errors="coerce", dayfirst=True)


def _is_valid_meal_str(v) -> bool:
    return isinstance(v, str) and v.strip() != ""


def _within_valid_range(date_series: pd.Series) -> pd.Series:
    """True para datas dentro da janela plausível do projeto (config/mappings.yaml
    `data_min_valida`/`data_max_valida`). Usado para descartar erros de
    digitação óbvios (ex.: '24/03/2027' em vez de 2026) que, sem esse filtro,
    distorceriam a data de "última atualização" exibida no dashboard."""
    mp = _mappings()
    lo = pd.Timestamp(mp["data_min_valida"])
    hi = pd.Timestamp(mp["data_max_valida"])
    return date_series.between(lo, hi)


# ---------------------------------------------------------------------------
# Fact: detalhe operacional (Panorama + Desperdício)
# ---------------------------------------------------------------------------

NUMERIC_COLS_DETALHE = [
    "temp_c", "peso_bruto", "repos", "qtd1", "tam1", "qtd2", "tam2",
    "peso_liq", "pce", "pc_pct", "previsao", "peso_previsto",
    "controle_cubas", "comensais", "ajustes", "sobra_limpa", "sobra_suja",
    "consumo_real", "pc_pres", "comensais_real", "bom", "regular", "ruim",
]


def build_fact_detalhe(df_raw: pd.DataFrame) -> pd.DataFrame:
    df = df_raw.copy()
    df["data"] = to_date_safe(df["data"])
    df["refeicao"] = normalize_refeicao(df["refeicao"])

    for col in NUMERIC_COLS_DETALHE:
        if col in df.columns:
            df[col] = to_numeric_safe(df[col])

    # linha só é válida se tiver data E refeição reconhecidas — descarta
    # milhares de linhas-template vazias identificadas na auditoria.
    df = df[df["data"].notna() & df["refeicao"].notna()]
    df = df[_within_valid_range(df["data"])]

    df = df.drop_duplicates(subset=["ru", "data", "refeicao", "prep"], keep="first")

    # limites plausíveis (defesa extra; validators.py também reporta isso)
    for col in ("comensais_real", "peso_bruto", "peso_liq", "sobra_limpa", "sobra_suja"):
        if col in df.columns:
            df.loc[df[col] < 0, col] = np.nan

    df["mes"] = df["data"].dt.to_period("M").astype(str)
    return df.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Fact: ISC
# ---------------------------------------------------------------------------


def build_fact_isc(df_raw: pd.DataFrame) -> pd.DataFrame:
    df = df_raw.copy()
    if df.empty:
        return df
    df["data"] = to_date_safe(df["data"])
    for col in ["otimo", "otimo_pct", "regular", "regular_pct", "ruim", "ruim_pct", "isc"]:
        df[col] = to_numeric_safe(df[col])
    df = df[df["data"].notna()]
    df = df[_within_valid_range(df["data"])]
    df = df.drop_duplicates(subset=["ru", "data", "refeicao", "preparacao"], keep="first")
    df["mes"] = df["data"].dt.to_period("M").astype(str)
    return df.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Fact: avaliação sensorial
# ---------------------------------------------------------------------------


def build_fact_sensorial(df_raw: pd.DataFrame) -> pd.DataFrame:
    df = df_raw.copy()
    df["data"] = to_date_safe(df["data"])
    df["ru"] = normalize_ru(df["refeitorio"])
    df["refeicao"] = normalize_refeicao(df["refeicao"])
    for col in ["aparencia", "textura", "sabor", "odor", "global", "nota"]:
        if col in df.columns:
            df[col] = to_numeric_safe(df[col])

    df = df[df["data"].notna() & df["ru"].notna()]
    df = df[_within_valid_range(df["data"])]
    df = df.drop_duplicates(
        subset=["ru", "data", "refeicao", "preparacao", "avaliador"], keep="first"
    )
    df["mes"] = df["data"].dt.to_period("M").astype(str)
    return df.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Fact: gestão (atendimentos + manutenção) — já sem PII (removida na extração)
# ---------------------------------------------------------------------------


def build_fact_gestao_atendimentos(df_raw: pd.DataFrame) -> pd.DataFrame:
    df = df_raw.copy()
    df["data"] = to_date_safe(df["data"])
    df["ru"] = normalize_ru(df["ru"])
    df["resolvido_flag"] = df["resolvido"].astype(str).str.strip().str.lower().eq("resolvido")
    df = df[df["data"].notna()]
    df = df[_within_valid_range(df["data"])]
    df = df.drop_duplicates()
    df["mes"] = df["data"].dt.to_period("M").astype(str)
    return df.reset_index(drop=True)


def build_fact_gestao_manutencao(df_raw: pd.DataFrame) -> pd.DataFrame:
    mp = _mappings()
    local_aliases = mp["local_ru_aliases"]
    ru_aliases = mp["ru_aliases"]

    df = df_raw.copy()
    df["data"] = to_date_safe(df.get("data"))
    df["data_resolucao"] = to_date_safe(df.get("data_resolucao"))

    def _map_ru(v):
        key = _norm_key(v)
        if key in local_aliases:
            return local_aliases[key]
        return ru_aliases.get(key, np.nan)

    df["ru"] = df.get("ru_texto").map(_map_ru)
    df["resolvido_flag"] = df["resolvido"].astype(str).str.strip().str.lower().isin(
        ["sim", "resolvido", "true", "1"]
    )
    df = df[df["data"].notna()]
    df = df[_within_valid_range(df["data"])]
    df = df.drop_duplicates(subset=["ru", "data", "tipo", "sheet_origem"], keep="first")
    df["mes"] = df["data"].dt.to_period("M").astype(str)
    return df.reset_index(drop=True)


# ---------------------------------------------------------------------------
# "Última atualização" — critério de dado efetivamente realizado
#
# Achado: as abas de detalhe e de ISC vêm pré-preenchidas com linhas de
# calendário para datas futuras (planejamento), sem produção/votação real
# ainda lançada. Essas linhas têm todas as colunas de medição zeradas/nulas
# (ex.: `peso_liq = 0.00` e `comensais_real` nulo em `fact_detalhe`;
# `otimo`/`regular`/`ruim` todos nulos em `fact_isc`), diferente de um dia
# real sem produção pontual (que teria só parte das colunas zeradas, não
# o bloco inteiro de RU/refeição). Usar `MAX(data)` sem esse filtro conta
# essas linhas de planejamento como se fossem atualização real — por isso
# `MAX(data)` simples não é a definição correta de "dados atualizados até".
# ---------------------------------------------------------------------------


def is_realizado_detalhe(df: pd.DataFrame) -> pd.Series:
    """Uma linha de `fact_detalhe` representa produção efetivamente
    realizada (não um placeholder de planejamento futuro) quando
    `peso_liq > 0`. Critério escolhido por ser a medida física mais direta
    de "algo foi de fato preparado" — linhas de calendário futuro vêm com
    `peso_liq = 0.00` de forma sistemática em todas as preparações do
    RU/refeição, não como um zero pontual isolado."""
    return df["peso_liq"].fillna(0) > 0


def is_realizado_isc(df: pd.DataFrame) -> pd.Series:
    """Uma linha de `fact_isc` representa votação efetivamente registrada
    quando ao menos uma das contagens (`otimo`/`regular`/`ruim`) não é
    nula — linhas de calendário futuro vêm com as 4 colunas
    (`otimo`/`regular`/`ruim`/`isc`) totalmente nulas."""
    return df[["otimo", "regular", "ruim"]].notna().any(axis=1)


def max_data_realizada(fact: dict[str, pd.DataFrame]) -> pd.Timestamp | None:
    """Calcula a data mais recente com dado efetivamente realizado, entre
    todas as tabelas fato. Para `detalhe` e `isc`, aplica o critério de
    realizado documentado acima (evita contar linhas de planejamento
    futuro); para as demais tabelas (`sensorial`, `atendimentos`,
    `manutencao`), usa `MAX(data)` direto — auditado nesta revisão e
    confirmado que não apresentam o mesmo padrão de linhas de calendário
    futuro pré-preenchidas com zero."""
    criterios = {
        "detalhe": is_realizado_detalhe,
        "isc": is_realizado_isc,
    }
    datas_max = []
    for key, df in fact.items():
        if "data" not in df.columns or df.empty:
            continue
        dt = pd.to_datetime(df["data"])
        mask = dt.notna()
        if key in criterios:
            mask &= criterios[key](df)
        if mask.any():
            datas_max.append(dt[mask].max())
    return max(datas_max) if datas_max else None


def transform_all(raw: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    return {
        "detalhe": build_fact_detalhe(raw["detalhe"]),
        "isc": build_fact_isc(raw["isc"]),
        "sensorial": build_fact_sensorial(raw["sensorial"]),
        "atendimentos": build_fact_gestao_atendimentos(raw["atendimentos"]),
        "manutencao": build_fact_gestao_manutencao(raw["manutencao"]),
    }


# ---------------------------------------------------------------------------
# Camada pública (para GitHub / Streamlit Community Cloud)
# ---------------------------------------------------------------------------

# Colunas de PII a remover por tabela fato, na camada pública. Nenhuma outra
# tabela do MVP carrega coluna de PII (ver docs/auditoria_dados.md e
# docs/dicionario_dados.md) — só `sensorial` tem o campo `avaliador` (nome de
# integrante da equipe que fez a avaliação sensorial).
PII_COLUMNS_BY_FACT = {
    "sensorial": ["avaliador"],
}


def build_public_layer(fact: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """A partir das tabelas fato privadas (já limpas), gera a versão segura
    para publicação: mesmas linhas e mesmo grão (nenhum indicador muda de
    fórmula), apenas com as colunas de PII removidas.

    Isso NÃO agrega estatisticamente os dados — `top_piores_preparacoes` e
    demais métricas de `src/metrics.py` continuam funcionando exatamente
    igual, pois nenhuma delas usa a coluna removida (`avaliador` só era
    usada em `build_fact_sensorial` para deduplicar, papel já cumprido).
    """
    public = {}
    for key, df in fact.items():
        cols_to_drop = [c for c in PII_COLUMNS_BY_FACT.get(key, []) if c in df.columns]
        public[key] = df.drop(columns=cols_to_drop).copy() if cols_to_drop else df.copy()
    return public
