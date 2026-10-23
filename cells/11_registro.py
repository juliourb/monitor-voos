# CÉLULA 11 — REGISTRO DA EXECUÇÃO E "ÚLTIMO RESULTADO"
# execucoes.csv: 1 linha por execução e rota (bom para ver no GitHub se o robô está saudável).
# dados/ultimo/: painel e tabela da última varredura completa, para abrir direto no GitHub.
for rota in ROTAS:
    nome = rota["nome"]
    est = [estatisticas.get((nome, s), {}) for s in ("ida", "volta")]
    cb = combos.get(nome, pd.DataFrame())
    hist.registrar_execucao(dict(
        data_busca=AGORA.isoformat(timespec="seconds"),
        rota=nome,
        modo=modos.get(nome),
        fonte=est[0].get("fonte"),
        consultas=sum(e.get("consultas", 0) for e in est),
        sem_voo=sum(e.get("sem_voo", 0) for e in est),
        falhas=sum(e.get("falhas", 0) for e in est),
        melhor_ida_volta=None if cb.empty else round(float(cb["total"].min()), 2),
        datas_no_teto=0 if cb.empty else int((cb["total"] <= rota["teto_ida_volta"]).sum()),
        alertas_enviados=sum(1 for a in registro_alertas if a["rota"] == nome),
        dry_run=DRY_RUN,
        duracao_seg=round((datetime.now(TZ) - AGORA).total_seconds()),
    ))
    if modos.get(nome) == "completo" and not cb.empty:
        i = ROTAS.index(rota)
        cols = ["data_voo_ida", "data_voo_volta", "noites", "total", "preco_ida", "preco_volta",
                "origem_ida", "destino_ida", "cia_ida", "partida_ida", "origem_volta", "destino_volta",
                "cia_volta", "partida_volta", "link_ida", "link_volta"]
        hist.salvar_ultimo(f"melhor_ida_volta_por_data_{i}.csv", conteudo_df=cb[cols])
        if nome in paineis:
            hist.salvar_ultimo(f"painel_{i}.png", arquivo_origem=paineis[nome])

print(f"Execução {ID_EXECUCAO} registrada em {PASTA_DADOS}/execucoes.csv. [CONCLUÍDO]")
