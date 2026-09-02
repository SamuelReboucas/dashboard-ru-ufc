# MVP do Dashboard RU — v1

**Critério de seleção:** indicador só entra se (a) a fonte tem confiabilidade Alta ou Média-tratável,
(b) o esforço de cálculo é baixo/médio, e (c) resolve diretamente uma pergunta que a gestão do RU faz
hoje. Total: **13 KPIs** em 4 áreas.

## A. Panorama (4 KPIs)

| KPI | Definição | Motivo no MVP | Fonte | Fórmula | Confiança | Filtros |
|---|---|---|---|---|---|---|
| Refeições realizadas | Nº de comensais atendidos no período | Métrica base de volume, usada em toda reunião de gestão | `P1D/P2D/BD/LD/PO2` (`Com. Real`) | `SUM(Comensais Real)` | Alta | RU, Refeição, período |
| % Execução (Previsto x Real) | Realizado / Previsto | Mede acurácia do planejamento de compras/produção | idem (`Previsão`, `Comensais Real`) | `Comensais Real / Previsão` | Alta | RU, Refeição, período |
| Evolução diária/mensal | Série temporal de refeições realizadas | Detecta sazonalidade e quedas atípicas | idem | Agregação por dia/semana/mês | Alta | RU, Refeição |
| Comparação entre RUs | Refeições realizadas por RU, lado a lado | Pergunta recorrente da gestão ("qual RU está performando melhor") | idem | Agregação por RU | Alta | Período, Refeição |

## B. Desperdício e eficiência (4 KPIs)

| KPI | Definição | Motivo no MVP | Fonte | Fórmula | Confiança | Filtros |
|---|---|---|---|---|---|---|
| Rejeito total (kg) | Volume de alimento descartado antes do consumo | Indicador de eficiência de produção | `xD/x2` (`Peso Bruto` − `Consumo Real`) | Recalculado no ETL | Alta | RU, período |
| Desperdício per capita | (Sobra limpa + Sobra suja) / Comensais reais | Indicador comparável entre RUs de tamanhos diferentes | idem (`S.L`,`S.S`,`Com. Real`) | `(S.L+S.S)/Com.Real` | Alta | RU, período |
| Índice de aceitabilidade (resto-ingesta) | % do prato efetivamente consumido | Indicador clássico de nutrição/qualidade | `xD/x2` recalculado (cross-check com `NAC *`) | `1 - (resto/servido)` | Média (tratar erros na fonte de apoio) | RU, período |
| Comparação de desperdício entre RUs | Per capita por RU | Suporta decisão de realocar cardápio/insumo | consolidação `xD/x2` | Agregação por RU | Alta | Período |

## C. Qualidade / satisfação (3 KPIs)

| KPI | Definição | Motivo no MVP | Fonte | Fórmula | Confiança | Filtros |
|---|---|---|---|---|---|---|
| Avaliação sensorial média | Média de `Global` por refeição/RU | Indicador direto de satisfação com o prato | `Av. Sensorial` | `AVG(Global)` | Alta | RU, Refeição, período |
| ISC (Índice de Satisfação do Cliente) | % ÓTIMO ponderado | Métrica que a gestão já reconhece e usa (nome já existente no sistema atual) | `ISC alm/jan/Café` (recalculado) | `(ÓTIMO*3+REGULAR*2+RUIM*1)/(3*total)` | Média (limpar `#VALUE!` antes) | RU, Refeição, período |
| Top 5 piores preparações do mês | Ranking por menor nota sensorial | Ação direta para nutrição/cozinha | `Av. Sensorial` | `RANK` por `AVG(Global)` | Alta | RU, período |

## D. Gestão (2 KPIs)

| KPI | Definição | Motivo no MVP | Fonte | Fórmula | Confiança | Filtros |
|---|---|---|---|---|---|---|
| Atendimentos e % resolvidos | Volume de chamados e taxa de resolução | Visibilidade de suporte ao estudante, sem expor dado pessoal | `Atendimentos Especializado` (agregado) | `COUNT`, `% Resolvido = Sim/Total` | Boa, mas volume baixo (39 registros) | RU, mês, status |
| OS de manutenção abertas x resolvidas | Nº de OS por status | Visibilidade operacional (infra + TI) | `UFC-INFRA` + `OS - STI` | `COUNT` por status | Boa | RU, tipo (infra/TI), período |

## Fora do MVP v1 (2ª evolução)
- Bloco de experiência do usuário (depende do piloto de pesquisa de satisfação, ainda não implantado — KR O3.2).
- Refeições vegetarianas (dado existe em `REFEIÇÕES VEG`, mas 6.698 erros de fórmula tornam o refazimento
  mais caro que o benefício imediato).
- Consumo de proteína/arroz por RU (`dados ajustes`) — nicho de nutrição, não citado como prioridade da gestão.
- Treinamentos da equipe — volume insuficiente (13 registros) para virar tendência confiável ainda.

## Nota sobre privacidade no dashboard
Nenhum dos 13 KPIs acima expõe CPF, nome de estudante ou texto livre de atendimento. Todos os dados de
`Atendimentos Especializado` entram **apenas agregados**.
