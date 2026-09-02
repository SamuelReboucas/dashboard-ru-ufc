# Atualizar o Dashboard RU

Manual operacional simples — qualquer pessoa da equipe deve conseguir seguir
estes passos sem precisar entender o código. Para o "porquê" de cada regra,
ver `docs/governanca_dados.md`.

## 1. Substituir a planilha

Coloque a nova versão do Sistema RU em `data/raw/`, com o mesmo nome já
configurado (`sistema_ru.xlsx` — ver `config/mappings.yaml`, chave
`excel_file`, caso o nome precise mudar):

```bash
cp /caminho/para/a/nova/planilha.xlsx data/raw/sistema_ru.xlsx
```

## 2. Executar o pipeline

```bash
python -m src.pipeline
```

Isso demora cerca de 2,5–3 minutos. Ao final, deve aparecer uma linha como:

```
[5/5] Concluído em 160.5s. Dados atualizados até 2026-09-07.
```

Se aparecer um erro (`ERRO no pipeline: ...`) em vez dessa linha, **pare
aqui** — não siga para os próximos passos. Volte a este documento depois de
corrigir (ver `docs/governanca_dados.md`, seção "Tratamento de erro").

## 3. Conferir

- A execução terminou com `[5/5] Concluído` (sem traceback)?
- Abra `outputs/relatorio_qualidade.csv` — o número de alertas de
  severidade alta/média mudou muito em relação à última vez? Se sim,
  investigue antes de publicar.
- Confira a "data máxima dos dados" impressa no final da execução — ela
  deve corresponder à data mais recente que você esperava encontrar na
  planilha nova.
- Rode `streamlit run app/streamlit_app.py` localmente e olhe os KPIs
  principais (refeições realizadas, % execução, ISC médio) — os números
  fazem sentido? Nenhum está zerado ou absurdamente alto?

## 4. Conferir privacidade

Garanta que `data/processed_public/` não contém PII antes de publicar:

```bash
grep -rEn "[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}" data/processed_public/   # CPF
grep -rEn "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}" data/processed_public/  # e-mail
head -1 data/processed_public/fact_sensorial_agg.csv | tr ',' '\n' | grep -i avaliador  # deve vir vazio
```

Os três comandos acima devem retornar **vazio**. Se qualquer um deles
encontrar algo, **não publique** — volte para `docs/governanca_dados.md` e
`docs/auditoria_dados.md` antes de continuar.

## 5. Versionar

```bash
git add data/processed_public
git commit -m "data: atualiza dashboard RU YYYY-MM-DD"
git push
```

Substitua `YYYY-MM-DD` pela data de hoje. Só adicione `data/processed_public`
— não use `git add .` neste passo, para evitar versionar acidentalmente
qualquer outro arquivo que não devesse ir (o `.gitignore` já bloqueia o
Excel e a camada privada, mas `git add data/processed_public` é mais
explícito e seguro para uma atualização de rotina).

## 6. Dashboard

Se o projeto já estiver publicado no Streamlit Community Cloud, o `git push`
acima é suficiente — o Streamlit Community Cloud observa a branch `main` do
repositório conectado e faz **redeploy automático** a cada push, sem
nenhuma ação manual adicional na plataforma. Em geral leva de 1 a alguns
minutos para o dashboard publicado refletir os novos dados; se demorar mais
que isso, verifique o painel de administração do app em
https://share.streamlit.io (opção "Manage app" → logs).

Se o projeto ainda não tiver sido publicado, este passo não se aplica — ver
`docs/implementacao_mvp.md` / resumo da etapa de publicação para o
passo a passo de deploy inicial.
