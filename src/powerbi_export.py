"""
Camada Power BI — modelo estrela.

Responsabilidade: transformar as tabelas fato JÁ TRATADAS por
src/transform.py (fact_detalhe, fact_isc) em um modelo dimensional
(dimensões + fatos) pronto para consumo direto no Power BI via medidas
simples (SUM/AVERAGE/DIVIDE), sem precisar de nenhuma correção de
granularidade ou regra de negócio em DAX/Power Query.

Regras de negócio validadas contra a base real antes de serem
implementadas aqui (ver docs/aderencia_orientacoes_gestao.md, seção 3):

  Cons. Real  = Peso Líq − Sobra Limpa − Sobra Suja     [validado 100%]
  ISC         = (ÓTIMO×10 + REGULAR×5 + RUIM×1) / total  [validado 100%]

Regras derivadas algebricamente da primeira (não precisam de validação
adicional, pois são a mesma equação reescrita):

  Quantidade distribuída = Peso Líq − Sobra Limpa = Cons. Real + Sobra Suja
  Resto-Ingesta (kg)     = Sobra Suja
  % Resto-Ingesta         = Sobra Suja / Quantidade distribuída × 100

O que esta camada NUNCA calcula (permanece bloqueado — ver
docs/perguntas_validacao_nutricao.md): conformidade de temperatura
(classe quente/fria, limites de conformidade).
"""
from __future__ import annotations

import re

import numpy as np
import pandas as pd

from src.config import load_mappings
from src.metrics import _meal_level


# ---------------------------------------------------------------------------
# Limpeza específica de temperatura (não fazia parte de transform.py porque,
# até esta etapa, `temp_c` não estava mapeada em nenhuma tabela fato)
# ---------------------------------------------------------------------------


def clean_temperatura(value) -> float:
    """Converte o valor bruto de `Temp (°C)` para float, tratando os padrões
    de sujeira observados na fonte:
      - leituras duplas na mesma célula, separadas por "/" (ex.: "14,9/14,9")
        -> média das leituras numéricas encontradas;
      - vírgula decimal brasileira (ex.: "60,,6" -> 60.6);
      - marcadores de ausência ("-", "NA", " ") -> NaN (nunca 0).
    Não faz nenhuma classificação de conformidade — só limpeza numérica.
    """
    if value is None:
        return np.nan
    if isinstance(value, (int, float)):
        return float(value)

    s = str(value).strip()
    if s == "" or s.upper() in {"-", "NA", "N/A"}:
        return np.nan

    partes = s.split("/")
    numeros = []
    for p in partes:
        p2 = p.strip().replace(",", ".")
        while ".." in p2:
            p2 = p2.replace("..", ".")
        try:
            numeros.append(float(p2))
        except ValueError:
            continue

    if not numeros:
        return np.nan
    return float(sum(numeros) / len(numeros))


def clean_temperatura_series(series: pd.Series) -> pd.Series:
    return series.map(clean_temperatura)


# Faixa fisicamente plausível para temperatura de alimento em serviço.
# NÃO é um limite de conformidade sanitária (isso segue bloqueado — ver
# docs/perguntas_validacao_nutricao.md) — é só uma checagem de qualidade de
# dado: acima de 100°C (ponto de ebulição da água) ou abaixo de -5°C não é
# uma leitura plausível de alimento e quase certamente é erro de digitação
# (ex.: "614" em vez de "61,4"). Achado real desta etapa: 4 de 15.786
# leituras (0,03%) excedem essa faixa.
TEMPERATURA_FISICA_MIN = -5.0
TEMPERATURA_FISICA_MAX = 100.0


def is_temperatura_plausivel(temperatura_c: pd.Series) -> pd.Series:
    return temperatura_c.between(TEMPERATURA_FISICA_MIN, TEMPERATURA_FISICA_MAX)


# ---------------------------------------------------------------------------
# Conformidade de temperatura — regra oficial confirmada pela Nutrição
# (config/mappings.yaml: limite_conformidade_quente_c / _fria_c). Operadores
# assimétricos preservados exatamente como fornecidos:
#   quente: > limite -> CONFORME · <= limite -> NAO_CONFORME
#   fria:   < limite -> CONFORME · >= limite -> NAO_CONFORME
# ---------------------------------------------------------------------------

STATUS_CONFORME = "CONFORME"
STATUS_NAO_CONFORME = "NAO_CONFORME"
STATUS_SEM_CLASSIFICACAO = "SEM_CLASSIFICACAO"
STATUS_SEM_MEDICAO = "SEM_MEDICAO"
STATUS_MEDICAO_INVALIDA = "MEDICAO_INVALIDA"


def get_classe_termica(tipo_preparacao) -> str | None:
    """Classificação quente/fria de um tipo_preparacao, só para as
    categorias listadas em config/mappings.yaml (`classe_termica_por_tipo_preparacao`)
    — NUNCA inferida a partir da temperatura observada. Categoria não
    listada -> None (vira SEM_CLASSIFICACAO)."""
    mp = load_mappings()
    mapa = mp.get("classe_termica_por_tipo_preparacao", {})
    return mapa.get(tipo_preparacao)


def compute_status_temperatura(
    temperatura_c: float,
    temperatura_valida: bool,
    temperatura_plausivel: bool,
    classe_termica: str | None,
) -> str:
    """Aplica a regra oficial da Nutrição, na ordem correta de precedência:
    1) sem medição -> SEM_MEDICAO
    2) medição fisicamente implausível -> MEDICAO_INVALIDA (nunca entra no
       denominador de conformidade)
    3) sem classificação térmica conhecida -> SEM_CLASSIFICACAO
    4) aplica o limite conforme a classe (operadores exatamente como
       fornecidos pela Nutrição — note a assimetria proposital entre
       quente e fria)
    """
    if not temperatura_valida:
        return STATUS_SEM_MEDICAO
    if not temperatura_plausivel:
        return STATUS_MEDICAO_INVALIDA
    if classe_termica is None:
        return STATUS_SEM_CLASSIFICACAO

    mp = load_mappings()
    limite_quente = mp["limite_conformidade_quente_c"]
    limite_fria = mp["limite_conformidade_fria_c"]

    if classe_termica == "quente":
        return STATUS_CONFORME if temperatura_c > limite_quente else STATUS_NAO_CONFORME
    if classe_termica == "fria":
        return STATUS_CONFORME if temperatura_c < limite_fria else STATUS_NAO_CONFORME
    return STATUS_SEM_CLASSIFICACAO


def build_status_temperatura_series(
    temperatura_c: pd.Series, temperatura_valida: pd.Series,
    temperatura_plausivel: pd.Series, classe_termica: pd.Series,
) -> pd.Series:
    return pd.Series(
        [
            compute_status_temperatura(t, v, p, c)
            for t, v, p, c in zip(temperatura_c, temperatura_valida, temperatura_plausivel, classe_termica)
        ],
        index=temperatura_c.index,
    )


# ---------------------------------------------------------------------------
# Recuperação determinística da chave composta em fact_isc["preparacao"]
# ---------------------------------------------------------------------------

_PADRAO_CHAVE_COMPOSTA = re.compile(r"^[A-Za-zÀ-ÿ]+(\d{4,6})(.*)$")
_EXCEL_EPOCH = pd.Timestamp("1899-12-30")


def recuperar_tipo_preparacao_de_chave_composta(
    preparacao_bruta: str, data_linha, tipos_validos: set[str]
) -> str | None:
    """Achado desta etapa: em ~40% das linhas de `fact_isc`, a coluna
    "Preparação" não traz o nome do prato, e sim uma chave cacheada no
    formato `Refeição + Serial de data do Excel + tipo_preparacao` (ex.:
    `"Café46167Especial Veg"`). Confirmado com 100% de cobertura e 100% de
    exatidão (644/644 linhas): o serial da chave bate exatamente com a
    `data` da própria linha, e o texto restante bate exatamente com um
    valor real de `tipo_preparacao` (coluna `Prep` da fonte) — nunca com o
    nome do prato (`Cardápio`). Por isso só recuperamos `tipo_preparacao`
    aqui, nunca `preparacao` (ver docs/aderencia_orientacoes_gestao.md).

    Retorna o `tipo_preparacao` recuperado só quando AMBAS as checagens
    baterem (serial = data da linha E texto restante = tipo_preparacao
    conhecido); caso contrário, retorna None — nunca adivinha.
    """
    if preparacao_bruta is None or pd.isna(data_linha):
        return None
    m = _PADRAO_CHAVE_COMPOSTA.match(str(preparacao_bruta).strip())
    if not m:
        return None
    serial_txt, resto = m.groups()
    resto = resto.strip()
    try:
        serial = int(serial_txt)
        data_calculada = _EXCEL_EPOCH + pd.Timedelta(days=serial)
    except (ValueError, OverflowError):
        return None
    if data_calculada.normalize() != pd.Timestamp(data_linha).normalize():
        return None
    if resto not in tipos_validos:
        return None
    return resto


# ---------------------------------------------------------------------------
# Limpeza de campos de texto contra erros de fórmula do Excel
# ---------------------------------------------------------------------------


def clean_text_field(series: pd.Series) -> pd.Series:
    """Colunas de texto (cardápio, preparação) não passam por
    `to_numeric_safe`, então um erro de fórmula do Excel cacheado como texto
    (ex.: `"#N/A"`) chega aqui como string literal, não como NaN. Achado
    real desta etapa: a coluna `cardapio` de `fact_detalhe` tinha 11 valores
    exatamente iguais à string `"#N/A"` (não a um NaN de fato), que
    passavam despercebidos por qualquer limpeza anterior."""
    mp = load_mappings()
    erros = set(mp["valores_erro"])

    def _clean(v):
        if v is None:
            return np.nan
        s = str(v).strip()
        if s == "" or s in erros:
            return np.nan
        return v

    return series.map(_clean)


# ---------------------------------------------------------------------------
# Dimensões
# ---------------------------------------------------------------------------


def build_dim_ru() -> pd.DataFrame:
    """1 linha por RU, a partir de config/mappings.yaml (fonte única de
    nomes canônicos — nunca hardcoded aqui)."""
    mp = load_mappings()
    rows = [{"codigo": k, "nome": v} for k, v in mp["ru_canonico"].items()]
    return pd.DataFrame(rows)


def build_dim_refeicao() -> pd.DataFrame:
    mp = load_mappings()
    nomes = sorted(set(mp["refeicao_aliases"].values()))
    return pd.DataFrame({"nome": nomes})


def build_dim_data(datas: pd.Series) -> pd.DataFrame:
    """1 linha por data distinta encontrada nos fatos (não um calendário
    completo do ano — só as datas que realmente aparecem nos dados)."""
    datas_validas = pd.to_datetime(datas.dropna().unique())
    df = pd.DataFrame({"data": sorted(datas_validas)})
    df["dia"] = df["data"].dt.day
    df["mes"] = df["data"].dt.strftime("%B")
    df["mes_numero"] = df["data"].dt.month
    df["ano"] = df["data"].dt.year
    df["ano_mes"] = df["data"].dt.strftime("%Y-%m")
    df["trimestre"] = df["data"].dt.quarter
    return df


def build_dim_preparacao(fact_detalhe: pd.DataFrame) -> pd.DataFrame:
    """1 linha por combinação distinta (tipo_preparacao, preparacao)
    observada na base.

    `tipo_preparacao` = coluna `prep` (categoria fechada e estável: PB, PV,
    VEG, Arroz/Baião, Feijão, Guarnição, Salada, Sobremesa, Suco, Café,
    Leite, Pão, Fruta etc. — confirmado por inspeção de valores distintos,
    ver docs/aderencia_orientacoes_gestao.md).
    `preparacao` = coluna `cardapio` (o prato específico do dia dentro
    daquela categoria, ex.: "Frango Grelhado" dentro de PB).

    ATENÇÃO — estabilidade do id: `id_preparacao` é um surrogate sequencial
    gerado pela ordenação alfabética do par (tipo, preparacao) encontrado
    NESTA execução do pipeline. Se novas combinações aparecerem em uma
    atualização futura, os ids podem ser reatribuídos. Isso é aceitável
    para o estágio atual (Power BI recarrega o modelo inteiro a cada
    atualização), mas não deve ser tratado como chave estável entre
    versões do Power BI publicadas separadamente sem reprocessar tudo.
    """
    df = fact_detalhe[["prep", "cardapio"]].dropna(subset=["prep"]).copy()
    df = df.rename(columns={"prep": "tipo_preparacao", "cardapio": "preparacao"})
    df["preparacao"] = clean_text_field(df["preparacao"])
    df["preparacao"] = df["preparacao"].fillna("(sem cardápio informado)")
    dim = df.drop_duplicates().sort_values(["tipo_preparacao", "preparacao"]).reset_index(drop=True)
    dim.insert(0, "id_preparacao", range(1, len(dim) + 1))
    return dim


def build_dim_tipo_preparacao(dim_preparacao: pd.DataFrame) -> pd.DataFrame:
    """1 linha por `tipo_preparacao` distinto (grão mais alto que
    `dim_preparacao`, que é por prato específico).

    Por quê esta dimensão existe: `fact_satisfacao` tem `tipo_preparacao`
    preenchido em 100% das linhas (960 por match direto do nome do prato +
    644 recuperadas da chave composta — ver `build_fact_satisfacao`), mas
    `id_preparacao` só em 60% (as 644 recuperadas não têm o prato
    específico identificado, só a categoria). Se o slicer oficial de "tipo
    de preparação" usasse `dim_preparacao[tipo_preparacao]` — relacionada
    via `id_preparacao` — as 644 linhas sem prato específico ficariam de
    fora do filtro (o Power BI não filtra linhas cuja chave de
    relacionamento é nula). `dim_tipo_preparacao` resolve isso: relaciona
    direto pelo texto de `tipo_preparacao` (presente em 100% das linhas
    das 3 tabelas fato), então o filtro por tipo passa a cobrir toda a
    base, inclusive as linhas de satisfação sem prato específico.

    `dim_preparacao` é preservada sem alteração para filtros/análises que
    precisem do prato específico (ex.: "Per Capita por Preparação",
    "Top piores preparações").
    """
    tipos = sorted(dim_preparacao["tipo_preparacao"].dropna().unique())
    return pd.DataFrame({"tipo_preparacao": tipos})


# ---------------------------------------------------------------------------
# Fatos
# ---------------------------------------------------------------------------


def build_fact_refeicoes(fact_detalhe: pd.DataFrame) -> pd.DataFrame:
    """Grão: RU + Data + Refeição — uma única linha por combinação.

    Reaproveita literalmente `metrics._meal_level` (mesma função já usada e
    testada pelo Streamlit/MVP) para garantir que o total de refeições não
    seja multiplicado pelo número de preparações do dia. Isso resolve a
    granularidade NA ORIGEM (Python), para que o Power BI nunca precise de
    uma medida DAX complexa para desduplicar.
    """
    meal = _meal_level(fact_detalhe)
    meal = meal.rename(columns={"comensais_previsto": "refeicoes_previstas",
                                 "comensais_real": "refeicoes_realizadas"})
    # refeicoes_previstas é uma aproximação (maior previsão de prato da
    # refeição) — ver docs/indicadores.md. Mantido aqui só por já ser usado
    # no MVP; não é uma definição validada pela gestão.
    return meal.reset_index(drop=True)


def build_fact_producao(fact_detalhe: pd.DataFrame, dim_preparacao: pd.DataFrame) -> pd.DataFrame:
    """Grão: RU + Data + Refeição + Tipo de Preparação + Preparação (== o
    grão original de `fact_detalhe`, um por linha de preparação).

    Campos derivados, todos calculados a partir de fórmulas já validadas
    contra a base real (ver docstring do módulo):
      - quantidade_distribuida = peso_liq - sobra_limpa
      - resto_ingesta_kg       = sobra_suja
      - pct_resto_ingesta      = resto_ingesta_kg / quantidade_distribuida
                                 (informativo, POR LINHA — para agregações
                                 de várias linhas, a medida do Power BI deve
                                 somar os numeradores e denominadores
                                 separadamente antes de dividir; nunca tirar
                                 média desta coluna. Ver docs/medidas_powerbi.md)
      - per_capita_g_comensal  = consumo_real (kg) × 1000 / comensais_real
                                 (informativo, POR LINHA — válido neste grão
                                 porque `comensais_real` já é o valor único
                                 da refeição; ao agregar entre preparações ou
                                 datas, a medida do Power BI deve buscar o
                                 denominador em `fact_refeicoes`, nunca somar
                                 `comensais_real` dentro de `fact_producao`)
    """
    df = fact_detalhe.copy()

    df["quantidade_distribuida"] = df["peso_liq"] - df["sobra_limpa"]
    df["resto_ingesta_kg"] = df["sobra_suja"]

    qd_safe = df["quantidade_distribuida"].replace(0, np.nan)
    df["pct_resto_ingesta"] = (df["resto_ingesta_kg"] / qd_safe) * 100

    comensais_safe = df["comensais_real"].replace(0, np.nan)
    df["per_capita_g_comensal"] = (df["consumo_real"] * 1000) / comensais_safe

    df = df.rename(columns={"prep": "tipo_preparacao", "cardapio": "preparacao"})
    df["preparacao"] = clean_text_field(df["preparacao"])
    df["preparacao"] = df["preparacao"].fillna("(sem cardápio informado)")

    df = df.merge(
        dim_preparacao[["id_preparacao", "tipo_preparacao", "preparacao"]],
        on=["tipo_preparacao", "preparacao"],
        how="left",
    )

    cols = [
        "ru", "data", "refeicao", "id_preparacao", "tipo_preparacao", "preparacao",
        "peso_bruto", "peso_liq", "sobra_limpa", "sobra_suja",
        "quantidade_distribuida", "consumo_real", "comensais_real",
        "resto_ingesta_kg", "pct_resto_ingesta", "per_capita_g_comensal",
    ]
    return df[cols].reset_index(drop=True)


def build_fact_satisfacao(fact_isc: pd.DataFrame, dim_preparacao: pd.DataFrame) -> pd.DataFrame:
    """Grão: RU + Data + Refeição + Preparação (quando identificável — ver
    achado sobre chave composta abaixo).

    Preserva as contagens brutas (`otimo`, `regular`, `ruim`) para que o
    Power BI agregue corretamente (soma de contagens, nunca média de
    percentuais/ISC pré-calculado). `isc_linha` é mantido só como referência
    do valor já calculado na fonte (validado 100% contra a fórmula oficial
    nesta etapa) — a medida agregada no Power BI deve ser recalculada a
    partir das somas de `otimo`/`regular`/`ruim` no contexto de filtro,
    nunca `AVERAGE(isc_linha)` (ver docs/medidas_powerbi.md).

    ACHADO DESTA ETAPA — chave composta parcialmente recuperável: a coluna
    "Preparação" das abas de ISC nem sempre contém o nome limpo do prato.
    Em ~40% das linhas ela é uma chave cacheada (ex.:
    `"Café46167Especial Veg"`, concatenando refeição + serial de data do
    Excel + tipo_preparacao). Essa chave é 100% recuperável de forma
    determinística para o campo `tipo_preparacao` (nunca para o nome do
    prato específico — ver `recuperar_tipo_preparacao_de_chave_composta`).
    Nenhuma linha é descartada: todas as 1.604 linhas continuam somáveis
    por RU/data/refeição; a quebra por preparação específica (`preparacao`)
    fica marcada como `"NAO_IDENTIFICADA"` quando não há nome de prato
    limpo, mas `tipo_preparacao` fica preenchido sempre que recuperável.
    """
    df = fact_isc.copy()
    df["total_respostas"] = df["otimo"] + df["regular"] + df["ruim"]
    df = df.rename(columns={"isc": "isc_linha"})
    df["preparacao_bruta"] = df["preparacao"]
    df["preparacao"] = clean_text_field(df["preparacao"])

    # 1) tentativa de match direto por nome limpo do prato (join em dim_preparacao)
    dim_join = dim_preparacao[["id_preparacao", "tipo_preparacao", "preparacao"]].drop_duplicates(subset=["preparacao"])
    df = df.merge(dim_join, on="preparacao", how="left")
    # Força dtype "object" em tipo_preparacao: se dim_preparacao vier vazia
    # (ex.: primeira execução, ou em testes), o merge cria a coluna como
    # float64 (todo-NaN), e atribuir texto/None nela mais abaixo levantaria
    # TypeError nas versões recentes do pandas.
    df["tipo_preparacao"] = df["tipo_preparacao"].astype(object)

    # 2) para as linhas sem match direto, tentar recuperar tipo_preparacao
    #    a partir da chave composta (determinístico, ver docstring acima)
    tipos_validos = set(dim_preparacao["tipo_preparacao"].dropna().unique())
    sem_match = df["id_preparacao"].isna()
    df.loc[sem_match, "tipo_preparacao"] = [
        recuperar_tipo_preparacao_de_chave_composta(bruta, data, tipos_validos)
        for bruta, data in zip(df.loc[sem_match, "preparacao_bruta"], df.loc[sem_match, "data"])
    ]
    # nome do prato específico continua desconhecido nesses casos — nunca
    # inventado (id_preparacao permanece nulo: sabemos a categoria, não o prato)
    df.loc[sem_match, "preparacao"] = "NAO_IDENTIFICADA"

    cols = ["ru", "data", "refeicao", "id_preparacao", "tipo_preparacao", "preparacao", "preparacao_bruta",
            "otimo", "regular", "ruim", "total_respostas", "isc_linha"]
    return df[cols].reset_index(drop=True)


def build_fact_temperatura(fact_detalhe: pd.DataFrame, dim_preparacao: pd.DataFrame) -> pd.DataFrame:
    """Grão: RU + Data + Refeição + Tipo de Preparação + Preparação — o
    mesmo grão de `fact_producao`, que é o grão real disponível na fonte
    hoje (ver ressalva sobre leituras duplas em docs/aderencia_orientacoes_gestao.md,
    seção 5 — o processo real pode ter mais de uma medição por linha, mas a
    planilha-fonte já as concatena em uma única célula antes de chegar aqui).

    `temperatura_plausivel` é uma checagem de QUALIDADE DE DADO (faixa
    fisicamente possível, -5°C a 100°C), não uma regra de conformidade
    sanitária — não confundir as duas. Achado desta etapa: 4 de 15.786
    leituras (0,03%) excedem essa faixa (ex.: "614°C"), quase certamente
    erro de digitação na fonte — essas leituras NUNCA entram no
    denominador de conformidade (`status_temperatura = MEDICAO_INVALIDA`).

    `classe_termica` e `status_temperatura` aplicam a regra oficial da
    Nutrição (config/mappings.yaml). Classificação só para tipos
    inequivocamente mapeados — as demais preparações recebem
    `SEM_CLASSIFICACAO`, nunca uma classe inferida da temperatura
    observada (isso seria circular/inválido).
    """
    df = fact_detalhe.copy()
    df["temperatura_c"] = clean_temperatura_series(df["temp_c"])
    df["temperatura_valida"] = df["temperatura_c"].notna()
    df["temperatura_plausivel"] = df["temperatura_c"].notna() & is_temperatura_plausivel(df["temperatura_c"])

    df = df.rename(columns={"prep": "tipo_preparacao", "cardapio": "preparacao"})
    df["preparacao"] = clean_text_field(df["preparacao"])
    df["preparacao"] = df["preparacao"].fillna("(sem cardápio informado)")

    df["classe_termica"] = df["tipo_preparacao"].map(get_classe_termica)

    mp = load_mappings()
    limite_quente = mp["limite_conformidade_quente_c"]
    limite_fria = mp["limite_conformidade_fria_c"]
    df["limite_referencia"] = df["classe_termica"].map(
        {"quente": f"> {limite_quente}°C", "fria": f"< {limite_fria}°C"}
    )

    df["status_temperatura"] = build_status_temperatura_series(
        df["temperatura_c"], df["temperatura_valida"], df["temperatura_plausivel"], df["classe_termica"]
    )

    df = df.merge(
        dim_preparacao[["id_preparacao", "tipo_preparacao", "preparacao"]],
        on=["tipo_preparacao", "preparacao"],
        how="left",
    )

    cols = ["ru", "data", "refeicao", "id_preparacao", "tipo_preparacao", "preparacao",
            "temperatura_c", "temperatura_valida", "temperatura_plausivel",
            "classe_termica", "limite_referencia", "status_temperatura"]
    return df[cols].reset_index(drop=True)


def build_relatorio_sem_classificacao_termica(fact_temperatura: pd.DataFrame) -> pd.DataFrame:
    """Relatório de auditoria: quais (tipo_preparacao, preparacao) ficaram
    sem classificação térmica, com volume e faixa de temperatura observada
    — só para a Nutrição decidir se vale a pena classificá-las. A faixa/
    mediana é puramente informativa; NUNCA é usada para decidir a classe
    automaticamente (isso seria circular)."""
    sem_classe = fact_temperatura[fact_temperatura["classe_termica"].isna()]
    if sem_classe.empty:
        return pd.DataFrame(columns=[
            "tipo_preparacao", "preparacao", "quantidade_registros",
            "quantidade_medicoes_validas", "temperatura_min", "temperatura_mediana", "temperatura_max",
        ])

    grouped = sem_classe.groupby(["tipo_preparacao", "preparacao"], dropna=False).agg(
        quantidade_registros=("temperatura_c", "size"),
        quantidade_medicoes_validas=("temperatura_valida", "sum"),
        temperatura_min=("temperatura_c", "min"),
        temperatura_mediana=("temperatura_c", "median"),
        temperatura_max=("temperatura_c", "max"),
    ).reset_index()
    return grouped.sort_values("quantidade_registros", ascending=False).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Referência de validação — Per Capita agregado (não é chamada pelo
# pipeline; existe para provar, em Python, que a medida DAX documentada em
# docs/medidas_powerbi.md está correta antes de ser adotada no Power BI —
# ver achado sobre `dim_preparacao` não propagar filtro para
# `fact_refeicoes`)
# ---------------------------------------------------------------------------


def per_capita_agregado_por_preparacao(fact_producao: pd.DataFrame, by: list[str] | None = None) -> pd.DataFrame:
    """Replica em Python exatamente o que a medida DAX
    `Per Capita (g/comensal) por Preparação` deve calcular:
    `SUM(consumo_real) × 1000 / SUM(comensais_real DEDUPLICADO por
    RU+Data+Refeição)`, agrupado por `by` (padrão: tipo_preparacao +
    preparacao).

    O ponto crítico que esta função existe para validar: `comensais_real`
    é o mesmo valor repetido em toda preparação da mesma refeição. Se o
    agrupamento somasse `comensais_real` direto (uma linha por
    preparação), o denominador seria inflado pelo número de preparações
    daquele grupo — o mesmo bug de granularidade já documentado em
    `metrics._meal_level`, só que agora no contexto de uma medida
    filtrada por preparação (onde `fact_refeicoes` não pode ser usada
    diretamente porque o filtro de `dim_preparacao`/`dim_tipo_preparacao`
    não se propaga a ela — não há relacionamento entre elas).
    """
    grupo = by or ["tipo_preparacao", "preparacao"]

    def _calc(g: pd.DataFrame) -> pd.Series:
        consumo_total = g["consumo_real"].sum()
        comensais_dedup = g.drop_duplicates(subset=["ru", "data", "refeicao"])["comensais_real"]
        comensais_total = comensais_dedup.sum()
        per_capita = (consumo_total * 1000 / comensais_total) if comensais_total else np.nan
        return pd.Series({
            "consumo_real_total": consumo_total,
            "comensais_correspondentes": comensais_total,
            "per_capita_g_comensal": per_capita,
        })

    return (
        fact_producao.groupby(grupo, dropna=False)
        .apply(_calc)
        .reset_index()
    )


def build_all_powerbi_tables(fact: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """`fact` é o dicionário já produzido por `src.transform.transform_all`
    (mesma camada privada usada pelo Streamlit) — nenhuma extração nova é
    feita aqui.

    Retorna também `relatorio_sem_classificacao_termica` (não é uma tabela
    do modelo estrela — é um relatório de auditoria, salvo pelo pipeline em
    `outputs/`, não em `data/powerbi/`)."""
    fact_detalhe = fact["detalhe"]
    fact_isc = fact["isc"]

    dim_ru = build_dim_ru()
    dim_refeicao = build_dim_refeicao()
    dim_preparacao = build_dim_preparacao(fact_detalhe)
    dim_tipo_preparacao = build_dim_tipo_preparacao(dim_preparacao)

    todas_datas = pd.concat([fact_detalhe["data"], fact_isc["data"]], ignore_index=True)
    dim_data = build_dim_data(todas_datas)

    fact_refeicoes = build_fact_refeicoes(fact_detalhe)
    fact_producao = build_fact_producao(fact_detalhe, dim_preparacao)
    fact_satisfacao = build_fact_satisfacao(fact_isc, dim_preparacao)
    fact_temperatura = build_fact_temperatura(fact_detalhe, dim_preparacao)

    relatorio_sem_classificacao = build_relatorio_sem_classificacao_termica(fact_temperatura)

    return {
        "dim_data": dim_data,
        "dim_ru": dim_ru,
        "dim_refeicao": dim_refeicao,
        "dim_preparacao": dim_preparacao,
        "dim_tipo_preparacao": dim_tipo_preparacao,
        "fact_refeicoes": fact_refeicoes,
        "fact_producao": fact_producao,
        "fact_satisfacao": fact_satisfacao,
        "fact_temperatura": fact_temperatura,
        "relatorio_sem_classificacao_termica": relatorio_sem_classificacao,
    }
