## Notas e limites

- **Custo de consultas:** a varredura completa faz ~1 consulta por data e sentido (≈ 360 por rota). O modo rápido faz ≈ 60. Se o Google começar a devolver páginas vazias, o notebook manda um aviso de “Monitor com problema” no Telegram — aí aumente `PAUSA_SEG` ou reduza `WORKERS`.
- **Ida e volta separadas:** o preço é a soma de dois bilhetes só ida. Quase sempre é igual ou mais barato que ida+volta fechado no mercado doméstico, mas são duas reservas.
- **Aviasales é cache:** preços dessa fonte vêm da busca de outros usuários nas últimas ~48 h; aparecem marcados como “confirme”.
- **Bagagem:** os preços são da tarifa mais barata (normalmente só bagagem de mão).
- **Testar sem internet:** rode com `FONTE="simulada"` e `DRY_RUN=1` — as mensagens aparecem impressas aqui em vez de ir para o Telegram.
