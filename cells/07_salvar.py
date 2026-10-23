# CÉLULA 7 — SALVA OS PREÇOS DESTA EXECUÇÃO NO HISTÓRICO
# (antes dos alertas: se o Telegram falhar, o histórico já está garantido)
hist.gravar_precos(df_atual)
hist.gravar_ofertas(df_ofertas)
df_hist = pd.concat([df for df in (df_hist, df_atual[COLS_PRECOS]) if not df.empty], ignore_index=True)
df_hist["data_busca"] = pd.to_datetime(df_hist["data_busca"], utc=True).dt.tz_convert(TZ)
for c in ("preco", "escalas", "duracao_min"):
    df_hist[c] = pd.to_numeric(df_hist[c], errors="coerce")
print(f"Histórico agora com {len(df_hist)} linhas.")
