# OKR Recovery — Plano de Acompanhamento RU 2026
**Arquivo:** `plano_acompanhamento_RU_OKR_2026.xlsx` · **Hoje:** 02/09/2026 · **Atraso:** ~2 meses (marco original 02/07/2026)

## Achado crítico
No arquivo de tracking, **as 21 KRs estão marcadas como "A iniciar"** — nenhuma foi movida para
"Em andamento" ou "Concluído". Isso **não reflete a realidade operacional**: a auditoria do Sistema RU
mostra dados correntes até 01–07/09/2026 em todas as bases-chave. Conclusão: o trabalho de *coleta* nunca
parou, mas o *tracker* nunca foi atualizado e o trabalho de *estruturação/BI* (o real objeto do OKR) de
fato não avançou. Isso é, ao mesmo tempo, boa notícia (matéria-prima existe) e alerta de governança
(processo de acompanhamento não está sendo usado).

## Matriz de priorização

| Prioridade | KR | Prazo original | Entrega | Impacto | Esforço | Dependências | Ação recomendada |
|---|---|---|---|---|---|---|---|
| 1 | O1.1 – Inventariar 100% das bases prioritárias | 03/05/2026 | Mapa das bases validado | MUITO ALTO | BAIXO | Acesso às planilhas | **Recuperável imediatamente** — `docs/auditoria_dados.md` já é 90% desse inventário; falta validar com a gestão do RU e formalizar como ata |
| 2 | O1.2 – Padronizar campos/formatos/categorias | 17/05/2026 | Padrão mínimo aplicado | MUITO ALTO | MÉDIO | O1.1 | Definir nomenclatura oficial de RUs (P1/P2/B/L/PO → nomes completos), formato único de data e chaves de refeição (Café/Almoço/Jantar) |
| 3 | O2.1 – Definir indicadores prioritários do RU | 03/05/2026 | Lista validada com gestão | ALTO | BAIXO | Reunião com gestão | **Recuperável rápido** — usar `docs/mvp_dashboard.md` como proposta inicial para validar em 1 reunião |
| 4 | O1.5 – Criar dicionário de dados v1 | 31/05/2026 | Campos críticos documentados | ALTO | BAIXO | Consolidação mínima | Direto a partir da tabela mestra da auditoria — baixo esforço adicional |
| 5 | O1.3 – Consolidar bases prioritárias em estrutura única v1 | 17/05/2026 | Base consolidada v1 | MUITO ALTO | MÉDIO | O1.2 | Script Python único lendo P1D/P2D/BD/LD/PO2 + CARDÁPIO → tabela fato única |
| 6 | O1.4 – Tratar inconsistências e definir chaves de cruzamento | 24/05/2026 | Base v2, chaves definidas | MUITO ALTO | MÉDIO | O1.3 | Tratar os ~11.900 erros de fórmula mapeados na auditoria; chave = RU + Data + Refeição + Preparação |
| 7 | O2.2 – Modelar base analítica mínima para dashboard | 07/06/2026 | Modelo analítico mínimo | ALTO | MÉDIO | O1.4 | Depende da base consolidada; usar estrutura proposta em `docs/arquitetura_proposta.md` |
| 8 | O2.3 – Entregar dashboard v1 funcional | 14/06/2026 | Dashboard funcional | ALTO | MÉDIO | O2.2 | Este é o entregável que a gestora está cobrando agora — ver plano de execução |
| 9 | O1.6 – Definir regras de atualização e governança mínima | 07/06/2026 | Fluxo mínimo de manutenção | ALTO | BAIXO | O1.5 | Curto: 1 documento de 1–2 páginas (quem atualiza o quê, com que frequência) |
| 10 | O1.7 – Definir estrutura mínima preparada para integração futura | 14/06/2026 | Modelo lógico simplificado | ALTO | BAIXO | O1.4 | Consequência natural do trabalho de O1.3/O1.4, custo marginal baixo |
| 11 | O5.1 – Fechar pacote do semestre e plano do 2º semestre | 02/07/2026 | Entrega consolidada e aprovada | MUITO ALTO | BAIXO | Frentes mínimas concluídas | Reagendar para logo após o dashboard v1 — é essencialmente esta apresentação executiva |
| 12 | O2.4 – Integrar bloco inicial de experiência do usuário ao painel | 21/06/2026 | Bloco de experiência visível | MÉDIO | BAIXO | Dados de satisfação | Depende de O3.1–O3.2 (pesquisa); pode entrar como placeholder no v1 e ativar depois |
| 13 | O3.1 – Definir instrumento mínimo da pesquisa de satisfação | 10/05/2026 | Questionário validado | ALTO | BAIXO | Validação operacional | Sem dependência técnica pesada — pode rodar em paralelo à BI |
| 14 | O3.2 – Implantar piloto funcional de satisfação | 21/06/2026 | Coleta inicial com dados reais | ALTO | MÉDIO | O3.1 | Depende de decisão de canal (QR Code/tablet); não depende do Sistema RU existente |
| 15 | O3.3 – Gerar feedback visível inicial para usuários | 28/06/2026 | Resultado visível ao público | MÉDIO | BAIXO | O3.2 em andamento | Pode virar 1 card simples dentro do próprio dashboard |
| 16 | O4.1 – Selecionar solução inovadora mais viável | 07/06/2026 | Solução escolhida | MÉDIO | BAIXO | Leitura da base disponível | Baixo esforço, mas de baixo impacto imediato — não é gargalo do dashboard |
| 17 | O4.2 – Rodar piloto da solução inovadora | 28/06/2026 | Piloto testado | MÉDIO | ALTO | O4.1 | Adiar para depois do MVP — maior esforço, menor urgência de apresentação |
| 18 | O5.2 – Aprofundar dashboards e rotina da satisfação | 30/09/2026 | Painéis ampliados | ALTO | ALTO | Fase 1 concluída | Fase 2 — não priorizar agora |
| 19 | O5.3 – Institucionalizar governança e documentação operacional | 30/11/2026 | Rotinas formalizadas | ALTO | MÉDIO | Fase 2 em andamento | Fase 2 |
| 20 | O5.4 – Fechamento final e recomendações | 31/12/2026 | Relatório final | ALTO | MÉDIO | Demais entregas | Fase 2 |

*(20 linhas de matriz — a 21ª KR, "Definir estrutura mínima" O1.7, está listada acima; o arquivo original
lista 21 IDs de O1.1 a O5.4, todos endereçados nesta matriz.)*

## Evidência necessária para considerar cada KR "atendido"
| KR | Evidência mínima aceitável |
|---|---|
| O1.1 | `docs/auditoria_dados.md` aprovado em ata com a gestão do RU |
| O1.2 | Documento de convenções de nomenclatura/formatos + amostra de 3 bases já padronizadas |
| O1.3 | Arquivo/tabela única versionada (CSV ou Parquet) com todos os RUs, com contagem de linhas batendo com a soma das fontes |
| O1.4 | Relatório de antes/depois do número de erros de fórmula e % de campos nulos |
| O1.5 | `docs/fontes_oficiais.md` como dicionário de dados v1 |
| O1.6 | Documento de governança (1–2 páginas) assinado/aprovado |
| O1.7 | Diagrama do modelo lógico (`docs/arquitetura_proposta.md`) |
| O2.1 | Lista de KPIs aprovada pela gestão (pode ser e-mail/ata simples) |
| O2.2 | Tabela de métricas versionada com fórmulas documentadas |
| O2.3 | Link do dashboard publicado + print |
| O2.4 | Card de satisfação visível no dashboard |
| O3.1–O3.3 | Protótipo do formulário + print da coleta rodando |
| O4.1–O4.2 | Documento de decisão + registro do piloto |
| O5.1 | Apresentação consolidada entregue à gestão |

**Regra aplicada:** nenhuma KR foi considerada "concluída" apenas por haver dados relacionados no Sistema
RU — a coluna "Fonte de evidência" do arquivo OKR original é o critério oficial.

## Resumo de recuperabilidade
- **Recuperáveis em 1–2 semanas com esforço baixo/médio:** O1.1, O1.5, O2.1, O1.6, O1.7, O3.1 → 6 KRs.
- **Recuperáveis em 2–4 semanas (dependem de ETL):** O1.2, O1.3, O1.4, O2.2, O2.3, O5.1 → 6 KRs (caminho crítico do dashboard).
- **Paralelas, sem dependência técnica do Sistema RU:** O3.2, O3.3, O4.1 → podem avançar simultaneamente.
- **Adiáveis para depois do marco de apresentação:** O2.4, O4.2, e todas as O5.2–O5.4 (Fase 2, prazo 31/12).

---

## Reavaliação com evidência real (pós-implementação do MVP)

Atualização feita após a implementação técnica do MVP (pipeline, dashboard,
testes) e a formalização da governança mínima. Critério aplicado: só
"ATENDIDO" com evidência concreta já existente; nenhuma KR é promovida por
estar "quase pronta".

| KR | Situação anterior | Situação atual | Evidência |
|---|---|---|---|
| O1.6 – Definir regras de atualização e governança mínima | Recuperável, baixo esforço | **ATENDIDO** | `docs/governanca_dados.md` (fonte oficial, papéis, periodicidade recomendada, fluxo, validação, versionamento, tratamento de erro, histórico) + `docs/atualizacao_dashboard.md` (manual operacional passo a passo). Responsáveis por papel ainda marcados `A DEFINIR COM A GESTÃO` — a governança do *processo* está formalizada; a atribuição de *pessoas* aos papéis, não. |
| O2.3 – Entregar dashboard v1 funcional | Caminho crítico do dashboard | **PARCIAL** | O dashboard está funcional e validado **localmente** (pipeline + 41 testes + smoke test real do Streamlit, todos passando) e **preparado para deploy** (repositório Git montado, `.gitignore` validado, `data/processed_public/` auditada). **Não está, até o momento, publicado online** — a criação do repositório no GitHub e o deploy no Streamlit Community Cloud dependem de autenticação da conta da pessoa responsável, que não foi executada nesta etapa. Só será promovido a "ATENDIDO" quando houver uma URL pública funcionando. |

**Nota sobre O5.1** (fechar pacote do semestre): a apresentação executiva
consolidada continua pendente de agendamento com a gestão — não avança
enquanto O2.3 não estiver com o dashboard efetivamente online.
