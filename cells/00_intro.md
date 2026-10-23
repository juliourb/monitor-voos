# Monitor de Voos — v4 (calendário de 6 meses, teto de R$ 1.000)

**O que mudou em relação à v3**

| v3 | v4 |
|---|---|
| Datas fixas (28/10 a 05/11) | Varre **todas as datas de hoje até +180 dias** |
| Só `fast-flights`, 1 consulta por par de aeroportos | **`fli`** (Google Flights) com **multi-aeroporto numa só consulta** + `fast-flights` como reserva + **Aviasales/Travelpayouts** (opcional, gratuito) como radar |
| Alerta repetia o mesmo voo a cada execução | Alerta **só quando é novo ou quando o preço caiu** de novo |
| Mensagem curta, sem contexto | Mensagem com **dia da semana, horários, escalas, duração, folga até o teto, comparação com o histórico e o porquê do alerta** |
| Gráfico de "evolução" misturava viagens diferentes | Gráficos separam **data do voo** × **data da busca** (cada linha = um mês de viagem) |
| Token do Telegram escrito no código | Segredos lidos de **variáveis de ambiente / Kaggle Secrets / GitHub Secrets** |
| Só Kaggle, 1×/dia | Roda em Kaggle **ou** GitHub Actions (várias vezes ao dia) |

**Como funciona**

1. Para cada rota, consulta o voo **só ida** mais barato de cada data, nos dois sentidos (Alagoas/Sergipe → São Paulo e São Paulo → Alagoas/Sergipe).
2. Combina qualquer ida com qualquer volta que respeite a permanência mínima/máxima → acha a melhor **ida + volta** para cada data de saída (podendo ser cias e aeroportos diferentes).
3. Alerta no Telegram quando `preço da ida + preço da volta ≤ teto` (padrão R$ 1.000, estadia de 5 a 7 dias).
4. Grava o histórico (Google Sheets ou CSV) e gera um painel.

**Modos de execução**
- `completo`: varre os 180 dias (≈ 360 consultas por rota). Roda 1×/dia.
- `rapido`: reconsulta só as datas mais baratas da última varredura completa + os próximos 14 dias (≈ 60 consultas). Ideal para rodar a cada poucas horas sem chamar atenção do Google.
- `auto` (padrão): decide sozinho — `completo` se a última varredura completa tem mais de 20 h, senão `rapido`.

**Segredos necessários** (Kaggle → *Add-ons → Secrets*; GitHub → *Settings → Secrets and variables → Actions*)

| Nome | Obrigatório | Conteúdo |
|---|---|---|
| `TELEGRAM_TOKEN` | sim | token do bot (BotFather) |
| `TELEGRAM_CHAT_IDS` | sim | ids separados por vírgula, ex.: `111111111,222222222` (os seus ficam só no segredo) |
| `GOOGLE_SHEETS_CREDS` | não | JSON da service account (se quiser histórico no Sheets) |
| `URL_PLANILHA` | não | link da planilha do histórico (junto com o segredo acima) |
| `TRAVELPAYOUTS_TOKEN` | não | token gratuito do Travelpayouts (ativa a 2ª fonte) |
