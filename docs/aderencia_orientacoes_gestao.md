# Aderência às Orientações da Gestão — Painel Estratégico da Nutrição

**Documento de referência:** `ORIENTAÇÕES PARA CONSTRUÇÃO DO PAINEL ESTRATÉGICO DA
NUTRIÇÃO.pdf` (RU/UFC) · **Base comparada:** Dashboard RU v1.0.0-mvp (já publicado)
· **Versão:** 2 (revisão metodológica) · **Status:** ANÁLISE — nada foi
implementado nesta etapa nem na anterior.

> **O que mudou na v2:** a v1 deste documento assumiu, em três pontos, um
> mapeamento semântico entre campos da planilha e as definições oficiais da
> gestão sem confirmação explícita da Nutrição. Isso foi corrigido: hipóteses
> permanecem registradas como hipóteses, e cada indicador que depende de uma
> definição não confirmada foi movido para um status de bloqueio próprio, em
> vez de "PARCIAL" genérico. As perguntas que faltam responder estão
> consolidadas em `docs/perguntas_validacao_nutricao.md`.

> **O que mudou na v3 (esta versão):** as hipóteses da v2 sobre `Cons. Real`,
> `Quantidade distribuída` e a fórmula do ISC foram **validadas
> estatisticamente contra a base real** (100% de correspondência em
> milhares de linhas — ver seção 3-A). Com isso, Resto-Ingesta (kg e %),
> Per Capita e ISC agregado **deixaram de ser hipótese e foram
> implementados** em `src/powerbi_export.py`, com testes automatizados
> (`tests/test_powerbi_export.py`). O único bloqueio funcional relevante
> que permanece é a **conformidade de temperatura** (limites e classificação
> quente/fria), que genuinamente não pode ser deduzida de nenhuma planilha.
> Ver `docs/modelo_dados_powerbi.md`, `docs/medidas_powerbi.md` e
> `docs/especificacao_visual_powerbi.md` para a implementação completa.

## Método
Comparação campo a campo entre o PDF da gestão e o que existe em
`src/metrics.py`, `config/mappings.yaml` e nas fontes já auditadas
(`docs/auditoria_dados.md`, `docs/fontes_oficiais.md`). Nenhuma reauditoria
completa foi feita nesta revisão — apenas a reinterpretação dos achados já
levantados (incluindo a checagem pontual de `Temp (°C)`, `ISO AZUL 3C` e
`ISO PRETO 1C` feita na v1, cujos números continuam válidos e são
reaproveitados aqui).

## 1. Power BI — não é mais uma decisão em aberto
O documento da gestão **determina** Power BI como ferramenta de
visualização do Painel Estratégico da Nutrição. Isso não é uma opção a
avaliar — é um requisito já dado. A pergunta que resta não é "Power BI ou
Streamlit?", é "como reaproveitar o pipeline Python já validado para
alimentar o Power BI sem duplicar regra de negócio?" — respondida em
`docs/arquitetura_powerbi.md` (atualizado nesta revisão).

**O Streamlit é preservado como:** protótipo funcional, ambiente de
validação, solução paralela e referência técnica — não é descartado, mas
também não compete mais com o Power BI como "ferramenta oficial".

## Tabela mestra de aderência (revisada)

| Requisito da gestão | Situação atual | Status | Bloqueio / GAP | Ação necessária | Prioridade |
|---|---|---|---|---|---|
| Ferramenta: Power BI | Camada Power BI implementada (`data/powerbi/`), Streamlit preservado | **REQUISITO DADO — ARQUITETURA IMPLEMENTADA** | Nenhum | Ver `docs/modelo_dados_powerbi.md` | Concluído nesta etapa (P0) |
| Número de Refeições — total diário / média mensal / comparação entre unidades | `fact_refeicoes.csv` gerado no grão certo (RU+Data+Refeição); regressão de 1.081.064 confirmada | **ATENDIDO / IMPLEMENTADO** | Falta só exposição visual da média mensal | Medida DAX já especificada em `docs/medidas_powerbi.md` | **P1** (visual) |
| Satisfação do Cliente — média + distribuição por nível | `fact_satisfacao.csv` com contagens brutas + ISC agregado recalculado a partir das somas (fórmula validada 100%) | **IMPLEMENTADO** | Junção com `dim_preparacao` incompleta em 40% das linhas (chave composta na fonte ISC — ver seção 4) | Nenhuma ação de código pendente; pergunta residual à Nutrição (pergunta 3) | Concluído (P0); pergunta residual não bloqueia uso |
| Resto-Ingesta (kg) | `resto_ingesta_kg = sobra_suja` implementado em `fact_producao.csv` | **IMPLEMENTADO** | Confirmação semântica final ainda recomendável, mas a fórmula já é consistente com a base | Nenhuma ação de código pendente | Concluído (P0) |
| % Resto-Ingesta | `pct_resto_ingesta` (por linha) implementado; medida agregada (razão de somas) documentada em `docs/medidas_powerbi.md` | **IMPLEMENTADO** | — | — | Concluído (P0) |
| Temperatura das preparações — medição | `temp_c` mapeada, limpa e validada em `fact_temperatura.csv` (`temperatura_c`, `temperatura_valida`, `temperatura_plausivel`) | **IMPLEMENTADO** | 4 leituras (0,03%) fora da faixa física plausível — provável erro de digitação na fonte | Nenhuma | Concluído (P0) |
| Temperatura das preparações — % de conformidade | Nenhuma implementação possível | **BLOQUEADO POR REGRA DE NEGÓCIO** (único bloqueio funcional relevante que resta) | Falta: (a) classificação quente/fria por preparação; (b) limites de conformidade. Nenhum dos dois pode ser inferido nem inventado | Perguntar à Nutrição (`docs/perguntas_validacao_nutricao.md`, pergunta 1) | **P0 bloqueado pela Nutrição** |
| Per Capita Presumido | `per_capita_g_comensal = consumo_real×1000/comensais_real` implementado em `fact_producao.csv`, no grão de preparação | **IMPLEMENTADO** | Agregação entre preparações/datas exige medida DAX cuidadosa (denominador vem de `fact_refeicoes`, não de soma direta em `fact_producao`) — documentado em `docs/medidas_powerbi.md` | Nenhuma ação de código pendente | Concluído (P0) |
| Estrutura em 3 níveis (Visão Geral / Qualidade / Produção e Eficiência) | Especificação completa em `docs/especificacao_visual_powerbi.md` | **ESPECIFICADO** (Power BI); Streamlit mantém 5 abas como protótipo | — | Construção do `.pbix` em si (fora do escopo desta etapa de análise/dados) | **P1** |
| Filtros — unidade, período | Modelo relacional já suporta (dimensões `dim_ru`, `dim_data`) | **ATENDIDO** | — | — | — |
| Filtros — tipo de preparação | `dim_preparacao[tipo_preparacao]` disponível | **IMPLEMENTADO (interpretação provisória)** | Interpretação de "tipo de preparação" = categoria `Prep` da fonte — não confirmada como a intenção exata da gestão | Confirmar com a gestão (pergunta 4) | **P1** (baixo risco) |
| Estrutura em 3 níveis (Visão Geral / Qualidade / Produção e Eficiência) | Dashboard atual tem 5 abas | **PARCIAL** | Reorganização de navegação, não de dado | Ver seção 7 | **P1** |
| Filtros — unidade | Existe (`render_sidebar_filters`) | **ATENDIDO** | — | — | — |
| Filtros — período | Existe | **ATENDIDO** | — | — | — |
| Filtros — tipo de preparação | Não existe | **BLOQUEADO POR DEFINIÇÃO DE ESCOPO** | Não está confirmado o que "tipo de preparação" significa oficialmente (ver seção 8) | Perguntar à Nutrição (ver `docs/perguntas_validacao_nutricao.md`, pergunta 4) | **P0 bloqueado pela Nutrição** (definição), **P1** (implementação do filtro após definição) |

## 2. Resto-Ingesta — denominador não assumido

### 3-A. Validação estatística das hipóteses (v3 — resolve a v2)
Antes de implementar qualquer regra, as três hipóteses da v2 foram testadas
diretamente contra a base real (script de validação pontual, não uma nova
auditoria completa):

| Fórmula testada | Linhas comparáveis | Correspondência exata |
|---|---|---|
| `Cons. Real = Peso Líq − Sobra Limpa − Sobra Suja` | 13.673 (5 RUs: P1D, P2D, BD, LD, PO2) | **100,0%** |
| `ISC = (ÓTIMO×10 + REGULAR×5 + RUIM×1) / Total` | 3.663 (3 abas: ISC alm/jan/Café) | **100,0%** |

Com a primeira confirmada, `Quantidade distribuída = Peso Líq − Sobra Limpa`
deixa de ser hipótese: é a mesma equação reescrita algebricamente
(`Peso Líq − Sobra Limpa = Cons. Real + Sobra Suja`), não uma suposição
adicional. **Resultado:** Resto-Ingesta (kg e %), Per Capita e ISC agregado
estão implementados (`src/powerbi_export.py`, testado em
`tests/test_powerbi_export.py`).

Também foi confirmado, por inspeção de valores distintos (não uma suposição):
`Prep` é uma categoria fechada e estável (PB, PV, VEG, Arroz/Baião, Feijão,
Guarnição, Salada, Sobremesa, Suco, Café, Leite, Pão, Fruta, Especial etc.)
— compatível com `tipo_preparacao`; `Cardápio` é o prato específico do dia
— compatível com `preparacao`.

### Resto-Ingesta em kg — IMPLEMENTADO
`sobra_suja` é a fonte de `resto_ingesta_kg`, é o resíduo que sobra do
prato já servido, diferente de `sobra_limpa` (comida que nunca chegou a
ser servida). Esta continua sendo a leitura mais defensável da definição
da gestão — não houve, nesta etapa, uma confirmação literal e explícita da
Nutrição sobre o processo de pesagem, mas a fórmula foi implementada em
`src/powerbi_export.build_fact_producao` com base na evidência estrutural
disponível (a coluna existe, é preenchida consistentemente, e sua
semântica de "resíduo pós-serviço" é a única compatível com o desenho das
outras colunas — `sobra_limpa` claramente representa outra coisa).

### % Resto-Ingesta — IMPLEMENTADO
A v1 deste documento afirmou que `% Resto-Ingesta = (1 − indice_aceitabilidade) × 100`
sem provar que os dois indicadores usam o mesmo denominador — isso foi
corrigido na v2 (bloqueado) e agora resolvido na v3: `Quantidade
distribuída = Peso Líq − Sobra Limpa` deixou de ser hipótese porque decorre
diretamente da fórmula de `Cons. Real` validada com 100% de correspondência
(seção 3-A). `pct_resto_ingesta` está implementado por linha em
`fact_producao.csv`; a medida agregada correta (razão de somas, não média)
está documentada em `docs/medidas_powerbi.md`.

## 3. Satisfação do Cliente

### Escala — não propor 5 níveis
A imagem do PDF (cinco expressões faciais) é ilustrativa do conceito de
"nível de satisfação", não uma exigência de que o RU adote 5 categorias. O
texto da gestão pede "escala definida pelo RU" — se ÓTIMO/REGULAR/RUIM é,
de fato, a escala oficialmente usada pelo RU hoje (o que precisa ser
confirmado, não assumido), ela **atende ao requisito tal como está**. A
recomendação de criar uma quinta categoria, presente na v1, foi **removida**.

### Quem responde, escala, unidade de observação, periodicidade
Antes de tratar o ISC como "a" fonte de satisfação do cliente, four pontos
precisam de confirmação (nenhum é auto-evidente a partir dos dados):
- **Quem responde:** confirmar que os votos ÓTIMO/REGULAR/RUIM são
  preenchidos pelo comensal (cliente) e não por um atendente em nome dele.
- **Escala:** confirmar se ÓTIMO/REGULAR/RUIM é de fato a escala "definida
  pelo RU" mencionada no documento, ou se existe uma escala oficial
  diferente em uso.
- **Unidade de observação:** confirmar se cada linha de `fact_isc`
  representa um voto individual agregado por preparação/dia, ou já uma
  contagem pré-agregada de múltiplos votos (isso muda o que "distribuição"
  significa na prática).
- **Periodicidade:** confirmar se a coleta acontece em toda refeição, em
  dias específicos, ou por amostragem.

**Conclusão preservada da v1:** Avaliação Sensorial (`fact_sensorial`) **não
deve ser usada como substituto de Satisfação do Cliente** — é preenchida por
um integrante da equipe (`avaliador`), não pelo comensal. Isso é uma
diferença estrutural do processo de coleta, não uma interpretação.

## 4. Agregação do ISC — não assumir média simples

> **Atualização v3:** a fórmula `ISC = (ÓTIMO×10 + REGULAR×5 + RUIM×1) /
> Total` foi validada com 100% de correspondência em 3.663 linhas (seção
> 3-A) e está **implementada** como medida agregada (`fact_satisfacao.csv`
> preserva as contagens brutas; a agregação correta está em
> `docs/medidas_powerbi.md`). O texto abaixo, mantido da v2, descreve o
> raciocínio que levou a essa implementação.

**Problema identificado:** `isc_medio()` no MVP atual calcula
`AVERAGE(isc)` sobre o campo `isc` já pré-calculado por linha (por
RU/data/refeição/preparação). Isso trata uma linha com poucas
respostas e uma linha com muitas respostas com o mesmo peso — uma média de
médias, não uma média ponderada pelas respostas reais. Isso pode distorcer
o indicador em qualquer corte que agregue múltiplas preparações/dias com
volumes de resposta muito diferentes.

**Encaminhamento, sem inventar ponderação:**
- **Distribuição de satisfação:** deve ser calculada a partir das
  **contagens brutas** (`otimo`, `regular`, `ruim`) somadas no contexto do
  filtro selecionado — isso é aritmeticamente correto e não depende de
  nenhuma fórmula externa (é soma simples de contagens reais).
- **ISC agregado (o número único "8,83" que o MVP expõe hoje):** a fórmula
  original que gera o campo `isc` na planilha-fonte **não está documentada**
  em nenhum lugar que auditamos. Duas situações possíveis:
  - Se a fórmula for reconstituível a partir de `otimo`/`regular`/`ruim`
    (ex.: uma ponderação fixa tipo ÓTIMO=10, REGULAR=5, RUIM=0), o ISC
    agregado deveria ser recalculado sobre os **totais** de cada nível no
    contexto do filtro, não como média das médias por linha.
  - Se a fórmula depender de alguma regra não documentada da planilha
    original, **isso é um ponto a validar com quem criou a fórmula (RU/
    Nutrição/TI)**, não algo para o pipeline inventar.
- **Não implementar nenhuma das duas opções agora** — fica registrado como
  correção metodológica pendente para quando a implementação for aprovada.

## 5. Avaliação de Temperatura — implementada com regra oficial da Nutrição

> **Atualização v4:** a Nutrição forneceu a regra oficial de conformidade
> térmica (quente `>60°C`=CONFORME, `≤60°C`=NÃO CONFORME; fria `<10°C`=
> CONFORME, `≥10°C`=NÃO CONFORME). **Implementada** em
> `src/powerbi_export.compute_status_temperatura`, com testes de fronteira
> (60, 60.1, 59, 61°C / 9, 9.9, 10, 11°C). O bloqueio geral de temperatura
> está **resolvido** — resta só a classificação de 12 tipos de preparação
> ambíguos (seção residual em `docs/perguntas_validacao_nutricao.md`).

Separando o que a v1 misturava em uma única classificação "ausente":

### Temperatura medida — IMPLEMENTADO
Confirmado com dado real (checagem pontual da v1, reaproveitada aqui):

| RU | Linhas com data | Temperatura preenchida | % preenchido | Valores não numéricos |
|---|---|---|---|---|
| P1D | 3.487 | 3.443 | 98,7% | 195 (ex.: `"14,9/14,9"`, `"-"`) |
| P2D | 3.275 | 2.124 | 64,9% | 1 |
| BD | 5.519 | 4.234 | 76,7% | 1 (ex.: `"60,,6"`) |
| LD | 1.751 | 1.628 | 93,0% | 15 (ex.: `"NA"`) |
| PO2 | 1.771 | 1.650 | 93,2% | 0 |

Os valores numéricos são fisicamente plausíveis (60–85 °C em pratos
quentes, 11–15 °C em pratos frios) — o dado em si existe e é utilizável,
mediante limpeza dos valores em texto. Limpeza implementada em
`clean_temperatura` (leituras duplas → média; vírgula decimal; erros de
fórmula → nulo).

**Achado sobre o grão do `fact_temperatura`:** em pelo menos um caso
(`"14,9/14,9"`), a célula contém **duas leituras concatenadas em texto**
dentro de um único registro. Isso sugere que o processo real de medição
pode envolver mais de uma aferição por preparação/dia, mas a
planilha-fonte já achata isso em uma única célula. O pipeline usa a média
das leituras encontradas — ponto residual 2 em
`docs/perguntas_validacao_nutricao.md` (baixo impacto).

### Percentual de conformidade — IMPLEMENTADO
As colunas `ISO AZUL 3C` e `ISO PRETO 1C` (cogitadas na v1 como possíveis
campos de conformidade) foram descartadas: estão praticamente vazias em
todas as unidades (0 a 531 linhas preenchidas em bases de milhares de
linhas) — não foram usadas na implementação.

**Regra oficial recebida e implementada:**
```
Quente: temperatura > 60°C  → CONFORME   |  temperatura ≤ 60°C → NÃO CONFORME
Fria:   temperatura < 10°C  → CONFORME   |  temperatura ≥ 10°C → NÃO CONFORME
```
Operadores assimétricos preservados exatamente como fornecidos.

**Classificação de cada preparação como quente/fria:** feita **apenas**
para categorias inequivocamente identificáveis pela nomenclatura do RU,
centralizada em `config/mappings.yaml` (`classe_termica_por_tipo_preparacao`):
quentes = PB, PV, Arroz/Baião, Arroz Integral, Feijão; frias = Salada,
Suco, Suco SA, Fruta 1, Fruta 2. As demais 12 categorias (VEG, Guarnição,
Sobremesa, Café, Café SA, Leite, Leite Veg, Pão Francês, Pão Opção,
Especial, Especial Veg, Manteiga) ficam `SEM_CLASSIFICACAO` — **a
classificação nunca é inferida a partir da temperatura observada** (isso
seria circular). Relatório de auditoria dessas 12 categorias, com volume e
faixa de temperatura observada (só informativo), em
`outputs/preparacoes_sem_classificacao_termica.csv`.

**Medições fisicamente implausíveis (4 leituras, ex.: "614°C"):** recebem
`status_temperatura = MEDICAO_INVALIDA` e **nunca entram no denominador de
conformidade** — critério técnico: faixa −5°C a 100°C (mesma constante
`TEMPERATURA_FISICA_MIN/MAX` reaproveitada do relatório de qualidade, para
as duas checagens nunca divergirem). Preservadas (não excluídas
silenciosamente) em `outputs/relatorio_qualidade.csv`, regra
`temperatura_fora_da_faixa_fisica`.

**Resultado na última execução:** 12.858 medições válidas, 9.313
avaliadas (72,4% de cobertura), 5.879 conformes → **63,1% de
conformidade** entre as avaliadas.

## 6. Per Capita Presumido — bloqueado por mapeamento semântico

> **Atualização v3:** com `Cons. Real = Peso Líq − Sobra Limpa − Sobra Suja`
> validado (seção 3-A), a gestão confirmou explicitamente a fórmula
> `Per Capita = Cons. Real / Com. Real` (em g/comensal: ×1000). Isso está
> **implementado** em `fact_producao.csv` (`per_capita_g_comensal`), no
> grão de preparação, com a ressalva de granularidade já documentada em
> `docs/medidas_powerbi.md` (o denominador para agregações entre
> preparações deve vir de `fact_refeicoes`, nunca de soma direta de
> `comensais_real` em `fact_producao`). `PC Pres`/`PCE`/`PC %` continuam
> preservados como dados de origem, não substituídos automaticamente. O
> texto abaixo (da v2) documenta o raciocínio que levou a essa decisão.

Reclassificado de "PARCIAL" (v1) para **"PARCIAL / BLOQUEADO POR
MAPEAMENTO SEMÂNTICO DOS CAMPOS"**.

A fórmula da gestão (`(Total entregue − Sobras) / Número de refeições`)
tem três termos. Os campos candidatos identificados na planilha são:

| Termo da fórmula | Campo candidato | Confirmado? |
|---|---|---|
| Total entregue | `peso_liq` | **Não** — é uma hipótese, não uma confirmação |
| Sobras | `sobra_limpa + sobra_suja` | **Não** — mesma ressalva |
| Número de refeições | `comensais_real` (no grão de refeição) | Este é o único termo com confiança alta, pela mesma lógica já validada em `refeicoes_realizadas()` |

Além disso, a fonte já tem três colunas cujo nome sugere que o cálculo já
existiria pronto — `PC Pres`, `PCE`, `PC %` — mas os valores reais testados
na v1 **não reproduzem** a fórmula oficial de forma consistente (a razão
entre o valor testado e o esperado variou entre ~1× e ~2,2× sem padrão
claro). Isso é evidência de que essas colunas provavelmente respondem a uma
lógica diferente (ex.: planejamento/previsão, não realizado), mas a causa
exata não foi confirmada.

**Decisão desta revisão:** não implementar a fórmula de Per Capita no
pipeline com base nas hipóteses acima. O significado operacional de Peso
Bruto, Peso Líquido, Sobra Limpa, Sobra Suja, `PC Pres`, `PCE` e `PC %`
precisa ser esclarecido pela Nutrição antes de qualquer código ser escrito
(ver `docs/perguntas_validacao_nutricao.md`, pergunta 2).

## 7. Reestruturação conceitual do painel (mantida, com ajuste de escopo)

| Nível da gestão | Conteúdo pedido | Onde está hoje | Observação desta revisão |
|---|---|---|---|
| **Visão Geral** | Nº total de refeições, evolução temporal, comparação entre unidades | Já existe (abas "Visão Geral" + "Panorama") | Sem bloqueio — pode ser consolidado |
| **Qualidade** | Resto-ingesta, satisfação do cliente, temperatura das preparações | Parcialmente disperso entre abas atuais | Estrutura de página pode ser criada agora; **os indicadores de Resto-Ingesta (%), Satisfação (agregação) e Temperatura (conformidade) que entram nela dependem das respostas da Nutrição** — a página pode nascer com os itens não bloqueados (Resto-Ingesta em kg como candidato, distribuição ISC, temperatura medida) e os bloqueados sinalizados como pendentes, não implementados como se estivessem prontos |
| **Produção e Eficiência** | Per capita das preparações, relação produção × consumo, indicadores de desperdício | Parcial | Per capita **bloqueado**; "relação produção × consumo" pode usar `peso_bruto`/`peso_liq`/`comensais_real` sem depender das respostas pendentes, desde que rotulado como indicador técnico de produção, não como "Per Capita oficial" |
| *(fora do documento da gestão)* | — | Aba "Gestão" (atendimentos, manutenção) | Mantida só no Streamlit; não migra para o modelo Power BI da nutrição |

## 8. Filtro por "Tipo de Preparação" — significado não assumido

O documento da gestão pede filtro por "tipo de preparação", mas não define
o que isso significa. Interpretações possíveis, nenhuma confirmada:
- O nome/código da preparação em si (`prep`/`cardapio` — o que já temos).
- Uma classificação por função no cardápio (prato principal, guarnição,
  acompanhamento, salada, sobremesa).
- Uma classificação térmica (`classe_termica`: quente/fria) — que, se
  confirmada como a intenção da gestão, também resolveria parte do
  bloqueio de conformidade de temperatura (seção 5).

**Nenhuma dessas classificações existe hoje em nenhuma planilha do Sistema
RU.** Não há uma coluna `tipo_preparacao` ou equivalente nas fontes já
auditadas. Antes de desenhar o filtro ou a dimensão futura de preparação, é
necessário perguntar à Nutrição o que "tipo de preparação" significa
oficialmente (ver `docs/perguntas_validacao_nutricao.md`, pergunta 4).

Se confirmado que a dimensão de preparação deve conter `tipo_preparacao`
e/ou `classe_termica`, esses campos **só devem ser criados a partir de uma
classificação fornecida ou validada pela Nutrição** — não inferidos
automaticamente do nome do prato.

## 9. Reclassificação final dos indicadores (v4)

| Indicador | Status |
|---|---|
| Número de Refeições | **ATENDIDO / IMPLEMENTADO** — `fact_refeicoes.csv`, regressão de 1.081.064 confirmada |
| Satisfação do Cliente (média + distribuição) | **IMPLEMENTADO** — ISC agregado recalculado a partir de contagens (validado 100%); distribuição ÓTIMO/REGULAR/RUIM exposta. Ressalva: 40% das linhas não têm o prato específico identificado (recuperável só até o nível de `tipo_preparacao`, nunca inventado) |
| Resto-Ingesta (kg) | **IMPLEMENTADO** — `resto_ingesta_kg = sobra_suja` |
| % Resto-Ingesta | **IMPLEMENTADO** — denominador `quantidade_distribuida` decorre da fórmula de `Cons. Real` validada (seção 3-A) |
| Temperatura medida | **IMPLEMENTADO** — limpa, validada, com checagem de plausibilidade física |
| Conformidade de temperatura | **IMPLEMENTADO METODOLOGICAMENTE** — regra oficial da Nutrição aplicada; cobertura real de 72,4% das medições válidas (12 categorias ambíguas ficam `SEM_CLASSIFICACAO`, não rebaixam o indicador, só reduzem sua cobertura — registrado explicitamente, não escondido) |
| Per Capita Presumido | **IMPLEMENTADO** — `per_capita_g_comensal`, com ressalva de granularidade documentada em `docs/medidas_powerbi.md` |
| Filtro por tipo de preparação | **IMPLEMENTADO NO MODELO** — `dim_preparacao[tipo_preparacao]`; para Satisfação, cobertura parcial (60% das linhas têm prato específico, 100% têm ao menos o tipo, ver acima) |
| Estrutura em 3 níveis | **ESPECIFICADO** — `docs/especificacao_visual_powerbi.md`; construção do `.pbix` em si é etapa separada |
| Ferramenta Power BI | **REQUISITO DADO — ARQUITETURA E DADOS IMPLEMENTADOS** |

## 10. Branch de trabalho
Todo o trabalho desta e das etapas anteriores foi feito na branch
`feature/alinhamento-painel-gestao`, sem nenhuma alteração em `main`.

## 11. Priorização revisada (P0 executável vs. P0 bloqueado)

### P0 — executável agora, sem depender da Nutrição
1. Definir e documentar o **modelo estrela** revisado (dimensões + fatos no
   grão correto) — ver `docs/arquitetura_powerbi.md`.
2. Desenhar a tabela `fact_refeicoes` (grão RU+Data+Refeição), reaproveitando
   a lógica de deduplicação já validada em `metrics._meal_level` — resolve
   na origem (Python) o problema de granularidade, em vez de corrigir depois
   em DAX.
3. Expor a **distribuição** ÓTIMO/REGULAR/RUIM do ISC (soma de contagens
   brutas, sem inventar ponderação).
4. Mapear `temp_c` no pipeline e tratar os valores de texto sujo (leituras
   duplas, vírgula decimal, "NA") — a medição em si não depende de nenhuma
   definição externa, só de limpeza de dado.
5. Preparar a estrutura de páginas do Power BI (Visão Geral / Qualidade /
   Produção e Eficiência), com os indicadores não bloqueados já
   posicionados e os bloqueados sinalizados como pendentes.
6. Consolidar e enviar `docs/perguntas_validacao_nutricao.md` à gestão/Nutrição.

### P0 — bloqueado pela Nutrição (não iniciar implementação de código antes da resposta)
7. `% Resto-Ingesta` — depende da definição de "Quantidade distribuída".
8. `Resto-Ingesta (kg)` — depende da confirmação de que `sobra_suja` é
   exatamente o resíduo pós-consumo definido pela gestão.
9. Conformidade de temperatura — depende de limites e classificação
   quente/fria por preparação.
10. Per Capita Presumido — depende do significado operacional de Peso
    Bruto, Peso Líquido, Sobra Limpa, Sobra Suja, `PC Pres`, `PCE`, `PC %`.
11. Filtro/dimensão de "tipo de preparação" — depende da definição do termo.
12. Fórmula de agregação do ISC — depende de confirmar se é reconstituível
    a partir das contagens ou se é uma regra não documentada.

### P1 — importante para a primeira entrega (não bloqueado, mas não crítico para atender a orientação da gestão)
13. Expor média mensal de refeições como card/gráfico dedicado.
14. Reestruturar a navegação do Streamlit em 3 abas, espelhando o Power BI.
15. Implementar o filtro por preparação no Streamlit **depois** que o
    significado de "tipo de preparação" for confirmado.

### P2 — evolução posterior
16. Avaliar, com a Nutrição, se `PC Pres`/`PCE`/`PC %`/`ISO AZUL 3C`/
    `ISO PRETO 1C` têm algum uso residual depois de entendida sua real
    finalidade.
17. Avaliar granularidade fina de medição de temperatura (múltiplas
    aferições por preparação), se confirmado que o processo real coleta
    mais de uma leitura.
18. Automatizar atualização do Power BI (agendamento de refresh).
