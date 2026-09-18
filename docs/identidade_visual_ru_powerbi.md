# Identidade visual aplicada ao Power BI

**Escopo:** documento curto e operacional — traduz o Manual de Identidade
Visual do RU/UFC em decisões aplicáveis ao Power BI. Não substitui o
manual original; sempre que houver dúvida, o material anexado prevalece.

## Fonte oficial

Arquivo analisado: `identidade_visual_do_restaurante_universtário.html`
(export de visualização do Canva, design "Manual de Identidade Visual do
Restaurante Universitário", RU/UFC, 2025). O conteúdo textual e os
metadados de cor/fonte foram extraídos diretamente da estrutura do
arquivo — nenhuma informação foi copiada de memória ou suposta.

**Nota de segurança:** o HTML original contém dados da conta Canva de
quem exportou o arquivo (e-mail, tokens de acesso temporários, IDs de
usuário). Por isso ele **não entra no ZIP de entrega** (ver seção
"Privacidade e Segurança" do pedido desta etapa) — apenas este documento
derivado, sem nenhum desses dados.

## Paleta

| Cor | HEX | Função identificada no manual |
|---|---|---|
| Azul institucional (primária) | `#06668A` | Cor de todos os títulos de seção do manual ("Apresentação e Objetivos", "Identidade Visual", "Orientações Básicas", "Exemplos de Aplicação") — é a cor mais associada à marca no próprio documento |
| Azul claro / ciano (secundária) | `#09A0C7` | Cor de preenchimento de um elemento circular decorativo que se repete no topo de quase todas as páginas do manual — funciona como um selo/acento visual recorrente |
| Amarelo / dourado (destaque) | `#FDC903` | O texto do manual associa explicitamente: **"Amarelo: eventos"** |
| Fundo alternativo | `#FFFBF2` | Usado como cor de fundo de página em pelo menos uma das artes do manual (branco levemente amarelado/creme, não branco puro) |
| Vermelho institucional | `#D41614` | Cor do título de capa do manual ("IDENTIDADE VISUAL DO RESTAURANTE UNIVERSITÁRIO", em maiúsculas) |

As 5 cores acima estão confirmadas **literalmente** — o manual tem uma
página de referência que lista o texto "Cores:" seguido exatamente destes
5 códigos hexadecimais, na mesma ordem. Não é uma inferência.

**Divergência encontrada:** o texto de "Orientações Básicas" também diz
*"Verde: educativos"* — mas **nenhum código de cor verde aparece em
nenhuma parte do arquivo analisado**. Isso é registrado como:
`NÃO CONFIRMADO NO MATERIAL DISPONÍVEL`. Não foi inventado nenhum HEX para
"verde" — se essa cor for necessária, precisa ser solicitada a quem mantém
o manual original.

## Tipografia

| Uso | Fonte | Evidência |
|---|---|---|
| Títulos | **MediaPro** | Texto explícito no manual: *"Título: Mediapro"* |
| Corpo | **Open Sans** | Texto explícito no manual: *"Corpo: opensans"* |

**Fallback técnico para o Power BI** (nenhuma das duas é observação
inventada — é uma limitação real da ferramenta):

- **MediaPro** é uma fonte proprietária/customizada carregada especificamente
  dentro do arquivo do Canva — não é uma fonte padrão do Windows nem do
  Power BI Desktop. **Fallback recomendado: `Segoe UI Semibold`** (fonte
  padrão de títulos do Power BI, sempre disponível, sem necessidade de
  instalação). *Fonte oficial: MediaPro. Fallback no Power BI: Segoe UI
  Semibold (usado apenas por limitação técnica da ferramenta — não é a
  fonte oficial da marca).*
- **Open Sans** é uma fonte do Google Fonts — só aparece na lista de fontes
  do Power BI se estiver instalada no Windows que roda o Power BI Desktop.
  Se estiver instalada, usar diretamente. **Fallback recomendado, caso não
  esteja instalada: `Segoe UI`** (regular, para textos de corpo/rótulos).
  *Fonte oficial: Open Sans. Fallback no Power BI: Segoe UI (usado apenas
  se Open Sans não estiver instalada na máquina).*

## Logo

**Regras de uso encontradas no manual** (texto literal da página
"Identidade Visual"):
- A logo principal do RU/UFC **deve aparecer em todos os materiais oficiais**.
- As logos dos projetos associados (SENUT, De Bandeja etc.) compartilham a
  mesma estrutura visual (formas circulares, tipografia harmônica, cores
  institucionais) e devem preservar a unidade institucional.
- Aplicar preferencialmente **em fundo branco ou claro**, respeitando
  contraste e legibilidade.
- **Proibido:** modificar cores, proporções, tipografia; rotacionar;
  sobrepor indevidamente.
- Marca d'água (quando necessária): apenas a **versão monocromática** do logo.
- Em materiais de comunicação (posts/stories), sempre incluir também o
  **brasão da UFC**, em local visível, sem sobrepor elementos importantes.

**Arquivo gráfico da logo:** `NÃO CONFIRMADO NO MATERIAL DISPONÍVEL` de
forma segura. O manual contém várias imagens embutidas (fotos e possíveis
elementos gráficos), mas nenhuma foi identificada de forma inequívoca,
nos metadados textuais analisados, como sendo especificamente o arquivo
da logo (o material só traz a instrução "para usar as logos, basta copiar
e colar no seu documento", o que pressupõe abrir o Canva original, não
uma exportação PNG/SVG isolada e identificável). Também existem imagens de
pré-visualização de página (thumbnails) geradas pelo Canva, mas são
capturas de baixa resolução com URLs assinadas e temporárias — **não
qualificam como ativo oficial exportável** (a própria orientação desta
etapa veda usar screenshot de baixa qualidade como logo oficial).
**Ação:** o arquivo oficial da logo deve ser exportado diretamente do
Canva (ou obtido com a equipe de comunicação do RU) e inserido
posteriormente em `assets/branding/logo_ru_ufc.png` (caminho sugerido,
pasta ainda não criada nesta etapa).

## Layout — princípios gerais

- Fundo de página: branco (`#FFFFFF`) como padrão, ou `#FFFBF2` como
  alternativa mais próxima da identidade (creme suave) — nunca fundos
  saturados em grandes áreas (regra de acessibilidade do próprio manual:
  *"Evite combinações que comprometam a legibilidade, como texto claro
  sobre fundo claro ou cores muito saturadas juntas"*).
- Títulos de página/seção: `#06668A`, fonte de título (MediaPro/fallback
  Segoe UI Semibold).
- Texto de corpo/rótulos: preto ou cinza escuro sobre fundo claro (o
  manual usa `#000000` para corpo de texto), fonte de corpo (Open
  Sans/fallback Segoe UI).
- Ícones e ilustrações: minimalistas, alinhados à temática de alimentação/
  sustentabilidade/bem-estar (regra explícita do manual) — no Power BI,
  isso se traduz em usar os ícones nativos simples do próprio Power BI
  (Format → Icons), não ilustrações elaboradas.

## Cards

- Fundo branco ou `#FFFBF2`.
- Borda sutil ou nenhuma borda (evitar poluição visual — instrução geral
  do pedido desta etapa, consistente com o tom "minimalista" do manual).
- Raio de borda pequeno (4–8px), consistente em todos os cards.
- Sem sombra pronunciada — se usar, sombra leve apenas.
- Título do card: texto de corpo, cinza escuro, tamanho pequeno (10–12pt).
- Valor do card: `#06668A` (cor institucional primária) para KPIs neutros;
  reservar vermelho/verde de semântica (ver seção "Estados e alertas")
  apenas para os indicadores que representam status, nunca para KPIs
  neutros como "Total de Refeições".
- Unidade (kg, %, g/comensal): junto ao valor, fonte menor.
- Espaçamento interno consistente (8–12px de padding).
- **Não** usar uma cor de fundo diferente por card sem motivo — os cards
  neutros compartilham o mesmo estilo; só os estados de alerta (ver
  abaixo) mudam de cor, e mudam por significado, não por decoração.

## Gráficos

- Paleta de séries categóricas (RU, refeição, tipo de preparação):
  `#06668A` e `#09A0C7` como cores primárias de barras/linhas; `#FDC903`
  como cor de destaque pontual (ex.: para chamar atenção a uma barra
  específica); evitar usar as 5 cores institucionais todas ao mesmo tempo
  em um único gráfico com muitas categorias — se houver mais categorias
  que cores disponíveis (ex.: 5 RUs, 20 tipos de preparação), usar uma
  progressão de tons de azul (da paleta) em vez de introduzir cores fora
  da identidade.
- Linhas de evolução temporal: `#06668A` como cor principal da série.
- Gráficos de comparação entre RUs: uma cor por RU, usando variações de
  tom dentro da paleta azul (não cores arbitrárias do tema padrão do
  Power BI).
- **Nunca** usar `#D41614` (vermelho institucional) para representar uma
  categoria neutra "que por acaso é vermelha no tema" — essa cor fica
  reservada para o significado de alerta/não conformidade (ver abaixo),
  para não confundir identidade visual com semântica do dado.

## Filtros (slicers)

- Fundo branco ou `#FFFBF2`, borda `#09A0C7` fina (1px) ou cinza claro.
- Texto: fonte de corpo, preto ou cinza escuro.
- Item selecionado: fundo `#09A0C7` com texto branco (ou `#06668A`, mais
  escuro, para reforço de contraste).
- Título do filtro (ex.: "Unidade", "Período"): fonte de título pequena,
  `#06668A`.
- Espaçamento consistente entre slicers, alinhados em uma faixa dedicada
  (não espalhados livremente pela página).

## Estados e alertas

**Aqui a identidade visual cede lugar à semântica do dado — isso é
proposital, não uma inconsistência:**

| Situação | Cor | Justificativa |
|---|---|---|
| Conforme / dentro do padrão | Verde (ex.: `#2E7D32` ou similar verde de acessibilidade — **não faz parte da paleta institucional, é uma cor funcional de semântica de dado**, já que o manual não define um verde oficial, ver divergência acima) | Convenção universal de "positivo/ok", essencial para leitura rápida do painel |
| Não conforme / fora do padrão | `#D41614` (vermelho institucional) | Coincide com uma cor já institucional, reforçando urgência sem introduzir cor nova |
| Alerta/atenção (não crítico) | `#FDC903` (amarelo institucional) | Já associado a destaque no manual |
| Informação neutra / sem classificação | Cinza médio | Neutro, não compete com os estados acima |

Isso está alinhado à instrução desta etapa: **não usar uma cor
institucional de forma que possa ser confundida com status positivo ou
negativo** — por isso o "conforme" usa uma cor de semântica de dado
(verde, fora da paleta de marca), enquanto "não conforme" reaproveita o
vermelho institucional (que já carrega, no dia a dia, a mesma conotação
de atenção).

## Acessibilidade

- Contraste mínimo: texto escuro (`#000000` ou `#06668A`) sobre fundo
  claro (`#FFFFFF`/`#FFFBF2`); nunca texto claro sobre `#FDC903` puro sem
  verificar contraste (amarelo claro tem contraste baixo com branco).
- Nunca depender só de cor para indicar conformidade — sempre acompanhar
  o rótulo textual ("CONFORME"/"NÃO CONFORME"), não só a cor do card.
- Tamanho mínimo de texto em cards/rótulos: 10pt para rótulos secundários,
  14pt+ para valores de KPI.
- Evitar `#D41614` ou `#FDC903` em grandes áreas de fundo — usar como
  acento (ícone, borda, texto), não como bloco de cor extenso.

## O que NÃO fazer

- Não inventar um HEX para "verde" só porque o texto do manual menciona
  "Verde: educativos" — ficou registrado como não confirmado.
- Não usar o vermelho institucional (`#D41614`) para nada que não seja
  "não conforme"/alerta ou o próprio título/marca — não usar como cor de
  categoria neutra em gráficos.
- Não distorcer, esticar, rotacionar, recolorir ou aplicar efeitos na logo
  quando ela for inserida.
- Não usar screenshot/thumbnail de baixa resolução do Canva como arquivo
  final da logo.
- Não sobrecarregar o painel com as 5 cores institucionais ao mesmo tempo
  em todos os gráficos — a identidade deve ser reconhecível (cabeçalho,
  títulos, cards, detalhes), sem competir com a leitura dos dados.
