"""
Pipeline principal. Execução:

    python -m src.pipeline

Fluxo: Excel (data/raw/) -> extração -> validação de qualidade ->
transformação -> dados processados (data/processed/) + relatório de
qualidade (outputs/relatorio_qualidade.csv) + metadata.json (usado pelo
dashboard para exibir "Dados atualizados até: DD/MM/AAAA").
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime

import pandas as pd

from src.config import (
    ensure_dirs,
    excel_path,
    FACT_PATHS,
    METADATA_PATH,
    METADATA_PUBLIC_PATH,
    QUALIDADE_REPORT_PATH,
)
from src.extract import extract_all
from src.transform import transform_all, build_public_layer, PII_COLUMNS_BY_FACT
from src.validators import build_quality_report


def run(verbose: bool = True) -> dict:
    ensure_dirs()
    t0 = time.time()

    xlsx = excel_path()
    if verbose:
        print(f"[1/5] Lendo Excel: {xlsx}")
    raw = extract_all(xlsx)
    if verbose:
        for k, df in raw.items():
            print(f"      - {k}: {len(df)} linhas brutas extraídas")

    if verbose:
        print("[2/5] Rodando validações de qualidade...")
    quality_df = build_quality_report(raw)
    quality_df.to_csv(QUALIDADE_REPORT_PATH, index=False, encoding="utf-8-sig")
    n_alertas = int(quality_df.loc[quality_df["severidade"].isin(["alta", "media"]), "quantidade"].sum())
    if verbose:
        print(f"      -> {QUALIDADE_REPORT_PATH} ({len(quality_df)} regras, {n_alertas} ocorrências alta/média)")

    if verbose:
        print("[3/5] Transformando (limpeza, normalização, tabelas fato)...")
    fact = transform_all(raw)
    for k, df in fact.items():
        if verbose:
            print(f"      - fact_{k}: {len(df)} linhas após limpeza")

    if verbose:
        print("[4/5] Salvando dados processados (camada privada + camada pública)...")
    for key, (private_path, public_path) in FACT_PATHS.items():
        fact[key].to_csv(private_path, index=False, encoding="utf-8-sig")

    public = build_public_layer(fact)
    for key, (private_path, public_path) in FACT_PATHS.items():
        public[key].to_csv(public_path, index=False, encoding="utf-8-sig")
    if verbose:
        print(f"      -> camada pública salva em data/processed_public/ "
              f"(colunas de PII removidas: {PII_COLUMNS_BY_FACT})")

    datas_max = []
    for df in fact.values():
        if "data" in df.columns and df["data"].notna().any():
            datas_max.append(pd.to_datetime(df["data"]).max())
    data_atualizacao = max(datas_max).strftime("%Y-%m-%d") if datas_max else None

    metadata = {
        "gerado_em": datetime.now().isoformat(timespec="seconds"),
        "dados_atualizados_ate": data_atualizacao,
        "n_alertas_qualidade": n_alertas,
        "linhas": {k: int(len(df)) for k, df in fact.items()},
        "tempo_execucao_segundos": round(time.time() - t0, 1),
    }
    # metadata.json não contém nenhum dado individual (só datas/contagens),
    # então é salvo igual nas duas camadas.
    with open(METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    with open(METADATA_PUBLIC_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    if verbose:
        print(f"[5/5] Concluído em {metadata['tempo_execucao_segundos']}s. "
              f"Dados atualizados até {data_atualizacao}.")
    return metadata


if __name__ == "__main__":
    try:
        run()
    except Exception as exc:  # noqa: BLE001
        print(f"ERRO no pipeline: {exc}", file=sys.stderr)
        raise
