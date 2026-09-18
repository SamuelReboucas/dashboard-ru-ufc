# Modelo de Dados — Power BI (Painel Estratégico da Nutrição)

**Status:** implementado e gerado pelo pipeline (`python -m src.pipeline`,
etapa `[5/6]`) em `data/powerbi/`. Números abaixo são da última execução
real contra a base atual (02–07/09/2026).

## Princípio geral
Todas as regras de negócio (limpeza, granularidade, fórmulas) são
resolvidas em `src/powerbi_export.py`, a partir das tabelas já tratadas por
`src/transform.py`. O Power BI só relaciona tabelas e calcula medidas
simples sobre colunas já prontas — nenhuma correção de granularidade nem
limpeza de dado bruto acontece em DAX/Power Query (ver
`docs/medidas_powerbi.md` para o porquê disso importar, especialmente para
Refeições e Per Capita).

## Dimensões

### `dim_data.csv`
1 linha por data distinta observada nos fatos (não um calendário completo
do ano). **162 linhas** na última execução.

| Campo | Tipo | Descrição |
|---|---|---|
| `data` | data | Chave |
| `dia` | inteiro | Dia do mês |
| `mes` | texto | Nome do mês (locale do servidor) |
| `mes_numero` | inteiro | 1–12 |
| `ano` | inteiro | — |
| `ano_mes` | texto | `AAAA-MM`, útil para agrupar por mês no Power BI |
| `trimestre` | inteiro | 1–4 |

### `dim_ru.csv`
1 linha por unidade. **5 linhas.** Campos: `codigo` (P1/P2/B/L/PO), `nome`
(nome completo). Fonte: `config/mappings.yaml` (`ru_canonico`) — nunca
hardcoded.

### `dim_refeicao.csv`
1 linha por refeição. **3 linhas:** Café, Almoço, Jantar.

### `dim_preparacao.csv`
1 linha por combinação distinta (`tipo_preparacao`, `preparacao`)
observada em `fact_detalhe`. **213 linhas.**

| Campo | Tipo | Descrição |
|---|---|---|
| `id_preparacao` | inteiro (surrogate) | Chave — **não estável entre execuções** se o conjunto de combinações mudar (ver aviso abaixo) |
| `tipo_preparacao` | texto | Vem da coluna `Prep` da fonte — categoria fechada (PB, PV, VEG, Arroz/Baião, Arroz Integral, Feijão, Guarnição, Salada, Sobremesa, Suco, Suco SA, Café, Café SA, Leite, Leite Veg, Pão Francês, Pão Opção, Fruta 1, Fruta 2, Especial e outras já existentes na base — confirmado por inspeção de valores, nenhuma categoria foi inventada) |
| `preparacao` | texto | Vem da coluna `Cardápio` — o prato específico do dia. Erros de fórmula (`"#N/A"` literal) e valores vazios viram `"(sem cardápio informado)"` |

**Aviso sobre estabilidade do id:** o surrogate é gerado por ordenação
alfabética das combinações encontradas na execução atual. Se pratos novos
aparecerem numa atualização futura, os ids podem ser reatribuídos. Isso é
aceitável porque o Power BI recarrega o modelo inteiro a cada atualização
(não há necessidade de id estável entre versões).

### `dim_tipo_preparacao.csv`
1 linha por `tipo_preparacao` distinto — grão mais alto que
`dim_preparacao` (que é por prato específico). **22 linhas.**

| Campo | Tipo | Descrição |
|---|---|---|
| `tipo_preparacao` | texto | Mesmos valores de `dim_preparacao[tipo_preparacao]`, sem repetição |

**Por que esta dimensão existe (achado desta revisão técnica):**
`fact_satisfacao` tem `tipo_preparacao` preenchido em **100%** das 1.604
linhas (960 por match direto do nome do prato + 644 recuperadas da chave
composta — ver seção de `fact_satisfacao` abaixo), mas `id_preparacao` só
em 60%. Se o filtro global de "tipo de preparação" usasse
`dim_preparacao[tipo_preparacao]` — relacionada via `id_preparacao` — as
644 linhas sem prato específico ficariam **fora do filtro** (chave de
relacionamento nula não é filtrada pelo Power BI). `dim_tipo_preparacao`
relaciona direto pelo texto de `tipo_preparacao`, presente em 100% das
linhas de `fact_producao`, `fact_satisfacao` e `fact_temperatura` — por
isso é ela, e não `dim_preparacao`, que deve alimentar o **slicer oficial
de tipo de preparação**. `dim_preparacao` continua existindo, inalterada,
para filtros/análises que precisem do prato específico (ex.: "Per Capita
por Preparação", "Top piores preparações").

## Fatos

### `fact_refeicoes.csv` — grão RU + Data + Refeição
**1.380 linhas** (uma por combinação real observada). **Uma única linha
por refeição**, mesmo que aquela refeição tenha várias preparações.

| Campo | Descrição |
|---|---|
| `ru`, `data`, `refeicao` | Chaves para as dimensões |
| `refeicoes_realizadas` | Comensais reais da refeição (`comensais_real`, já deduplicado — ver `metrics._meal_level`) |
| `refeicoes_previstas` | Maior previsão de prato da refeição (aproximação já documentada em `docs/indicadores.md` — **não é uma definição validada pela gestão**, mantida por já ser usada no MVP) |

**Teste de regressão:** `SUM(refeicoes_realizadas)` = **1.081.064**, valor
idêntico ao já validado no Streamlit/MVP (ver `tests/test_powerbi_export.py`,
`test_fact_refeicoes_soma_total_correta` usa dados sintéticos; a checagem
contra o valor real de produção foi feita manualmente nesta etapa, não é
hardcoded em nenhum teste).

### `fact_producao.csv` — grão RU + Data + Refeição + Tipo de Preparação + Preparação
**15.786 linhas** (mesmo grão de `fact_detalhe`, um por linha de preparação).

| Campo | Fórmula / origem | Status |
|---|---|---|
| `peso_bruto`, `peso_liq`, `sobra_limpa`, `sobra_suja`, `consumo_real`, `comensais_real` | Direto de `fact_detalhe` | Já validado no MVP |
| `quantidade_distribuida` | `peso_liq − sobra_limpa` | **Validado** (decorre da fórmula de `Cons. Real` confirmada) |
| `resto_ingesta_kg` | `sobra_suja` | **Validado** |
| `pct_resto_ingesta` | `resto_ingesta_kg / quantidade_distribuida × 100` | **Validado** — informativo por linha; agregação correta é razão de somas, não média (ver `docs/medidas_powerbi.md`) |
| `per_capita_g_comensal` | `consumo_real × 1000 / comensais_real` | **Validado** — informativo por linha. **A agregação entre preparações/datas NÃO pode usar esta coluna nem `SUM(comensais_real)` diretamente** — exige a medida DAX com deduplicação por RU+Data+Refeição (ver `docs/medidas_powerbi.md` e `src.powerbi_export.per_capita_agregado_por_preparacao`, a referência em Python que validou a fórmula antes de ela ser adotada em DAX) |

### `fact_satisfacao.csv` — grão RU + Data + Refeição + Preparação (quando identificável)
**1.604 linhas** (mesmo grão de `fact_isc`).

| Campo | Descrição |
|---|---|
| `otimo`, `regular`, `ruim` | Contagens brutas — fonte para toda agregação correta |
| `total_respostas` | `otimo + regular + ruim` |
| `isc_linha` | Valor de ISC já calculado na fonte, só para referência — **não usar `AVERAGE(isc_linha)` como medida agregada** |
| `id_preparacao` | Nulo em **644 de 1.604 linhas (40%)** — ver achado abaixo |

**Achado desta etapa:** a coluna "Preparação" das abas de ISC nem sempre
contém o nome limpo do prato — em parte das linhas é uma chave composta
cacheada (ex.: `"Café46167Especial Veg"`). Isso não é um bug de extração;
é uma inconsistência da própria planilha-fonte. Enquanto não houver
esclarecimento (ver `docs/perguntas_validacao_nutricao.md`, pergunta 3), a
satisfação continua **totalmente somável por RU/data/refeição** (nenhuma
linha é perdida), só a quebra por preparação específica fica incompleta.

### `fact_temperatura.csv` — grão RU + Data + Refeição + Tipo de Preparação + Preparação
**15.786 linhas** (mesmo grão de `fact_producao` — é o grão real
disponível hoje; ver ressalva sobre leituras múltiplas abaixo).

| Campo | Descrição |
|---|---|
| `temperatura_c` | Limpa (vírgula decimal, leituras duplas em uma célula viram média, erros de fórmula e marcadores de ausência viram nulo) |
| `temperatura_valida` | `True` se havia algum valor interpretável (12.858 de 15.786 = 81,5%) |
| `temperatura_plausivel` | `True` se além de válida está numa faixa fisicamente possível (−5°C a 100°C) — **checagem de qualidade de dado, não regra de conformidade sanitária**. 4 leituras (0,03%) ficaram fora dessa faixa (ex.: "614°C", quase certamente erro de digitação) |
| `classe_termica` | `"quente"`, `"fria"` ou nulo (`SEM_CLASSIFICACAO`) — classificação de `tipo_preparacao`, centralizada em `config/mappings.yaml` (`classe_termica_por_tipo_preparacao`), **implementada nesta etapa** |
| `limite_referencia` | Texto descritivo do limite aplicado (`"> 60°C"` para quente, `"< 10°C"` para fria), nulo quando sem classe |
| `status_temperatura` | `CONFORME` / `NAO_CONFORME` / `SEM_CLASSIFICACAO` / `SEM_MEDICAO` / `MEDICAO_INVALIDA` — **implementado nesta etapa**, com a regra oficial confirmada pela Nutrição |

**Regra oficial de conformidade (confirmada pela Nutrição, implementada em
`src.powerbi_export.compute_status_temperatura`):**
```
Quente: temperatura > 60°C  → CONFORME   |  temperatura ≤ 60°C → NÃO CONFORME
Fria:   temperatura < 10°C  → CONFORME   |  temperatura ≥ 10°C → NÃO CONFORME
```
Operadores assimétricos preservados exatamente como fornecidos (não é
erro de digitação). Ordem de precedência do `status_temperatura`: sem
medição → `SEM_MEDICAO`; medição fisicamente implausível → nunca entra em
CONFORME/NAO_CONFORME, fica `MEDICAO_INVALIDA`; sem classe térmica
conhecida → `SEM_CLASSIFICACAO`; só então aplica o limite da classe.

**Classificação térmica (`classe_termica`)** — só para as categorias
inequivocamente identificáveis pela nomenclatura do RU: quentes = PB, PV,
Arroz/Baião, Arroz Integral, Feijão; frias = Salada, Suco, Suco SA, Fruta
1, Fruta 2. As demais 12 categorias (VEG, Guarnição, Sobremesa, Café, Café
SA, Leite, Leite Veg, Pão Francês, Pão Opção, Especial, Especial Veg,
Manteiga) ficam `SEM_CLASSIFICACAO` — nunca inferida a partir da
temperatura observada (seria circular). Relatório de auditoria dessas 12
categorias em `outputs/preparacoes_sem_classificacao_termica.csv`.

**Resultado na última execução:** 12.858 medições válidas, 9.313
avaliadas (72,4% de cobertura da classificação), 5.879 conformes → **63,1%
de conformidade** entre as avaliadas. `% Conformidade` sempre deve ser
lido junto com `% Cobertura da Classificação` (ver `docs/medidas_powerbi.md`).

**Achado sobre grão real:** ao menos um caso observado
(`"14,9/14,9"`) mostra duas leituras concatenadas numa única célula —
sugerindo que o processo real de medição pode ter mais de uma aferição por
preparação/dia, mas a planilha-fonte já achata isso antes do pipeline
receber o dado. O pipeline usa a média das leituras encontradas (ver
pergunta residual 2 em `docs/perguntas_validacao_nutricao.md`).

## Relacionamentos

```
dim_data (data)              1 ──── * fact_refeicoes, fact_producao, fact_satisfacao, fact_temperatura
dim_ru (codigo)               1 ──── * fact_refeicoes, fact_producao, fact_satisfacao, fact_temperatura
dim_refeicao (nome)           1 ──── * fact_refeicoes, fact_producao, fact_satisfacao, fact_temperatura
dim_preparacao (id)           1 ──── * fact_producao, fact_satisfacao (parcial, 60%), fact_temperatura
dim_tipo_preparacao (tipo)    1 ──── * fact_producao, fact_satisfacao (100%), fact_temperatura
```

Todos os relacionamentos são **1 para muitos, filtro único (Single)**, sem
relação fato↔fato e sem muitos-para-muitos. `fact_refeicoes` não se
relaciona com nenhuma das duas dimensões de preparação (não tem esse
grão). `fact_satisfacao` se relaciona com `dim_preparacao` de forma
parcial (60% das linhas), mas com `dim_tipo_preparacao` em **100%** das
linhas — por isso o **slicer oficial de "tipo de preparação" usa
`dim_tipo_preparacao[tipo_preparacao]`**, não `dim_preparacao`.

## O que NÃO existe nesta versão (por decisão, não por esquecimento)
- Nenhuma tabela `fact_desperdicio` separada — o Resto-Ingesta já está em
  `fact_producao`.
- Nenhuma tabela de Gestão (atendimentos/manutenção) — fora do escopo do
  Painel Estratégico da Nutrição, permanece só no Streamlit.
- Nenhum relacionamento entre `dim_preparacao`/`dim_tipo_preparacao` e
  `fact_refeicoes` — por isso a medida de Per Capita agregado não pode
  puxar o denominador de `fact_refeicoes`; ela deduplica `comensais_real`
  diretamente dentro de `fact_producao` (ver `docs/medidas_powerbi.md`).
