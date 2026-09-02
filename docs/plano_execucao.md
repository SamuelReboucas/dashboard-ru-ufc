# Plano de Execução — Recuperação do Projeto RU

## MVP imediato (alvo: 3–4 semanas a partir de 02/09/2026)

| Atividade | Prioridade | Impacto | Esforço | Dependência | KR relacionado |
|---|---|---|---|---|---|
| Validar `docs/auditoria_dados.md` e `docs/fontes_oficiais.md` com a gestão do RU (1 reunião) | Muito alta | Muito alto | Baixo | — | O1.1, O1.5 |
| Validar lista de 13 KPIs do MVP com a gestão (1 reunião, pode ser a mesma acima) | Muito alta | Alto | Baixo | Auditoria validada | O2.1 |
| Escrever ETL: extração + limpeza das 5 abas `xD/x2` + `CARDÁPIO` | Muito alta | Muito alto | Médio | — | O1.2, O1.3 |
| Escrever ETL: extração + limpeza de `Av. Sensorial` e `ISC alm/jan/Café` | Alta | Alto | Médio | — | O1.3, O1.4 |
| Construir tabela fato única + dimensão RU/Calendário/Cardápio | Muito alta | Muito alto | Médio | ETLs acima | O1.3, O1.4 |
| Implementar as 13 métricas do MVP em Python | Alta | Alto | Médio | Tabela fato pronta | O2.2 |
| Construir dashboard Streamlit (4 páginas) | Alta | Alto | Médio | Métricas prontas | O2.3 |
| Publicar repositório no GitHub + deploy do dashboard | Alta | Alto | Baixo | Dashboard funcional | O2.3 |
| Documento de governança mínima (quem atualiza o Excel, com que frequência, quem roda o ETL) | Alta | Alto | Baixo | — | O1.6 |
| Apresentação executiva de fechamento do "pacote atrasado" à gestão | Muito alta | Muito alto | Baixo | Dashboard publicado | O5.1 |

## Segunda evolução (após o MVP, dentro da Fase 2 até 31/12)

| Atividade | Prioridade | Impacto | Esforço | Dependência | KR relacionado |
|---|---|---|---|---|---|
| Definir e aplicar instrumento de pesquisa de satisfação (piloto) | Alta | Alto | Médio | — | O3.1, O3.2 |
| Integrar bloco de satisfação ao dashboard | Média | Médio | Baixo | Piloto de satisfação rodando | O2.4 |
| Fechar ciclo de feedback visível ao público (card simples) | Média | Médio | Baixo | Piloto em andamento | O3.3 |
| Refazer refeições vegetarianas (`REFEIÇÕES VEG`) do zero, sem herdar fórmulas quebradas | Média | Médio | Médio | Tabela fato consolidada | Backlog do OKR (não crítico) |
| Selecionar e pilotar solução inovadora (ex.: "melhor horário para ir ao RU") | Média | Médio | Alto | Base analítica pronta | O4.1, O4.2 |
| Ampliar indicadores e melhorar usabilidade do dashboard | Média | Médio | Médio | MVP em produção | O5.2 |
| Institucionalizar governança e documentação operacional completa | Média | Alto | Médio | Governança mínima aprovada | O5.3 |

## Backlog (pode esperar)

| Item | Motivo de baixa prioridade |
|---|---|
| Consumo de proteína/arroz por RU (`dados ajustes`) | Nicho de nutrição, não citado como prioridade pela gestão |
| Automação agendada do ETL (cron) | Atualização manual é suficiente no volume atual |
| Banco de dados relacional (Postgres) | Volume de dados não justifica ainda |
| Autenticação/controle de acesso no dashboard | Definir necessidade após decidir se o painel é público ou interno |
| Investigação da aba `Entregas` duplicada dentro do Sistema RU | Resolver via decisão de governança (fonte única), não é bloqueio técnico |
| Reaproveitamento de `Controle de Estoque` (99,8% vazio) | Validar primeiro se a equipe pretende retomar o preenchimento |
| Coleta de Resíduo (projeto de pesquisa) | Fora do escopo de indicadores operacionais do RU |

## Sequenciamento sugerido (visão de calendário)

| Semana (a partir de 02/09) | Foco |
|---|---|
| 1 | Validação da auditoria e dos KPIs com a gestão + início do ETL das abas `xD/x2` |
| 2 | ETL de qualidade (`Av. Sensorial`, `ISC *`) + montagem da tabela fato |
| 3 | Implementação das métricas + primeira versão do dashboard local |
| 4 | Deploy, documento de governança e apresentação executiva de fechamento |
| 5 em diante | Início da 2ª evolução (satisfação, inovação, ampliação) |
