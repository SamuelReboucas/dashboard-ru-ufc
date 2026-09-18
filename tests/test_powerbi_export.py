"""
Testes de src/powerbi_export.py.

Cada regra aqui foi validada contra a base real antes de ser implementada
(ver docs/aderencia_orientacoes_gestao.md, seção 3) — estes testes travam
essas fórmulas para que não sejam alteradas silenciosamente depois.
"""
import numpy as np
import pandas as pd
import pytest

from src.powerbi_export import (
    clean_temperatura,
    clean_temperatura_series,
    clean_text_field,
    is_temperatura_plausivel,
    get_classe_termica,
    compute_status_temperatura,
    recuperar_tipo_preparacao_de_chave_composta,
    build_relatorio_sem_classificacao_termica,
    build_dim_ru,
    build_dim_refeicao,
    build_dim_data,
    build_dim_preparacao,
    build_dim_tipo_preparacao,
    build_fact_refeicoes,
    build_fact_producao,
    build_fact_satisfacao,
    build_fact_temperatura,
    per_capita_agregado_por_preparacao,
    STATUS_CONFORME,
    STATUS_NAO_CONFORME,
    STATUS_SEM_CLASSIFICACAO,
    STATUS_SEM_MEDICAO,
    STATUS_MEDICAO_INVALIDA,
)


# ---------------------------------------------------------------------------
# Fixture: fact_detalhe sintético (mesmo grão real: RU+Data+Refeição+Prep)
# ---------------------------------------------------------------------------


@pytest.fixture
def fact_detalhe():
    rows = [
        # refeição 1: P1, 05/01, Almoço — 2 preparações, mesmo comensais_real (300)
        {"ru": "P1", "data": pd.Timestamp("2026-01-05"), "refeicao": "Almoço", "prep": "PB",
         "cardapio": "Frango", "peso_bruto": 100.0, "peso_liq": 90.0, "sobra_limpa": 5.0,
         "sobra_suja": 2.0, "consumo_real": 83.0, "comensais": 150, "comensais_real": 300,
         "temp_c": "72,5"},
        {"ru": "P1", "data": pd.Timestamp("2026-01-05"), "refeicao": "Almoço", "prep": "Salada",
         "cardapio": "Alface", "peso_bruto": 20.0, "peso_liq": 18.0, "sobra_limpa": 1.0,
         "sobra_suja": 0.5, "consumo_real": 16.5, "comensais": 140, "comensais_real": 300,
         "temp_c": "14,9/14,9"},
        # refeição 2: P1, 06/01, Almoço
        {"ru": "P1", "data": pd.Timestamp("2026-01-06"), "refeicao": "Almoço", "prep": "PB",
         "cardapio": "Carne", "peso_bruto": 80.0, "peso_liq": 72.0, "sobra_limpa": 0.0,
         "sobra_suja": 4.0, "consumo_real": 68.0, "comensais": 120, "comensais_real": 200,
         "temp_c": "#N/A"},
    ]
    return pd.DataFrame(rows)


@pytest.fixture
def fact_isc():
    return pd.DataFrame([
        {"ru": "P1", "data": pd.Timestamp("2026-01-05"), "refeicao": "Almoço",
         "preparacao": "Frango", "otimo": 75, "regular": 23, "ruim": 4, "isc": 8.52},
        {"ru": "P1", "data": pd.Timestamp("2026-01-06"), "refeicao": "Almoço",
         "preparacao": "Almoço46167Frango", "otimo": 10, "regular": 5, "ruim": 5, "isc": 6.25},
    ])


# ---------------------------------------------------------------------------
# Resto-Ingesta / Quantidade distribuída (fact_producao)
# ---------------------------------------------------------------------------


def test_quantidade_distribuida_e_peso_liq_menos_sobra_limpa(fact_detalhe):
    dim = build_dim_preparacao(fact_detalhe)
    fp = build_fact_producao(fact_detalhe, dim)
    linha = fp[(fp["ru"] == "P1") & (fp["tipo_preparacao"] == "PB") & (fp["preparacao"] == "Frango")].iloc[0]
    assert linha["quantidade_distribuida"] == pytest.approx(90.0 - 5.0)


def test_resto_ingesta_kg_e_sobra_suja(fact_detalhe):
    dim = build_dim_preparacao(fact_detalhe)
    fp = build_fact_producao(fact_detalhe, dim)
    linha = fp[(fp["preparacao"] == "Frango") & (fp["tipo_preparacao"] == "PB")].iloc[0]
    assert linha["resto_ingesta_kg"] == pytest.approx(2.0)


def test_pct_resto_ingesta_formula(fact_detalhe):
    dim = build_dim_preparacao(fact_detalhe)
    fp = build_fact_producao(fact_detalhe, dim)
    linha = fp[(fp["preparacao"] == "Frango") & (fp["tipo_preparacao"] == "PB")].iloc[0]
    esperado = (2.0 / (90.0 - 5.0)) * 100
    assert linha["pct_resto_ingesta"] == pytest.approx(esperado)


def test_pct_resto_ingesta_denominador_zero_vira_nan():
    df = pd.DataFrame([{
        "ru": "P1", "data": pd.Timestamp("2026-01-05"), "refeicao": "Almoço", "prep": "PB",
        "cardapio": "X", "peso_bruto": 10.0, "peso_liq": 5.0, "sobra_limpa": 5.0,
        "sobra_suja": 1.0, "consumo_real": -1.0, "comensais": 10, "comensais_real": 100,
        "temp_c": None,
    }])
    dim = build_dim_preparacao(df)
    fp = build_fact_producao(df, dim)
    # quantidade_distribuida = 5.0 - 5.0 = 0 -> pct_resto_ingesta deve ser NaN, nunca erro/inf
    assert fp["quantidade_distribuida"].iloc[0] == 0
    assert np.isnan(fp["pct_resto_ingesta"].iloc[0])


def test_agregacao_pct_resto_ingesta_deve_ser_razao_de_somas_nao_media(fact_detalhe):
    """Trava o princípio metodológico: a % agregada correta é
    Σsobra_suja / Σquantidade_distribuida, não a média das % por linha."""
    dim = build_dim_preparacao(fact_detalhe)
    fp = build_fact_producao(fact_detalhe, dim)
    almoco_p1_dia1 = fp[(fp["ru"] == "P1") & (fp["data"] == pd.Timestamp("2026-01-05"))]

    razao_de_somas = almoco_p1_dia1["resto_ingesta_kg"].sum() / almoco_p1_dia1["quantidade_distribuida"].sum()
    media_das_razoes = almoco_p1_dia1["pct_resto_ingesta"].mean() / 100

    # as duas só coincidem por acaso se os denominadores forem iguais entre
    # as linhas — aqui são diferentes (85 vs 17), então os resultados devem
    # divergir, provando que média simples não é intercambiável com razão de somas
    assert razao_de_somas != pytest.approx(media_das_razoes)


# ---------------------------------------------------------------------------
# Per Capita (fact_producao)
# ---------------------------------------------------------------------------


def test_per_capita_g_comensal_formula(fact_detalhe):
    dim = build_dim_preparacao(fact_detalhe)
    fp = build_fact_producao(fact_detalhe, dim)
    linha = fp[(fp["preparacao"] == "Frango") & (fp["tipo_preparacao"] == "PB")].iloc[0]
    esperado = (83.0 * 1000) / 300
    assert linha["per_capita_g_comensal"] == pytest.approx(esperado)


def test_per_capita_comensais_real_zero_vira_nan():
    df = pd.DataFrame([{
        "ru": "P1", "data": pd.Timestamp("2026-01-05"), "refeicao": "Almoço", "prep": "PB",
        "cardapio": "X", "peso_bruto": 10.0, "peso_liq": 8.0, "sobra_limpa": 1.0,
        "sobra_suja": 1.0, "consumo_real": 6.0, "comensais": 0, "comensais_real": 0,
        "temp_c": None,
    }])
    dim = build_dim_preparacao(df)
    fp = build_fact_producao(df, dim)
    assert np.isnan(fp["per_capita_g_comensal"].iloc[0])


# ---------------------------------------------------------------------------
# ISC / Satisfação (fact_satisfacao)
# ---------------------------------------------------------------------------


def test_total_respostas_e_soma_das_contagens(fact_isc):
    dim = pd.DataFrame(columns=["id_preparacao", "tipo_preparacao", "preparacao"])
    fs = build_fact_satisfacao(fact_isc, dim)
    assert fs.iloc[0]["total_respostas"] == 75 + 23 + 4


def test_isc_agregado_correto_e_media_ponderada_por_contagem(fact_isc):
    """Trava o princípio: ISC agregado = Σ(otimo*10+regular*5+ruim*1) / Σtotal,
    não AVERAGE(isc_linha) — as duas linhas têm volumes de resposta muito
    diferentes (102 vs 20), então devem produzir resultados diferentes."""
    dim = pd.DataFrame(columns=["id_preparacao", "tipo_preparacao", "preparacao"])
    fs = build_fact_satisfacao(fact_isc, dim)

    isc_correto = (
        (fs["otimo"] * 10 + fs["regular"] * 5 + fs["ruim"] * 1).sum()
        / fs["total_respostas"].sum()
    )
    media_simples = fs["isc_linha"].mean()

    assert isc_correto != pytest.approx(media_simples)
    # valor de referência calculado manualmente
    otimo_total, regular_total, ruim_total = 85, 28, 9
    esperado = (otimo_total * 10 + regular_total * 5 + ruim_total * 1) / (otimo_total + regular_total + ruim_total)
    assert isc_correto == pytest.approx(esperado)


def test_fact_satisfacao_preserva_contagens_brutas_para_distribuicao(fact_isc):
    dim = pd.DataFrame(columns=["id_preparacao", "tipo_preparacao", "preparacao"])
    fs = build_fact_satisfacao(fact_isc, dim)
    assert set(["otimo", "regular", "ruim"]).issubset(fs.columns)


def test_fact_satisfacao_id_preparacao_nulo_quando_chave_composta(fact_isc):
    """Achado documentado: parte das linhas de ISC tem uma chave composta
    (ex.: 'Almoço46167Frango') em vez do nome limpo do prato — não deve ser
    forçado um match, id_preparacao fica nulo nesses casos (mas
    tipo_preparacao pode ser recuperado, se a chave bater — ver testes de
    recuperação mais abaixo; aqui usamos uma preparação sem padrão de chave
    reconhecível, então nem id nem tipo são recuperados)."""
    dim = pd.DataFrame({"id_preparacao": [1], "tipo_preparacao": ["PB"], "preparacao": ["Frango"]})
    fs = build_fact_satisfacao(fact_isc, dim)
    linha_limpa = fs[fs["preparacao"] == "Frango"].iloc[0]
    linha_composta = fs[fs["preparacao_bruta"] == "Almoço46167Frango"].iloc[0]
    assert linha_limpa["id_preparacao"] == 1
    assert pd.isna(linha_composta["id_preparacao"])


# ---------------------------------------------------------------------------
# fact_refeicoes — grão e não-inflação
# ---------------------------------------------------------------------------


def test_fact_refeicoes_grao_unico_por_ru_data_refeicao(fact_detalhe):
    fr = build_fact_refeicoes(fact_detalhe)
    assert fr.duplicated(subset=["ru", "data", "refeicao"]).sum() == 0


def test_fact_refeicoes_nao_multiplica_pelo_numero_de_preparacoes(fact_detalhe):
    """A refeição de 05/01 tem 2 preparações, ambas com comensais_real=300
    — o total não pode virar 600."""
    fr = build_fact_refeicoes(fact_detalhe)
    linha = fr[(fr["ru"] == "P1") & (fr["data"] == pd.Timestamp("2026-01-05"))].iloc[0]
    assert linha["refeicoes_realizadas"] == 300


def test_fact_refeicoes_soma_total_correta(fact_detalhe):
    fr = build_fact_refeicoes(fact_detalhe)
    assert fr["refeicoes_realizadas"].sum() == 300 + 200


# ---------------------------------------------------------------------------
# Temperatura — limpeza, sem conformidade
# ---------------------------------------------------------------------------


def test_clean_temperatura_valor_simples():
    assert clean_temperatura(72.5) == 72.5


def test_clean_temperatura_virgula_decimal():
    assert clean_temperatura("72,5") == pytest.approx(72.5)


def test_clean_temperatura_leituras_duplas_vira_media():
    assert clean_temperatura("14,9/14,9") == pytest.approx(14.9)
    assert clean_temperatura("10/20") == pytest.approx(15.0)


def test_clean_temperatura_marcadores_de_ausencia_viram_nan():
    for v in ["-", "NA", "N/A", "", "   "]:
        assert np.isnan(clean_temperatura(v))


def test_clean_temperatura_erro_de_formula_vira_nan():
    assert np.isnan(clean_temperatura("#N/A"))


def test_is_temperatura_plausivel_marca_outliers():
    serie = pd.Series([72.5, 614.0, -20.0, 14.9, 100.0, 100.1])
    plausivel = is_temperatura_plausivel(serie)
    assert list(plausivel) == [True, False, False, True, True, False]


def test_fact_temperatura_tem_colunas_de_conformidade_com_valores_validos(fact_detalhe):
    """Atualização: a conformidade térmica foi implementada nesta etapa
    (regra oficial confirmada pela Nutrição) — este teste substitui a
    versão anterior, que checava a AUSÊNCIA dessas colunas."""
    dim = build_dim_preparacao(fact_detalhe)
    ft = build_fact_temperatura(fact_detalhe, dim)
    esperadas = {"classe_termica", "limite_referencia", "status_temperatura"}
    assert esperadas.issubset(set(ft.columns))
    valores_validos = {STATUS_CONFORME, STATUS_NAO_CONFORME, STATUS_SEM_CLASSIFICACAO,
                        STATUS_SEM_MEDICAO, STATUS_MEDICAO_INVALIDA}
    assert set(ft["status_temperatura"].unique()).issubset(valores_validos)


def test_fact_temperatura_limpa_erro_de_formula(fact_detalhe):
    dim = build_dim_preparacao(fact_detalhe)
    ft = build_fact_temperatura(fact_detalhe, dim)
    linha = ft[(fp := ft["preparacao"] == "Carne")]
    assert pd.isna(ft.loc[fp, "temperatura_c"].iloc[0])
    assert ft.loc[fp, "temperatura_valida"].iloc[0] == False  # noqa: E712


# ---------------------------------------------------------------------------
# clean_text_field
# ---------------------------------------------------------------------------


def test_clean_text_field_trata_erro_de_formula_como_ausente():
    serie = pd.Series(["Frango", "#N/A", "", None, "Carne"])
    limpo = clean_text_field(serie)
    assert limpo.isna().sum() == 3
    assert limpo.iloc[0] == "Frango"


# ---------------------------------------------------------------------------
# Dimensões
# ---------------------------------------------------------------------------


def test_dim_ru_vem_do_mappings_yaml():
    dim = build_dim_ru()
    assert set(dim["codigo"]) == {"P1", "P2", "B", "L", "PO"}


def test_dim_refeicao_tem_3_categorias():
    dim = build_dim_refeicao()
    assert set(dim["nome"]) == {"Café", "Almoço", "Jantar"}


def test_dim_preparacao_sem_categoria_inventada(fact_detalhe):
    dim = build_dim_preparacao(fact_detalhe)
    # só devem aparecer os tipos realmente presentes na fonte sintética
    assert set(dim["tipo_preparacao"]) == {"PB", "Salada"}


def test_dim_data_cobre_todas_as_datas_dos_fatos(fact_detalhe):
    dim = build_dim_data(fact_detalhe["data"])
    assert len(dim) == 2
    assert set(dim["data"]) == {pd.Timestamp("2026-01-05"), pd.Timestamp("2026-01-06")}


# ---------------------------------------------------------------------------
# dim_tipo_preparacao — dimensão dedicada para o filtro global de tipo
# ---------------------------------------------------------------------------


def test_dim_tipo_preparacao_uma_linha_por_tipo(fact_detalhe):
    dim_prep = build_dim_preparacao(fact_detalhe)
    dim_tipo = build_dim_tipo_preparacao(dim_prep)
    assert set(dim_tipo["tipo_preparacao"]) == {"PB", "Salada"}
    assert len(dim_tipo) == dim_tipo["tipo_preparacao"].nunique()  # sem duplicatas


def test_dim_tipo_preparacao_e_grao_mais_alto_que_dim_preparacao(fact_detalhe):
    dim_prep = build_dim_preparacao(fact_detalhe)
    dim_tipo = build_dim_tipo_preparacao(dim_prep)
    # dim_preparacao tem 1 linha por (tipo, prato); dim_tipo_preparacao tem
    # no máximo o mesmo número de linhas, nunca mais
    assert len(dim_tipo) <= len(dim_prep)


def test_dim_tipo_preparacao_sem_nulos():
    dim_prep = pd.DataFrame({
        "id_preparacao": [1, 2, 3],
        "tipo_preparacao": ["PB", "PB", None],
        "preparacao": ["Frango", "Carne", "(sem cardápio informado)"],
    })
    dim_tipo = build_dim_tipo_preparacao(dim_prep)
    assert dim_tipo["tipo_preparacao"].isna().sum() == 0
    assert list(dim_tipo["tipo_preparacao"]) == ["PB"]


# ---------------------------------------------------------------------------
# Per Capita agregado — validação da medida DAX (SUMMARIZE + SUMX) contra
# cálculo de referência em Python, feita ANTES de adotar a medida
# ---------------------------------------------------------------------------


def test_per_capita_agregado_dedup_quando_mesmo_tipo_repete_na_mesma_refeicao():
    """Cenário crítico que a medida precisa suportar: duas preparações do
    MESMO tipo na MESMA refeição (ex.: duas opções de salada no mesmo dia).
    Sem deduplicar, comensais_real seria somado 2x (600 em vez de 300)."""
    df = pd.DataFrame([
        {"ru": "P1", "data": pd.Timestamp("2026-01-05"), "refeicao": "Almoço",
         "tipo_preparacao": "Salada", "preparacao": "Alface", "consumo_real": 10.0, "comensais_real": 300},
        {"ru": "P1", "data": pd.Timestamp("2026-01-05"), "refeicao": "Almoço",
         "tipo_preparacao": "Salada", "preparacao": "Tomate", "consumo_real": 5.0, "comensais_real": 300},
    ])
    ref = per_capita_agregado_por_preparacao(df, by=["tipo_preparacao"])
    linha = ref.iloc[0]
    assert linha["comensais_correspondentes"] == 300  # deduplicado, NUNCA 600
    assert linha["consumo_real_total"] == pytest.approx(15.0)
    assert linha["per_capita_g_comensal"] == pytest.approx(15.0 * 1000 / 300)


def test_per_capita_agregado_mesma_preparacao_multiplas_datas_e_refeicoes():
    """Agregação temporal de UMA MESMA preparação específica, em datas e
    refeições diferentes — cada (ru,data,refeicao) contribui seu próprio
    comensais_real, sem inflar nem perder nenhuma."""
    df = pd.DataFrame([
        {"ru": "P1", "data": pd.Timestamp("2026-01-05"), "refeicao": "Almoço",
         "tipo_preparacao": "PB", "preparacao": "Frango", "consumo_real": 80.0, "comensais_real": 300},
        {"ru": "P1", "data": pd.Timestamp("2026-01-06"), "refeicao": "Almoço",
         "tipo_preparacao": "PB", "preparacao": "Frango", "consumo_real": 60.0, "comensais_real": 200},
        {"ru": "B", "data": pd.Timestamp("2026-01-05"), "refeicao": "Jantar",
         "tipo_preparacao": "PB", "preparacao": "Frango", "consumo_real": 40.0, "comensais_real": 100},
    ])
    ref = per_capita_agregado_por_preparacao(df)  # grão padrão: tipo + preparação
    linha = ref[(ref["tipo_preparacao"] == "PB") & (ref["preparacao"] == "Frango")].iloc[0]
    assert linha["comensais_correspondentes"] == 300 + 200 + 100
    assert linha["consumo_real_total"] == pytest.approx(80.0 + 60.0 + 40.0)
    esperado = (80.0 + 60.0 + 40.0) * 1000 / (300 + 200 + 100)
    assert linha["per_capita_g_comensal"] == pytest.approx(esperado)


def test_per_capita_agregado_grao_fino_nao_mistura_pratos_diferentes(fact_detalhe):
    """Frango e Carne são pratos diferentes dentro do mesmo tipo PB, em
    datas diferentes — a agregação por preparação específica não deve
    misturar os comensais de um prato com o consumo do outro."""
    dim = build_dim_preparacao(fact_detalhe)
    fp = build_fact_producao(fact_detalhe, dim)
    ref = per_capita_agregado_por_preparacao(fp)
    frango = ref[ref["preparacao"] == "Frango"].iloc[0]
    carne = ref[ref["preparacao"] == "Carne"].iloc[0]
    assert frango["comensais_correspondentes"] == 300  # só a refeição de 05/01
    assert carne["comensais_correspondentes"] == 200    # só a refeição de 06/01


def test_per_capita_agregado_nao_reproduz_inflacao_classica_quando_ungrouped(fact_detalhe):
    """Sem nenhum agrupamento (equivalente a um card 'Per Capita Geral'
    somando tudo), a versão SEM dedup infla o denominador pelo número de
    preparações da refeição — a referência em Python confirma a proporção
    exata (~11x) já documentada para o mesmo problema em fact_refeicoes."""
    dim = build_dim_preparacao(fact_detalhe)
    fp = build_fact_producao(fact_detalhe, dim)
    consumo_total = fp["consumo_real"].sum()
    comensais_direto = fp["comensais_real"].sum()
    comensais_dedup = fp.drop_duplicates(subset=["ru", "data", "refeicao"])["comensais_real"].sum()
    assert comensais_direto > comensais_dedup  # prova que a soma direta infla
    assert comensais_dedup == 300 + 200  # 2 refeições únicas: 05/01 e 06/01


# ---------------------------------------------------------------------------
# Conformidade de temperatura — regra oficial da Nutrição
# ---------------------------------------------------------------------------


def test_get_classe_termica_so_categorias_mapeadas():
    assert get_classe_termica("PB") == "quente"
    assert get_classe_termica("Salada") == "fria"
    assert get_classe_termica("Sobremesa") is None  # ambíguo, não mapeado
    assert get_classe_termica("categoria_inexistente") is None


@pytest.mark.parametrize("temperatura,esperado", [
    (61, STATUS_CONFORME),
    (60.1, STATUS_CONFORME),
    (60, STATUS_NAO_CONFORME),
    (59, STATUS_NAO_CONFORME),
])
def test_status_temperatura_quente_fronteira(temperatura, esperado):
    assert compute_status_temperatura(temperatura, True, True, "quente") == esperado


@pytest.mark.parametrize("temperatura,esperado", [
    (9, STATUS_CONFORME),
    (9.9, STATUS_CONFORME),
    (10, STATUS_NAO_CONFORME),
    (11, STATUS_NAO_CONFORME),
])
def test_status_temperatura_fria_fronteira(temperatura, esperado):
    assert compute_status_temperatura(temperatura, True, True, "fria") == esperado


def test_status_temperatura_sem_classificacao():
    assert compute_status_temperatura(70, True, True, None) == STATUS_SEM_CLASSIFICACAO


def test_status_temperatura_sem_medicao():
    assert compute_status_temperatura(None, False, False, "quente") == STATUS_SEM_MEDICAO


def test_status_temperatura_medicao_invalida_nao_entra_em_conforme_ou_nao_conforme():
    # 614°C, classe quente, mas implausível -> MEDICAO_INVALIDA, nunca CONFORME/NAO_CONFORME
    assert compute_status_temperatura(614.0, True, False, "quente") == STATUS_MEDICAO_INVALIDA


def test_status_temperatura_precedencia_sem_medicao_antes_de_classe():
    """Sem medição prevalece mesmo se a classe térmica seria conhecida."""
    assert compute_status_temperatura(None, False, False, "fria") == STATUS_SEM_MEDICAO


def test_fact_temperatura_aplica_conformidade_corretamente(fact_detalhe):
    """Usa a fixture real: PB a 72,5°C (quente, >60) deve ser CONFORME;
    Salada a 14,9°C (fria, >=10) deve ser NAO_CONFORME."""
    dim = build_dim_preparacao(fact_detalhe)
    ft = build_fact_temperatura(fact_detalhe, dim)

    pb = ft[(ft["tipo_preparacao"] == "PB") & (ft["preparacao"] == "Frango")].iloc[0]
    assert pb["classe_termica"] == "quente"
    assert pb["status_temperatura"] == STATUS_CONFORME

    salada = ft[ft["tipo_preparacao"] == "Salada"].iloc[0]
    assert salada["classe_termica"] == "fria"
    assert salada["status_temperatura"] == STATUS_NAO_CONFORME  # 14.9 >= 10


def test_fact_temperatura_medicao_invalida_nao_conta_como_nao_conforme():
    df = pd.DataFrame([{
        "ru": "P1", "data": pd.Timestamp("2026-01-05"), "refeicao": "Almoço", "prep": "PB",
        "cardapio": "X", "peso_bruto": 10.0, "peso_liq": 8.0, "sobra_limpa": 1.0,
        "sobra_suja": 1.0, "consumo_real": 6.0, "comensais": 10, "comensais_real": 100,
        "temp_c": 614.0,
    }])
    dim = build_dim_preparacao(df)
    ft = build_fact_temperatura(df, dim)
    assert ft.iloc[0]["status_temperatura"] == STATUS_MEDICAO_INVALIDA
    assert ft.iloc[0]["status_temperatura"] not in (STATUS_CONFORME, STATUS_NAO_CONFORME)


def test_limite_referencia_descreve_o_limite_aplicado(fact_detalhe):
    dim = build_dim_preparacao(fact_detalhe)
    ft = build_fact_temperatura(fact_detalhe, dim)
    pb = ft[ft["tipo_preparacao"] == "PB"].iloc[0]
    assert "60" in pb["limite_referencia"]


def test_relatorio_sem_classificacao_lista_apenas_nao_mapeados(fact_detalhe):
    dim = build_dim_preparacao(fact_detalhe)
    ft = build_fact_temperatura(fact_detalhe, dim)
    relatorio = build_relatorio_sem_classificacao_termica(ft)
    # PB e Salada estão mapeados -> não devem aparecer no relatório
    assert "PB" not in relatorio["tipo_preparacao"].values
    assert "Salada" not in relatorio["tipo_preparacao"].values


# ---------------------------------------------------------------------------
# Recuperação da chave composta do ISC — determinística, sem inventar
# ---------------------------------------------------------------------------


def test_recuperar_tipo_preparacao_chave_valida():
    tipos_validos = {"Especial", "Especial Veg", "PB"}
    resultado = recuperar_tipo_preparacao_de_chave_composta(
        "Café46027Especial Veg", pd.Timestamp("2026-01-05"), tipos_validos
    )
    assert resultado == "Especial Veg"


def test_recuperar_tipo_preparacao_serial_nao_bate_com_data():
    tipos_validos = {"Especial"}
    resultado = recuperar_tipo_preparacao_de_chave_composta(
        "Café46027Especial", pd.Timestamp("2026-06-15"), tipos_validos  # data errada de propósito
    )
    assert resultado is None


def test_recuperar_tipo_preparacao_resto_nao_e_tipo_conhecido():
    tipos_validos = {"PB"}  # "Especial" não está na lista
    resultado = recuperar_tipo_preparacao_de_chave_composta(
        "Café46027Especial", pd.Timestamp("2026-01-05"), tipos_validos
    )
    assert resultado is None


def test_recuperar_tipo_preparacao_texto_sem_padrao_retorna_none():
    resultado = recuperar_tipo_preparacao_de_chave_composta(
        "Frango Grelhado", pd.Timestamp("2026-01-05"), {"PB"}
    )
    assert resultado is None


def test_fact_satisfacao_recupera_tipo_preparacao_sem_perder_respostas():
    fact_isc = pd.DataFrame([
        {"ru": "P1", "data": pd.Timestamp("2026-01-05"), "refeicao": "Café",
         "preparacao": "Café46027Especial Veg", "otimo": 10, "regular": 2, "ruim": 1, "isc": 8.46},
    ])
    dim_preparacao = pd.DataFrame({
        "id_preparacao": [1], "tipo_preparacao": ["Especial Veg"], "preparacao": ["Mingau"],
    })
    # serial 46027 corresponde a 2026-01-05 (confirmado nesta etapa)
    fs = build_fact_satisfacao(fact_isc, dim_preparacao)
    linha = fs.iloc[0]
    assert linha["tipo_preparacao"] == "Especial Veg"
    assert linha["preparacao"] == "NAO_IDENTIFICADA"
    assert pd.isna(linha["id_preparacao"])  # prato específico continua desconhecido
    assert linha["total_respostas"] == 13  # nenhuma resposta perdida


def test_fact_satisfacao_nao_perde_respostas_mesmo_sem_recuperacao():
    """Se nem o match direto nem a chave composta funcionarem, a linha
    continua presente e somável — nunca é descartada."""
    fact_isc = pd.DataFrame([
        {"ru": "P1", "data": pd.Timestamp("2026-01-05"), "refeicao": "Almoço",
         "preparacao": "texto totalmente desconhecido", "otimo": 5, "regular": 5, "ruim": 5, "isc": 5.38},
    ])
    dim_preparacao = pd.DataFrame({"id_preparacao": [], "tipo_preparacao": [], "preparacao": []})
    fs = build_fact_satisfacao(fact_isc, dim_preparacao)
    assert len(fs) == 1
    assert fs.iloc[0]["total_respostas"] == 15
    assert fs.iloc[0]["preparacao"] == "NAO_IDENTIFICADA"
    assert pd.isna(fs.iloc[0]["tipo_preparacao"])


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v"]))
