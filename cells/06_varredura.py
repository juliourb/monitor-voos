# CÉLULA 6 — VARREDURA (decide o modo, escolhe a fonte e consulta as datas)

def ultima_completa(rota_nome):
    if df_hist.empty:
        return None
    h = df_hist[(df_hist["rota"] == rota_nome) & (df_hist["modo"] == "completo")]
    return None if h.empty else h["data_busca"].max()


def decidir_modo(rota_nome):
    if MODO in ("completo", "rapido"):
        return MODO if (MODO == "completo" or ultima_completa(rota_nome) is not None) else "completo"
    t = ultima_completa(rota_nome)
    if t is None or (AGORA - t) > timedelta(hours=HORAS_ENTRE_COMPLETAS):
        return "completo"
    return "rapido"


def datas_para(rota_nome, sentido, modo, extra=0):
    todas = datas_horizonte(extra if sentido == "volta" else 0)
    if modo == "completo":
        return todas
    t = ultima_completa(rota_nome)
    h = df_hist[(df_hist["rota"] == rota_nome) & (df_hist["sentido"] == sentido) &
                (df_hist["data_busca"] == t) & (df_hist["data_voo"] >= todas[0])]
    baratas = set(h.nsmallest(TOP_DATAS_RAPIDO, "preco")["data_voo"])
    proximas = set(todas[:DIAS_PROXIMOS_RAPIDO])
    return sorted(baratas | proximas)


ofertas_execucao, estatisticas, modos = [], {}, {}
for rota in ROTAS:
    nome = rota["nome"]
    modo = decidir_modo(nome)
    modos[nome] = modo
    print(f"\n=== {nome} · modo {modo} ===")
    fonte = escolher_fonte(rota)
    for sentido in ("ida", "volta"):
        datas = datas_para(nome, sentido, modo, extra=rota["max_noites"])
        if not datas:
            estatisticas[(nome, sentido)] = {"consultas": 0, "sem_voo": 0, "falhas": 0, "erros": [], "extras": [], "fonte": fonte}
            continue
        print(f"{sentido}: {len(datas)} datas ({fmt_data(datas[0], False)} a {fmt_data(datas[-1], False)})")
        ofs, st = varrer(rota, sentido, datas, fonte)
        st["fonte"] = fonte
        if modo == "completo":
            meses = sorted({d.strftime("%Y-%m") for d in datas})
            radar = buscar_aviasales(rota, sentido, meses)
            st["aviasales"] = len(radar)
            ofs += radar
        estatisticas[(nome, sentido)] = st
        ofertas_execucao += ofs

df_atual = pd.DataFrame([asdict(o) for o in ofertas_execucao])
if df_atual.empty:
    df_atual = pd.DataFrame(columns=COLS_PRECOS)
df_atual["data_busca"] = AGORA
df_atual["modo"] = df_atual["rota"].map(modos)
df_atual["data_voo"] = pd.to_datetime(df_atual["data_voo"]).dt.date

# dado extra: a opção mais barata de cada companhia, em cada data consultada
df_ofertas = pd.DataFrame([e for st in estatisticas.values() for e in st["extras"]])
df_ofertas["data_busca"] = AGORA

print(f"\n{len(df_atual)} preços coletados nesta execução · {len(df_ofertas)} opções por companhia.")
for (r, s), st in estatisticas.items():
    print(f"  {r} / {s}: {st['consultas']} consultas · {st['sem_voo']} sem voo · {st['falhas']} falhas"
          + (f" · {st.get('aviasales', 0)} datas do Aviasales" if 'aviasales' in st else ""))
