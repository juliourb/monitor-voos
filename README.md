# ✈️ Monitor de voos baratos (Google Flights → Telegram)

Robô que roda sozinho no GitHub Actions e guarda o histórico de preços no próprio repositório. Ele faz quatro coisas:
- Varre todas as datas dos próximos 180 dias.
- Combina a ida e a volta mais baratas dentro da estadia que você escolher.
- Manda um alerta no Telegram quando a soma fica abaixo do seu teto.
- Uma vez por dia, manda também um resumo com gráficos.

Configuração padrão: ida **MCZ/AJU → GRU/CGH/VCP**, volta 5 a 7 dias depois, teto de **R$ 1.000** somando os dois trechos. Tudo isso se muda na célula 2 do notebook ([passo 6](#6-personalizar-a-rota)).

**Nada de token ou id fica no código.** Tudo entra como *Secret* do GitHub, então o repositório pode ser público.

---

## Sumário
1. [Copiar o projeto para a sua conta](#1-copiar-o-projeto-para-a-sua-conta)
2. [Criar o bot do Telegram e pegar o token](#2-criar-o-bot-do-telegram-e-pegar-o-token)
3. [Descobrir os chat ids](#3-descobrir-os-chat-ids)
4. [(Opcional) Segunda fonte de preços: Travelpayouts](#4-opcional-segunda-fonte-de-preços-travelpayouts)
5. [Cadastrar os Secrets no GitHub](#5-cadastrar-os-secrets-no-github)
6. [Personalizar a rota](#6-personalizar-a-rota)
7. [Testar e ligar](#7-testar-e-ligar)
8. [Onde ficam os dados](#8-onde-ficam-os-dados)
9. [Problemas comuns](#9-problemas-comuns)
10. [Segurança](#10-segurança)

---

## 1. Copiar o projeto para a sua conta

**Opção A — Fork (mais fácil):**
1. No topo deste repositório, clique em **Fork → Create fork**.
2. No seu fork, abra a aba **Actions** e clique em **I understand my workflows, go ahead and enable them**. Em forks, o GitHub desliga os workflows até você autorizar.

**Opção B — Repositório novo, enviando os arquivos:**
1. **New repository** → escolha um nome → *Public* → **Create**.
2. **Add file → Upload files** → arraste todos os arquivos do projeto.
3. **Confira se a pasta `.github` subiu.** A raiz do repositório precisa mostrar `.github/workflows/monitor.yml`. Por começar com ponto, essa pasta fica oculta no Windows e no Mac, e o upload pelo navegador costuma pulá-la. Se ela não estiver lá:
   1. Clique em **Add file → Create new file**.
   2. No nome, digite exatamente `.github/workflows/monitor.yml`. As barras criam as pastas.
   3. Cole o conteúdo do arquivo `monitor.yml` → **Commit changes**.

Em qualquer opção, libere o robô para gravar o histórico: **Settings → Actions → General → Workflow permissions → Read and write permissions → Save**.

## 2. Criar o bot do Telegram e pegar o token

Documentação oficial: [Telegram — From BotFather to 'Hello World'](https://core.telegram.org/bots/tutorial), seção *Obtain your bot token*.

1. No Telegram, abra o **@BotFather** (o perfil oficial tem selo azul).
2. Envie `/newbot`.
3. Dê um nome (ex.: `Alerta de Voos`) e um usuário terminado em `bot` (ex.: `meus_voos_alerta_bot`).
4. O BotFather responde com o **token**, no formato `123456789:AA...`. Guarde-o: ele vai para o Secret `TELEGRAM_TOKEN`.
5. Abra o seu bot e toque em **Iniciar**. Um bot só consegue mandar mensagem para quem falou com ele antes.

> Token vazou? Envie `/mybots` ao BotFather → escolha o bot → **API Token → Revoke current token**, e atualize o Secret.

## 3. Descobrir os chat ids

Cada pessoa que vai receber alertas precisa:
1. Mandar qualquer mensagem para o **seu** bot.
2. Descobrir o próprio id por um destes caminhos:
   - **Mais simples:** mandar uma mensagem para o **@userinfobot**. Ele responde com o `Id`.
   - **Pelo próprio bot:** abrir no navegador `https://api.telegram.org/bot<SEU_TOKEN>/getUpdates` e procurar `"chat":{"id": ...}`. Esse é o método [`getUpdates` da Bot API](https://core.telegram.org/bots/api#getupdates). Faça isso só no seu computador, porque a URL contém o token.

Junte os ids **separados por vírgula, sem espaço**:

```
123456789,987654321
```

Grupos têm id negativo e entram do mesmo jeito, por exemplo `-1001234567890`. Nesse caso, adicione o bot ao grupo antes.

## 4. (Opcional) Segunda fonte de preços: Travelpayouts

Crie uma conta grátis em [travelpayouts.com](https://www.travelpayouts.com) → perfil → seção **API token**. Cadastre como `TRAVELPAYOUTS_TOKEN`. Os preços dessa fonte vêm do cache do Aviasales (até ~48 h) e aparecem marcados como "confirme".

## 5. Cadastrar os Secrets no GitHub

No seu repositório: **Settings → Secrets and variables → Actions → aba Secrets → New repository secret**. O *Name* tem que ser exatamente este:

| Name | Obrigatório | Valor |
|---|---|---|
| `TELEGRAM_TOKEN` | **sim** | token do BotFather ([passo 2](#2-criar-o-bot-do-telegram-e-pegar-o-token)) |
| `TELEGRAM_CHAT_IDS` | **sim** | ids separados por vírgula ([passo 3](#3-descobrir-os-chat-ids)) |
| `TRAVELPAYOUTS_TOKEN` | não | token do Travelpayouts ([passo 4](#4-opcional-segunda-fonte-de-preços-travelpayouts)) |

Depois de salvo, ninguém consegue ler um Secret, nem você. Para trocar o valor, clique no lápis e cole o novo.

## 6. Personalizar a rota

Edite a **célula 2** do `monitor_voos_v4.ipynb`. No GitHub, abra o arquivo → ícone de lápis. O notebook é JSON, então é mais confortável editar no Jupyter ou no VS Code e reenviar.

```python
ROTAS = [
    dict(
        nome="Alagoas ⇄ São Paulo",
        origens=["MCZ", "AJU"],            # de onde sai a ida
        destinos=["GRU", "CGH", "VCP"],    # para onde vai a ida
        teto_ida_volta=1000,               # alerta se ida + volta <= isto
        min_noites=5, max_noites=7,        # estadia
        teto_trecho=None,                  # ou ex.: 450 para alertar trechos avulsos
    ),
]
```

Outras opções da mesma célula:
- `HORIZONTE_DIAS`: até quantos dias à frente procurar.
- `MAX_ESCALAS`: 0 = só voos diretos.
- `PERMITIR_AEROPORTOS_DIFERENTES`: `False` obriga a voltar pelo mesmo aeroporto da ida.

Se você mantém a fonte em `cells/`, rode `python montar_notebook.py` para gerar o notebook de novo.

## 7. Testar e ligar

1. **Actions → Monitor de voos → Run workflow** → `dry_run = 1` → **Run workflow**.
2. Espere uns 10 min e abra a execução. Em **Artifacts**, baixe `execucao-N`. Lá estão as mensagens que seriam enviadas (`executado.ipynb`) e o painel (`painel_0.png`). No lugar dos segredos deve aparecer só `***`.
3. Rode de novo com `dry_run = 0`. Agora as mensagens chegam no Telegram.
4. Daí em diante ele roda sozinho às 06h17, 09h17, 12h17, 15h17, 18h17 e 21h17 (Brasília). A das 06h17 faz a varredura completa (~360 consultas); as outras fazem checagens rápidas.

Para mudar os horários, edite o `cron` em `.github/workflows/monitor.yml`. Ele está em UTC, que é o horário de Brasília + 3 h.

## 8. Onde ficam os dados

Cada execução grava arquivos **novos e pequenos** em `dados/` (nunca reescreve os antigos). Assim o git guarda só o que mudou e o repositório cresce devagar: ~15 MB por mês, quase tudo do painel diário. O limite recomendado pelo GitHub é 1 GB.

> O robô faz commits em `dados/` a cada execução. Se você editar o projeto no seu computador, rode `git pull` antes de fazer `push`.

```
dados/
├── precos/AAAA/MM/<execução>.parquet    menor preço por rota, sentido e data do voo
├── ofertas/AAAA/MM/<execução>.parquet   menor preço de CADA companhia por data
├── alertas/AAAA/MM/<execução>.parquet   o que foi enviado no Telegram (evita repetir)
├── execucoes.csv                         1 linha por execução: modo, falhas, melhor preço, duração
└── ultimo/                               painel e tabela da última varredura completa
    ├── painel_0.png
    └── melhor_ida_volta_por_data_0.csv
```

- **Ver rápido, no navegador:** abra `dados/ultimo/painel_0.png` ou `dados/execucoes.csv`. O GitHub mostra CSV como tabela.
- **Analisar:** clone o repositório (ou faça `git pull`) e consulte direto com pandas ou DuckDB:

```python
import duckdb
duckdb.sql("""
    select data_voo, min(preco) as menor, count(distinct data_busca) as buscas
    from 'dados/precos/**/*.parquet'
    where sentido = 'ida'
    group by 1 order by 1
""").df()
```

- **Por companhia:** `dados/ofertas` permite comparar LATAM × GOL × Azul por data, ver qual cia lidera em cada mês, etc.

Os arquivos são públicos num repositório público, mas só contêm datas, aeroportos, companhias e preços.

## 9. Problemas comuns

**O workflow não aparece na aba Actions.**
- Confira se existe o arquivo `.github/workflows/monitor.yml` na raiz do repositório. O nome da pasta é `.github`, com ponto, e `workflows` vai no plural. Esta é a causa mais comum quando o envio foi pelo navegador; veja o [passo 1](#1-copiar-o-projeto-para-a-sua-conta).
- O arquivo precisa estar na branch padrão (`main`).
- Em fork, abra a aba Actions e clique para habilitar os workflows.
- Em **Settings → Actions → General**, verifique se *Allow all actions* está marcado.
- Se o workflow aparece mas o botão **Run workflow** não, o YAML pode ter erro de indentação. Cole o arquivo de novo.

**`[ERRO TELEGRAM destinatário 1] HTTP 400 chat not found`:** essa pessoa não iniciou conversa com o bot, ou o id está errado.

**`HTTP 401 Unauthorized`:** o token está errado ou foi revogado. Atualize o Secret `TELEGRAM_TOKEN`.

**O passo "Guardar histórico" falhou com `Permission denied` / `403`:** falta liberar a escrita em **Settings → Actions → General → Workflow permissions → Read and write permissions**.

**"Monitor com problema: X de Y consultas falharam":** o Google pode estar limitando as consultas. Reduza `WORKERS` ou aumente `PAUSA_SEG` na célula 2.

**Os horários agendados não rodam:** o GitHub pode atrasar ou pular execuções em horários de pico. Plano B: uma tarefa grátis no cron-job.org que chama

```
POST https://api.github.com/repos/<usuario>/<repo>/actions/workflows/monitor.yml/dispatches
Authorization: Bearer <token fine-grained só deste repositório, permissão "Actions: Read and write">
Body: {"ref":"main"}
```

## 10. Segurança

- Nunca escreva token ou ids em células do notebook, nem "só para testar".
- Se algo secreto entrou num commit, apagar o arquivo não basta: o histórico do git guarda. **Revogue e troque** a credencial.
- O workflow mascara os ids nos logs e apaga os segredos do notebook executado antes de anexá-lo. Em caso de erro, o notebook mostra só "destinatário 1/2".
- Mantenha ligado **Settings → Code security → Secret scanning / Push protection**.
- Pull requests vindos de forks não recebem os Secrets. Não troque o gatilho para `pull_request_target`.

---

### Teste local, sem internet

```
pip install -r requirements.txt
FONTE=simulada DRY_RUN=1 PASTA_DADOS=/tmp/dados_teste jupyter nbconvert --to notebook --execute monitor_voos_v4.ipynb --output teste.ipynb
```

### Fontes de preço

| Fonte | Como acessa | Observação |
|---|---|---|
| **fli** (principal) | Google Flights, todos os aeroportos numa consulta | traz o link do voo exato |
| **fast-flights** (reserva) | Google Flights | usada se a fli falhar |
| **Travelpayouts / Aviasales** (opcional) | API grátis, 1 chamada = mês inteiro | preços em cache, marcados "confirme" |
