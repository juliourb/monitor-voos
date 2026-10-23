# Monitor de voos v4 — Alagoas ⇄ São Paulo

Varre todas as datas de amanhã até +180 dias e procura ida **MCZ/AJU → GRU/CGH/VCP** com volta 5 a 7 dias depois. Avisa no Telegram quando **ida + volta ≤ R$ 1.000**.

| Arquivo | Para quê |
|---|---|
| `monitor_voos_v4.ipynb` | o monitor. Só a célula 2 (parâmetros) precisa ser editada |
| `.github/workflows/monitor.yml` | agenda no GitHub Actions: 6 execuções por dia |
| `requirements.txt` | dependências |
| `dados/` | histórico de preços em CSV (criado pelo próprio robô) |
| `cells/` + `montar_notebook.py` | fonte do notebook, célula por célula (opcional) |

---

## Tutorial: repositório público sem expor token e ids

**Como funciona a proteção.** O código nunca contém segredos. O notebook lê `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_IDS` e `URL_PLANILHA` de variáveis de ambiente. No GitHub, essas variáveis vêm de **Secrets**, que são criptografados: ninguém consegue lê-los, nem você, depois de salvos. Além disso:
- o GitHub troca qualquer segredo por `***` nos logs;
- o workflow mascara cada chat id separadamente;
- o workflow apaga os segredos do notebook executado antes de anexá-lo;
- o notebook, se der erro no Telegram, mostra só "destinatário 1/2", nunca o id nem o token.

### Passo 0 — Troque o token do bot (obrigatório)

O token antigo estava escrito no notebook v3. Considere-o vazado.

1. No Telegram, abra **@BotFather**.
2. Envie `/mybots`, escolha o bot e toque em **API Token → Revoke current token**.
3. Guarde o token novo. Ele vai **só** para o segredo do GitHub (e para os Secrets do Kaggle, se ainda usar o v3).

> **Não suba o `voos-al2florianolis.ipynb` (v3) para o repositório.** Ele tem o token, os ids e o link da planilha escritos no código. Suba apenas os arquivos deste pacote.

### Passo 1 — Criar o repositório

1. Em github.com, clique em **New repository**.
2. Nome: `monitor-voos` · **Public** · marque *Add a README* · **Create repository**.

### Passo 2 — Enviar os arquivos (pelo navegador, sem git)

1. Descompacte o `monitor-voos-v4.zip` no seu computador.
2. No repositório, clique em **Add file → Upload files**.
3. Arraste **o conteúdo** da pasta `monitor-voos`: `monitor_voos_v4.ipynb`, `requirements.txt`, `README.md`, `montar_notebook.py`, `.gitignore` e as pastas `cells` e `.github`.
   - A pasta `.github` começa com ponto e pode estar oculta. No Windows: Explorador → *Exibir → Itens ocultos*. No Mac: `Cmd + Shift + .` no Finder.
   - Se o upload ignorar a pasta `.github`, crie o arquivo à mão: **Add file → Create new file**, digite o nome `.github/workflows/monitor.yml` (as barras criam as pastas) e cole o conteúdo do `monitor.yml`.
4. **Commit changes**.

<details><summary>Alternativa pelo terminal (git)</summary>

```bash
git clone https://github.com/<seu-usuario>/monitor-voos.git
cd monitor-voos
# copie para cá os arquivos do pacote
git add .
git status          # confira: não pode aparecer o notebook v3 nem nenhum .json de credencial
git commit -m "monitor de voos v4"
git push
```
</details>

### Passo 3 — Cadastrar os segredos

**Settings → Secrets and variables → Actions → New repository secret.** Crie um por vez (o nome tem que ser exatamente este):

| Name | Secret | Obrigatório |
|---|---|---|
| `TELEGRAM_TOKEN` | o token **novo** do BotFather | sim |
| `TELEGRAM_CHAT_IDS` | seus ids separados por vírgula, sem espaço | sim |
| `GOOGLE_SHEETS_CREDS` | o JSON inteiro da service account (cole tudo, com as chaves `{ }`) | não |
| `URL_PLANILHA` | o link da planilha do histórico | não (só junto com o anterior) |
| `TRAVELPAYOUTS_TOKEN` | token do Travelpayouts | não |

Sem `GOOGLE_SHEETS_CREDS` + `URL_PLANILHA`, o histórico vai para `dados/*.csv.gz` no próprio repositório. Esses arquivos só têm datas, cias e preços. Se preferir que nem isso fique público, cadastre os dois segredos do Sheets.

### Passo 4 — Liberar o robô para gravar o histórico

**Settings → Actions → General → Workflow permissions → Read and write permissions → Save.**

### Passo 5 — Primeiro teste, sem enviar nada

1. Aba **Actions**. Se aparecer um aviso, clique em *I understand my workflows, go ahead and enable them*.
2. Clique em **Monitor de voos → Run workflow**, escolha `dry_run = 1` e clique em **Run workflow**.
3. Abra a execução. No passo *Rodar o notebook*, ela deve terminar em verde em ~10 min.
4. No fim da página, em *Artifacts*, baixe `execucao-N`. O `executado.ipynb` mostra as mensagens que seriam enviadas e o `painel_0.png`.
5. Confira que no log e no notebook baixado não aparece nenhum id nem token, só `***`.

### Passo 6 — Ligar de verdade

Rode **Run workflow** de novo com `dry_run = 0`. As mensagens chegam no Telegram. Daí em diante ele roda sozinho às 06h17, 09h17, 12h17, 15h17, 18h17 e 21h17 (Brasília). A das 06h17 faz a varredura completa; as outras fazem checagens rápidas.

### Cuidados que mantêm os segredos seguros

- **Nunca** escreva token, ids ou links da planilha em células do notebook, nem "só para testar".
- Se um segredo for parar num commit, apagar o arquivo não basta: o histórico do git guarda. Revogue e troque o segredo.
- Na aba **Security**, mantenha ligado o *Secret scanning / Push protection*. Ele bloqueia push com tokens conhecidos.
- Pull requests de forks não recebem segredos. Não troque o gatilho para `pull_request_target`.

### Se os horários agendados falharem

O GitHub pode atrasar ou pular execuções agendadas em horários de pico. Plano B gratuito: no cron-job.org, crie uma tarefa que chama

```
POST https://api.github.com/repos/<usuario>/monitor-voos/actions/workflows/monitor.yml/dispatches
Authorization: Bearer <token fine-grained só deste repositório, permissão "Actions: Read and write">
Content-Type: application/json
Body: {"ref":"main"}
```

O token fine-grained fica guardado no cron-job.org, não no repositório.

---

## Kaggle (alternativa, 1×/dia)

O agendamento do Kaggle só oferece diário, semanal ou mensal. Cadastre os mesmos nomes em *Add-ons → Secrets*, ligue *Internet* e agende *Daily*.

## Testar no computador, sem internet

```
FONTE=simulada DRY_RUN=1 HIST_BACKEND=csv jupyter nbconvert --to notebook --execute monitor_voos_v4.ipynb --output teste.ipynb
```

## Fontes de preço

| Fonte | Como acessa | Observação |
|---|---|---|
| **fli** (principal) | Google Flights, todos os aeroportos numa consulta | traz o link do voo exato |
| **fast-flights** (reserva) | Google Flights | usada se a fli falhar |
| **Aviasales / Travelpayouts** (opcional) | API grátis, 1 chamada = mês inteiro | preços em cache (~48 h), marcados como "confirme" |
