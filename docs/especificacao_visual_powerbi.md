# Especificação Visual — Power BI (Painel Estratégico da Nutrição)

**Versão 2 — identidade visual do RU/UFC incorporada.** Estrutura de 3
páginas conforme `ORIENTAÇÕES PARA CONSTRUÇÃO DO PAINEL ESTRATÉGICO DA
NUTRIÇÃO.pdf` (inalterada nesta revisão). Todas as medidas citadas estão
detalhadas em `docs/medidas_powerbi.md`; o modelo de dados subjacente está
em `docs/modelo_dados_powerbi.md`; as regras de cor/tipografia/logo estão
detalhadas em `docs/identidade_visual_ru_powerbi.md` (fonte de verdade
para qualquer dúvida visual — este documento só referencia as decisões,
não as redefine).

## Identidade visual — resumo (ver `docs/identidade_visual_ru_powerbi.md` para o detalhe completo)
- **Paleta institucional confirmada:** `#06668A` (azul primário, títulos),
  `#09A0C7` (azul secundário, acentos/seleção), `#FDC903` (amarelo,
  destaque/alerta), `#FFFBF2` (fundo alternativo), `#D41614` (vermelho,
  título/não conformidade).
- **Tipografia:** títulos em MediaPro (fallback técnico: Segoe UI
  Semibold), corpo em Open Sans (fallback técnico: Segoe UI).
- **Logo:** RU/UFC no cabeçalho das 3 páginas, discreta, sem distorção —
  arquivo gráfico ainda não confirmado/inserido (ver documento de
  identidade visual).
- **Regra de ouro:** identidade visual não deve ser confundida com
  semântica do dado — conformidade usa verde/vermelho por convenção,
  não pela paleta institucional pura.

## Cabeçalho (padrão nas 3 páginas)
```
[ LOGO RU/UFC ]   PAINEL ESTRATÉGICO DA NUTRIÇÃO
                  Nome da página (Visão Geral / Qualidade / Produção e Eficiência)
                                          [período selecionado]  [dados atualizados até: DD/MM/AAAA]
```
- Logo à esquerda, discreta (altura aproximada 32–40px), sobre fundo
  branco ou claro, sem distorção nem recolorir.
- Título do painel: fonte de título, `#06668A`, tamanho maior.
- Nome da página: fonte de título, tamanho menor, mesma cor ou cinza escuro.
- Período selecionado e data de atualização: à direita, discretos, fonte
  de corpo, tamanho pequeno.

## Filtros globais (em todas as páginas)
- **Unidade** (`dim_ru[nome]`) — slicer, estilo conforme
  `docs/identidade_visual_ru_powerbi.md` (fundo claro, seleção `#09A0C7`)
- **Período** (`dim_data[data]`) — slicer de intervalo de datas
- **Refeição** (`dim_refeicao[nome]`) — slicer (Café/Almoço/Jantar), mantido como filtro complementar por já ser uma dimensão útil
- **Tipo de preparação** (`dim_tipo_preparacao[tipo_preparacao]`) — slicer. Usa a dimensão dedicada `dim_tipo_preparacao`, não `dim_preparacao`, porque `fact_satisfacao` só tem `id_preparacao` (chave de `dim_preparacao`) preenchido em 60% das linhas — as 644 linhas restantes (chave composta recuperada) têm `tipo_preparacao` mas não o prato específico, e ficariam fora do filtro se o slicer usasse `dim_preparacao` (ver `docs/modelo_dados_powerbi.md`). **Nota:** interpretação provisória de "tipo de preparação" = a categoria `Prep` da fonte (PB, PV, VEG, Salada, Sobremesa etc.) — pendente de confirmação final com a gestão (ver `docs/perguntas_validacao_nutricao.md`, pergunta 3)

Slicers sincronizados entre as 3 páginas, agrupados em uma faixa dedicada
logo abaixo do cabeçalho (não espalhados pela página).

---

## Página 1 — Visão Geral

**Aplicação de cor:** cards e gráfico de evolução em `#06668A`/`#09A0C7`
(paleta institucional neutra) — nenhum indicador desta página tem
semântica de conformidade, então a paleta de marca se aplica sem ressalva.

### KPIs (cards)
- **Total de Refeições** — `[Total Refeições]`
- **Média Mensal** — `[Média Mensal de Refeições]`
- **% Execução** — `[% Execução]` (rotulado com nota "previsto é aproximado")

### Gráficos
- **Evolução temporal** — gráfico de linha, eixo X = `dim_data[data]`, valor = `[Total Refeições]`
- **Comparação entre unidades** — gráfico de barras, eixo X = `dim_ru[nome]`, valor = `[Total Refeições]`
- **Distribuição por refeição** — gráfico de pizza/rosca, categoria = `dim_refeicao[nome]`, valor = `[Total Refeições]` (útil, não obrigatório)

---

## Página 2 — Qualidade

**Aplicação de cor nesta página (ver `docs/identidade_visual_ru_powerbi.md`,
seção "Estados e alertas"):** os cards de Resto-Ingesta, ISC e Total de
Respostas usam o estilo neutro padrão (`#06668A` no valor). Os cards e
visuais de **conformidade de temperatura usam a paleta de semântica**
(verde = conforme, `#D41614` = não conforme, cinza = sem classificação/sem
medição) — nunca a paleta institucional pura para esse indicador
específico, para não confundir identidade de marca com status do dado.

### Cards
- **Resto-Ingesta (kg)** — `[Resto-Ingesta (kg)]`
- **% Resto-Ingesta** — `[% Resto-Ingesta]`
- **ISC** — `[ISC Agregado]`
- **Total de Respostas** — `[Total Respostas]`
- **% Conformidade da Temperatura** — `[% Conformidade]`, com `[% Cobertura da Classificação]` visível ao lado (rótulo secundário, ex.: "72% das medições avaliadas")
- **Medições Fora do Padrão** — `[Medições Fora do Padrão]`

### Temperatura — visuais sugeridos
- **Conformidade por RU** — gráfico de barras, eixo X = `dim_ru[nome]`, valor = `[% Conformidade]`
- **Evolução temporal da conformidade** — gráfico de linha de `[% Conformidade]` ao longo do tempo
- **Não conformidades por tipo de preparação** — gráfico de barras, eixo X = `dim_tipo_preparacao[tipo_preparacao]`, valor = `[Medições Fora do Padrão]` (só para tipos com `classe_termica` conhecida)
- **Distribuição das temperaturas** — histograma ou gráfico de dispersão de `fact_temperatura[temperatura_c]` (filtrado por `temperatura_plausivel = TRUE`)
- **Cobertura de classificação térmica** — informação secundária (cartão pequeno ou tooltip), não um gráfico principal — é contexto para interpretar a conformidade, não um KPI de destaque

Sem exagerar na quantidade de gráficos: os 5 visuais acima já cobrem
Resto-Ingesta, Satisfação e Temperatura sem sobrecarregar a página.

### Outros visuais da página
- **Distribuição Ótimo/Regular/Ruim** — gráfico de barras empilhadas ou pizza, usando `[% Ótimo]`, `[% Regular]`, `[% Ruim]`
- **Resto-Ingesta por RU** — gráfico de barras, eixo X = `dim_ru[nome]`, valor = `[% Resto-Ingesta]` (percentual, não kg absoluto, para comparação justa entre unidades de tamanhos diferentes)

---

## Página 3 — Produção e Eficiência

**Aplicação de cor:** paleta institucional neutra (`#06668A`/`#09A0C7`)
para todos os cards e gráficos — nenhum indicador desta página tem
semântica de conformidade.

### KPIs (cards)
- **Consumo Real (kg)** — `[Consumo Real (kg)]`
- **Sobra Limpa (kg)** — `[Sobra Limpa (kg)]`
- **Sobra Suja (kg)** — `[Sobra Suja (kg)]`
- **Per Capita médio (g/comensal)** — `[Per Capita (g/comensal) por Preparação]`, com filtro de preparação aplicado (card só faz sentido com uma preparação selecionada ou em contexto de uma linha de tabela/gráfico — ver nota abaixo)

### Visuais
- **Per Capita por tipo/preparação** — gráfico de barras horizontal, eixo Y = `dim_preparacao[preparacao]` (ou `tipo_preparacao` para visão mais agregada), valor = `[Per Capita (g/comensal) por Preparação]`. Como a medida é calculada por grupo (contexto de linha do visual), este gráfico é seguro mesmo mostrando várias preparações ao mesmo tempo.
- **Produção × Consumo** — gráfico de colunas agrupadas, comparando `[Peso Líquido (kg)]` vs `[Consumo Real (kg)]` por RU ou por período
- **Sobras / Desperdício** — gráfico de área ou barras empilhadas com `[Sobra Limpa (kg)]` e `[Sobra Suja (kg)]` ao longo do tempo
- **Comparação entre RUs** — tabela ou gráfico de barras com `[Consumo Real (kg)]`, `[% Resto-Ingesta]` e `[Per Capita (g/comensal) por Preparação]` lado a lado por `dim_ru[nome]`

**Nota sobre o card de Per Capita geral:** não criar um card único de
"Per Capita" sem contexto de preparação selecionada — conforme já
registrado em `docs/medidas_powerbi.md`, misturar preparações diferentes
num único número não tem interpretação gerencial clara. O card desta
página deve ser lido junto com um slicer de preparação ativo, ou
substituído por uma tabela/gráfico que já mostre a quebra por preparação.

---

## O que não entra em nenhuma página (por decisão de escopo)
- Indicadores de Gestão (atendimentos, manutenção) — não fazem parte do
  Painel Estratégico da Nutrição; permanecem só na aba "Gestão" do
  Streamlit.
- Conformidade térmica de preparações sem `classe_termica` conhecida
  (VEG, Guarnição, Sobremesa, Café, Leite, Pão, Especial, Manteiga etc.)
  — aparecem em `outputs/preparacoes_sem_classificacao_termica.csv` para
  auditoria, mas não entram no cálculo de `% Conformidade` até serem
  classificadas.
- Qualquer meta, benchmark ou limite (de Resto-Ingesta, satisfação, per
  capita) — a gestão não forneceu nenhum valor de referência; nenhum foi
  inventado.
- **Arquivo gráfico da logo RU/UFC** — não confirmado/extraído com
  segurança do material de identidade visual analisado (ver
  `docs/identidade_visual_ru_powerbi.md`). O cabeçalho das 3 páginas deve
  reservar o espaço para a logo, mas o arquivo em si precisa ser inserido
  posteriormente por quem tiver acesso ao Canva original.
