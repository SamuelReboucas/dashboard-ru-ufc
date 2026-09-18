"""
Configuração central do projeto: paths (via pathlib, sem caminhos absolutos
hardcoded) e carregamento do config/mappings.yaml.
"""
from __future__ import annotations

from pathlib import Path
from functools import lru_cache
import yaml

# BASE_DIR = raiz do projeto (um nível acima de src/)
BASE_DIR = Path(__file__).resolve().parent.parent

DATA_RAW_DIR = BASE_DIR / "data" / "raw"
DATA_PROCESSED_DIR = BASE_DIR / "data" / "processed"
DATA_PROCESSED_PUBLIC_DIR = BASE_DIR / "data" / "processed_public"
DATA_POWERBI_DIR = BASE_DIR / "data" / "powerbi"
OUTPUTS_DIR = BASE_DIR / "outputs"
DOCS_DIR = BASE_DIR / "docs"
CONFIG_DIR = BASE_DIR / "config"

MAPPINGS_PATH = CONFIG_DIR / "mappings.yaml"

# ---------------------------------------------------------------------------
# Camada privada (data/processed/) — dados completos, NUNCA versionados
# (bloqueados pelo .gitignore). Usada localmente quando existir.
# ---------------------------------------------------------------------------
FACT_DETALHE_PATH = DATA_PROCESSED_DIR / "fact_detalhe.csv"
FACT_SENSORIAL_PATH = DATA_PROCESSED_DIR / "fact_sensorial.csv"
FACT_ISC_PATH = DATA_PROCESSED_DIR / "fact_isc.csv"
FACT_GESTAO_ATENDIMENTOS_PATH = DATA_PROCESSED_DIR / "fact_gestao_atendimentos.csv"
FACT_GESTAO_MANUTENCAO_PATH = DATA_PROCESSED_DIR / "fact_gestao_manutencao.csv"
METADATA_PATH = DATA_PROCESSED_DIR / "metadata.json"

# ---------------------------------------------------------------------------
# Camada pública (data/processed_public/) — mesma estrutura, sem nenhuma
# coluna de PII (ver src/transform.build_public_layer). É a única camada de
# dados que vai para o GitHub / Streamlit Community Cloud.
#
# `sensorial` tem nome de arquivo diferente (fact_sensorial_agg.csv) para
# deixar explícito, já no nome do arquivo, que essa versão não é a bruta
# (a original tem a coluna `avaliador`, removida na versão pública).
# ---------------------------------------------------------------------------
FACT_DETALHE_PUBLIC_PATH = DATA_PROCESSED_PUBLIC_DIR / "fact_detalhe.csv"
FACT_SENSORIAL_PUBLIC_PATH = DATA_PROCESSED_PUBLIC_DIR / "fact_sensorial_agg.csv"
FACT_ISC_PUBLIC_PATH = DATA_PROCESSED_PUBLIC_DIR / "fact_isc.csv"
FACT_GESTAO_ATENDIMENTOS_PUBLIC_PATH = DATA_PROCESSED_PUBLIC_DIR / "fact_gestao_atendimentos.csv"
FACT_GESTAO_MANUTENCAO_PUBLIC_PATH = DATA_PROCESSED_PUBLIC_DIR / "fact_gestao_manutencao.csv"
METADATA_PUBLIC_PATH = DATA_PROCESSED_PUBLIC_DIR / "metadata.json"

# Mapa único {chave lógica: (caminho privado, caminho público)} — usado tanto
# pelo pipeline (para salvar) quanto pelo dashboard (para ler, com fallback).
FACT_PATHS = {
    "detalhe": (FACT_DETALHE_PATH, FACT_DETALHE_PUBLIC_PATH),
    "isc": (FACT_ISC_PATH, FACT_ISC_PUBLIC_PATH),
    "sensorial": (FACT_SENSORIAL_PATH, FACT_SENSORIAL_PUBLIC_PATH),
    "atendimentos": (FACT_GESTAO_ATENDIMENTOS_PATH, FACT_GESTAO_ATENDIMENTOS_PUBLIC_PATH),
    "manutencao": (FACT_GESTAO_MANUTENCAO_PATH, FACT_GESTAO_MANUTENCAO_PUBLIC_PATH),
}

QUALIDADE_REPORT_PATH = OUTPUTS_DIR / "relatorio_qualidade.csv"
PREPARACOES_SEM_CLASSIFICACAO_PATH = OUTPUTS_DIR / "preparacoes_sem_classificacao_termica.csv"

# ---------------------------------------------------------------------------
# Camada Power BI (data/powerbi/) — modelo estrela derivado das tabelas fato
# já tratadas (src/powerbi_export.py). Sem PII (auditado — só ISC/produção/
# temperatura, nunca fact_sensorial nem dados de atendimento/gestão).
# ---------------------------------------------------------------------------
DIM_DATA_PATH = DATA_POWERBI_DIR / "dim_data.csv"
DIM_RU_PATH = DATA_POWERBI_DIR / "dim_ru.csv"
DIM_REFEICAO_PATH = DATA_POWERBI_DIR / "dim_refeicao.csv"
DIM_PREPARACAO_PATH = DATA_POWERBI_DIR / "dim_preparacao.csv"
DIM_TIPO_PREPARACAO_PATH = DATA_POWERBI_DIR / "dim_tipo_preparacao.csv"
FACT_REFEICOES_PATH = DATA_POWERBI_DIR / "fact_refeicoes.csv"
FACT_PRODUCAO_PATH = DATA_POWERBI_DIR / "fact_producao.csv"
FACT_SATISFACAO_PATH = DATA_POWERBI_DIR / "fact_satisfacao.csv"
FACT_TEMPERATURA_PATH = DATA_POWERBI_DIR / "fact_temperatura.csv"

POWERBI_PATHS = {
    "dim_data": DIM_DATA_PATH,
    "dim_ru": DIM_RU_PATH,
    "dim_refeicao": DIM_REFEICAO_PATH,
    "dim_preparacao": DIM_PREPARACAO_PATH,
    "dim_tipo_preparacao": DIM_TIPO_PREPARACAO_PATH,
    "fact_refeicoes": FACT_REFEICOES_PATH,
    "fact_producao": FACT_PRODUCAO_PATH,
    "fact_satisfacao": FACT_SATISFACAO_PATH,
    "fact_temperatura": FACT_TEMPERATURA_PATH,
}


@lru_cache(maxsize=1)
def load_mappings() -> dict:
    """Carrega e cacheia config/mappings.yaml (fonte única de aliases/regras)."""
    with open(MAPPINGS_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def excel_path() -> Path:
    """Caminho do Excel bruto dentro de data/raw/, conforme mappings.yaml."""
    mp = load_mappings()
    return DATA_RAW_DIR / mp["excel_file"]


def ensure_dirs() -> None:
    for d in (DATA_RAW_DIR, DATA_PROCESSED_DIR, DATA_PROCESSED_PUBLIC_DIR, DATA_POWERBI_DIR, OUTPUTS_DIR, DOCS_DIR):
        d.mkdir(parents=True, exist_ok=True)


def resolve_fact_path(key: str) -> Path | None:
    """Resolve o caminho de leitura para uma tabela fato: prioriza a camada
    privada (data/processed/, dados completos, uso local) e cai para a
    camada pública (data/processed_public/, é a única presente em produção/
    Streamlit Community Cloud, pois a privada é bloqueada pelo .gitignore).
    Retorna None se nenhuma das duas existir."""
    private_path, public_path = FACT_PATHS[key]
    if private_path.exists():
        return private_path
    if public_path.exists():
        return public_path
    return None


def resolve_metadata_path() -> Path | None:
    if METADATA_PATH.exists():
        return METADATA_PATH
    if METADATA_PUBLIC_PATH.exists():
        return METADATA_PUBLIC_PATH
    return None
