# CÉLULA 10 — MENSAGENS NO TELEGRAM
import html

TG_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
NOME_MODO = {"completo": "varredura completa", "rapido": "checagem rápida"}


def _tg_post(metodo, n, **kw):
    """Chama a API do Telegram sem nunca imprimir o token nem o chat id (o repositório é público).
    Erros mostram só o nº do destinatário (1º, 2º...) e o código HTTP."""
    try:
        r = requests.post(f"{TG_API}/{metodo}", timeout=60, **kw)
        if r.status_code == 200:
            return True
            desc = r.json().get("description", "") if r.headers.get("content-type", "").startswith("application/json") else ""
            print(f"[ERRO TELEGRAM destinatário {n}] HTTP {r.status_code} {desc[:120]}")
    except Exception as e:                      # a mensagem da exceção contém a URL com o token
        print(f"[ERRO TELEGRAM destinatário {n}] {type(e).__name__} (detalhes ocultos)")
    return False


def tg_texto(texto):
    if DRY_RUN or not TELEGRAM_TOKEN or not TELEGRAM_CHAT_IDS:
        print("—" * 60 + "\n[TELEGRAM — não enviado]\n" + texto + "\n" + "—" * 60)
        return False
    partes, atual = [], ""
    for bloco in texto.split("\n\n"):            # respeita o limite de 4096 caracteres
        if len(atual) + len(bloco) + 2 > 3900:
            partes.append(atual); atual = ""
        atual += ("\n\n" if atual else "") + bloco
    partes.append(atual)
    algum_ok = False
    for n, cid in enumerate(TELEGRAM_CHAT_IDS, 1):
        for p in partes:
            algum_ok |= _tg_post("sendMessage", n, data=dict(chat_id=cid, text=p, parse_mode="HTML",
                                                              disable_web_page_preview=True))
    return algum_ok


def tg_foto(caminho, legenda):
    if DRY_RUN or not TELEGRAM_TOKEN or not TELEGRAM_CHAT_IDS:
        print(f"[TELEGRAM foto — não enviada] {caminho}: {legenda}")
        return
    for n, cid in enumerate(TELEGRAM_CHAT_IDS, 1):
        with open(caminho, "rb") as f:
            _tg_post("sendPhoto", n, files={"photo": f},
                     data=dict(chat_id=cid, caption=legenda[:1000], parse_mode="HTML"))


def linha_trecho(rotulo, emoji, d, o, x, cia, partida, chegada, escalas, dur, preco, fonte, link, idade_h):
    extra = " <i>(cache Aviasales — confirme)</i>" if fonte == "aviasales" else ""
    if idade_h and idade_h > 2:
        extra += f" <i>(preço de {idade_h:.0f} h atrás)</i>"
    return (f"{emoji} <b>{rotulo}</b> {fmt_data(d)} · {o}→{x} · {html.escape(str(cia))}\n"
            f"     {partida}→{chegada} · {fmt_escalas(escalas)} · {fmt_dur(dur)} · <b>{brl(preco)}</b>{extra}\n"
            f"     <a href=\"{html.escape(link, quote=True)}\">abrir este voo</a>")


def motivos_oferta(r, rota):
    m = [f"cabe no teto com folga de {brl(rota['teto_ida_volta'] - r.total)}"]
    pct = r.total / r.tipico - 1
    if pct <= -0.05:
        m.append(f"{abs(pct):.0%} abaixo da mediana das próximas datas ({brl(r.tipico)})")
    for rot, ctx, preco, d in (("ida", r.ctx_ida, r.preco_ida, r.data_voo_ida),
                               ("volta", r.ctx_volta, r.preco_volta, r.data_voo_volta)):
        if ctx["min_ant"] is not None and preco < ctx["min_ant"]:
            m.append(f"{rot} no menor preço já visto para {fmt_data(d, False)} (antes {brl(ctx['min_ant'])})")
        elif ctx["var_24h"] is not None and abs(ctx["var_24h"]) >= 10:
            verbo = "caiu" if ctx["var_24h"] < 0 else "subiu"
            m.append(f"{rot} {verbo} {brl(abs(ctx['var_24h']))} desde ontem")
    return m


def bloco_oferta(k, r, rota):
    avisos = []
    if r.destino_ida != r.origem_volta:
        avisos.append(f"chega em {r.destino_ida} e volta saindo de {r.origem_volta}")
    if r.origem_ida != r.destino_volta:
        avisos.append(f"sai de {r.origem_ida} e retorna para {r.destino_volta}")
    if r.cia_ida != r.cia_volta:
        avisos.append("cias diferentes = 2 reservas separadas")
    txt = (f"<b>{k}) {brl(r.total)} ida+volta</b> · {int(r.noites)} noites "
           f"({fmt_data(r.data_voo_ida)} → {fmt_data(r.data_voo_volta)}) · {(r.data_voo_ida - HOJE).days} dias até a viagem\n"
           + linha_trecho("Ida", "🛫", r.data_voo_ida, r.origem_ida, r.destino_ida, r.cia_ida, r.partida_ida,
                          r.chegada_ida, r.escalas_ida, r.duracao_min_ida, r.preco_ida, r.fonte_ida, r.link_ida, r.idade_h_ida) + "\n"
           + linha_trecho("Volta", "🛬", r.data_voo_volta, r.origem_volta, r.destino_volta, r.cia_volta, r.partida_volta,
                          r.chegada_volta, r.escalas_volta, r.duracao_min_volta, r.preco_volta, r.fonte_volta, r.link_volta, r.idade_h_volta)
           + "\n💡 <i>Por que avisei:</i> " + "; ".join(motivos_oferta(r, rota)) + ".")
    if avisos:
        txt += "\n⚠️ " + "; ".join(avisos) + "."
    return txt


RODAPE = ("<i>Preços para 1 adulto, econômica, só bagagem de mão. Ida e volta são compradas separadamente "
          "(por isso podem ser de cias diferentes). O preço muda rápido: confira no link antes de pagar.</i>")


def filtrar_novas(nome, df):
    """Remove viagens já alertadas, a não ser que o preço tenha caído pelo menos QUEDA_MIN_PARA_REALERTAR."""
    ant = df_alertas_ant[df_alertas_ant["rota"] == nome]
    ultimo = ant.groupby(["data_ida", "data_volta"])["total"].min().to_dict() if not ant.empty else {}
    novas = []
    for r in df.itertuples():
        prev = ultimo.get((str(r.data_voo_ida), str(r.data_voo_volta)))
        if prev is None or r.total <= prev * (1 - QUEDA_MIN_PARA_REALERTAR):
            novas.append(r)
    return novas


registro_alertas = []
for rota in ROTAS:
    nome = rota["nome"]
    est = [estatisticas[(nome, s)] for s in ("ida", "volta")]
    n_consultas = sum(e["consultas"] for e in est)
    n_falhas = sum(e["falhas"] for e in est)
    cab = (f"<i>{NOME_MODO[modos[nome]]} · {AGORA:%d/%m %H:%M} · {n_consultas} datas consultadas "
           f"via {est[0]['fonte']}</i>")

    # 1) Saúde: muitas falhas = provável bloqueio
    if n_consultas and n_falhas / n_consultas > 0.5:
        erros = pd.Series(sum((e["erros"] for e in est), [])).value_counts().head(2)
        tg_texto(f"⚠️ <b>Monitor com problema — {nome}</b>\n{cab}\n{n_falhas} de {n_consultas} consultas falharam. "
                 f"Erros mais comuns:\n<code>{html.escape(chr(10).join(erros.index))}</code>\n"
                 "Se repetir, o Google pode estar bloqueando o IP: aumente PAUSA_SEG ou reduza WORKERS.")

    # 2) Ofertas abaixo do teto (só as novas ou que baratearam)
    df_of = ofertas_teto.get(nome, pd.DataFrame())
    novas = filtrar_novas(nome, df_of) if len(df_of) else []
    if novas:
        msg = [f"✈️ <b>{len(novas)} ida+volta até {brl(rota['teto_ida_volta'])} — {nome}</b>\n{cab}"]
        for k, r in enumerate(novas[:MAX_OFERTAS_POR_MSG], 1):
            msg.append(bloco_oferta(k, r, rota))
        if len(novas) > MAX_OFERTAS_POR_MSG:
            resto = [fmt_data(d, False) for d in sorted({r.data_voo_ida for r in novas[MAX_OFERTAS_POR_MSG:]})]
            msg.append(f"…e mais {len(novas) - MAX_OFERTAS_POR_MSG} datas de saída abaixo do teto: {', '.join(resto[:15])}.")
        msg.append(RODAPE)
        enviado = tg_texto("\n\n".join(msg))
        if enviado:   # só marca como alertado se chegou a pelo menos um destinatário
            registro_alertas += [dict(enviado_em=AGORA.isoformat(), rota=nome, data_ida=str(r.data_voo_ida),
                                      data_volta=str(r.data_voo_volta), total=r.total) for r in novas]
    else:
        print(f"{nome}: nenhuma oferta nova abaixo do teto.")

    # 3) Trechos avulsos (se teto_trecho estiver ligado)
    tt = trechos_teto.get(nome)
    if tt is not None and len(tt):
        linhas = [f"🎯 <b>Trechos só ida até {brl(rota['teto_trecho'])} — {nome}</b>"]
        for r in tt.head(MAX_OFERTAS_POR_MSG).itertuples():
            linhas.append(linha_trecho(r.sentido.capitalize(), "🛫" if r.sentido == "ida" else "🛬", r.data_voo,
                                       r.origem, r.destino, r.cia, r.partida, r.chegada, r.escalas,
                                       r.duracao_min, r.preco, r.fonte, r.link, r.idade_h))
        tg_texto("\n\n".join(linhas))

    # 4) Resumo diário + painel (só depois da varredura completa)
    cb = combos[nome]
    if ENVIAR_RESUMO_DIARIO and modos[nome] == "completo" and not cb.empty:
        teto = rota["teto_ida_volta"]
        j = cb["total"].idxmin()
        cb2 = cb.assign(mes=pd.to_datetime(cb["data_voo_ida"]).dt.to_period("M"))
        tabela = ["Mês     Melhor     Saída  Volta", "─" * 32]
        for mes, g in cb2.groupby("mes"):
            m = g.loc[g["total"].idxmin()]
            marca = " ✓" if m["total"] <= teto else ""
            tabela.append(f"{MESES[mes.month - 1]}/{str(mes.year)[2:]}  {brl(m['total']):>9}  "
                          f"{fmt_data(m['data_voo_ida'], False)}  {fmt_data(m['data_voo_volta'], False)}{marca}")
        ev = evolucao_por_mes(rota)
        tendencia = ""
        if not ev.empty and ev["dia"].nunique() >= 2:
            por_dia = ev.groupby("dia")["total"].min().sort_index()
            dif = por_dia.iloc[-1] - por_dia.iloc[-2]
            tendencia = (f"\n📈 Em relação à busca anterior ({por_dia.index[-2]:%d/%m}): melhor total "
                         + ("estável" if abs(dif) < 10 else f"{'caiu' if dif < 0 else 'subiu'} {brl(abs(dif))}") + ".")
        tab = tabelas[nome]
        ida_min = tab[tab["sentido"] == "ida"].nsmallest(1, "preco")
        vol_min = tab[tab["sentido"] == "volta"].nsmallest(1, "preco")
        resumo = (f"📊 <b>Resumo diário — {nome}</b>\n{cab}\n\n"
                  f"Melhor ida+volta: <b>{brl(cb.loc[j, 'total'])}</b> ({fmt_data(cb.loc[j, 'data_voo_ida'])} → "
                  f"{fmt_data(cb.loc[j, 'data_voo_volta'])}, {int(cb.loc[j, 'noites'])} noites) — "
                  + (f"{brl(teto - cb.loc[j, 'total'])} abaixo do teto." if cb.loc[j, 'total'] <= teto
                     else f"{brl(cb.loc[j, 'total'] - teto)} acima do teto.")
                  + f"\nDatas de saída dentro do teto: <b>{int((cb['total'] <= teto).sum())}</b> de {len(cb)}."
                  + (f"\nIda mais barata: {brl(ida_min['preco'].iloc[0])} em {fmt_data(ida_min['data_voo'].iloc[0])} "
                     f"({ida_min['cia'].iloc[0]})" if len(ida_min) else "")
                  + (f"\nVolta mais barata: {brl(vol_min['preco'].iloc[0])} em {fmt_data(vol_min['data_voo'].iloc[0])} "
                     f"({vol_min['cia'].iloc[0]})" if len(vol_min) else "")
                  + tendencia
                  + "\n\n<b>Melhor ida+volta por mês de saída</b> (✓ = dentro do teto)\n<pre>"
                  + html.escape("\n".join(tabela)) + "</pre>")
        tg_texto(resumo)
        if nome in paineis:
            tg_foto(paineis[nome], f"📊 Painel — {html.escape(nome)} · {AGORA:%d/%m %H:%M}\n"
                                    "A: preço por dia do voo · B: ida+volta vs teto · C: tendência por mês da viagem")

if not DRY_RUN:   # em teste não marca como enviado, para o alerta real ainda sair
    hist.gravar_alertas(pd.DataFrame(registro_alertas, columns=COLS_ALERTAS))
print(f"\n{len(registro_alertas)} oferta(s) alertada(s) nesta execução. [CONCLUÍDO]")
