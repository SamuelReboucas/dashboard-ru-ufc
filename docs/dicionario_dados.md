# Dicionário de Dados — Modelo Analítico do MVP

Cobre apenas os campos que efetivamente chegam às tabelas fato em
`data/processed/` e alimentam algum KPI do dashboard. Para o inventário
completo das 42 abas do Excel (incluindo o que **não** foi usado), ver
`docs/auditoria_dados.md`.

## fact_detalhe.csv (grão: 1 linha = 1 preparação de 1 refeição de 1 RU em 1 data)

| Campo | Descrição | Fonte | Aba original | Tipo | Transformação | Unidade |
|---|---|---|---|---|---|---|
| `ru` | Código canônico da unidade (P1/P2/B/L/PO) | Atribuído no `extract.py` a partir da aba lida | P1D/P2D/BD/LD/PO2 | texto | Definido por sheet, não por coluna | — |
| `data` | Data da refeição | Coluna "Data" | idem | data | `to_date_safe` (dayfirst=True) + filtro de intervalo válido (2025–2026) | dd/mm/aaaa |
| `refeicao` | Tipo de refeição | Coluna "Pici 1"/"Refeição"/"REF" (varia por RU) | idem | texto | `normalize_refeicao` via alias | Café/Almoço/Jantar |
| `prep` | Código da preparação (ex.: PB, PV, VEG, Arroz) | Coluna "Prep" | idem | texto | sem transformação | — |
| `cardapio` | Nome do prato | Coluna "Cardápio" | idem | texto | sem transformação | — |
| `peso_bruto` | Peso recebido antes do preparo | Coluna "Peso Bruto" | idem | numérico | `to_numeric_safe` | kg |
| `peso_liq` | Peso líquido preparado/servido | Coluna "Peso Líq" | idem | numérico | `to_numeric_safe` | kg |
| `comensais` | Previsão de comensais **por prato** (varia entre pratos da mesma refeição) | Coluna "Comensais" | idem | numérico | `to_numeric_safe` | pessoas |
| `comensais_real` | Comensais reais da refeição — valor único repetido em todas as linhas de preparação daquela refeição | Coluna "Com. Real"/"C. Real"/"Consumo Real" | idem | numérico | `to_numeric_safe`; negativos → NaN | pessoas |
| `sobra_limpa` | Sobra limpa (não servida) | Coluna "S.L" | idem | numérico | `to_numeric_safe` | kg |
| `sobra_suja` | Sobra suja (resto de prato) | Coluna "S.S" | idem | numérico | `to_numeric_safe` | kg |
| `bom` / `regular` / `ruim` | Contagem de votos de satisfação por preparação | Colunas "BOM"/"REG"/"RUIM" | idem | numérico | `to_numeric_safe` | votos |
| `mes` | Mês (AAAA-MM) | Derivado de `data` | — | texto | `data.dt.to_period("M")` | — |

Campos lidos mas **não usados em nenhum KPI do MVP** (mantidos no extract por
completude, mas fora do dicionário de uso): `temp_c`, `repos`, `qtd1`, `tam1`,
`qtd2`, `tam2`, `pce`, `pc_pct`, `previsao`, `peso_previsto`,
`controle_cubas`, `ajustes`, `consumo_real`, `pc_pres`.

## fact_sensorial.csv (grão: 1 linha = 1 avaliação sensorial)

| Campo | Descrição | Fonte | Aba original | Tipo | Transformação | Unidade |
|---|---|---|---|---|---|---|
| `ru` | RU avaliado | Coluna "Refeitório" | Av. Sensorial | texto | `normalize_ru` (nome completo → código) | — |
| `data` | Data da avaliação | Coluna "data" | idem | data | `to_date_safe` + filtro de intervalo válido | dd/mm/aaaa |
| `refeicao` | Tipo de refeição avaliada | Coluna "Refeição" | idem | texto | `normalize_refeicao` | Café/Almoço/Jantar |
| `preparacao` | Prato avaliado | Coluna "Preparação" | idem | texto | sem transformação | — |
| `avaliador` | Identificação de quem avaliou (equipe interna) | Coluna "Avaliador" | idem | texto | usado só para deduplicar, nunca exibido | — |
| `global` | Nota consolidada da avaliação | Coluna "Global" | idem | numérico | `to_numeric_safe` | escala 0–5 |

## fact_isc.csv (grão: 1 linha = 1 RU × 1 preparação × 1 data × 1 refeição)

| Campo | Descrição | Fonte | Aba original | Tipo | Transformação | Unidade |
|---|---|---|---|---|---|---|
| `ru` | RU do bloco de colunas identificado dinamicamente | Nome do RU na linha de cabeçalho | ISC alm / ISC jan / ISC Café | texto | Casado via `ru_aliases` | — |
| `data` | Data da avaliação | Coluna "Data"/"data" | idem | data | `to_date_safe` + filtro de intervalo válido | dd/mm/aaaa |
| `refeicao` | Café/Almoço/Jantar (fixo por aba de origem) | Nome da aba | idem | texto | atribuído por aba | — |
| `preparacao` | Prato avaliado | Coluna "Preparação"/"prep" | idem | texto | sem transformação | — |
| `isc` | Índice de Satisfação do Cliente já calculado na origem | Última coluna do bloco de 7 do RU | idem | numérico | `to_numeric_safe` | escala 0–10 |

Campos `otimo`, `otimo_pct`, `regular`, `regular_pct`, `ruim`, `ruim_pct`
também são extraídos (compõem o bloco de 7 colunas) mas não alimentam nenhum
KPI do MVP v1 — mantidos para uso futuro/auditoria.

## fact_gestao_atendimentos.csv (grão: 1 linha = 1 atendimento)

| Campo | Descrição | Fonte | Aba original | Tipo | Transformação | Unidade |
|---|---|---|---|---|---|---|
| `ru` | RU do atendimento | Coluna "RU" | Atendimentos Especializado | texto | `normalize_ru` | — |
| `data` | Data do atendimento | Coluna "Coluna 1" (rotulada incorretamente na planilha-fonte) | idem | data | `to_date_safe` + filtro de intervalo válido | dd/mm/aaaa |
| `resolvido_flag` | Se o atendimento foi resolvido | Coluna "Resolvido" | idem | booleano | `== "resolvido"` (case-insensitive) | — |

**Nunca extraídos** (PII, ver `docs/auditoria_dados.md`): "Nome ou CPF do
atendido", "Motivo", "Responsável", "Observações".

## fact_gestao_manutencao.csv (grão: 1 linha = 1 ordem de serviço)

| Campo | Descrição | Fonte | Aba original | Tipo | Transformação | Unidade |
|---|---|---|---|---|---|---|
| `ru` | RU/local mapeado para código canônico | Coluna "Local" (UFC-INFRA) / "RU" (OS - STI) | UFC-INFRA / OS - STI | texto | `local_ru_aliases` + `ru_aliases`; valores não mapeáveis (ex.: "SENUT") → NaN | — |
| `data` | Data de abertura da OS | Coluna "Data" / "Data da Solicitação" | idem | data | `to_date_safe` (dayfirst=True) + filtro de intervalo válido | dd/mm/aaaa |
| `data_resolucao` | Data de resolução | Coluna "Data de Resolução" | idem | data | `to_date_safe` | dd/mm/aaaa |
| `tipo` | Infraestrutura ou TI | Atribuído por sheet de origem | idem | texto | fixo por fonte | — |
| `resolvido_flag` | Se a OS foi resolvida | Coluna "Resolvido" | idem | booleano | `.isin(["sim","resolvido","true","1"])` | — |

**Nunca extraídos** (texto livre/nome de colaborador): "Responsável",
"Motivo", "Observação(ões)".
