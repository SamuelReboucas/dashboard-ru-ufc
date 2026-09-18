# Arquitetura para Power BI — camada oficial de visualização

**Versão 4 (final desta etapa de implementação).** As versões 1–3 deste
documento documentaram a evolução da decisão (de "Power BI ou Streamlit?"
para "Power BI é requisito dado") e do modelo de dados (de um fato único
para fatos separados por grão real). Esta versão consolida o estado
**implementado**: código em `src/powerbi_export.py`, dados gerados em
`data/powerbi/`, 57 testes automatizados em `tests/test_powerbi_export.py`.

Detalhes completos estão em três documentos dedicados, para não duplicar
conteúdo:
- **`docs/modelo_dados_powerbi.md`** — dimensões, fatos, grão, relacionamentos, contagem de linhas real
- **`docs/medidas_powerbi.md`** — todas as medidas DAX, incluindo temperatura/conformidade
- **`docs/especificacao_visual_powerbi.md`** — as 3 páginas, filtros, visuais

## Papel de cada ferramenta (sem mudança desde a v2)

| Camada | Ferramenta | Responsabilidade |
|---|---|---|
| Tratamento e regra de negócio | **Python** (`src/extract.py`, `src/transform.py`, `src/powerbi_export.py`) | Única fonte de verdade para limpeza, normalização, granularidade e fórmulas de indicador — incluindo Resto-Ingesta, Per Capita, ISC agregado e conformidade de temperatura, todos implementados aqui, nunca em DAX |
| Visualização e análise oficial da gestão | **Power BI** | Consome as tabelas já tratadas; calcula no DAX apenas agregações de exibição (somas, razões de somas/contagens) sobre colunas já limpas |
| Protótipo, validação, solução paralela | **Streamlit** (`app/streamlit_app.py`) | Preservado e testado a cada mudança (smoke test de regressão) — continua sendo onde o pipeline é validado no dia a dia |

## Fluxo (sem mudança)

```
Sistema RU (Excel privado)
        |
        v
Pipeline Python (src/pipeline.py)
        |
        +--> data/processed/          (privada, uso local/Streamlit dev)
        +--> data/processed_public/   (publica, sem PII, Streamlit Cloud)
        +--> data/powerbi/            (modelo estrela, sem PII, Power BI)
             + outputs/preparacoes_sem_classificacao_termica.csv (auditoria)
```

## O que foi validado contra a base real antes de implementar
Nenhuma fórmula abaixo foi assumida — todas foram testadas contra milhares
de linhas reais antes do código ser escrito (ver
`docs/aderencia_orientacoes_gestao.md`, seção 3-A):

| Fórmula | Resultado |
|---|---|
| `Cons. Real = Peso Líq − Sobra Limpa − Sobra Suja` | 100% em 13.673 linhas |
| `ISC = (ÓTIMO×10+REGULAR×5+RUIM×1) / Total` | 100% em 3.663 linhas |
| Chave composta do ISC = Refeição+Serial+tipo_preparacao | 100% em 644 linhas |

## Estado final do modelo (resumo — ver `docs/modelo_dados_powerbi.md` para detalhe)

| Tabela | Linhas | Observação |
|---|---|---|
| `dim_data.csv` | 162 | — |
| `dim_ru.csv` | 5 | — |
| `dim_refeicao.csv` | 3 | — |
| `dim_preparacao.csv` | 213 | Grão: prato específico |
| `dim_tipo_preparacao.csv` | 22 | Grão: categoria (tipo). Usada pelo slicer oficial de "tipo de preparação" — cobre 100% de `fact_satisfacao`, diferente de `dim_preparacao` (60%) |
| `fact_refeicoes.csv` | 1.380 | Grão RU+Data+Refeição; regressão de 1.081.064 confirmada |
| `fact_producao.csv` | 15.786 | Resto-Ingesta, % Resto-Ingesta, Per Capita implementados |
| `fact_satisfacao.csv` | 1.604 | 100% das linhas com `tipo_preparacao` (direto ou recuperado); 60% com prato específico |
| `fact_temperatura.csv` | 15.786 | Conformidade térmica implementada; 72,4% de cobertura de classificação |

## Por que não duplicar granularidade/regras em DAX (reforçado)
O princípio mais importante desta arquitetura continua sendo: qualquer
correção de granularidade (Refeições, Per Capita) ou fórmula de negócio
(Resto-Ingesta, ISC, conformidade térmica) é resolvida uma vez, em Python,
antes do CSV existir. O Power BI nunca precisa de `SUMMARIZE`, `DISTINCT`
ou lógica condicional complexa em DAX para compensar dado mal
granularizado — se isso parecer necessário em algum momento, o sinal
correto é pedir uma nova coluna/tabela ao pipeline, não escrever DAX mais
esperto.

## O que NÃO fazer (sem mudança)
- Não recriar em Power Query a limpeza de erros de fórmula do Excel.
- Não ler o Excel bruto diretamente do Power BI.
- Não reimplementar em DAX nenhuma correção de granularidade já resolvida no Python.
- Não inferir `classe_termica` a partir da temperatura observada (circular).
- Não forçar relacionamento entre `fact_satisfacao` e `dim_preparacao` nas linhas onde só o `tipo_preparacao` foi recuperado — o prato específico permanece desconhecido nesses casos, isso é registrado, não escondido.

## Status desta proposta
Modelo de dados, regras de negócio e testes implementados e validados. A
construção do arquivo `.pbix` em si é tratada separadamente — ver
`docs/guia_construcao_powerbi.md` para o passo a passo (o ambiente onde
este projeto foi desenvolvido não tem Power BI Desktop disponível para
construir e validar o `.pbix` diretamente).
