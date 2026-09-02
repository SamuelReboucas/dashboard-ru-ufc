# Governança de Dados — Dashboard RU

Documento curto e prático que formaliza o KR **O1.6** (definir regras de
atualização e governança mínima). Complementa `docs/atualizacao_dashboard.md`
(o passo a passo operacional).

## Fonte oficial

Hoje, o processo é alimentado por **um único arquivo Excel**: o Sistema RU
(`data/raw/sistema_ru.xlsx`), mantido pela equipe operacional do RU. É esse
arquivo — e nenhuma cópia paralela — que deve ser atualizado e colocado em
`data/raw/` antes de cada execução do pipeline.

Achado de governança já registrado em `docs/auditoria_dados.md`: existe uma
aba `Entregas` dentro do próprio Sistema RU que duplica parcialmente o
conteúdo do arquivo `plano_acompanhamento_RU_OKR_2026.xlsx`. Enquanto essa
duplicação não for resolvida pela gestão, **o arquivo OKR oficial continua
sendo a fonte de verdade para acompanhamento de entregas**, não a aba
`Entregas` do Sistema RU.

## Responsável pela atualização

`A DEFINIR COM A GESTÃO`

Papéis que precisam ser atribuídos formalmente (nenhum nome é presumido
aqui):

| Papel | Responsabilidade |
|---|---|
| Equipe responsável pelo Sistema RU | Manter o Excel atualizado diariamente (como já faz hoje) e avisar quando uma nova versão consolidada estiver pronta para virar dashboard |
| Responsável técnico pelo pipeline | Substituir o arquivo em `data/raw/`, executar `python -m src.pipeline`, conferir o relatório de qualidade e fazer o commit/push da camada pública |
| Responsável pela validação dos indicadores | Conferir se os KPIs do dashboard continuam fazendo sentido após cada atualização (comparação com o período anterior, checagem de valores fora do padrão) |

## Periodicidade

Não há periodicidade oficial definida pela gestão até o momento. **Recomendação** (não é uma regra já aprovada): atualização **semanal ou quinzenal**, o suficiente para acompanhar a operação sem gerar trabalho manual excessivo de re-execução do pipeline (~2,5–3 minutos por execução). Ajustar conforme a cadência real de decisões da gestão do RU.

## Fluxo

```
Sistema RU privado (Excel, atualizado pela equipe operacional)
        │
        ▼
Substituição do arquivo em data/raw/
        │
        ▼
Execução do pipeline: python -m src.pipeline
        │
        ▼
Validações automáticas (src/validators.py → outputs/relatorio_qualidade.csv)
        │
        ▼
Geração automática das duas camadas: data/processed/ (privada) e
data/processed_public/ (pública, sem PII)
        │
        ▼
Validação manual antes de publicar (ver seção abaixo)
        │
        ▼
git add data/processed_public + commit + push
        │
        ▼
Atualização do dashboard online (Streamlit Community Cloud faz redeploy
automático a cada push na branch main)
```

## Validação antes da publicação

Antes de dar `git push`, verificar obrigatoriamente:

1. **Pipeline concluiu sem erro** — a mensagem final deve ser
   `[5/5] Concluído em ...` sem traceback.
2. **Relatório de qualidade** (`outputs/relatorio_qualidade.csv`) — comparar
   a contagem de alertas de severidade alta/média com a execução anterior;
   um salto muito grande é sinal de que algo mudou na estrutura do Excel e
   merece investigação antes de publicar.
3. **PII** — conferir que `data/processed_public/` não ganhou nenhuma
   coluna nova que não passou pela auditoria (checklist rápido: nenhuma
   coluna chamada nome/CPF/e-mail/telefone/matrícula/avaliador/responsável).
4. **Consistência dos principais KPIs** — olhar ao menos "refeições
   realizadas", "% execução" e "ISC médio" no dashboard local e confirmar
   que os números são plausíveis (não zerados, não multiplicados por uma
   ordem de grandeza inesperada).

## Versionamento

O GitHub é usado para versionar:
- código (`app/`, `src/`, `config/`, `tests/`);
- documentação (`docs/`, `README.md`);
- configuração (`config/mappings.yaml`, `requirements.txt`, `.gitignore`);
- dados públicos anonimizados (`data/processed_public/`).

**Nunca deve ser versionado** (garantido hoje pelo `.gitignore`):
- o Excel bruto (`data/raw/*.xlsx`);
- a camada privada de dados (`data/processed/*`);
- qualquer dado pessoal (CPF, nome, matrícula, telefone, e-mail);
- segredos e credenciais (`.env`, `.streamlit/secrets.toml`).

## Tratamento de erro

Se o pipeline falhar (exceção, traceback, ou o relatório de qualidade
indicar um problema estrutural grave):

1. **Não publicar** a nova base — não rodar `git add`/`commit`/`push` da
   camada pública gerada com erro.
2. **Manter a versão anterior** no dashboard online (o Streamlit Community
   Cloud só atualiza no próximo `push`; sem push, o ar público continua
   servindo os últimos dados públicos válidos já commitados).
3. **Investigar o erro** — checar o log do pipeline e, se for um problema
   de estrutura do Excel (aba renomeada, coluna removida), comparar com
   `config/mappings.yaml` e `docs/dicionario_dados.md`.
4. **Corrigir** — ajustar o Excel de origem ou, se for uma mudança
   estrutural legítima e permanente, ajustar `config/mappings.yaml` (nunca
   hardcode no código).
5. **Executar novamente** o pipeline e repetir a validação antes de
   publicar.

## Histórico

Qualquer alteração de regra de negócio (fórmula de indicador, critério de
limpeza de dados, novo alias de RU/refeição etc.) deve ser:
- **registrada** em `docs/implementacao_mvp.md` (seção de limitações/adendos)
  ou em um novo documento de changelog, se o volume de mudanças justificar;
- **documentada** — atualizando `docs/indicadores.md` e/ou
  `docs/dicionario_dados.md` conforme o caso;
- **versionada via Git** — cada mudança de regra deve corresponder a um
  commit com mensagem clara (ex.: `fix: corrige fórmula de X` ou
  `data: adiciona alias Y para RU Z`), nunca uma edição silenciosa.
