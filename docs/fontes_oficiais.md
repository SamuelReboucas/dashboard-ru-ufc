# Fontes Oficiais por Domínio de Indicador

Princípio aplicado: **dados operacionais > células calculadas > dashboard existente**. As abas de
detalhe (`P1D`, `P2D`, `BD`, `LD`, `PO2`) têm zero ou poucos erros de fórmula e granularidade de
preparação/dia — são preferidas como fonte. As abas consolidadas (`P1`, `P2`, `B`, `L`, `PO`) e o
`Painel RU` existente **não** devem ser usados como fonte de verdade; servem apenas de referência de
layout/nomenclatura.

## Panorama (refeições previstas/realizadas, por RU e tipo)

| Indicador / domínio | Aba fonte | Campos | Transformação necessária | Confiabilidade |
|---|---|---|---|---|
| Refeições previstas x realizadas | `P1D`,`P2D`,`BD`,`LD`,`PO2` | `Data`, `Previsão`, `Peso Previsto`, `Comensais`, `Com. Real`/`Comensais Real` | Agregar por RU+Data+Refeição (o cardápio/prep é o grão original) | Alta (P1D/P2D/PO2 sem erros; BD com 281 a tratar) |
| Refeições por tipo (Café/Almoço/Jantar) | idem + `CARDÁPIO` | `Refeição` (Pici1)/`REF` (demais) | Padronizar nome do campo (`Refeição` vs `REF`) entre as 5 abas | Alta |
| Histórico diário/mensal | idem | `Data`, `Mês` | Derivar mês a partir da data (coluna `Mês` já existe mas é texto livre) | Alta |
| Comparação entre RUs | consolidação das 5 abas `xD/x2` | `RU` (a criar, hoje é implícito pelo nome da aba) | **Adicionar coluna `RU` explícita** no ETL — hoje o RU é identificado só pelo nome da aba | Alta, após ETL |
| Cardápio do dia (dimensão) | `CARDÁPIO ` | `Refeição`, `mÊS`, `Data`, `Prep`, `Cardápio` | Corrigir 1 célula com `#REF!`; normalizar nome da coluna `mÊS` | Boa |

## Desperdício e eficiência

| Indicador / domínio | Aba fonte | Campos | Transformação necessária | Confiabilidade |
|---|---|---|---|---|
| Rejeito | `P1D`,`P2D`,`BD`,`LD`,`PO2` | `Peso Bruto`, `Peso Líq`, `S.L` (sobra limpa), `S.S` (sobra suja) | Fórmula: Rejeito = Peso Bruto − Consumo Real | Alta |
| Desperdício per capita | idem | `PC %`, `PC Pres`, `Com. Real` | Recalcular per capita = (S.L+S.S)/Comensais Real; **não herdar fórmula das abas `x` (P1/B/L/PO)**, que têm erros | Alta na fonte, mas recalcular do zero |
| Sobra limpa / sobra suja | idem | `S.L`, `S.S` | Direto | Alta |
| Resto-ingesta (RI) | `NAC ALM`/`NAC JAN`/`NAC CAFÉ` (colunas "Indice de Aceitação") | `B/L/P1/P2/PO IA` | Recalcular a partir de `xD` (Peso Bruto vs Consumo) em vez de copiar do NAC, que tem erros | Média — usar como cross-check, não fonte única |
| Índice de aceitabilidade | idem | `MIA` (média) | idem | Média |
| Comparação entre RUs | consolidação `xD/x2` | — | idem Panorama | Alta após ETL |

## Qualidade / satisfação

| Indicador / domínio | Aba fonte | Campos | Transformação necessária | Confiabilidade |
|---|---|---|---|---|
| Avaliação sensorial (aparência/textura/sabor/odor/global) | `Av. Sensorial` | `Refeitório`, `data`, `Refeição`, `Preparação`, `Aparência`, `Textura`, `Sabor`, `Odor`, `Global`, `Nota` | Corrigir header `mês` com `#REF!`; padronizar nome de coluna `Refeitório`→`RU` | Alta (só 3 erros pontuais em 5.516 linhas) |
| ISC (Índice de Satisfação do Cliente) | `ISC alm`, `ISC jan`, `ISC Café` | Blocos `ÓTIMO/REGULAR/RUIM/ISC` por RU | Recalcular ISC = (ÓTIMO×3+REGULAR×2+RUIM×1)/total; tratar 209–752 erros `#VALUE!` por refeição | Média — exige limpeza antes do uso |
| Melhores/piores preparações | `Prep menos aceitas mês`, `Tabela dinâmica 1`, `Av. Sensorial` (agregando) | `Preparação`, `Global`/`Nota` | Recalcular ranking direto de `Av. Sensorial`, sem depender do pivot legado | Alta, recomputando |
| Evolução no tempo | `Av. Sensorial` + `ISC *` | `data` | Agregação semanal/mensal | Alta |

## Gestão

| Indicador / domínio | Aba fonte | Campos | Transformação necessária | Confiabilidade |
|---|---|---|---|---|
| Atendimentos | `Atendimentos Especializado` | `Data`, `RU`, `Motivo`, `Resolvido`, `Responsável` | **Nunca expor `Nome ou CPF do atendido` nem o texto de `Motivo`/`Observações` em painel** — agregar por RU/mês/status | Boa, mas baixo volume (39 registros) |
| % resolução | idem | `Resolvido` (Sim/Não) | Contagem simples | Boa |
| Treinamentos | `Treinamentos` | `Mês`, `Tema`, `Facilitador`, colunas booleanas por RU (`P1`,`P2`,`B`,`PO`,`L`) | Poucos registros (13) — considerar KPI só se a gestão mantiver o registro atualizado | Baixa (volume) |
| Manutenção / OS | `UFC-INFRA`, `OS - STI` | `Data`, `Motivo`, `Resolvido`, `Data de Resolução` | `UFC-INFRA` tem datas como texto dd/mm/aaaa — converter para data | Boa |
| Entregas do plano de ação | Arquivo **OKR oficial** (`plano_acompanhamento_RU_OKR_2026.xlsx`, aba `OKRs`) | — | **Não usar** a aba `Entregas` dentro do Sistema RU (duplicada e 98% vazia) — ver achado de governança na auditoria | Definir fonte única com a gestão |

## Não recomendado como fonte (mas mantido como referência)
- `Painel RU`, `dados PAINÉIS`, `Per capitas`, `Relatório Desperdício`, `Página20/17/23/42/38`,
  `REFEIÇÕES VEG`, `sobras e rejeitos`, `Controle de Estoque` (baixíssima cobertura),
  `Coleta de Resíduo` (fora de escopo) — motivos detalhados em `docs/auditoria_dados.md`.
