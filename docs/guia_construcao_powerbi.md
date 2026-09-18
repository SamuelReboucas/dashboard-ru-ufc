# Guia de Construcao do Painel no Power BI Desktop

**Por que este guia existe:** o ambiente onde este projeto foi desenvolvido
nao tem Power BI Desktop instalado (e um container Linux sem interface
grafica) - nao e possivel criar nem validar um .pbix diretamente aqui.
**MODELO POWER BI PRONTO PARA CONSTRUCAO** - todos os dados,
relacionamentos, DAX e layout estao especificados; falta apenas a
montagem manual no Power BI Desktop (Windows), que so pode ser feita por
quem tiver acesso a ferramenta.

## 0. Identidade visual — aplicar em todas as etapas abaixo
Antes de montar qualquer pagina, revisar `docs/identidade_visual_ru_powerbi.md`
(fonte de verdade para cor/tipografia/logo) e `docs/especificacao_visual_powerbi.md`
(onde cada cor se aplica por pagina). Resumo rapido para referencia
durante a montagem:

- Cores institucionais: `#06668A` (azul primario, titulos/cards neutros),
  `#09A0C7` (azul secundario, selecao de slicer/acentos), `#FDC903`
  (amarelo, destaque), `#FFFBF2` (fundo alternativo), `#D41614` (vermelho,
  titulo/nao conformidade).
- Fontes: titulos em MediaPro (fallback tecnico: Segoe UI Semibold, pois
  MediaPro nao e fonte padrao do Windows/Power BI); corpo em Open Sans
  (fallback tecnico: Segoe UI, se Open Sans nao estiver instalada na
  maquina).
- Logo RU/UFC: reservar espaco no cabecalho de cada pagina; o arquivo
  grafico em si ainda **nao foi confirmado/inserido** nesta etapa (ver
  identidade_visual_ru_powerbi.md) - inserir manualmente quando disponivel,
  sem distorcer, recolorir ou rotacionar.
- Regra de ouro: conformidade de temperatura usa verde/vermelho por
  semantica de dado, nao a paleta institucional pura (ver secao 9 abaixo).

## 1. Quais CSVs importar
Da pasta data/powerbi/ (gerada por `python -m src.pipeline`):

- dim_data.csv
- dim_ru.csv
- dim_refeicao.csv
- dim_preparacao.csv
- dim_tipo_preparacao.csv
- fact_refeicoes.csv
- fact_producao.csv
- fact_satisfacao.csv
- fact_temperatura.csv

No Power BI Desktop: Pagina Inicial -> Obter Dados -> Texto/CSV, um por
um, ou Obter Dados -> Pasta apontando para data/powerbi/ inteira.

Se o repositorio ja estiver publicado no GitHub, tambem e possivel usar
Obter Dados -> Web com a URL "raw" de cada CSV
(https://raw.githubusercontent.com/USUARIO/REPO/main/data/powerbi/ARQUIVO.csv),
o que permite atualizacao agendada sem depender de um arquivo local (ver
item 14).

## 2. Tipos de dados

> ⚠️ **ACHADO IMPORTANTE — bug de localidade decimal (descoberto testando
> num Power BI Desktop configurado em pt-BR).** Todas as colunas
> "Número decimal" listadas abaixo vêm do CSV com ponto como separador
> decimal (ex.: `"82.5"`, `"1081064.0"`) — formato padrão de exportação
> Python. Se o Power BI Desktop estiver com localidade regional em
> português (Brasil), o conversor de tipo padrão pode interpretar esse
> ponto como separador de **milhar**, e não decimal — transformando
> `"82.5"` em `825` (10x maior) silenciosamente, sem erro nenhum
> aparecer. Isso já foi confirmado acontecendo em `temperatura_c`,
> `refeicoes_realizadas`/`refeicoes_previstas` e `comensais_real`, e é
> bem provável que aconteça em **qualquer** coluna decimal de qualquer
> uma das 4 tabelas fato, não só nessas três.
>
> **Por isso, para TODA coluna "Número decimal" listada abaixo, não use o
> ícone de tipo simples — use sempre:**
> **botão direito no cabeçalho da coluna → Alterar Tipo → Usando
> Localidade → Tipo de Dados: Número Decimal, Localidade: Inglês (Estados
> Unidos) → Inserir.** Isso deixa explícito que o ponto é decimal,
> independente da localidade regional do Windows/Power BI.
>
> Se você já converteu alguma coluna com o método simples (ícone de tipo)
> antes de ler este aviso: volte ao passo **"Cabeçalhos Promovidos"** na
> lista de Etapas Aplicadas (antes da conversão de tipo), refaça a
> conversão pelo caminho "Usando Localidade" a partir dali, e delete o
> passo de conversão antigo que sobrou depois — só reaplicar um novo tipo
> em cima de um número já convertido errado não resolve, porque o valor
> de texto original já foi perdido nesse ponto.

Ao importar, confira/ajuste no Power Query (usando sempre "Alterar Tipo →
Usando Localidade → Inglês (Estados Unidos)" para as colunas marcadas com
🔸):

- dim_data: data = Data; dia, mes_numero, ano, trimestre = Numero inteiro
- dim_preparacao: id_preparacao = Numero inteiro
- dim_tipo_preparacao: tipo_preparacao = Texto (única coluna)
- fact_refeicoes: data = Data; 🔸 refeicoes_realizadas, refeicoes_previstas = Numero decimal
- fact_producao: data = Data; id_preparacao = Numero inteiro; 🔸 peso_bruto, peso_liq, sobra_limpa, sobra_suja, quantidade_distribuida, consumo_real, resto_ingesta_kg, pct_resto_ingesta, per_capita_g_comensal = Numero decimal; 🔸 comensais_real = Numero decimal
- fact_satisfacao: data = Data; id_preparacao = Numero inteiro; otimo, regular, ruim, total_respostas = Numero inteiro; 🔸 isc_linha = Numero decimal
- fact_temperatura: data = Data; id_preparacao = Numero inteiro; 🔸 temperatura_c = Numero decimal; temperatura_valida, temperatura_plausivel = Verdadeiro/Falso; classe_termica, limite_referencia, status_temperatura = Texto

Todas as demais colunas de texto (ru, refeicao, tipo_preparacao,
preparacao, codigo, nome etc.) ficam como Texto.

**Checagem rápida depois de importar tudo:** arraste `SUM(fact_refeicoes[refeicoes_realizadas])`
pra um cartão em branco antes mesmo de criar a medida oficial — se
mostrar algo em "Mi" (milhões) tipo "10,8 Mi", a coluna está com o bug de
localidade (o valor certo é 1.081.064, na casa das centenas de milhar,
nunca milhões).

## 3. Relacionamentos
Criar em Modelagem -> Gerenciar Relacionamentos, um por linha:

- fact_refeicoes[ru] -> dim_ru[codigo]
- fact_refeicoes[data] -> dim_data[data]
- fact_refeicoes[refeicao] -> dim_refeicao[nome]
- fact_producao[ru] -> dim_ru[codigo]
- fact_producao[data] -> dim_data[data]
- fact_producao[refeicao] -> dim_refeicao[nome]
- fact_producao[id_preparacao] -> dim_preparacao[id_preparacao]
- fact_satisfacao[ru] -> dim_ru[codigo]
- fact_satisfacao[data] -> dim_data[data]
- fact_satisfacao[refeicao] -> dim_refeicao[nome]
- fact_satisfacao[id_preparacao] -> dim_preparacao[id_preparacao]
- fact_temperatura[ru] -> dim_ru[codigo]
- fact_temperatura[data] -> dim_data[data]
- fact_temperatura[refeicao] -> dim_refeicao[nome]
- fact_temperatura[id_preparacao] -> dim_preparacao[id_preparacao]
- fact_producao[tipo_preparacao] -> dim_tipo_preparacao[tipo_preparacao]
- fact_satisfacao[tipo_preparacao] -> dim_tipo_preparacao[tipo_preparacao]
- fact_temperatura[tipo_preparacao] -> dim_tipo_preparacao[tipo_preparacao]

Total: 17 relacionamentos. Nenhum relacionamento fato-fato, nenhum
muitos-para-muitos.

Nota sobre fact_satisfacao[id_preparacao]: esse relacionamento (com
dim_preparacao) so resolve cerca de 60% das linhas de fact_satisfacao (as
outras 40% tem id_preparacao em branco, porque so o tipo_preparacao foi
recuperavel, nao o prato especifico - ver docs/modelo_dados_powerbi.md).
Isso e esperado; o Power BI trata linhas com chave em branco como "sem
correspondencia" e elas continuam aparecendo nos totais gerais, so nao
aparecem quando o visual for filtrado/quebrado por preparacao especifica.

**Por isso existe dim_tipo_preparacao, separada de dim_preparacao:**
fact_satisfacao[tipo_preparacao] -> dim_tipo_preparacao cobre **100%** das
linhas (as 644 recuperadas por chave composta tem tipo_preparacao
preenchido, so nao tem o prato especifico). O slicer oficial de "tipo de
preparacao" (secao 7 abaixo) usa dim_tipo_preparacao, nao dim_preparacao,
exatamente para nao perder essas 644 linhas do filtro.

## 4. Cardinalidades
Todos os 17 relacionamentos listados no item 3 sao Muitos para 1 (fato =
lado "muitos", dimensao = lado "1"). O Power BI detecta isso
automaticamente ao criar o relacionamento arrastando fato para dimensao;
confira no editor de relacionamento que o simbolo mostrado e "1" do lado
da dimensao e "*" do lado do fato. Se aparecer "1 para 1" ou "Muitos para
muitos" em algum caso, e sinal de que a coluna de origem tem valores
duplicados na dimensao (nao deveria acontecer com os CSVs gerados pelo
pipeline).

## 5. Direcao dos filtros
Todos os relacionamentos: filtro unico (Single), das dimensoes para os
fatos (esse e o padrao do Power BI ao criar um relacionamento Muitos para
1 - nao precisa configurar nada manualmente). Nao alterar para "Ambas as
direcoes" - isso criaria ambiguidade entre fact_producao, fact_satisfacao
e fact_temperatura ao filtrar por dim_preparacao ou dim_tipo_preparacao.

## 6. Medidas DAX a criar
Copiar todas as formulas prontas de docs/medidas_powerbi.md (Modelagem ->
Nova Medida, colar o codigo DAX de cada uma). Resumo do que criar, por
tabela:

- Em fact_refeicoes: Total Refeicoes, Total Refeicoes Previstas, % Execucao, Media Mensal de Refeicoes
- Em fact_producao: Resto-Ingesta (kg), Quantidade Distribuida (kg), % Resto-Ingesta, Consumo Real (kg), Sobra Limpa (kg), Sobra Suja (kg), Peso Bruto (kg), Peso Liquido (kg), Relacao Producao x Consumo, Per Capita (g/comensal) por Preparacao (usa SUMMARIZE+SUMX, ver secao "Correcao nesta revisao" em docs/medidas_powerbi.md - NAO usar CALCULATE(SUM(fact_refeicoes[...])), esse caminho nao existe no modelo)
- Em fact_satisfacao: **nesta ordem** — Total Otimo, Total Regular, Total Ruim (essas 3 primeiro), depois Total Respostas (= soma das 3 medidas, NAO `SUM(fact_satisfacao[total_respostas])` — ver "Correcao" em docs/medidas_powerbi.md), depois % Otimo/Regular/Ruim, ISC Agregado
- Em fact_temperatura: Total Medicoes, Medicoes Validas, Medicoes Avaliadas, Medicoes Conformes, Medicoes Fora do Padrao, % Conformidade, % Cobertura da Classificacao, Temperatura Media, Temperatura Mediana

Nenhuma medida deve ser criada com uma formula diferente da que esta em
docs/medidas_powerbi.md - especialmente % Conformidade, % Resto-Ingesta,
Total Respostas, ISC Agregado e Per Capita, que usam razao de somas/contagens (ou
SUMMARIZE+SUMX, no caso do Per Capita), nunca AVERAGE sobre uma coluna de
percentual ja calculada por linha nem um relacionamento que nao existe no
modelo.

## 7. Slicers
Um conjunto de slicers sincronizados entre as 3 paginas (Modo de Exibicao
-> Sincronizar Slicers, marcar as 3 paginas para cada slicer). Estilo
(ver docs/identidade_visual_ru_powerbi.md, secao "Filtros"): fundo branco
ou #FFFBF2, borda fina #09A0C7 ou cinza claro, item selecionado com fundo
#09A0C7 e texto branco, titulo do slicer em #06668A.

- dim_ru[nome] - lista ou botoes
- dim_data[data] - intervalo de datas (slicer "Entre")
- dim_refeicao[nome] - lista ou botoes
- dim_tipo_preparacao[tipo_preparacao] - lista suspensa (22 valores distintos; usar esta dimensao, NAO dim_preparacao[tipo_preparacao] - dim_tipo_preparacao cobre 100% de fact_satisfacao, dim_preparacao so 60%, ver secao 3)

## 8. Pagina 1 - Visao Geral
Seguir docs/especificacao_visual_powerbi.md, secao "Pagina 1". Resumo:
- Cabecalho: logo RU/UFC a esquerda (quando disponivel), titulo "PAINEL ESTRATEGICO DA NUTRICAO" em #06668A (fonte de titulo), nome da pagina abaixo, periodo/data de atualizacao a direita
- Cards (fundo branco ou #FFFBF2, valor em #06668A): Total de Refeicoes, Media Mensal, % Execucao (com nota "previsto e aproximado")
- Grafico de linha: evolucao temporal (eixo X = dim_data[data], valor = Total Refeicoes), linha em #06668A
- Grafico de barras: comparacao entre unidades (eixo X = dim_ru[nome]), barras em tons de azul da paleta (#06668A/#09A0C7)
- Opcional: grafico de pizza com distribuicao por refeicao

## 9. Pagina 2 - Qualidade
Seguir docs/especificacao_visual_powerbi.md, secao "Pagina 2". Resumo:
- Cards neutros (valor em #06668A): Resto-Ingesta (kg), % Resto-Ingesta, ISC, Total de Respostas
- Cards de conformidade termica: usar paleta de SEMANTICA DE DADO, nao a paleta institucional - verde para % Conformidade quando alta, vermelho (#D41614, que ja e institucional) para Medicoes Fora do Padrao. Exibir sempre % Cobertura da Classificacao ao lado de % Conformidade (rotulo secundario)
- Distribuicao Otimo/Regular/Ruim (barras empilhadas ou pizza) - cores neutras da paleta institucional, nao semantica de conformidade
- Resto-Ingesta por RU (barras, valor em %, nao em kg absoluto) - tons de azul
- Conformidade por RU (barras) - verde/vermelho por semantica, nao azul institucional
- Evolucao temporal da conformidade (linha) - verde/vermelho por semantica
- Nao conformidades por tipo de preparacao (barras, so tipos com classe_termica conhecida) - vermelho institucional (#D41614)
- Distribuicao das temperaturas (histograma, filtrado por temperatura_plausivel = TRUE) - azul neutro
- Cobertura de classificacao termica como informacao secundaria (cartao pequeno, nao grafico principal)

## 10. Pagina 3 - Producao e Eficiencia
Seguir docs/especificacao_visual_powerbi.md, secao "Pagina 3". Resumo:
- Cards (valor em #06668A): Consumo Real (kg), Sobra Limpa (kg), Sobra Suja (kg), Per Capita medio (com filtro de preparacao aplicado)
- Per Capita por tipo/preparacao (barras horizontais) - tons de azul
- Producao x Consumo (colunas agrupadas) - #06668A e #09A0C7 lado a lado
- Sobras/Desperdicio ao longo do tempo (area ou barras empilhadas) - tons de azul
- Comparacao entre RUs (tabela ou barras com Consumo Real, % Resto-Ingesta e Per Capita lado a lado)

Nao criar um card unico de "Per Capita Geral" sem filtro de preparacao -
ver nota em docs/medidas_powerbi.md sobre por que isso nao tem
interpretacao gerencial clara.

## 11. Ordem dos visuais
Em cada pagina: cards de KPI no topo (ocupando a largura toda, lado a
lado), grafico de evolucao temporal logo abaixo (largura toda), demais
graficos de comparacao/distribuicao na metade inferior da pagina, lado a
lado. Essa ordem ja esta implicita na ordem em que os itens aparecem nas
secoes 8, 9 e 10 acima.

## 12. Formatacao recomendada
- Paleta de cores: mesma cor por RU em todas as paginas (Modelagem -> cor
  por valor de categoria em dim_ru[nome], usando tons de #06668A/#09A0C7,
  para nao depender da ordem alfabetica escolhida automaticamente).
- Fontes: titulos em MediaPro se instalada, senao Segoe UI Semibold
  (fallback tecnico); corpo em Open Sans se instalada, senao Segoe UI.
  Ver docs/identidade_visual_ru_powerbi.md para a justificativa completa
  do fallback.
- Formato de numero: refeicoes sem casas decimais; percentuais com 1 casa
  decimal; temperatura_c com 1 casa decimal e sufixo "C" (formato de
  numero customizado).
- Cards de KPI: fundo branco ou #FFFBF2, valor em #06668A (fonte grande),
  rotulo pequeno acima em cinza escuro. Excecao: cards de conformidade
  termica usam verde/vermelho por semantica de dado (ver secao 9).
- Cabecalho das 3 paginas: logo RU/UFC a esquerda (quando disponivel,
  sem distorcer/recolorir), titulo do painel em #06668A, periodo/data de
  atualizacao discretos a direita.
- Avisos textuais obrigatorios (caixa de texto visivel na pagina, nao
  tooltip): "Previsto (aproximado)" perto de % Execucao na Pagina 1; nota
  de cobertura perto de % Conformidade na Pagina 2.

## 13. Validacao dos numeros
Depois de montado, confira estes valores (sem nenhum filtro aplicado)
contra a ultima execucao real do pipeline (tambem documentados em
docs/resumo_final_painel_estrategico.md):

- Total Refeicoes: 1.081.064
- % Conformidade (temperatura): aprox. 63,1%
- % Cobertura da Classificacao: aprox. 72,4%
- Total de linhas em fact_satisfacao: 1.604
- Total Respostas (Total Otimo + Total Regular + Total Ruim): **141.505** (NAO 137.578 — esse era o valor da coluna `total_respostas` pre-calculada, que subconta por causa do bug de dado parcial corrigido em docs/medidas_powerbi.md)
- ISC Agregado: aprox. **9,36** (NAO 9,09 nem 9,63 — ver a mesma correcao acima)
- Resto-Ingesta (kg): aprox. **74.929**

Se algum desses numeros nao bater, o problema esta na importacao ou no
relacionamento (revisar itens 1 a 4 deste guia), nao na regra de negocio
(ja testada em Python - ver tests/test_powerbi_export.py, 57 testes
cobrindo exatamente essas formulas).

## 14. Atualizacao futura
Sempre que o Excel do Sistema RU for atualizado e o pipeline rodar de
novo (python -m src.pipeline), os CSVs em data/powerbi/ sao regerados.

- Se os CSVs foram importados como arquivo local: Pagina Inicial ->
  Atualizar (o Power BI le os arquivos do disco de novo).
- Se foram importados via URL do GitHub (Obter Dados -> Web): publicar o
  .pbix no Power BI Service e configurar atualizacao agendada em
  Configuracoes do conjunto de dados -> Atualizacao agendada - nao
  precisa de gateway de dados local, pois a fonte e uma URL HTTPS
  publica.

Nenhuma medida DAX precisa ser recriada entre atualizacoes - todas
recalculam automaticamente sobre os dados novos.
