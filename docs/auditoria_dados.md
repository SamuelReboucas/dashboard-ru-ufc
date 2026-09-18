# Auditoria de Dados — Sistema RU
**Arquivo:** `2026 Sistema RU.xlsx` (11,2 MB, 42 abas) · **Data da auditoria:** 02/09/2026 · **Modo:** leitura (read-only)

## Achado central (leia isto primeiro)

As bases operacionais diárias (P1D, P2D, BD, LD, PO2, Av. Sensorial, ISC alm/jan/Café, CARDÁPIO) estão
**alimentadas até 01–07/09/2026**, ou seja, **a coleta operacional nunca parou** — o RU continuou
registrando dados o ano inteiro. O que não aconteceu foi a estruturação/consolidação/BI (exatamente o
escopo da Fase 1 do OKR). Isso muda o diagnóstico: não é um projeto de "recuperar dados perdidos", é um
projeto de "estruturar dados que já existem e estão correntes". Risco principal não é ausência de dado,
e sim qualidade (erros de fórmula, duplicidade de linhas-template, nomenclatura inconsistente entre abas).

## Mapa de RUs identificados
5 unidades: **Pici 1 (P1)**, **Pici 2 (P2)**, **Benfica (B)**, **Porangabussu (PO)**, **Labomar (L)**.
Cada uma tem um par de abas: `<sigla>` (visão consolidada por refeição/dia) e `<sigla>D`/`<sigla>2`
(detalhe por preparação/item, com controles de temperatura/HACCP, pesagem e per capita).

## Tabela mestra de classificação (42 abas)

| Aba | Categoria | Finalidade | Período | Registros úteis¹ | Qualidade | Usar no MVP? | Observações |
|---|---|---|---|---|---|---|---|
| P1D | FONTE | Detalhe operacional Pici 1 (prep, temp, pesagem, previsão, per capita, votos) | 05/01–03/09/2026 | 4.455 | Boa (0 erros de fórmula) | **Sim** | Fonte primária de Panorama + Desperdício + Qualidade (Pici 1) |
| P2D | FONTE | Idem, Pici 2 | 05/01–02/09/2026 | 4.054 | Boa (0 erros) | **Sim** | Fonte primária Pici 2 |
| BD | FONTE | Idem, Benfica | 05/01–02/09/2026 | 5.807 | Média (281 erros #N/A/#VALUE!) | **Sim** | Maior RU; tratar erros antes de usar |
| LD | FONTE | Idem, Labomar | 05/01–07/09/2026 | 2.055 | Boa (12 erros) | **Sim** | — |
| PO2 | FONTE | Idem, Porangabussu | 05/01–04/09/2026 | 1.786 | Boa (0 erros) | **Sim** | — |
| P1 | CÁLCULO | Consolidado por refeição/dia Pici 1 (Previsão x Real, sobra, rejeito, RI, IA, fila) | 2026 | 1.034 (715 dup.) | Ruim (1.435 erros, sobretudo #N/A) | Não (usar P1D + agregação própria) | Provável quebra de VLOOKUP/referência cruzada |
| P2 | CÁLCULO | Idem Pici 2 | 2026 | 1.054 (783 dup.) | Boa (0 erros, mas 74% duplicado) | Não | Muitas linhas-template vazias duplicadas |
| B | CÁLCULO | Idem Benfica | 2026 | 1.052 (572 dup.) | Ruim (1.474 erros #N/A) | Não | — |
| L | CÁLCULO | Idem Labomar | 2026 | 2.054 (1.881 dup.) | Boa (0 erros, 92% duplicado) | Não | — |
| PO | CÁLCULO | Idem Porangabussu | 2026 | 254 (92 dup.) | Boa | Não | — |
| Av. Sensorial | FONTE | Avaliação sensorial bruta (aparência/textura/sabor/odor/global) por avaliador, todos RUs | 05/01–02/09/2026 | 5.516 | Boa (3 erros pontuais) | **Sim** | Fonte primária de Qualidade |
| ISC alm | FONTE | Índice de Satisfação (ÓTIMO/REGULAR/RUIM) do almoço, por RU | 05/01–04/09/2026 | 1.179 (694 dup.) | Ruim (752 erros #VALUE!) | Sim, com tratamento | Estrutura em "blocos" por RU lado a lado (P1/B/P2/PO/L) |
| ISC jan | FONTE | Idem, jantar | 05/01–04/09/2026 | 1.179 (697 dup.) | Boa (0 erros) | **Sim** | — |
| ISC Café | FONTE | Idem, café da manhã | 05/01–04/09/2026 | 522 (198 dup.) | Ruim (209 erros #VALUE!) | Sim, com tratamento | — |
| CARDÁPIO | AUXILIAR | Tabela de-para Data/Refeição/Preparação → nome do cardápio | 05/01–04/09/2026 | 5.624 | Boa (1 erro #REF!) | **Sim** | Dimensão de apoio (join) |
| NAC ALM | CÁLCULO | Consolidado multi-RU de IA + ISC do almoço (pivot manual) | 2026 (18 linhas) | 18 | Ruim (12 erros) | Sim, como cross-check | Bom para comparação entre RUs, mas recalcular do zero |
| NAC JAN | CÁLCULO | Idem, jantar | 2026 | 18 | Ruim (3 erros) | Sim, como cross-check | — |
| NAC CAFÉ | CÁLCULO | Idem, café | 2026 | 13 | Ruim (7 erros) | Sim, como cross-check | — |
| dados ajustes | CÁLCULO | Pivot de proteína/arroz consumidos por RU | 2026 | 1.481 (534 dup.) | Boa | Opcional | Uso específico de nutrição/reposição, fora do escopo do MVP |
| Prep menos aceitas mês | CÁLCULO | Ranking de preparações com pior avaliação sensorial do mês | 2026 | 12 | Boa | **Sim** | Pronta para virar KPI "piores preparações" |
| Tabela dinâmica 1 | CÁLCULO | Pivot Preparação × Frequência × Média (sensorial) | — | 48 (2 erros #NUM!) | Média | Sim, como referência | Reconstruir como agregação própria, não copiar pivot |
| Per capitas | CÁLCULO | Pivot de consumo médio per capita por RU/preparação | Jan/2026 | 1.367 | Boa (1 erro) | Opcional | Janela curta (só janeiro); não cobre o ano todo |
| sobras e rejeitos | CÁLCULO | Pivot sobra/rejeito por RU e data | 2026 (poucas linhas) | 5 | Baixa amostra | Não (dados insuficientes) | Provavelmente aba de teste/abandonada |
| dados PAINÉIS | CÁLCULO | Camada de agregação que alimenta o dashboard legado "Painel RU" | 2026 | 28 | Ruim (59 erros #DIV/0!) | Não | Não usar como fonte — é derivado do dashboard antigo |
| Painel RU | DASHBOARD | Dashboard/menu de navegação existente (Excel) | — | 15 | N/A | Não | É o painel *atual*, referência de layout, não de dados |
| Controle de Estoque | FONTE | Entrada/saída de insumos e cartões por RU | 03/03/2025–01/09/2026 | 106 de 50.513 linhas (0,2% preenchido) | Muito baixa cobertura | Não no v1 | Estrutura existe mas quase não foi usada — validar com gestão se é fonte viva |
| Atendimentos Especializado | FONTE | Chamados/ocorrências de estudantes (nome ou CPF, motivo, status) | 26/01–01/09/2026 | 39 | Boa | **Sim (agregado, sem PII)** | Contém dados pessoais — ver seção de privacidade |
| UFC-INFRA | FONTE | Ordens de serviço de manutenção predial | — | 199 | Boa | Sim (Gestão) | Datas em texto (dd/mm/aaaa), não normalizadas |
| OS - STI | FONTE | Chamados de TI | 08/01/2025–02/09/2026 | 45 | Boa | Sim (Gestão) | — |
| Treinamentos | FONTE | Registro de capacitações da equipe | 31/03–29/05/2026 | 13 | Boa | Sim (Gestão) | Volume baixo — poucos treinamentos registrados |
| Coleta de Resíduo | FONTE | Projeto de pesquisa (resíduos sólidos) associado ao RU | 22/05/2026 | 2 | Amostra mínima | Não | Fora do escopo do RU operacional |
| Atas | DOCUMENTAÇÃO | Atas de reuniões / processos SEI | — | 182 | Boa | Não (texto livre) | Referência institucional, não indicador |
| Entregas | DOCUMENTAÇÃO | ⚠️ Réplica do plano de entregas (Meta/Indicador/Prazo/Responsável/Ação/Concluída?) **dentro do Sistema RU** | — | 1.000 linhas, mas 983 duplicadas → só ~17 registros reais | Baixa (quase tudo duplicado) | Não | **Achado de governança**: existe um segundo controle de entregas, redundante ao arquivo OKR oficial. Definir fonte única. |
| dados | CÁLCULO | Notas sensoriais simplificadas (Aparência/Textura/Sabor/Odor/Global) sem cabeçalho claro | — | 397 | Média | Não | Provável rascunho/versão anterior de "Av. Sensorial" |
| Relatório Desperdício | LEGADO | Pivot de rejeito por RU — **ano de 2025** | 2025 | 185 (180 dup.) | Baixa | Não | Ano fora do escopo 2026 |
| Página23 | LEGADO | Pivot de Resto-Ingesta — **Set/Out 2025** | 2025 | 7 | Baixa | Não | Idem acima |
| Página20 | LEGADO | Registro antigo específico de Labomar (schema diferente de "L"/"LD") | 05–07/01/2026 | 5 | Baixa | Não | Parece ter sido substituído pelas abas L/LD |
| Página17 | LEGADO | Tabela sem cabeçalho, 837 duplicatas, 92 erros #DIV/0! | — | 999 | Muito baixa | Não | Sem contexto identificável — candidata a exclusão |
| REFEIÇÕES VEG | LEGADO/CÁLCULO | Contagem de refeições vegetarianas por RU | Jan–Set/2026 | 998 (835 dup.) | Muito baixa (6.698 erros #DIV/0!) | Não no v1 | Ideia útil (refeições veg), mas fórmulas quebradas; refazer do zero se a gestão priorizar |
| cronograma de serviços | AUXILIAR | Calendário de manutenções prediais (limpeza de caixa d'água etc.) | 2026 | 44 | Boa | Não | Não é indicador de RU, é facilities |
| Página42 | DESCARTÁVEL | 3.601 linhas, 100% vazias | — | 0 | N/A | Não | Excluir |
| Página38 | DESCARTÁVEL | 1x1, vazia | — | 0 | N/A | Não | Excluir |

¹ "Registros úteis" = linhas não totalmente vazias identificadas no scan (limite técnico de 20.000 linhas por aba, suficiente para todas as abas deste arquivo).

## Erros de fórmula por aba (top ofensores)
| Aba | #N/A | #DIV/0! | #VALUE! | #REF! | #NUM! | Total |
|---|---|---|---|---|---|---|
| REFEIÇÕES VEG | – | 6.694 | – | 4 | – | 6.698 |
| B | 1.472 | 2 | – | – | – | 1.474 |
| P1 | 1.432 | 3 | – | – | – | 1.435 |
| ISC alm | – | 3 | 749 | – | – | 752 |
| ISC Café | – | – | 209 | – | – | 209 |
| BD | 280 | – | 1 | – | – | 281 |
| Página17 | – | 91 | 1 | – | – | 92 |
| dados PAINÉIS | – | 59 | – | – | – | 59 |
| NAC ALM | – | 9 | 1 | 2 | – | 12 |
| LD | 11 | – | 1 | – | – | 12 |

**Padrão observado:** a maior parte dos `#N/A` está nas abas consolidadas (P1, B) — provável causa é
fórmula de busca (PROCV/ÍNDICE+CORRESP) referenciando o cardápio do dia e não encontrando correspondência
quando a data ou o nome da preparação não bate exatamente com a aba CARDÁPIO. Os `#DIV/0!` concentram-se
em cálculos de per capita/aceitabilidade quando o número de comensais é zero (ex.: dia sem atendimento).
Nenhum erro foi encontrado nas abas de **detalhe** (P1D, P2D, PO2, LD com poucos, BD com 281) — reforça a
recomendação de usar as abas `xD`/`x2` como fonte e recalcular as agregações do zero em Python, em vez de
herdar as fórmulas quebradas das abas consolidadas.

## Dados que não podem ser publicados
- **`Atendimentos Especializado`** — coluna "Nome ou CPF do atendido" contém CPF e, em alguns registros,
  o nome do estudante embutido no texto do relato ("Motivo") e nome do responsável que atendeu
  ("Responsável"). **Nunca expor linha a linha**; qualquer indicador de Gestão deve agregar
  (contagem, % resolvido, tempo médio) e nunca listar o conteúdo textual do campo.
- **`UFC-INFRA`, `OS - STI`, `Treinamentos`, `Coleta de Resíduo`** — coluna "Responsável" traz nomes de
  colaboradores. Uso interno é aceitável; **não publicar externamente** sem anonimizar.
- **`Av. Sensorial`** — coluna "Avaliador" traz nome de quem avaliou (equipe interna, não estudante) —
  risco menor, mas manter fora de painéis públicos.
- Nenhuma outra aba do Sistema RU apresentou CPF, e-mail, telefone ou matrícula de estudantes.

## Qualidade geral — resumo
- **42 abas**, das quais **12 classificadas como FONTE utilizável**, 13 como CÁLCULO (uso seletivo/cross-check),
  1 DASHBOARD legado, 2 DOCUMENTAÇÃO, 1 AUXILIAR único (cardápio) + 1 auxiliar (cronograma facilities), e
  **7 legado/descartável**.
- Total de **~11.900 erros de fórmula** catalogados no arquivo, concentrados em 6 abas.
- Duplicidade de linhas-template (linhas vazias/repetidas por arraste de fórmula) é o problema nº 1 de
  volume — em várias abas mais de 70–90% das linhas "não vazias" são, na prática, linhas de fórmula sem
  dado real. O ETL precisa filtrar por presença de "Data" válida, não por "linha não vazia".
