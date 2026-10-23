# CÉLULA 8 — MONTA AS MELHORES IDA+VOLTA E O CONTEXTO DE CADA OFERTA

def tabela_vigente(rota_nome, ate=None, janela_h=30):
    """Preço mais recente de cada (sentido, data do voo), usando buscas das últimas `janela_h` horas.
    No modo rápido, as datas não reconsultadas usam o preço da última varredura completa."""
    ate = ate or AGORA
    h = df_hist[(df_hist["rota"] == rota_nome) & (df_hist["data_busca"] <= ate) &
                (df_hist["data_busca"] > ate - timedelta(hours=janela_h))].copy()
    if h.empty:
        return h
    h = h[h["data_voo"] > pd.Timestamp(ate).date()]
    h = (h.sort_values("data_busca").drop_duplicates(["sentido", "data_voo", "fonte"], keep="last")
          .sort_values("preco").drop_duplicates(["sentido", "data_voo"], keep="first"))
    h["idade_h"] = (ate - h["data_busca"]).dt.total_seconds() / 3600
    return h.reset_index(drop=True)


def combinar(tab, rota):
    """Todas as combinações ida × volta válidas → a melhor volta para cada data de ida."""
    ida, volta = tab[tab["sentido"] == "ida"], tab[tab["sentido"] == "volta"]
    if ida.empty or volta.empty:
        return pd.DataFrame()
    m = ida.add_suffix("_ida").merge(volta.add_suffix("_volta"), how="cross")
    m["noites"] = (pd.to_datetime(m["data_voo_volta"]) - pd.to_datetime(m["data_voo_ida"])).dt.days
    m = m[m["noites"].between(rota["min_noites"], rota["max_noites"])]
    if not PERMITIR_AEROPORTOS_DIFERENTES:
        m = m[(m["destino_ida"] == m["origem_volta"]) & (m["origem_ida"] == m["destino_volta"])]
    m["total"] = m["preco_ida"] + m["preco_volta"]
    m = m.sort_values("total").drop_duplicates("data_voo_ida").sort_values("data_voo_ida")
    return m.reset_index(drop=True)


def contexto_trecho(rota_nome, sentido, d, preco_agora):
    """Compara o preço de hoje com o histórico da MESMA data de voo."""
    h = df_hist[(df_hist["rota"] == rota_nome) & (df_hist["sentido"] == sentido) &
                (df_hist["data_voo"] == d) & (df_hist["data_busca"] < AGORA)]
    if h.empty:
        return dict(min_ant=None, quando_min=None, primeira_vez=True, var_24h=None)
    i = h["preco"].idxmin()
    ontem = h[h["data_busca"] <= AGORA - timedelta(hours=20)]
    ref = ontem.sort_values("data_busca")["preco"].iloc[-1] if not ontem.empty else None
    return dict(min_ant=h.loc[i, "preco"], quando_min=h.loc[i, "data_busca"], primeira_vez=False,
                var_24h=None if ref is None else preco_agora - ref)


tabelas, combos, ofertas_teto, trechos_teto = {}, {}, {}, {}
for rota in ROTAS:
    nome = rota["nome"]
    tab = tabela_vigente(nome)
    tabelas[nome] = tab
    cb = combinar(tab, rota)
    combos[nome] = cb
    if cb.empty:
        print(f"{nome}: sem combinações válidas.")
        continue
    tipico = cb["total"].median()
    abaixo = cb[cb["total"] <= rota["teto_ida_volta"]].copy()
    abaixo["tipico"] = tipico
    abaixo["ctx_ida"] = [contexto_trecho(nome, "ida", r.data_voo_ida, r.preco_ida) for r in abaixo.itertuples()]
    abaixo["ctx_volta"] = [contexto_trecho(nome, "volta", r.data_voo_volta, r.preco_volta) for r in abaixo.itertuples()]
    ofertas_teto[nome] = abaixo.sort_values("total")
    if rota.get("teto_trecho"):
        trechos_teto[nome] = tab[tab["preco"] <= rota["teto_trecho"]].sort_values("preco")
    print(f"{nome}: {len(cb)} datas de ida com volta possível · melhor {brl(cb['total'].min())} · "
          f"mediana {brl(tipico)} · {len(abaixo)} abaixo do teto de {brl(rota['teto_ida_volta'])}")

if ofertas_teto:
    nome0 = next(iter(ofertas_teto))
    cols = ["data_voo_ida", "data_voo_volta", "noites", "origem_ida", "destino_ida", "origem_volta",
            "destino_volta", "cia_ida", "cia_volta", "preco_ida", "preco_volta", "total"]
    display(ofertas_teto[nome0][cols].head(10)) if len(ofertas_teto[nome0]) else None
