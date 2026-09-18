# Perguntas de Validação — Nutrição / Gestão do RU

**Versão 4** — atualizado após a Nutrição fornecer a regra oficial de
conformidade térmica. O bloqueio metodológico geral de temperatura está
**resolvido**. Restam apenas pontos residuais e de baixo risco.

## ✅ Resolvido nesta etapa

### Limites de conformidade térmica
Confirmado pela Nutrição e implementado em
`src/powerbi_export.compute_status_temperatura`:

- **Preparações quentes:** `temperatura > 60°C` → CONFORME · `≤ 60°C` → NÃO CONFORME
- **Preparações frias:** `temperatura < 10°C` → CONFORME · `≥ 10°C` → NÃO CONFORME

Operadores assimétricos preservados exatamente como fornecidos (quente usa
`>`/`≤`, fria usa `<`/`≥` — não é inconsistência, é a regra recebida).

### Classificação térmica por tipo de preparação
Classificado **apenas** para categorias inequivocamente identificáveis pela
nomenclatura do RU (ver `config/mappings.yaml`,
`classe_termica_por_tipo_preparacao`):
- **Quentes:** PB, PV, Arroz/Baião, Arroz Integral, Feijão
- **Frias:** Salada, Suco, Suco SA, Fruta 1, Fruta 2

### Chave composta em fact_isc — resolvido por recuperação determinística
A coluna "Preparação" das abas de ISC, quando não é o nome limpo do prato,
segue o padrão `Refeição + serial de data do Excel + tipo_preparacao` (ex.:
`"Café46167Especial Veg"`). Confirmado com **100% de exatidão em 644/644
linhas**: o serial bate com a data da própria linha, e o texto restante
bate com um `tipo_preparacao` real. Implementado em
`recuperar_tipo_preparacao_de_chave_composta` — nenhuma resposta de
satisfação é perdida, e `tipo_preparacao` fica preenchido em 100% das
linhas de `fact_satisfacao` (o nome específico do prato continua
desconhecido nesses 644 casos, marcado como `"NAO_IDENTIFICADA"`).

## Residual — não bloqueia o painel, mas vale confirmar quando possível

### 1. Classificação térmica das categorias ambíguas
12 tipos de preparação ficaram como `SEM_CLASSIFICACAO` por não terem uma
leitura inequívoca a partir do nome: **VEG, Guarnição, Sobremesa, Café,
Café SA, Leite, Leite Veg, Pão Francês, Pão Opção, Especial, Especial Veg,
Manteiga**. A lista completa, com volume de registros e faixa de
temperatura observada (só para referência, nunca usada para decidir a
classe), está em `outputs/preparacoes_sem_classificacao_termica.csv`.
**Pergunta:** alguma dessas categorias deveria ser classificada como
quente ou fria? Sem resposta, elas continuam fora do cálculo de
conformidade (não entram no denominador, mas também não distorcem o
indicador).

### 2. Medição de temperatura — leituras múltiplas
O pipeline usa a **média** das leituras quando a célula contém mais de uma
(ex.: `"14,9/14,9"` → 14,9°C). Isso é adequado, ou existe uma leitura
específica (ex.: só a de início da distribuição) que deveria prevalecer?
Baixo impacto — poucos casos observados.

### 3. Tipo de preparação — filtro do painel
Confirmado que `Prep` (PB, PV, VEG, Salada, Sobremesa, Suco etc.) é a
categoria estável usada como `tipo_preparacao`. **Pergunta residual:**
essa é exatamente a categorização que a gestão quer no filtro "tipo de
preparação", ou havia em mente um agrupamento diferente (ex.: PB+PV+VEG
como "proteínas")?

---
*Perguntas sobre Per Capita, denominador do Resto-Ingesta e fórmula do
ISC, presentes em versões anteriores, foram removidas — a própria base
confirmou essas relações com evidência estatística completa (ver
`docs/aderencia_orientacoes_gestao.md`, seção 3-A).*
