"""
Camada de extração.

Responsabilidade única: ler as abas do Excel indicadas em config/mappings.yaml
e devolver DataFrames "crus" (com nomes de coluna já canonizados, mas SEM
regras de negócio, limpeza ou cálculo de indicador). Isso fica em transform.py
e metrics.py.

Nenhuma função aqui deve importar streamlit nem plotly.
"""
from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Iterable

import openpyxl
import pandas as pd

from src.config import load_mappings, excel_path

# ---------------------------------------------------------------------------
# Utilidades de normalização de cabeçalho
# ---------------------------------------------------------------------------


def _normalize_header(value) -> str:
    """strip + colapsa espaços + minúsculas. Mantém acentos (aliases no yaml
    também têm acentos) para não perder distinção semântica."""
    if value is None:
        return ""
    s = str(value)
    s = s.replace("\n", " ")
    s = re.sub(r"\s+", " ", s).strip().lower()
    return s


def _strip_accents(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn"
    )


def _match_alias(header_norm: str, aliases: Iterable[str]) -> bool:
    for a in aliases:
        if header_norm == _normalize_header(a):
            return True
    return False


def _build_header_index(header_row_values: list) -> dict[int, str]:
    """dict {coluna_1_based: header_normalizado}"""
    return {i + 1: _normalize_header(v) for i, v in enumerate(header_row_values)}


def _find_column(header_index: dict[int, str], aliases: list[str]) -> int | None:
    for col, h in header_index.items():
        if _match_alias(h, aliases):
            return col
    return None


def _load_workbook(path: Path | None = None):
    p = path or excel_path()
    if not p.exists():
        raise FileNotFoundError(
            f"Excel não encontrado em {p}. Copie a planilha para data/raw/ "
            f"com o nome definido em config/mappings.yaml (excel_file)."
        )
    return openpyxl.load_workbook(p, data_only=True, read_only=False)


# ---------------------------------------------------------------------------
# Abas de detalhe (P1D, P2D, BD, LD, PO2) — fonte primária de Panorama/Desperdício
# ---------------------------------------------------------------------------


def extract_detalhe(wb=None) -> pd.DataFrame:
    """Lê as 5 abas de detalhe e retorna um único DataFrame no formato longo,
    com coluna `ru` (código canônico) explícita, conforme
    docs/fontes_oficiais.md."""
    mp = load_mappings()
    wb = wb or _load_workbook()
    col_aliases = mp["colunas_detalhe"]
    frames = []

    for ru_code, sheet_cfg in mp["sheets_detalhe"].items():
        ws = wb[sheet_cfg["sheet"]]
        header_row = sheet_cfg["header_row"]
        data_start = sheet_cfg["data_start_row"]

        header_values = [ws.cell(row=header_row, column=c).value for c in range(1, ws.max_column + 1)]
        header_index = _build_header_index(header_values)

        col_positions = {
            canonical: _find_column(header_index, aliases)
            for canonical, aliases in col_aliases.items()
        }

        rows = []
        for row in ws.iter_rows(min_row=data_start, max_row=ws.max_row, values_only=True):
            record = {"ru": ru_code}
            for canonical, pos in col_positions.items():
                record[canonical] = row[pos - 1] if pos else None
            rows.append(record)

        df = pd.DataFrame(rows)
        df["sheet_origem"] = sheet_cfg["sheet"]
        frames.append(df)

    result = pd.concat(frames, ignore_index=True)
    return result


# ---------------------------------------------------------------------------
# Abas ISC (satisfação) — layout largo, blocos de 7 colunas por RU
# ---------------------------------------------------------------------------


def extract_isc(wb=None) -> pd.DataFrame:
    """Varre as 3 abas de ISC (almoço/jantar/café), localiza dinamicamente os
    blocos de cada RU pela linha de cabeçalho e devolve um DataFrame longo:
    data, ru, refeicao, preparacao, otimo, otimo_pct, regular, regular_pct,
    ruim, ruim_pct, isc.
    """
    mp = load_mappings()
    wb = wb or _load_workbook()
    ru_aliases = mp["ru_aliases"]
    bloco_largura = mp["isc_bloco_largura"]
    frames = []

    for cfg in mp["sheets_isc"]:
        ws = wb[cfg["sheet"]]
        header_row = cfg["header_row"]
        data_start = cfg["data_start_row"]
        refeicao = cfg["refeicao"]

        header_values = [ws.cell(row=header_row, column=c).value for c in range(1, ws.max_column + 1)]
        header_index = _build_header_index(header_values)

        data_col = _find_column(header_index, mp["isc_data_col_labels"])
        prep_col = _find_column(header_index, mp["isc_prep_col_labels"])

        # localizar blocos de RU: procurar, na linha de header, células cujo
        # texto normalizado (sem acento, maiúsculo) bate com algum alias de RU
        ru_blocks = []  # (coluna_inicio, ru_code)
        for col, raw_header in enumerate(header_values, start=1):
            if raw_header is None:
                continue
            key = _strip_accents(str(raw_header)).strip().upper()
            if key in ru_aliases:
                ru_blocks.append((col, ru_aliases[key]))

        if not ru_blocks or data_col is None:
            continue  # aba sem estrutura reconhecível; não interrompe o pipeline

        rows = []
        for row in ws.iter_rows(min_row=data_start, max_row=ws.max_row, values_only=True):
            data_val = row[data_col - 1] if data_col else None
            prep_val = row[prep_col - 1] if prep_col else None
            for col_start, ru_code in ru_blocks:
                bloco = row[col_start - 1: col_start - 1 + bloco_largura]
                if len(bloco) < bloco_largura:
                    continue
                otimo, otimo_pct, regular, regular_pct, ruim, ruim_pct, isc = bloco
                rows.append(
                    {
                        "data": data_val,
                        "ru": ru_code,
                        "refeicao": refeicao,
                        "preparacao": prep_val,
                        "otimo": otimo,
                        "otimo_pct": otimo_pct,
                        "regular": regular,
                        "regular_pct": regular_pct,
                        "ruim": ruim,
                        "ruim_pct": ruim_pct,
                        "isc": isc,
                    }
                )
        df = pd.DataFrame(rows)
        df["sheet_origem"] = cfg["sheet"]
        frames.append(df)

    if not frames:
        return pd.DataFrame(
            columns=["data", "ru", "refeicao", "preparacao", "otimo", "otimo_pct",
                     "regular", "regular_pct", "ruim", "ruim_pct", "isc", "sheet_origem"]
        )
    return pd.concat(frames, ignore_index=True)


# ---------------------------------------------------------------------------
# Avaliação sensorial
# ---------------------------------------------------------------------------


def extract_sensorial(wb=None) -> pd.DataFrame:
    mp = load_mappings()
    wb = wb or _load_workbook()
    cfg = mp["sheet_sensorial"]
    col_aliases = mp["colunas_sensorial"]

    ws = wb[cfg["sheet"]]
    header_values = [ws.cell(row=cfg["header_row"], column=c).value for c in range(1, ws.max_column + 1)]
    header_index = _build_header_index(header_values)
    col_positions = {c: _find_column(header_index, a) for c, a in col_aliases.items()}

    rows = []
    for row in ws.iter_rows(min_row=cfg["data_start_row"], max_row=ws.max_row, values_only=True):
        record = {c: (row[p - 1] if p else None) for c, p in col_positions.items()}
        rows.append(record)

    df = pd.DataFrame(rows)
    df["sheet_origem"] = cfg["sheet"]
    return df


# ---------------------------------------------------------------------------
# Gestão: atendimentos e manutenção — SEM colunas de PII/texto livre
# ---------------------------------------------------------------------------


def _extract_generic(wb, cfg: dict) -> pd.DataFrame:
    """Lê apenas as colunas mapeadas em `colunas_uteis` (canônico -> aliases;
    nunca as de `colunas_pii_excluidas`), casando por nome de cabeçalho
    normalizado. Retorna já com os nomes de coluna canônicos."""
    ws = wb[cfg["sheet"]]
    header_values = [ws.cell(row=cfg["header_row"], column=c).value for c in range(1, ws.max_column + 1)]
    header_index = _build_header_index(header_values)

    col_positions = {
        canonical: _find_column(header_index, aliases)
        for canonical, aliases in cfg["colunas_uteis"].items()
    }

    rows = []
    for row in ws.iter_rows(min_row=cfg["data_start_row"], max_row=ws.max_row, values_only=True):
        record = {canonical: (row[p - 1] if p else None) for canonical, p in col_positions.items()}
        if any(v is not None for v in record.values()):
            rows.append(record)

    return pd.DataFrame(rows)


def extract_atendimentos(wb=None) -> pd.DataFrame:
    mp = load_mappings()
    wb = wb or _load_workbook()
    df = _extract_generic(wb, mp["sheet_atendimentos"])
    df["sheet_origem"] = mp["sheet_atendimentos"]["sheet"]
    return df


def extract_manutencao(wb=None) -> pd.DataFrame:
    """Combina UFC-INFRA (infraestrutura) e OS - STI (TI) em um único
    DataFrame de gestão, com coluna `tipo` indicando a origem. Ambas as
    fontes já saem com colunas canônicas iguais (data, ru_texto, resolvido,
    data_resolucao), definidas em config/mappings.yaml."""
    mp = load_mappings()
    wb = wb or _load_workbook()

    infra_cfg = mp["sheet_ufc_infra"]
    sti_cfg = mp["sheet_os_sti"]

    df_infra = _extract_generic(wb, infra_cfg)
    df_infra["tipo"] = "Infraestrutura"
    df_infra["sheet_origem"] = infra_cfg["sheet"]

    df_sti = _extract_generic(wb, sti_cfg)
    df_sti["tipo"] = "TI"
    df_sti["sheet_origem"] = sti_cfg["sheet"]

    return pd.concat([df_infra, df_sti], ignore_index=True)


# ---------------------------------------------------------------------------
# Metadados (data máxima disponível nas fontes, usada no cabeçalho do dashboard)
# ---------------------------------------------------------------------------


def extract_all(wb_path: Path | None = None) -> dict[str, pd.DataFrame]:
    wb = _load_workbook(wb_path)
    return {
        "detalhe": extract_detalhe(wb),
        "isc": extract_isc(wb),
        "sensorial": extract_sensorial(wb),
        "atendimentos": extract_atendimentos(wb),
        "manutencao": extract_manutencao(wb),
    }
