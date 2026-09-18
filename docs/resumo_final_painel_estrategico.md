# Resumo Final - Painel Estrategico da Nutricao

**Branch:** feature/alinhamento-painel-gestao | **Commit:** f452c3d
**Data desta validacao final:** 03/09/2026

# Status Geral

**APROVADO COM RESSALVAS**

Ressalva principal: **Power BI - MODELO PRONTO PARA CONSTRUCAO**. O .pbix
ainda nao foi produzido porque o ambiente atual nao possui Power BI
Desktop (e um container Linux sem interface grafica). Todos os dados,
relacionamentos, medidas DAX e layout estao especificados e prontos para
montagem manual - ver docs/guia_construcao_powerbi.md.

## Formulas validadas

| Formula | Resultado |
|---|---|
| Consumo Real (Peso Liq - Sobra Limpa - Sobra Suja) | PASSOU - 100% de correspondencia em 13.673 linhas comparaveis |
| Resto-Ingesta (= Sobra Suja) | PASSOU - implementado em fact_producao.csv |
| % Resto-Ingesta (Sobra Suja / (Peso Liq - Sobra Limpa) x 100) | PASSOU - denominador decorre da formula de Consumo Real, ja validada |
| Per Capita (Consumo Real x 1000 / Comensais Real, g/comensal) | PASSOU - implementado por preparacao, com ressalva de granularidade documentada (docs/medidas_powerbi.md) |
| ISC ((OTIMO x 10 + REGULAR x 5 + RUIM x 1) / Total) | PASSOU - 100% de correspondencia em 3.663 linhas comparaveis; agregado recalculado por soma de contagens, nunca AVERAGE |
| Conformidade termica (quente >60C / <=60C; fria <10C / >=10C) | PASSOU - regra oficial da Nutricao aplicada com os operadores exatos, testada em todas as fronteiras (60, 60.1, 59, 61C / 9, 9.9, 10, 11C) |

## Modelo analitico

### Dimensoes
| Tabela | Linhas |
|---|---|
| dim_data.csv | 162 |
| dim_ru.csv | 5 |
| dim_refeicao.csv | 3 |
| dim_preparacao.csv | 213 |

### Fatos
| Tabela | Linhas | Grao |
|---|---|---|
| fact_refeicoes.csv | 1.380 | RU + Data + Refeicao |
| fact_producao.csv | 15.786 | RU + Data + Refeicao + Tipo de Preparacao + Preparacao |
| fact_satisfacao.csv | 1.604 | RU + Data + Refeicao + Preparacao (quando identificavel) |
| fact_temperatura.csv | 15.786 | RU + Data + Refeicao + Tipo de Preparacao + Preparacao |

Regressao confirmada: SUM(fact_refeicoes[refeicoes_realizadas]) =
**1.081.064**, identico ao valor ja validado no MVP Streamlit.

## Temperatura

| Metrica | Valor |
|---|---|
| Medicoes validas | 12.858 |
| Avaliadas (com classe termica conhecida) | 9.313 |
| Conformes | 5.879 |
| Nao conformes | 3.434 |
| Sem classificacao | 3.541 |
| Invalidas (fora da faixa fisica, ex.: "614C") | 4 |
| **% Conformidade** | **63,1%** |
| **% Cobertura da classificacao** | **72,4%** |

**Leitura obrigatoria do indicador:** `% Conformidade` usa **somente**
medicoes validas com classificacao termica conhecida (9.313 de 12.858) -
nao e sobre o total de medicoes. Por isso `% Cobertura da Classificacao`
deve **sempre** aparecer ao lado de `% Conformidade` em qualquer visual
(ja especificado assim em docs/especificacao_visual_powerbi.md) - sem
esse contexto, 63,1% poderia ser mal interpretado como cobrindo toda a
operacao, quando na verdade cobre 72,4% dela. As 3.541 medicoes sem
classificacao (12 tipos de preparacao ambiguos: VEG, Guarnicao, Sobremesa,
Cafe, Cafe SA, Leite, Leite Veg, Pao Frances, Pao Opcao, Especial,
Especial Veg, Manteiga) nao entram no calculo nem o distorcem - ficam
auditaveis em outputs/preparacoes_sem_classificacao_termica.csv. As 4
medicoes invalidas tambem nunca entram no denominador.

## Satisfacao

| Metrica | Valor |
|---|---|
| Total de respostas | 141.505 (corrigido — ver docs/medidas_powerbi.md; 137.578 era o valor da coluna pré-calculada, que subconta 26 linhas com dado parcial) |
| Linhas com tipo_preparacao identificado | **100%** (1.604/1.604 - 960 diretas + 644 recuperadas de forma deterministica via chave composta) |
| Linhas com prato especifico (preparacao) identificado | 60% (960/1.604) |
| Respostas descartadas | **0** - nenhuma linha foi descartada por falta de identificacao da preparacao |
| ISC agregado | Calculado por soma das contagens ((SOMA_OTIMOx10 + SOMA_REGULARx5 + SOMA_RUIMx1) / SOMA_Total), nunca por media dos valores pre-calculados por linha |

## Testes

**98/98 passaram** (41 da camada MVP/privacidade + 57 da camada Power BI,
incluindo os testes de fronteira de temperatura e de recuperacao da chave
composta do ISC).

## Streamlit

**PASSOU** - servidor sobe sem erro (/_stcore/health = ok, GET / = HTTP
200, sessao de stream sem traceback no log). Nenhuma mudanca de codigo foi
feita no Streamlit nesta etapa; a regressao confirma que as mudancas no
pipeline/Power BI nao afetaram o MVP ja publicado.

## PII

**PASSOU** - auditoria direcionada em data/powerbi/ e em
outputs/preparacoes_sem_classificacao_termica.csv: nenhum CPF, e-mail,
matricula ou nome de avaliador/comensal/atendente encontrado.

## Power BI

**MODELO PRONTO PARA CONSTRUCAO**

- **Tabelas:** 4 dimensoes + 4 fatos, todas geradas automaticamente pelo
  pipeline em data/powerbi/ (ver contagens acima).
- **Relacionamentos:** 14 relacionamentos 1-para-muitos (dimensoes ->
  fatos), documentados em docs/modelo_dados_powerbi.md e
  docs/guia_construcao_powerbi.md. Nenhum fato-fato, nenhum
  muitos-para-muitos.
- **DAX:** todas as medidas (Refeicoes, Resto-Ingesta, Satisfacao/ISC,
  Producao, Per Capita, Temperatura/Conformidade) especificadas em
  docs/medidas_powerbi.md, com a regra de razao-de-somas/contagens
  explicita em cada uma.
- **Layout:** 3 paginas (Visao Geral, Qualidade, Producao e Eficiencia)
  especificadas em docs/especificacao_visual_powerbi.md, incluindo
  filtros globais (unidade, periodo, refeicao, tipo de preparacao).
- **Guia de construcao:** docs/guia_construcao_powerbi.md - passo a passo
  completo (CSVs, tipos de coluna, relacionamentos, DAX, paginas,
  slicers, formatacao, validacao dos numeros, atualizacao futura).

O que falta e exclusivamente a montagem manual no Power BI Desktop, que
nao pode ser feita neste ambiente.

---

## Adendo — Achados reais da construcao manual no Power BI Desktop

Durante a montagem efetiva do modelo (nao simulavel neste ambiente,
so descoberta testando de verdade), dois problemas reais foram
encontrados e corrigidos:

### 1. Formula de "Total Respostas" inconsistente (ISC inflado)
26 linhas de `fact_satisfacao` tem `otimo` preenchido mas `regular`
e/ou `ruim` vazios na fonte. A coluna `total_respostas` (calculada como
`otimo+regular+ruim`) fica nula nessas linhas, mesmo com voto real de
`otimo` registrado. A medida `Total Respostas = SUM(fact_satisfacao[total_respostas])`
por isso subconta o denominador (137.578) enquanto `Total Otimo`
conta o numerador incluindo essas linhas (126.688) — os dois deixam de
ser consistentes, inflando o ISC Agregado para 9,63 em vez do valor
correto, 9,36. **Corrigido:** `Total Respostas = [Total Otimo] + [Total Regular] + [Total Ruim]`
(ver docs/medidas_powerbi.md). Valor correto de Total Respostas:
**141.505** (nao 137.578).

### 2. Bug de localidade decimal no Power Query (import, nao Python)
Com o Power BI Desktop configurado em localidade pt-BR, a conversao de
tipo padrao ("Numero Decimal" via icone simples) interpretou o ponto
decimal dos CSVs (formato Python, ex.: `"82.5"`) como separador de
milhar, multiplicando os valores por 10 silenciosamente (`82.5` virou
`825`). Confirmado em `temperatura_c` (Media saiu 485 em vez de 48,3;
Mediana saiu 626 em vez de 62,6), `refeicoes_realizadas`/`refeicoes_previstas`
(Total Refeicoes saiu "10,8 Mi" em vez de 1.081.064) e `comensais_real`.
**Correcao:** usar sempre "Alterar Tipo -> Usando Localidade -> Numero
Decimal, Ingles (Estados Unidos)" para toda coluna decimal, aplicada
a partir do passo "Cabecalhos Promovidos" (antes de qualquer conversao
de tipo automatica) — nao em cima de uma coluna ja convertida errada.
Ver alerta completo em docs/guia_construcao_powerbi.md, secao 2.

Nenhum dos dois achados exigiu mudanca em `src/powerbi_export.py` nem no
pipeline Python — sao ajustes exclusivos da camada DAX/Power Query,
consistentes com o principio "Python trata os dados, Power BI so
relaciona e agrega".
