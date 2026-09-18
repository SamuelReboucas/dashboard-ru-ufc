# Medidas Power BI — Painel Estratégico da Nutrição

Todas as medidas abaixo são agregações simples sobre colunas já tratadas
pelo pipeline (`data/powerbi/`). Nenhuma delas precisa (nem deve) corrigir
granularidade ou limpar dado — isso já foi feito em `src/powerbi_export.py`.

## Princípio obrigatório: razão de somas, nunca média de percentuais
Sempre que um indicador for um percentual ou uma razão (per capita, %
Resto-Ingesta, ISC), a medida correta soma os componentes (numerador e
denominador) **separadamente**, no contexto de filtro atual, e só então
divide. Nunca usar `AVERAGE()` sobre uma coluna de percentual/razão já
calculada por linha — isso dá peso igual a linhas com volumes de dado
muito diferentes (ex.: uma preparação com 10 respostas de ISC e outra com
500 não podem pesar igual numa média simples).

## Refeições (`fact_refeicoes`)

```dax
Total Refeições = SUM(fact_refeicoes[refeicoes_realizadas])

Total Refeições Previstas = SUM(fact_refeicoes[refeicoes_previstas])
-- Rótulo obrigatório no visual: "Previsto (aproximado)" — não é uma
-- definição validada pela gestão, ver docs/indicadores.md.

% Execução = DIVIDE([Total Refeições], [Total Refeições Previstas])

Média Mensal de Refeições =
    AVERAGEX(
        SUMMARIZE(fact_refeicoes, dim_data[ano_mes], "TotalMes", SUM(fact_refeicoes[refeicoes_realizadas])),
        [TotalMes]
    )
```
`Total Refeições` já é seguro porque `fact_refeicoes` está no grão
RU+Data+Refeição — não precisa de nenhum truque de deduplicação em DAX.

## Resto-Ingesta (`fact_producao`)

```dax
Resto-Ingesta (kg) = SUM(fact_producao[resto_ingesta_kg])

Quantidade Distribuída (kg) = SUM(fact_producao[quantidade_distribuida])

% Resto-Ingesta =
    DIVIDE(
        SUM(fact_producao[resto_ingesta_kg]),
        SUM(fact_producao[quantidade_distribuida])
    ) * 100
```
**Nunca** `AVERAGE(fact_producao[pct_resto_ingesta])` — essa coluna existe
na tabela só como referência informativa por linha (útil para inspecionar
um caso específico numa tabela detalhada), não como base de agregação.

## Satisfação / ISC (`fact_satisfacao`)

> **Correção (achado em teste real no Power BI Desktop):** a fórmula
> `Total Respostas = SUM(fact_satisfacao[total_respostas])` está **errada**
> e não deve ser usada. Existem 26 linhas em `fact_satisfacao` onde `otimo`
> tem valor real mas `regular` e/ou `ruim` vieram vazios na fonte — como
> `total_respostas` foi calculado como `otimo + regular + ruim` (soma que
> vira nula se qualquer um dos três for nulo), essas 26 linhas ficam com
> `total_respostas` nulo mesmo tendo até centenas de votos de `otimo`
> registrados. Resultado: `SUM(total_respostas)` subconta o denominador
> (137.578) enquanto `SUM(otimo)` conta os votos dessas linhas no
> numerador (126.688) — os dois deixam de ser consistentes entre si, e o
> ISC Agregado sai inflado (testado: 9,63 em vez do valor correto, 9,36).

```dax
Total Ótimo   = SUM(fact_satisfacao[otimo])
Total Regular = SUM(fact_satisfacao[regular])
Total Ruim    = SUM(fact_satisfacao[ruim])

Total Respostas = [Total Ótimo] + [Total Regular] + [Total Ruim]

% Ótimo   = DIVIDE([Total Ótimo],   [Total Respostas])
% Regular = DIVIDE([Total Regular], [Total Respostas])
% Ruim    = DIVIDE([Total Ruim],    [Total Respostas])

ISC Agregado =
    DIVIDE(
        [Total Ótimo] * 10 + [Total Regular] * 5 + [Total Ruim] * 1,
        [Total Respostas]
    )
```
Somando o denominador a partir das próprias medidas `Total Ótimo`/`Total
Regular`/`Total Ruim` (em vez de uma coluna `total_respostas` pré-calculada
que pode ficar nula por dado parcial), o numerador e o denominador do ISC
usam exatamente o mesmo conjunto de votos — sem essa inconsistência.

`ISC Agregado` foi validado nesta etapa: a fórmula
`(ÓTIMO×10 + REGULAR×5 + RUIM×1) / Total` reproduz com 100% de exatidão o
valor de `isc_linha` já calculado na fonte, em 3.663 linhas comparadas —
por isso pode ser recalculada com segurança a partir das somas de
contagens em qualquer contexto de filtro do Power BI (RU, período,
preparação), em vez de médias do campo pré-calculado.

## Produção (`fact_producao`)

```dax
Consumo Real (kg)  = SUM(fact_producao[consumo_real])
Sobra Limpa (kg)   = SUM(fact_producao[sobra_limpa])
Sobra Suja (kg)    = SUM(fact_producao[sobra_suja])
Peso Bruto (kg)    = SUM(fact_producao[peso_bruto])
Peso Líquido (kg)  = SUM(fact_producao[peso_liq])

Relação Produção x Consumo = DIVIDE([Consumo Real (kg)], [Peso Líquido (kg)])
```

## Per Capita (`fact_producao`)

> **Correção nesta revisão:** a versão anterior desta medida buscava o
> denominador em `CALCULATE(SUM(fact_refeicoes[refeicoes_realizadas]), ...)`,
> presumindo que o contexto de filtro de `dim_preparacao`/`dim_tipo_preparacao`
> se propagaria até `fact_refeicoes`. **Isso está errado:** não existe
> relacionamento entre as dimensões de preparação e `fact_refeicoes` (ver
> `docs/modelo_dados_powerbi.md`, seção "O que NÃO existe nesta versão") —
> o Power BI não filtra uma tabela sem um caminho de relacionamento até
> ela. A medida corrigida abaixo deduplica `comensais_real` **diretamente
> dentro de `fact_producao`**, no contexto de filtro já ativo (RU, data,
> refeição e preparação), sem depender de nenhum relacionamento externo.

**Cuidado de granularidade — leia antes de criar a medida.** `comensais_real`
em `fact_producao` é o mesmo valor repetido em todas as preparações da
mesma refeição (por desenho — é assim que a fonte grava o dado). Somar essa
coluna direto reproduz o mesmo problema de inflação já corrigido no MVP
(ver `docs/implementacao_mvp.md`) — **confirmado nesta revisão em
`tests/test_powerbi_export.py`**: sem deduplicar, o denominador infla
**11,08×** (11.980.794 em vez dos 1.081.064 comensais reais).

```dax
Per Capita (g/comensal) por Preparação =
VAR RefeicoesDistintas =
    SUMMARIZE(
        fact_producao,
        fact_producao[ru],
        fact_producao[data],
        fact_producao[refeicao],
        "Comensais", MAX(fact_producao[comensais_real])
    )
VAR ComensaisCorrespondentes = SUMX(RefeicoesDistintas, [Comensais])
RETURN
    DIVIDE(SUM(fact_producao[consumo_real]) * 1000, ComensaisCorrespondentes)
```

Como funciona: `SUMMARIZE` roda **dentro do contexto de filtro já ativo**
no visual (ex.: uma barra do gráfico "Per Capita por Preparação", filtrada
a um `tipo_preparacao`/`preparacao` específico via `dim_tipo_preparacao`
ou `dim_preparacao`) e produz uma linha por combinação distinta de
RU+Data+Refeição **entre as linhas de `fact_producao` já filtradas** —
exatamente a deduplicação necessária, sem precisar de relacionamento
externo. `SUMX` soma essas combinações distintas.

**Validação em Python antes de adotar (`src.powerbi_export.per_capita_agregado_por_preparacao`,
ver `tests/test_powerbi_export.py`):**
- Duas preparações do mesmo tipo na mesma refeição (ex.: 2 saladas no
  mesmo dia) → deduplicação correta confirmada (comensais contado 1x, não 2x).
- Mesma preparação específica em datas/refeições diferentes → cada
  RU+Data+Refeição soma seu próprio `comensais_real`, sem perda nem
  duplicação (testado com 3 combinações RU/data/refeição distintas).
- Pratos diferentes dentro do mesmo tipo (ex.: "Frango" e "Carne" dentro de
  "PB", em dias diferentes) → cada prato mantém seus próprios comensais
  correspondentes, sem misturar.
- Exemplo real (dados de produção, sem filtro de data): tipo `PB` →
  92,6 g/comensal; tipo `Suco` → 246,9 g/comensal; prato específico
  "Sobrecoxa Assada" (dentro de PB) → 88,6 g/comensal — todos plausíveis
  para porções de alimento.

**Não criar** uma medida "Per Capita Geral" que misture várias preparações
diferentes sem filtro — o numerador (soma de consumo de pratos diferentes,
com densidades e propósitos nutricionais diferentes) não tem uma
interpretação gerencial única. Se um visual mostrar múltiplas preparações
ao mesmo tempo (ex.: um gráfico de barras "Per Capita por Preparação"), a
medida acima já funciona corretamente porque o DAX a recalcula por grupo
(contexto de linha do visual), não como um número único ambíguo.

## Temperatura (`fact_temperatura`)

**Regra oficial confirmada pela Nutrição** (implementada em
`src/powerbi_export.py`, não em DAX — os status já vêm calculados por
linha): preparações quentes são conformes acima de 60°C (`> 60`, não
`≥`); preparações frias são conformes abaixo de 10°C (`< 10`, não `≤`).
Medições fisicamente implausíveis (fora de −5°C a 100°C) nunca entram no
denominador de conformidade — ficam com `status_temperatura = MEDICAO_INVALIDA`.

```dax
Total Medições = COUNTROWS(fact_temperatura)

Medições Válidas =
    CALCULATE(COUNTROWS(fact_temperatura), fact_temperatura[temperatura_valida] = TRUE)

Medições Avaliadas =
    CALCULATE(
        COUNTROWS(fact_temperatura),
        fact_temperatura[status_temperatura] IN {"CONFORME", "NAO_CONFORME"}
    )

Medições Conformes =
    CALCULATE(COUNTROWS(fact_temperatura), fact_temperatura[status_temperatura] = "CONFORME")

Medições Fora do Padrão =
    CALCULATE(COUNTROWS(fact_temperatura), fact_temperatura[status_temperatura] = "NAO_CONFORME")

% Conformidade = DIVIDE([Medições Conformes], [Medições Avaliadas])

% Cobertura da Classificação = DIVIDE([Medições Avaliadas], [Medições Válidas])
-- Importante exibir este número ao lado de "% Conformidade" — ele diz
-- quanto da conformidade está de fato sendo medido. Na última execução:
-- 72,4% de cobertura (9.313 de 12.858 medições válidas puderam ser
-- avaliadas; o restante caiu em SEM_CLASSIFICACAO).

Temperatura Média =
    CALCULATE(AVERAGE(fact_temperatura[temperatura_c]), fact_temperatura[temperatura_plausivel] = TRUE)

Temperatura Mediana =
    CALCULATE(MEDIAN(fact_temperatura[temperatura_c]), fact_temperatura[temperatura_plausivel] = TRUE)
```

**Por que `% Conformidade` e `% Cobertura` usam contagens de linhas, não
percentuais pré-calculados:** cada preparação/dia é uma medição
independente; contar quantas caem em cada status e dividir só no final
(razão de contagens) é equivalente a uma "razão de somas" no caso binário
— o mesmo princípio de não usar `AVERAGE` sobre uma coluna de percentual
já se aplica aqui.

**`Medições Fora da Faixa Física`** (as 4 leituras tipo "614°C") continuam
disponíveis como `COUNTROWS(FILTER(fact_temperatura, [status_temperatura] = "MEDICAO_INVALIDA"))`
para controle de qualidade — nunca somadas a `NAO_CONFORME`.
