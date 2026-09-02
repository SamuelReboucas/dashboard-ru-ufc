# Implementação do MVP — Relatório desta etapa

**Data:** 02/09/2026 · **Escopo:** implementação do pipeline, indicadores,
validações e dashboard definidos na etapa de auditoria anterior
(`docs/auditoria_dados.md`, `docs/okr_recovery.md`, `docs/fontes_oficiais.md`,
`docs/mvp_dashboard.md`, `docs/arquitetura_proposta.md`, `docs/plano_execucao.md`).

## O que foi construído

Pipeline completo `Excel → extração → validação → transformação → dados
processados → métricas → dashboard`, seguindo a arquitetura já definida na
etapa anterior, sem desvios de escopo.

### Arquivos criados

```
ru_dashboard/
├── README.md, requirements.txt, .gitignore
├── app/streamlit_app.py
├── app/components/{data_loader,filters,kpi_cards,charts}.py
├── src/{config,extract,transform,metrics,validators,pipeline}.py
├── config/mappings.yaml
├── docs/{dicionario_dados,indicadores,implementacao_mvp}.md (novos)
│    + os 6 documentos da auditoria anterior (copiados)
├── tests/{test_transform,test_metrics}.py (41 testes)
└── outputs/relatorio_qualidade.csv (gerado pelo pipeline)
```

### Fontes utilizadas (das 42 abas auditadas, 9 entraram no MVP)
`P1D`, `P2D`, `BD`, `LD`, `PO2` (detalhe operacional), `Av. Sensorial`,
`ISC alm`, `ISC jan`, `ISC Café`, `Atendimentos Especializado`, `UFC-INFRA`,
`OS - STI`. Todas as demais (`Painel RU`, `dados PAINÉIS`, `Controle de
Estoque` etc.) foram mantidas fora, conforme já recomendado em
`docs/fontes_oficiais.md`.

### Indicadores implementados (13, conforme `docs/mvp_dashboard.md`)
Panorama: refeições realizadas, refeições previstas, % execução, evolução
temporal. Desperdício: rejeito total, desperdício per capita, índice de
aceitabilidade, comparação por RU. Qualidade: avaliação sensorial média, ISC
médio, top 5 piores preparações. Gestão: % atendimentos resolvidos, % OS de
manutenção resolvidas. Fórmula, fonte e limitação de cada um em
`docs/indicadores.md`.

## Bugs reais encontrados e corrigidos

Nenhum destes apareceu na checagem de sintaxe — só apareceram ao rodar o
pipeline e o dashboard de verdade contra o Excel real. Ordem cronológica:

### 1. Coluna de data de "Atendimentos Especializado" mal identificada
O cabeçalho da coluna de data nessa aba está, na própria planilha-fonte,
rotulado **"Coluna 1"** (erro de digitação de quem preencheu a planilha), não
"Data". O extrator genérico procurava por um cabeçalho literalmente chamado
"data" e não encontrava nada — `fact_atendimentos` saía com **0 linhas**
após a limpeza. Corrigido adicionando um alias explícito
(`colunas_uteis: {data: ["coluna 1"], ...}`) em `config/mappings.yaml`.
Resultado: de 0 para 29 linhas válidas.

### 2. Datas brasileiras interpretadas com mês primeiro
`UFC-INFRA` e `OS - STI` gravam parte das datas como **texto** no formato
`dd/mm/aaaa` (ex.: `"13/01/2026"`). `pd.to_datetime` sem `dayfirst=True`
assume formato americano e descarta como inválida qualquer data com dia >
12 — 114 das 244 linhas brutas de manutenção estavam sendo perdidas por
esse motivo (apareciam erradamente na regra `data_invalida` do relatório de
qualidade). Corrigido em `src/transform.to_date_safe` com `dayfirst=True`
(datas que já chegam como `datetime` do Excel não são afetadas). Resultado:
`fact_manutencao` foi de 83 para 166 linhas.

### 3. Alias `LAB` → Labomar ausente
A planilha `Atendimentos Especializado` usa a abreviação `"LAB"` para
Labomar, que não estava em `ru_aliases` — 6 registros caíam como
`ru_desconhecido`. Adicionado o alias em `config/mappings.yaml`.

### 4. `comensais_real` duplicado por prato inflava "refeições realizadas" em ~11x
Encontrado no smoke test direto da lógica do dashboard (não pela suíte de
testes, que ainda não existia nesse ponto). `comensais_real` é um valor
**único por refeição**, mas vem **repetido em todas as linhas de
preparação** daquela refeição (ex.: 11 pratos no almoço = mesmo valor
repetido 11 vezes). Somar direto na tabela de detalhe (grão = preparação)
multiplicava o resultado pelo número de pratos do dia: o primeiro cálculo
deu **11.980.794** refeições realizadas no período — número claramente
absurdo para 5 RUs em 8 meses. Corrigido com `metrics._meal_level()`, que
colapsa a tabela ao grão de refeição (RU+data+refeição) antes de somar.
Depois da correção: **1.081.064** refeições — compatível com o volume diário
observado (~6.000–7.000 refeições/dia nos 5 RUs). O mesmo bug existia
escondido em `desperdicio_per_capita` (usava `comensais_real` como
denominador direto) e foi corrigido do mesmo jeito — o indicador foi de
0,010 kg/comensal (subestimado ~11x) para 0,112 kg/comensal.

### 5. `pandas.resample(freq="M")` incompatível com a versão instalada
`'M'` foi descontinuado como alias de frequência mensal no pandas 3.x (usar
`'ME'`). Como o gráfico de evolução no MVP é diário, trocado o padrão da
função para `freq="D"`, eliminando a dependência do alias problemático no
caminho principal.

## Validações de qualidade implementadas
25 regras cobrindo as 5 fontes, gravadas em `outputs/relatorio_qualidade.csv`
a cada execução do pipeline. Achados reais da última execução (ver tabela
completa no CSV):

| Achado | Quantidade | Severidade |
|---|---|---|
| Datas inválidas em UFC-INFRA/OS-STI (ex.: `"23/202/2026"`, erro de digitação) | 3 | alta |
| `ru_desconhecido` = `SENUT` em UFC-INFRA/OS-STI (departamento, não é um dos 5 RUs — comportamento esperado, não é bug) | 4 | média |
| Datas fora do período válido 2025–2026 (ex.: `"24/03/2027"`, provável erro de digitação de ano) | 3 | média |
| Inconsistência previsto × realizado no grão de preparação (ver limitação: `comensais` varia por prato, `comensais_real` é único por refeição — a comparação de negócio correta está em `refeicoes_previstas`/`pct_execucao`, que já operam no grão certo) | 2.420 | média |
| Duplicidade de linha (linhas-template vazias/repetidas, já esperado pela auditoria anterior) | 7.675 (ISC) + 2.358 (detalhe) + 779 (sensorial) + 32 (manutenção) + 11 (atendimentos) | baixa |

Nenhum CPF, nome ou dado pessoal aparece no relatório de qualidade — os
"exemplos" nunca vêm das colunas de PII (que são excluídas na extração,
antes mesmo de qualquer validação rodar).

## Testes
37 testes em `tests/test_transform.py` (17) e `tests/test_metrics.py` (20),
todos passando na última execução. Cobrem especificamente as 5 regressões
acima (cada bug tem pelo menos 1 teste de regressão nomeado explicitamente)
mais os KPIs de Panorama, Desperdício, Qualidade e Gestão com valores
calculados à mão nas fixtures (não apenas "não lança exceção").
(4 testes adicionais para `build_public_layer` foram incluídos na revisão de
arquitetura de dados para deploy — ver adendo no final deste documento —
totalizando 41.)

## Dashboard
`app/streamlit_app.py`, 5 abas (Visão Geral, Panorama, Desperdício e
Eficiência, Qualidade/Satisfação, Gestão), filtros globais de período/RU/
refeição, cabeçalho com data de atualização e contagem de alertas de
qualidade. Testado com smoke test real do servidor (não só checagem de
sintaxe) — ver seção de validação no README e resultado consolidado no
resumo final desta etapa.

## Limitações conhecidas
1. `comensais_previsto` é uma aproximação (maior previsão de prato da
   refeição) — não existe um "previsto oficial" da refeição inteira nas
   abas de detalhe. Tratar % execução como indicador direcional.
2. `rejeito_total` usa `peso_bruto - peso_liq` como proxy, não uma coluna de
   rejeito explícita (que só existe nas abas consolidadas descartadas por
   erro). Validar com a nutricionista do RU.
3. ISC é usado com o valor já calculado na origem (não recalculamos a
   ponderação original, que não está documentada e tem erros `#VALUE!`
   parciais na fonte).
4. `Controle de Estoque`, `Treinamentos`, `Coleta de Resíduo` e as demais
   abas classificadas como legado/baixa cobertura na auditoria continuam
   fora do MVP — nenhuma mudança de escopo nesta etapa.
5. O relatório de qualidade sinaliza `inconsistencia_previsto_realizado` no
   grão de preparação por simplicidade de implementação; o KPI de negócio
   (`pct_execucao`) já usa o grão correto — ver `docs/indicadores.md`.

## Pendências para auditoria final
- Validar com a gestão do RU se o proxy de `comensais_previsto` (maior
  previsão de prato) é aceitável ou se existe um dado de previsão de
  headcount total que não identificamos nas abas de detalhe.
- Confirmar com a equipe de nutrição o cálculo de "rejeito" (peso
  bruto−líquido) antes de publicar externamente.
- Decidir o destino da aba `Entregas` duplicada dentro do Sistema RU
  (achado de governança já registrado em `docs/auditoria_dados.md`).

## KRs do OKR — situação após esta etapa

| KR | Situação | Evidência |
|---|---|---|
| O1.1 Inventariar bases | **Atendido** | `docs/auditoria_dados.md`, aguardando só validação formal com a gestão |
| O1.5 Dicionário de dados v1 | **Atendido** | `docs/dicionario_dados.md` |
| O2.1 Definir indicadores prioritários | **Atendido** | `docs/mvp_dashboard.md` + `docs/indicadores.md`, aguardando validação com a gestão |
| O1.2 Padronizar campos/formatos | **Parcial** | `config/mappings.yaml` padroniza RU/refeição/datas para as 9 abas usadas no MVP; as demais 33 abas não foram padronizadas (fora do escopo do MVP) |
| O1.3 Consolidar bases em estrutura única v1 | **Parcial** | 5 tabelas fato separadas por domínio (`data/processed/*.csv`), não uma única tabela; suficiente para o MVP, mas não é "estrutura única" literal |
| O1.4 Tratar inconsistências e definir chaves | **Parcial** | Chaves definidas (`ru`+`data`+`refeicao`+`prep`/`preparacao`); inconsistências tratadas nas 9 abas do MVP, não nas 42 |
| O1.6 Governança mínima | **Não atendido** | Ainda não formalizado documento de "quem atualiza o quê" — ver Plano de Execução |
| O1.7 Estrutura preparada para integração futura | **Atendido** | `docs/arquitetura_proposta.md` + tabelas fato em CSV, prontas para virar tabelas de banco |
| O2.2 Modelar base analítica mínima | **Atendido** | `src/metrics.py`, 13 indicadores documentados e testados |
| O2.3 Entregar dashboard v1 funcional | **Atendido** | `app/streamlit_app.py`, smoke test real passou |
| O5.1 Fechar pacote do semestre | **Parcial** | Insumos prontos (esta implementação); falta a apresentação formal à gestão |
| O2.4, O3.x, O4.x, O5.2–O5.4 | **Não atendido** | Fora do escopo desta etapa (satisfação, inovação, Fase 2) — conforme já planejado em `docs/plano_execucao.md` |

---

## Adendo — Revisão de arquitetura de dados para deploy online

**Contexto:** o MVP havia sido aprovado com ressalvas. Antes de publicar no
GitHub/Streamlit Community Cloud, era preciso resolver: `data/processed/`
está (corretamente) bloqueada pelo `.gitignore` por conter a coluna
`avaliador` em `fact_sensorial.csv`; mas o Streamlit Community Cloud só
clona o que está no Git — logo, sem uma camada de dados versionável, o
dashboard não teria dados nenhum em produção.

### O que foi feito
- Auditoria das 5 tabelas fato usadas pelo dashboard: **apenas
  `fact_sensorial.csv` tem coluna de PII** (`avaliador`, nome de integrante
  da equipe). As outras 4 (`fact_detalhe`, `fact_isc`,
  `fact_gestao_atendimentos`, `fact_gestao_manutencao`) já são 100%
  anônimas (nenhuma delas tem nome, CPF, e-mail, telefone ou matrícula —
  confirmado em `docs/auditoria_dados.md` e revalidado agora por varredura
  automática).
- Criada `data/processed_public/`: camada gerada automaticamente pelo
  pipeline (`src/transform.build_public_layer`), com as 4 tabelas sem PII
  copiadas linha a linha e `fact_sensorial_agg.csv` = `fact_sensorial.csv`
  **sem a coluna `avaliador`** (mesmo grão, mesmas linhas — nenhum
  indicador muda de fórmula).
- `src/pipeline.py` passou a gravar as duas camadas a cada execução.
- `src/config.py` ganhou `resolve_fact_path()`: prioriza
  `data/processed/` (privada, local) e cai para `data/processed_public/`
  (pública) quando a privada não existir — é assim que o dashboard
  funciona em produção sem nunca ter acesso ao Excel nem à camada privada.
  Essa lógica fica inteiramente em `src/`, não no Streamlit.
- `.gitignore` atualizado: continua bloqueando `data/raw/*.xlsx` e
  `data/processed/*` (privado); passou a **permitir explicitamente**
  `data/processed_public/`.

### Auditoria de privacidade em `data/processed_public/`
Varredura por CPF, e-mail, telefone, matrícula e nomes conhecidos
(avaliadores/atendentes identificados na auditoria original) em todos os
arquivos da pasta: **nenhum achado**. Coluna `avaliador` confirmada ausente
em `fact_sensorial_agg.csv` (e em todos os outros arquivos).

### Simulação real de `git add`
Rodado `git init` + `git add -A` no projeto e inspecionado
`git status --porcelain`: 40 arquivos seriam versionados. Confirmado que
**nenhum** `.xlsx` e **nenhum** CSV de `data/processed/` (privado) entram;
os 6 arquivos de `data/processed_public/` (5 CSVs + `metadata.json`)
entram corretamente.

### Smoke test de produção (sem Excel, sem camada privada)
Montado um diretório espelhando exatamente `git ls-files` (ou seja, só o
que iria para o GitHub) — sem `data/raw/*.xlsx` e sem
`data/processed/*.csv`. Nesse diretório:
- `python -m src.pipeline` **não foi executado** (propositalmente, para
  simular o Streamlit Community Cloud, que nunca roda o pipeline);
- `streamlit run app/streamlit_app.py --server.headless true`: servidor
  subiu, `/_stcore/health` → `ok`, `GET /` → HTTP 200, sessão de stream
  aberta sem erro no log;
- todas as chamadas de `src/metrics.py` e `app/components/charts.py` usadas
  pelo dashboard foram executadas manualmente nesse ambiente e confirmaram
  ler os arquivos de `data/processed_public/` (via `resolve_fact_path`) e
  produzir **exatamente os mesmos valores de KPI** da camada privada (ex.:
  1.081.064 refeições realizadas, 72,5% de execução, 0,112 kg/comensal de
  desperdício per capita) — prova de que a camada pública não altera
  nenhum indicador.

### Testes
4 testes novos em `tests/test_transform.py` cobrindo `build_public_layer`
(remoção da coluna `avaliador`, preservação do grão/valores, tabelas sem
PII cadastrada permanecem inalteradas, e documentação de quais tabelas têm
PII). Suíte completa: **41/41 passando**.

### Conclusão
O projeto está pronto para deploy: o dashboard funciona de ponta a ponta
usando exclusivamente o que estaria no GitHub, sem qualquer dependência do
Excel bruto ou de arquivos bloqueados pelo `.gitignore`.

---

## Adendo — Publicação, versionamento e governança mínima

**Contexto:** MVP tecnicamente validado (pipeline, 41 testes, smoke test,
camada pública, auditoria de PII — todos passando). Esta etapa cobre
exclusivamente publicação/versionamento/governança, sem alterar fórmulas,
ETL, arquitetura, layout, mappings ou regras de negócio.

### O que foi efetivamente feito (executado nesta sessão)
- Repositório Git local inicializado, branch renomeada para `main`.
- Todos os arquivos revisados via `git status --porcelain` antes do commit
  (42 arquivos — os 40 já auditados na etapa anterior + os 2 novos
  documentos de governança).
- Commit criado: `feat: release MVP dashboard RU v1.0.0` (42 arquivos,
  26.972 inserções, nenhuma remoção — é o primeiro commit do repositório).
- Tag anotada local criada: `v1.0.0-mvp`.
- Auditoria final de Git (`git status`, `git ls-files`) confirmando:
  nenhum `.xlsx`, `data/raw/` e `data/processed/` só com `.gitkeep`,
  nenhum secret/`.env`, `data/processed_public/` presente com os 6 arquivos
  esperados.
- `docs/governanca_dados.md` e `docs/atualizacao_dashboard.md` criados.
- `docs/okr_recovery.md` reavaliado: **O1.6 → ATENDIDO** (governança
  formalizada); **O2.3 → PARCIAL** (funcional e validado, ainda não
  publicado online).

### O que NÃO foi feito, e por quê
Este ambiente **não possui autenticação/autorização para a conta GitHub ou
Streamlit Community Cloud da pessoa responsável** (confirmado: `gh` CLI não
instalado, nenhuma credencial Git configurada). Por isso:
- **Nenhum repositório foi criado no GitHub.**
- **Nenhum push foi realizado.**
- **Nenhuma release foi criada no GitHub.**
- **Nenhum deploy foi realizado no Streamlit Community Cloud.**

Criar ou publicar qualquer um desses itens exigiria a conta pessoal da
pessoa responsável — publicar sem essa autorização seria tanto tecnicamente
impossível (sem credenciais) quanto inadequado. O repositório está pronto
localmente; os comandos abaixo são para executar manualmente.

### Comandos para publicar no GitHub

O repositório local já está pronto (commit + tag criados). Só falta criar o
repositório remoto e enviar:

```bash
# 1. Crie o repositório no GitHub (via https://github.com/new), nome sugerido:
#    dashboard-ru-ufc — SEM inicializar com README/gitignore (o projeto já os tem)

# 2. Dentro da pasta do projeto (onde já existe o commit local):
git remote add origin https://github.com/<seu-usuario>/dashboard-ru-ufc.git
git push -u origin main
git push origin v1.0.0-mvp   # envia a tag da release
```

Se preferir recomeçar do zero (por exemplo, copiando os arquivos para uma
pasta nova sem o `.git` já preparado), o fluxo completo é:

```bash
git init
git add .
git status --porcelain   # confira a lista antes de commitar (ver checklist acima)
git commit -m "feat: release MVP dashboard RU v1.0.0"
git branch -M main
git tag -a v1.0.0-mvp -m "Dashboard RU — MVP v1.0.0"
git remote add origin https://github.com/<seu-usuario>/dashboard-ru-ufc.git
git push -u origin main
git push origin v1.0.0-mvp
```

### Como criar a Release no GitHub (manual, via interface)
1. No repositório já publicado, acesse **Releases → Draft a new release**.
2. Em "Choose a tag", selecione `v1.0.0-mvp` (já foi enviada pelo `git push
   origin v1.0.0-mvp` acima).
3. Título: `Dashboard RU — MVP v1.0.0`.
4. Descrição sugerida:
   ```
   - Pipeline reproduzível (Excel -> extração -> validação -> transformação -> métricas)
   - Camada pública anonimizada (data/processed_public/) para deploy seguro
   - 13 KPIs documentados (Panorama, Desperdício, Qualidade, Gestão)
   - Controles de qualidade automatizados (outputs/relatorio_qualidade.csv)
   - 41 testes automatizados (pytest)
   - Dashboard Streamlit com filtros globais
   - Documentação completa (auditoria, dicionário de dados, indicadores, governança)
   - Preparado para deploy no Streamlit Community Cloud
   ```
5. **Não** anexar o Excel bruto nem qualquer arquivo de `data/processed/`
   como asset da release.
6. Publicar a release.

Alternativa via `gh` CLI (se instalado e autenticado):
```bash
gh release create v1.0.0-mvp --title "Dashboard RU — MVP v1.0.0" \
  --notes "Ver docs/implementacao_mvp.md para detalhes completos."
```

### Passo a passo para deploy no Streamlit Community Cloud (manual)
1. Acesse https://share.streamlit.io e autentique com sua conta GitHub.
2. Clique em "New app".
3. Selecione o repositório `dashboard-ru-ufc` (já publicado no passo
   anterior) e a branch `main`.
4. Em "Main file path", informe: `app/streamlit_app.py`.
5. Não é necessário configurar nenhum secret adicional — o projeto não usa
   nenhuma credencial externa (confirmado: `requirements.txt` só tem
   pandas/openpyxl/PyYAML/streamlit/plotly/pytest; nenhuma variável de
   ambiente é lida pelo código).
6. Clique em "Deploy".

Checklist pré-deploy (já confirmado nesta e nas etapas anteriores):
`requirements.txt` completo e com versões fixadas; nenhum `import` fora do
pacote (`src`/`app`) usa caminho absoluto; `src/config.py` resolve tudo via
`pathlib` relativo à raiz do projeto; `data/processed_public/` presente no
Git; dashboard testado (smoke test) sem `data/raw/` nem `data/processed/`
disponíveis.

### Teste pós-deploy (a ser feito por quem publicar)
Depois que o deploy acima for realizado manualmente, confira na URL
publicada:
- a página abre e responde (sem tela de erro do Streamlit);
- os 13 KPIs aparecem nas 5 abas;
- os filtros (período, RU, refeição) respondem;
- os gráficos renderizam;
- o cabeçalho mostra "Dados atualizados até" com a mesma data da versão
  local (2026-09-07, na última execução do pipeline nesta etapa);
- compare pelo menos: refeições realizadas (1.081.064), % execução
  (72,5%), desperdício per capita (0,112 kg/comensal) e ISC médio (8,83) —
  devem ser idênticos aos valores validados localmente, pois a camada
  pública é, linha a linha, a mesma base (ver seção de smoke test acima).

Como o deploy não foi executado nesta etapa (falta de autenticação), este
teste pós-deploy **não foi realizado** — fica registrado aqui como roteiro
para quando o deploy manual for concluído.
