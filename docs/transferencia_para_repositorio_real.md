# Transferencia para o Repositorio Real

O commit mais recente desta entrega (confira com `git log -1` no
sandbox), branch `feature/alinhamento-painel-gestao`, existe apenas neste
sandbox de desenvolvimento - o historico `.git` daqui **nao** vai dentro
do ZIP e nao deve ser presumido como transferivel. Este documento explica
a forma mais segura de levar o conteudo para o seu repositorio GitHub
real (`dashboard-ru-ufc`), preservando tudo que ja esta publicado em `main`.

## Antes de comecar
Seu repositorio real ja tem, em `main`, o MVP v1.0.0-mvp publicado e
funcionando online (https://github.com/SamuelReboucas/dashboard-ru-ufc,
dashboard em https://dashboard-ru-ufc-25gfxvetmeah4rev4x44cj.streamlit.app/).
Nada disso sera tocado - todo o trabalho desta entrega (camada Power BI +
identidade visual) entra em uma branch separada,
`feature/alinhamento-painel-gestao`.

## Passo 1 - Preservar o seu repositorio real atual
No seu Codespace (ou clone local), confirme que esta tudo limpo antes de
comecar:

```bash
git status
git branch
```

Se houver qualquer alteracao nao commitada, resolva isso primeiro (commit
ou descarte) antes de seguir - assim fica claro o que veio desta entrega e
o que ja existia.

## Passo 2 - Criar/usar localmente a branch feature/alinhamento-painel-gestao

```bash
git checkout main
git pull origin main
git checkout -b feature/alinhamento-painel-gestao
```

Se a branch ja existir localmente (de uma tentativa anterior), use:

```bash
git checkout feature/alinhamento-painel-gestao
git pull origin feature/alinhamento-painel-gestao   # se ja tiver sido enviada antes
```

## Passo 3 - Copiar os novos arquivos
Baixe e extraia o ZIP desta entrega (`painel_estrategico_ru_powerbi_ready_v3.zip`)
no seu computador, fora da pasta do repositorio. Dentro dele esta a pasta
do projeto completa. Envie o conteudo extraido para dentro do Codespace
(mesmo processo de upload ja usado nas etapas anteriores: botao direito no
Explorer -> Upload), depois:

```bash
# o zip extrai para uma pasta chamada painel_delivery_v3/
cp -r painel_delivery_v3/. .
rm -rf painel_delivery_v3 painel_estrategico_ru_powerbi_ready_v3.zip
```

Isso vai sobrescrever/adicionar arquivos de codigo, config, docs e
`data/powerbi/` - sem tocar no que ja existe em `.git`.

## Passo 4 - Conferir o git diff
**Este e o passo mais importante antes de commitar.** Revise exatamente o
que mudou:

```bash
git status
git diff --stat
```

Confirme especificamente:
- os arquivos alterados/adicionados batem com a lista deste resumo (ver
  `docs/resumo_final_painel_estrategico.md` e a lista de arquivos no fim
  deste documento);
- **nenhum** `.xlsx` aparece;
- **nenhum** arquivo de `data/raw/` (alem de `.gitkeep`) aparece;
- **nenhum** arquivo de `data/processed/` privado (alem de `.gitkeep`)
  aparece;
- `data/powerbi/*.csv` aparece como novo (8 arquivos).

Se algo inesperado aparecer, pare e investigue antes do proximo passo -
nao commite as cegas.

## Passo 5 - Executar os testes
Com as dependencias instaladas (`pip install -r requirements.txt`, se
ainda nao estiver feito neste Codespace):

```bash
python -m pytest tests/ -v
```

Resultado esperado: **91 passed**. Se algo falhar, isso indica que a copia
de arquivos ficou incompleta ou misturada com uma versao antiga - revise o
Passo 3 antes de continuar.

Opcional, mas recomendado - rodar o pipeline uma vez para confirmar que
`data/powerbi/` bate com o que esta na entrega (requer o Excel em
`data/raw/`, que **nao** vem no ZIP por conter dados pessoais):

```bash
python -m src.pipeline
```

## Passo 6 - Commit

```bash
git add .
git status --porcelain   # confira a lista final antes do commit
git commit -m "feat: implementa modelo analitico do painel estrategico RU"
```

## Passo 7 - Push da branch

```bash
git push -u origin feature/alinhamento-painel-gestao
```

Isso cria a branch no GitHub remoto **sem afetar `main`**.

## Passo 8 - NAO fazer merge em main ainda
A branch fica disponivel no GitHub para revisao (voce pode abrir um Pull
Request de `feature/alinhamento-painel-gestao` para `main` se quiser
revisar visualmente o diff pela interface do GitHub) - mas **o merge para
`main` so deve acontecer depois da sua aprovacao explicita**, e
idealmente depois de:
- construir e validar o `.pbix` no Power BI Desktop (ver
  `docs/guia_construcao_powerbi.md`);
- resolver ou aceitar formalmente os residuais em
  `docs/perguntas_validacao_nutricao.md`.

## Checklist final de arquivos esperados no diff
Código: `src/powerbi_export.py` (novo), `src/pipeline.py`,
`src/validators.py`, `src/config.py`, `config/mappings.yaml` (alterados).
Testes: `tests/test_powerbi_export.py` (novo, 57 testes). Dados:
`data/powerbi/*.csv` (**9 arquivos** — incluindo `dim_tipo_preparacao.csv`,
adicionada na revisão técnica final). Documentação: `README.md`,
`docs/aderencia_orientacoes_gestao.md`, `docs/arquitetura_powerbi.md`,
`docs/perguntas_validacao_nutricao.md`, `docs/modelo_dados_powerbi.md`,
`docs/medidas_powerbi.md`, `docs/especificacao_visual_powerbi.md`,
`docs/guia_construcao_powerbi.md` (alterados/atualizados);
`docs/identidade_visual_ru_powerbi.md`,
`docs/resumo_final_painel_estrategico.md`,
`docs/transferencia_para_repositorio_real.md` (novos). `.gitignore`
(alterado, permite `data/powerbi/`).
