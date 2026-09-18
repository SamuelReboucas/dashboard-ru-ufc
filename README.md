# Dashboard RU

Painel executivo do Restaurante Universitário (RU) — **v1.0.0-mvp + camada
analítica Power BI**.

**Repositório GitHub:** https://github.com/SamuelReboucas/dashboard-ru-ufc
(branch `main` — o MVP Streamlit v1.0.0-mvp está publicado e no ar; o
trabalho de Power BI/identidade visual desta etapa está na branch
`feature/alinhamento-painel-gestao`, ainda não mesclada em `main`).
**Dashboard online (Streamlit, MVP):** https://dashboard-ru-ufc-25gfxvetmeah4rev4x44cj.streamlit.app/
**Painel Power BI:** modelo de dados, medidas e layout **concluídos e
testados** (ver seção "Power BI" abaixo) — o arquivo `.pbix` em si ainda
**não foi construído** (`MODELO PRONTO PARA CONSTRUÇÃO`), pois o ambiente
de desenvolvimento não tem Power BI Desktop disponível.

## Objetivo

Transformar as planilhas Excel que já existem e são preenchidas
diariamente pela equipe do RU em um painel de indicadores confiável,
reprodutível e versionável, sem depender de fórmulas frágeis de planilha.

## Contexto

Este projeto é a segunda etapa de um plano de recuperação de um projeto de
transformação digital do RU que estava ~2 meses atrasado em relação ao seu
cronograma original. A primeira etapa (auditoria) produziu os documentos em
`docs/auditoria_dados.md`, `docs/okr_recovery.md`, `docs/fontes_oficiais.md`,
`docs/mvp_dashboard.md`, `docs/arquitetura_proposta.md` e
`docs/plano_execucao.md`. Esta etapa implementa o MVP definido ali. Detalhes
de tudo que foi construído e dos bugs reais encontrados no caminho estão em
`docs/implementacao_mvp.md`. A governança mínima de atualização (KR O1.6)
está formalizada em `docs/governanca_dados.md`, com o manual operacional
correspondente em `docs/atualizacao_dashboard.md`.

## Arquitetura

```
Excel privado (data/raw/)
        │
        ▼
  extração (src/extract.py)
        │
        ▼
  validação de qualidade (src/validators.py) ──► outputs/relatorio_qualidade.csv
        │
        ▼
  transformação/limpeza (src/transform.py)
        │
        ├──► data/processed/         (camada PRIVADA — dados completos, uso local,
        │                              bloqueada pelo .gitignore)
        │
        └──► data/processed_public/  (camada PÚBLICA — mesmas linhas, sem
                                       nenhuma coluna de PII, é a ÚNICA
                                       versionada no Git e a única que existe
                                       no Streamlit Community Cloud)
        │
        ▼
  métricas (src/metrics.py) ◄── lê a camada privada se existir, senão a pública
        │
        ▼
  dashboard (app/streamlit_app.py)
```

A resolução de qual camada ler é feita em `src/config.resolve_fact_path` (não
no Streamlit — `app/streamlit_app.py` e os componentes em `app/components/`
não sabem nem precisam saber qual camada está sendo usada): se
`data/processed/<tabela>.csv` existir, é ela que é lida (ambiente local, após
rodar o pipeline com o Excel); caso contrário, cai para
`data/processed_public/` (ambiente de deploy, onde a camada privada nunca
existe porque nunca foi enviada ao Git).

Todo o pipeline é orquestrado por `src/pipeline.py` e não depende de nenhum
caminho absoluto — tudo é resolvido via `pathlib` a partir de
`src/config.py`. Aliases e regras de normalização (RU, refeição, colunas,
etc.) ficam centralizados em `config/mappings.yaml`, nunca espalhados pelo
código.

### Por que duas camadas de dados processados
`data/processed/` (privada) é gerada com fidelidade total a partir do Excel
e é a que a equipe usa localmente. Ela **não pode** ir para o GitHub porque
uma das tabelas (`fact_sensorial.csv`) carrega a coluna `avaliador` (nome de
integrante da equipe). Como o Streamlit Community Cloud só enxerga o que
está no repositório Git, criamos `data/processed_public/`: uma cópia gerada
automaticamente pelo próprio pipeline, linha a linha idêntica, mas sem
nenhuma coluna de PII (ver `src/transform.build_public_layer` e
`docs/implementacao_mvp.md`). Nenhum indicador muda de fórmula ou de grão
entre as duas camadas — a única diferença são as colunas removidas.

## Estrutura do projeto

```
ru_dashboard/
├── README.md
├── requirements.txt
├── .gitignore
├── app/
│   ├── streamlit_app.py        # dashboard (5 abas, filtros globais)
│   └── components/             # carregamento de dados, filtros, cards, gráficos
├── src/
│   ├── config.py                # paths (pathlib) + mappings.yaml
│   ├── extract.py                # leitura do Excel (sem lógica de negócio)
│   ├── transform.py             # limpeza, normalização, tabelas fato
│   ├── metrics.py                # os 13 KPIs, documentados e testáveis
│   ├── validators.py             # regras de qualidade -> relatorio_qualidade.csv
│   └── pipeline.py               # orquestração ponta a ponta
├── config/
│   └── mappings.yaml              # aliases de RU, refeição, colunas — fonte única
├── data/
│   ├── raw/                       # coloque o Excel aqui (NÃO versionado)
│   ├── processed/                 # camada PRIVADA — CSVs completos (NÃO versionado)
│   └── processed_public/          # camada PÚBLICA — sem PII (VERSIONADA no Git)
├── docs/                          # auditoria + dicionário + indicadores + relatório desta etapa
├── outputs/
│   └── relatorio_qualidade.csv   # gerado a cada execução do pipeline
└── tests/
    ├── test_transform.py
    └── test_metrics.py
```

## Requisitos

- Python 3.10+
- Bibliotecas em `requirements.txt` (pandas, openpyxl, PyYAML, streamlit, plotly, pytest)

## Instalação

```bash
pip install -r requirements.txt
```

## Inserção da base

Copie o Excel do Sistema RU para `data/raw/` com o nome definido em
`config/mappings.yaml` (`excel_file`, por padrão `sistema_ru.xlsx`):

```bash
cp /caminho/para/sua/planilha.xlsx data/raw/sistema_ru.xlsx
```

O arquivo original **nunca** deve ser commitado no Git — `.gitignore` já
bloqueia `data/raw/*.xlsx` e qualquer `*.xlsx`/`*.xls`/`*.xlsm` no repositório.

## Executar pipeline

```bash
python -m src.pipeline
```

Isso lê o Excel, roda as validações de qualidade, limpa e normaliza os
dados, e grava **duas camadas**:
- `data/processed/*.csv` + `data/processed/metadata.json` — camada
  **privada**, dados completos, uso local (não versionada);
- `data/processed_public/*.csv` + `data/processed_public/metadata.json` —
  camada **pública**, idêntica linha a linha, mas sem nenhuma coluna de PII
  (versionada — é a que vai para o GitHub e para o Streamlit Community Cloud);
- `outputs/relatorio_qualidade.csv` — relatório de qualidade completo.

A execução completa (extração das ~18 mil linhas brutas do Excel) leva
cerca de 2,5–3 minutos, a maior parte no carregamento do arquivo pelo
`openpyxl` (arquivo de ~11 MB com fórmulas e pivôs).

## Executar dashboard

```bash
streamlit run app/streamlit_app.py
```

Pré-requisito: já ter rodado `python -m src.pipeline` pelo menos uma vez. O
dashboard lê a camada privada (`data/processed/`) quando ela existir
(desenvolvimento local); se não existir — caso do deploy, onde só a camada
pública foi enviada ao Git — lê `data/processed_public/` automaticamente.
Essa resolução acontece em `src/config.py`; o Streamlit e seus componentes
não têm nenhuma lógica própria sobre qual camada usar.

## Dois fluxos importantes

### Fluxo 1 — Atualização dos dados

```
Excel privado (data/raw/) → python -m src.pipeline → dados públicos anonimizados (data/processed_public/) → git commit/push
```

Para atualizar o painel com uma nova versão da planilha, **sem alterar
nenhum código**:

1. Substitua o arquivo em `data/raw/sistema_ru.xlsx` pela versão mais recente
   (mesmo nome, mesma estrutura de abas).
2. Rode `python -m src.pipeline` novamente — isso regenera **as duas
   camadas** (`data/processed/` e `data/processed_public/`) de uma vez.
3. Localmente: reabra (ou dê refresh em) `streamlit run app/streamlit_app.py`.
4. Para atualizar o dashboard publicado: `git add data/processed_public docs
   ... && git commit && git push` — **o Excel original (`data/raw/`) e a
   camada privada (`data/processed/`) nunca são commitados**, só o código e
   `data/processed_public/`.

O cabeçalho do dashboard mostra **"Dados atualizados até: DD/MM/AAAA"**,
calculado automaticamente a partir da data mais recente encontrada nos
dados processados — não precisa ser editado manualmente.

Manual operacional passo a passo (para quem só precisa executar, sem ler
todo este README): `docs/atualizacao_dashboard.md`. Regras de governança
por trás desse fluxo (papéis, periodicidade, tratamento de erro): 
`docs/governanca_dados.md`.

### Fluxo 2 — Deploy

```
GitHub (código + data/processed_public/) → Streamlit Community Cloud
```

Ver seções "GitHub" e "Deploy" abaixo para o passo a passo.

## Indicadores

13 KPIs em 4 áreas — Panorama (refeições realizadas/previstas, % execução,
evolução), Desperdício e Eficiência (rejeito total, desperdício per capita,
índice de aceitabilidade, comparação por RU), Qualidade/Satisfação
(avaliação sensorial média, ISC médio, top 5 piores preparações) e Gestão
(% atendimentos resolvidos, % OS de manutenção resolvidas). Fórmula, fonte,
filtros, tratamento de ausentes e limitações de cada indicador estão em
`docs/indicadores.md` — a documentação foi escrita para responder "de onde
saiu esse número?" para qualquer KPI exibido.

## Power BI

Além do MVP em Streamlit, o projeto tem uma **camada analítica dedicada ao
Power BI** (`src/powerbi_export.py`), atendendo às orientações da gestão
para um Painel Estratégico da Nutrição em Power BI. Esse trabalho está na
branch `feature/alinhamento-painel-gestao` (ainda não mesclada em `main`).

**Status: modelo de dados, medidas e layout concluídos e testados —
`.pbix` ainda NÃO construído** (`MODELO PRONTO PARA CONSTRUÇÃO`; o
ambiente de desenvolvimento não tem Power BI Desktop disponível).

- **Modelo estrela:** `python -m src.pipeline` gera automaticamente 5
  dimensões e 4 fatos em `data/powerbi/` (`dim_data`, `dim_ru`,
  `dim_refeicao`, `dim_preparacao`, `dim_tipo_preparacao`,
  `fact_refeicoes`, `fact_producao`, `fact_satisfacao`,
  `fact_temperatura`), incluindo Resto-Ingesta, Per Capita, ISC agregado e
  conformidade de temperatura (regra oficial da Nutrição, confirmada:
  quente >60°C/≤60°C, fria <10°C/≥10°C). Detalhe completo em
  `docs/modelo_dados_powerbi.md`.
- **Medidas DAX:** todas documentadas e prontas para colar, com a lógica
  de agregação correta (razão de somas, nunca média de percentuais) —
  `docs/medidas_powerbi.md`.
- **Layout:** 3 páginas (Visão Geral, Qualidade, Produção e Eficiência),
  com a identidade visual oficial do RU/UFC incorporada (paleta, tipografia,
  regras de logo) — `docs/especificacao_visual_powerbi.md` e
  `docs/identidade_visual_ru_powerbi.md`.
- **Guia de construção:** passo a passo completo para montar o `.pbix` no
  Power BI Desktop — `docs/guia_construcao_powerbi.md`.
- **Testes:** 57 testes automatizados (`tests/test_powerbi_export.py`)
  cobrem as fórmulas de negócio (Resto-Ingesta, Per Capita, ISC,
  conformidade térmica) e a recuperação determinística de dados
  inconsistentes na fonte de satisfação — parte da suíte completa de 98
  testes do projeto.

## Qualidade dos dados

`outputs/relatorio_qualidade.csv` é gerado a cada execução do pipeline, com
colunas `regra | quantidade | severidade | fonte | exemplo`. O dashboard lê
esse arquivo e exibe, no cabeçalho, quantos alertas de severidade alta/média
existem (`⚠ Existem N alertas de qualidade dos dados`) — problemas não
críticos não impedem o painel de abrir. O relatório completo pode ser visto
dentro do próprio dashboard (seção expansível no topo) ou abrindo o CSV
diretamente.

## Privacidade

- O Excel original **nunca deve ser publicado nem commitado no Git** —
  contém CPF e texto livre de atendimentos individuais (ver
  `docs/auditoria_dados.md`, seção "Dados que não podem ser publicados").
- CPF, nome de estudante, matrícula e qualquer texto livre de relato
  **nunca são lidos** pela camada de extração (`src/extract.py` já as
  exclui explicitamente) — não chegam a nenhuma das duas camadas
  processadas, ao dashboard, nem ao relatório de qualidade.
- **Duas camadas de dados processados, com níveis de acesso diferentes:**
  - `data/processed/` (**privada**, local apenas): dados completos. A única
    coluna de PII que chega até aqui é `avaliador` (nome de integrante da
    equipe) em `fact_sensorial.csv`. Bloqueada pelo `.gitignore`.
  - `data/processed_public/` (**pública**, versionada): gerada
    automaticamente pelo pipeline (`src/transform.build_public_layer`) a
    partir da camada privada, removendo a coluna `avaliador` — mesmas
    linhas, mesmos indicadores, zero PII. É a única camada que existe no
    Streamlit Community Cloud. Auditada por varredura de CPF/nome/e-mail/
    telefone/matrícula antes de cada publicação (ver
    `docs/implementacao_mvp.md`, seção de auditoria de privacidade).
- `outputs/` contém apenas dados agregados por RU/data/preparação — nenhuma
  linha é identificável a uma pessoa.
- `.gitignore` bloqueia o Excel bruto, a camada privada
  (`data/processed/`), `outputs/*.csv`, `.env` e
  `.streamlit/secrets.toml` — e **permite explicitamente**
  `data/processed_public/`.

## Testes

```bash
python -m pytest tests/ -v
```

41 testes em `tests/test_transform.py` e `tests/test_metrics.py`, mais 57
em `tests/test_powerbi_export.py` (98 no total) — todos usando
dados sintéticos (não dependem do Excel real, então rodam em qualquer
máquina). Cobrem especificamente as regressões reais encontradas durante a
implementação (ver `docs/implementacao_mvp.md`): alias `LAB`→Labomar, datas
brasileiras com `dayfirst`, a inflação de "refeições realizadas" por
`comensais_real` duplicado por prato, e a geração correta da camada pública
sem PII (`build_public_layer`).

## GitHub

O repositório já está publicado em
https://github.com/SamuelReboucas/dashboard-ru-ufc (branch `main`, MVP
v1.0.0-mvp). Os comandos abaixo continuam válidos como referência — tanto
para reproduzir o setup em outro ambiente quanto para o fluxo de trabalho
com branches (ex.: a branch `feature/alinhamento-painel-gestao`, usada
para a camada Power BI e a identidade visual, ainda não mesclada em `main`).

Para versionar o projeto sem incluir dados brutos nem a camada privada:

```bash
git init
git add .
git status --porcelain   # confira a lista abaixo antes de commitar
git commit -m "MVP dashboard RU"
git remote add origin <url-do-seu-repositorio>
git push -u origin main
```

**O que `git status --porcelain` deve mostrar (confirmado por simulação
real nesta etapa):** todo o código-fonte, `config/mappings.yaml`, todos os
`docs/*.md`, `requirements.txt`, `.gitignore`, os `.gitkeep` de
`data/raw/`, `data/processed/` e `outputs/`, e **todos os CSVs +
`metadata.json` de `data/processed_public/`**. Nada de `data/raw/*.xlsx`,
nada de `data/processed/*.csv` (privado) — o `.gitignore` já impede os dois.

## Deploy

**Status atual (MVP Streamlit): publicado e online.**
- Repositório: https://github.com/SamuelReboucas/dashboard-ru-ufc (branch `main`)
- Dashboard: https://dashboard-ru-ufc-25gfxvetmeah4rev4x44cj.streamlit.app/

O deploy foi feito seguindo exatamente o roteiro abaixo, que continua
válido como referência para reproduzir em outro ambiente ou para o
próximo redeploy após atualização de dados:

1. Rode `python -m src.pipeline` localmente (com o Excel em `data/raw/`)
   para garantir que `data/processed_public/` esteja atualizado.
2. Repositório no GitHub com `git push` — **o Excel original nunca deve
   ser enviado ao GitHub**.
3. Em https://share.streamlit.io, conecte o repositório, selecione a
   branch `main` e aponte o arquivo principal para `app/streamlit_app.py`.
4. O dashboard publicado roda sem `data/raw/` e sem `data/processed/`
   (a camada privada) — ele detecta essa ausência automaticamente e lê
   `data/processed_public/`, que é a única camada presente no repositório.
   Isso foi validado com um smoke test em ambiente simulado sem acesso ao
   Excel nem à camada privada (ver `docs/implementacao_mvp.md`).
5. Para atualizar o dashboard publicado depois de uma nova versão do Excel,
   siga `docs/atualizacao_dashboard.md` — o Streamlit Community Cloud
   redeploya automaticamente a cada push na branch `main`.

## Limitações conhecidas

- `comensais_previsto` (previsto de refeições) é uma aproximação — não há,
  nas abas de detalhe, um campo de "previsto total da refeição"; usamos o
  maior valor de previsão entre os pratos daquele dia como proxy.
- `rejeito_total` usa `peso_bruto − peso_liq` como proxy, não uma coluna
  explícita de rejeito.
- O ISC é usado com o valor já calculado na planilha de origem; o pipeline
  não recalcula a ponderação original.
- Apenas 9 das 42 abas do Sistema RU entram neste MVP — as demais foram
  classificadas como legado/baixa cobertura/dashboard antigo na auditoria
  (`docs/auditoria_dados.md`) e ficaram fora de escopo intencionalmente.
- Ver `docs/implementacao_mvp.md` para a lista completa de limitações e
  pendências.

## Próximas etapas

Ver `docs/plano_execucao.md` (2ª evolução e backlog) e a seção "KRs do OKR"
em `docs/implementacao_mvp.md` para o que ainda falta amadurecer depois
deste MVP — como validação formal dos indicadores com a gestão do RU,
documento de governança de atualização (O1.6), e o piloto de pesquisa de
satisfação (O3.x).
