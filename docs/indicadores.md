# Indicadores do Dashboard — "De onde saiu esse número?"

Cada seção corresponde a uma função em `src/metrics.py`. Os valores de
exemplo abaixo foram calculados na última execução real do pipeline
(02/09/2026, sem filtros) e servem para conferência — não são "metas".

## A. Panorama

### Refeições realizadas — `refeicoes_realizadas()`
- **Definição:** nº de comensais efetivamente atendidos no recorte.
- **Fórmula:** `SUM(comensais_real)`, calculado no **grão de refeição**
  (RU + data + refeição) — ver limitação abaixo.
- **Fonte:** `fact_detalhe`, campo `comensais_real`.
- **Filtros:** ru, refeição, período.
- **Tratamento de ausentes:** linhas sem `comensais_real` são ignoradas na soma (não contam como zero).
- **Premissa/limitação crítica:** `comensais_real` vem **repetido em todas as
  linhas de preparação da mesma refeição** (é uma contagem de cabeça única
  por refeição, não por prato). A função primeiro colapsa a tabela ao grão
  de refeição (`metrics._meal_level`, pegando o valor — constante — por
  RU+data+refeição) e só então soma. Sem esse passo, o resultado é inflado
  pelo número médio de pratos por refeição (~11x nos dados reais — esse foi
  um bug real encontrado e corrigido durante o smoke test, ver
  `docs/implementacao_mvp.md`).
- **Valor de referência (02/09/2026, sem filtro):** 1.081.064 refeições.

### Refeições previstas — `refeicoes_previstas()`
- **Definição:** estimativa de comensais no recorte.
- **Fórmula:** `SUM(comensais_previsto)`, onde `comensais_previsto` é o
  **maior** valor de `comensais` entre os pratos daquela refeição.
- **Fonte:** `fact_detalhe`, campo `comensais`.
- **Filtros:** ru, refeição, período.
- **Limitação:** `comensais` é uma previsão **por prato** (quantas pessoas
  escolheriam aquele prato específico), não existe nas abas de detalhe um
  campo de "previsto total da refeição". Usamos o maior valor entre os
  pratos como proxy (tipicamente a proteína principal, melhor preditor do
  total). Tratar como indicador direcional, não como número orçamentário de
  precisão.
- **Valor de referência:** 1.492.119 (proxy).

### % Execução (Realizado / Previsto) — `pct_execucao()`
- **Fórmula:** `SUM(comensais_real) / SUM(comensais_previsto)`, ambos no
  grão de refeição.
- **Fonte:** `fact_detalhe`.
- **Tratamento de ausentes:** se o previsto somado for 0, retorna `NaN`
  ("sem dado"), nunca 0% ou erro de divisão.
- **Valor de referência:** 72,5%.

### Evolução de refeições — `evolucao_refeicoes()`
- **Fórmula:** `SUM(comensais_real)` (grão de refeição) por dia (`freq="D"`,
  aceita `"W"`/`"ME"` para semanal/mensal).
- **Fonte:** `fact_detalhe`.
- **Filtros:** ru, refeição, período.

## B. Desperdício e eficiência

### Rejeito total — `rejeito_total()`
- **Fórmula:** `SUM(peso_bruto − peso_liq)`, grão de preparação (aditivo — cada prato contribui seu próprio rejeito).
- **Fonte:** `fact_detalhe`, campos `peso_bruto` e `peso_liq`.
- **Limitação documentada:** não existe coluna explícita "Rejeito" nas abas
  de detalhe (só existe nas abas consolidadas P1/P2/B/L/PO, descartadas por
  alta taxa de erro — ver `docs/auditoria_dados.md`). `peso_bruto - peso_liq`
  é uma proxy (peso perdido entre o recebido e o efetivamente preparado/servido). Validar com a nutricionista do RU antes de publicar externamente.
- **Valor de referência:** 138.488 kg no período.

### Desperdício per capita — `desperdicio_per_capita()`
- **Fórmula:** `SUM(sobra_limpa + sobra_suja)` [grão de prato, aditivo] `/
  SUM(comensais_real)` [grão de refeição — mesma correção de `_meal_level`
  aplicada aqui].
- **Fonte:** `fact_detalhe`, campos `sobra_limpa`, `sobra_suja`, `comensais_real`.
- **Valor de referência:** 0,112 kg/comensal.

### Índice de aceitabilidade (resto-ingesta) — `indice_aceitabilidade()`
- **Fórmula:** `1 − (SUM(sobra_suja) / SUM(peso_liq))`, ambos aditivos no
  grão de prato (não precisa da correção de `_meal_level`).
- **Fonte:** `fact_detalhe`, campos `sobra_suja` e `peso_liq`.
- **Interpretação:** quanto mais próximo de 100%, menor o resto no prato
  (melhor aceitação do cardápio).
- **Valor de referência:** 93,2%.

## C. Qualidade / satisfação

### Avaliação sensorial média — `avaliacao_sensorial_media()`
- **Fórmula:** `AVG(global)`.
- **Fonte:** `fact_sensorial`, campo `global` (nota consolidada 0–5).
- **Tratamento de ausentes:** avaliações sem nota (`NaN`) são ignoradas na média.
- **Valor de referência:** 3,90 (escala 0–5).

### ISC médio — `isc_medio()`
- **Fórmula:** `AVG(isc)`, usando o valor de ISC **já calculado na fonte**
  por preparação/dia/RU.
- **Fonte:** `fact_isc` (abas ISC alm / ISC jan / ISC Café), campo `isc`.
- **Premissa:** o pipeline não reconstrói a ponderação original do ISC
  (fórmula da planilha original não documentada e com erros de `#VALUE!` em
  parte das linhas); agregamos por média simples dos valores válidos no
  recorte.
- **Valor de referência:** 8,83 (escala 0–10).

### Top 5 piores preparações — `top_piores_preparacoes()`
- **Fórmula:** `AVG(global)` por preparação, ordenado ascendente.
- **Fonte:** `fact_sensorial`, campos `preparacao`, `global`.
- **Premissa:** preparações com **menos de 3 avaliações** no recorte são
  excluídas do ranking, para não destacar 1 avaliação isolada como "pior prato".

## D. Gestão

### Atendimentos e % resolvidos — `atendimentos_resolvidos()`
- **Fórmula:** `COUNT(*)` e `SUM(resolvido_flag) / COUNT(*)`.
- **Fonte:** `fact_gestao_atendimentos` — já agregado e **sem qualquer dado
  pessoal** (CPF, nome, texto de relato nunca chegam a esta tabela; ver
  `docs/auditoria_dados.md`).
- **Filtros:** ru, período (não há filtro de refeição neste domínio).
- **Valor de referência:** 29 atendimentos no período, 75,9% resolvidos.

### OS de manutenção e % resolvidas — `manutencao_resolvida()`
- **Fórmula:** `COUNT(*)` e `SUM(resolvido_flag) / COUNT(*)`, com quebra
  adicional por `tipo` (Infraestrutura/TI).
- **Fonte:** `fact_gestao_manutencao` (UFC-INFRA + OS - STI combinadas).
- **Valor de referência:** 166 OS no período, 65,1% resolvidas.

## Limitações transversais (valem para todos os KPIs)
1. Todas as datas usam `dayfirst=True` na conversão — necessário porque parte
   das fontes grava data como texto no formato brasileiro (dd/mm/aaaa).
2. Registros com data fora da janela 2025-01-01–2026-12-31 são descartados
   antes de qualquer cálculo (evita que erros de digitação como "2027"
   distorçam os indicadores).
3. Nenhum KPI usa dado que possa identificar uma pessoa (estudante ou
   servidor) — a granularidade mínima exibida é sempre RU/dia/preparação.
