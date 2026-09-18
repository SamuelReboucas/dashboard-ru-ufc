# Arquitetura Proposta — Sistema RU

## Visão geral do pipeline

```
Excel (P1D, P2D, BD, LD, PO2, CARDÁPIO, Av. Sensorial, ISC alm/jan/Café,
       Atendimentos Especializado, UFC-INFRA, OS - STI)
        │
        ▼
  ETL Python (pandas)
   1. Extração  → leitura direta das abas fonte (openpyxl/pandas), ignorando abas legado/dashboard
   2. Limpeza   → remove linhas-template vazias/duplicadas; trata #N/A #DIV/0! #VALUE! na origem
   3. Padronização → nomenclatura única de RU, Refeição, Data; adiciona coluna RU explícita por aba
   4. Modelagem → tabela fato única (grão: RU + Data + Refeição + Preparação) + dimensões (Cardápio, RU, Calendário)
        │
        ▼
  Camada de métricas (Python) → calcula os 13 KPIs do MVP a partir da tabela fato, sem herdar fórmulas do Excel
        │
        ▼
  Dashboard (Streamlit + Plotly) → 4 abas (Panorama, Desperdício, Qualidade, Gestão), filtros por RU/Refeição/período
        │
        ▼
  GitHub (versionamento + CI leve) → cada atualização de dado é um commit; histórico auditável
        │
        ▼
  Deploy online (Streamlit Community Cloud ou equivalente institucional da UFC)
```

## Por que essa arquitetura
- **Sustentável:** separa dado bruto (Excel, que a equipe operacional continua alimentando) de dado
  tratado (camada padronizada versionada), então erros de fórmula no Excel original não se propagam.
- **Reproduzível/versionável:** todo o tratamento vira código (não fórmula de planilha), revisável e
  testável; cada nova exportação do Excel gera um novo "run" do ETL, não uma edição manual.
- **Atualizável:** a gestora só precisa continuar preenchendo o Excel como já faz — o pipeline lê o
  arquivo e recalcula tudo, sem trabalho manual adicional de consolidação.
- **Preparada para integração futura:** a tabela fato única facilita, mais adiante, conectar a um banco
  de dados real (Postgres/SQLite) sem redesenhar o modelo.

## Estrutura de repositório proposta

```
ru-dashboard/
├── src/
│   ├── etl/
│   │   ├── extract.py        # leitura das abas fonte
│   │   ├── clean.py          # tratamento de erros/duplicidade
│   │   ├── standardize.py    # nomenclatura, tipos, RU explícito
│   │   └── build_fact.py     # monta tabela fato + dimensões
│   ├── metrics/
│   │   ├── panorama.py
│   │   ├── desperdicio.py
│   │   ├── qualidade.py
│   │   └── gestao.py
│   └── utils/
│       └── io.py
├── app/
│   └── streamlit_app.py      # dashboard (4 páginas/abas)
├── config/
│   └── settings.yaml         # nomes de RU, mapeamento de colunas, caminhos
├── data/
│   ├── raw/                  # cópia do Excel original (não versionar dado sensível bruto)
│   ├── processed/            # tabela fato em parquet/csv
│   └── .gitignore            # raw/ fora do Git se houver PII
├── docs/                     # os 6 documentos desta etapa + futuros ADRs
├── tests/
│   └── test_etl.py           # valida contagem de linhas, ausência de erros pós-ETL
├── outputs/                  # exports pontuais (PDF/relatórios)
├── requirements.txt
└── README.md
```

## Tecnologias
| Camada | Escolha | Motivo |
|---|---|---|
| Extração/transformação | Python + pandas + openpyxl | Já validado na auditoria; sem custo de licença |
| Métricas | Python (funções puras, testáveis) | Substitui fórmulas de Excel frágeis |
| Visualização | Streamlit + Plotly | Deploy rápido, baixa curva de aprendizado, atende ao pedido de "painel funcional" |
| Versionamento | GitHub | Rastreabilidade e possibilidade de deploy contínuo |
| Deploy | Streamlit Community Cloud (gratuito) ou servidor institucional | Sem infraestrutura extra necessária no MVP |

## Cuidados de privacidade na arquitetura
- A pasta `data/raw/` (cópia do Excel com a coluna PII de `Atendimentos Especializado`) **não deve ir
  para o GitHub** — usar `.gitignore` e manter localmente ou em storage restrito.
- A camada de métricas de Gestão só deve produzir agregados; o ETL pode até descartar a coluna de
  PII/texto livre logo na extração, antes de qualquer output ser salvo em `data/processed/`.

## O que este MVP NÃO inclui (2ª evolução)
- Banco de dados relacional (Postgres) — o volume atual (dezenas de milhares de linhas) roda bem em
  arquivo (Parquet/CSV) sem necessidade de banco.
- Autenticação/controle de acesso no dashboard — avaliar se o painel será público ou restrito à gestão
  antes do deploy.
- Atualização automática agendada (cron) — no v1, a atualização pode ser manual (rodar o ETL quando o
  Excel for atualizado); automatizar na 2ª evolução.
