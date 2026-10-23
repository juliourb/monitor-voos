# CÉLULA 9 — PAINEL (3 gráficos, um por pergunta)
#  A) "Qual dia está mais barato?"          → preço só ida por DATA DO VOO (busca de agora)
#  B) "Qual ida+volta passa no teto?"       → melhor ida+volta por DATA DE SAÍDA, com a linha do teto
#  C) "Os preços estão caindo ou subindo?"  → menor ida+volta por MÊS DA VIAGEM ao longo das BUSCAS
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter

COR_IDA, COR_VOLTA, COR_BOA, COR_TETO = "#2a78d6", "#eb6834", "#008300", "#52514e"
SERIES_MES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
FMT_BRL = FuncFormatter(lambda v, _: brl(v))
plt.rcParams.update({"figure.dpi": 110, "font.size": 10, "axes.titlesize": 12, "axes.titleweight": "bold",
                     "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
                     "grid.color": "#e6e5e0", "grid.linewidth": 0.8, "axes.edgecolor": "#8a8984"})


def _eixo_datas(ax):
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_minor_locator(mdates.WeekdayLocator(byweekday=mdates.MO))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{MESES[mdates.num2date(v).month - 1]}/{mdates.num2date(v):%y}"))
    ax.yaxis.set_major_formatter(FMT_BRL)


def evolucao_por_mes(rota):
    """Para cada dia de busca: menor ida+volta por mês de saída (só com dados daquele dia)."""
    nome = rota["nome"]
    h = df_hist[df_hist["rota"] == nome]
    if h.empty:
        return pd.DataFrame()
    linhas = []
    for dia in sorted(h["data_busca"].dt.date.unique())[-45:]:
        fim = datetime.combine(dia, datetime.max.time(), TZ)
        cb = combinar(tabela_vigente(nome, ate=min(fim, AGORA), janela_h=30), rota)
        if cb.empty:
            continue
        cb["mes"] = pd.to_datetime(cb["data_voo_ida"]).dt.to_period("M")
        for mes, g in cb.groupby("mes"):
            linhas.append(dict(dia=pd.Timestamp(dia), mes=mes, total=g["total"].min()))
    return pd.DataFrame(linhas)


def desenhar_painel(rota, arquivo):
    nome, teto = rota["nome"], rota["teto_ida_volta"]
    tab, cb = tabelas[nome], combos[nome]
    fig, axs = plt.subplots(3, 1, figsize=(12, 13), constrained_layout=True,
                            gridspec_kw={"height_ratios": [1, 1, 0.9]})
    fig.suptitle(f"{nome} — busca de {AGORA:%d/%m/%Y %H:%M} · 1 adulto, econômica",
                 fontsize=14, fontweight="bold")

    # A) preço só ida por data de voo
    ax = axs[0]
    for sentido, cor, rot in (("ida", COR_IDA, f"Ida ({'/'.join(rota['origens'])} → {'/'.join(rota['destinos'])})"),
                              ("volta", COR_VOLTA, f"Volta ({'/'.join(rota['destinos'])} → {'/'.join(rota['origens'])})")):
        s = tab[tab["sentido"] == sentido].sort_values("data_voo")
        if s.empty:
            continue
        x = pd.to_datetime(s["data_voo"])
        i = s["preco"].idxmin()
        rot += f" — mín. {brl(s.loc[i, 'preco'])} em {fmt_data(s.loc[i, 'data_voo'])}"
        ax.plot(x, s["preco"], color=cor, lw=1.6, label=rot)
        ax.scatter(pd.to_datetime(s.loc[i, "data_voo"]), s.loc[i, "preco"], s=70, color=cor,
                   edgecolor="white", lw=2, zorder=3)
    if rota.get("teto_trecho"):
        ax.axhline(rota["teto_trecho"], ls="--", color=COR_TETO, lw=1.2)
        ax.text(1, rota["teto_trecho"], f" teto por trecho {brl(rota['teto_trecho'])}", transform=ax.get_yaxis_transform(),
                va="bottom", ha="right", fontsize=9, color=COR_TETO)
    ax.set_title("A · Preço do trecho só ida, por data do voo")
    ax.set_ylabel("Preço do trecho")
    ax.legend(loc="upper left", frameon=False)
    _eixo_datas(ax)

    # B) melhor ida+volta por data de saída
    ax = axs[1]
    if not cb.empty:
        x = pd.to_datetime(cb["data_voo_ida"])
        j = cb["total"].idxmin()
        ax.plot(x, cb["total"], color=COR_IDA, lw=1.6,
                label=(f"Melhor ida+volta saindo neste dia — melhor de todos: {brl(cb.loc[j, 'total'])} "
                       f"({fmt_data(cb.loc[j, 'data_voo_ida'])} → {fmt_data(cb.loc[j, 'data_voo_volta'])}, "
                       f"{int(cb.loc[j, 'noites'])} noites)"))
        ok = cb["total"] <= teto
        ax.scatter(x[ok], cb.loc[ok, "total"], s=40, color=COR_BOA, edgecolor="white", lw=1.5, zorder=3,
                   label=f"✓ dentro do teto ({ok.sum()} de {len(cb)} datas)")
    ax.axhline(teto, ls="--", color=COR_TETO, lw=1.2)
    ax.text(1, teto, f" teto {brl(teto)}", transform=ax.get_yaxis_transform(), va="bottom", ha="right",
            fontsize=9, color=COR_TETO)
    ax.set_title(f"B · Melhor ida+volta por data de saída ({rota['min_noites']} a {rota['max_noites']} noites)")
    ax.set_ylabel("Total ida+volta")
    ax.legend(loc="upper left", frameon=False)
    _eixo_datas(ax)

    # C) evolução ao longo das buscas
    ax = axs[2]
    ev = evolucao_por_mes(rota)
    if ev.empty or ev["dia"].nunique() < 2:
        ax.text(0.5, 0.5, "A evolução aparece a partir da 2ª busca em dias diferentes.",
                ha="center", va="center", transform=ax.transAxes, color="#52514e", fontsize=11)
        ax.set_xticks([]); ax.set_yticks([])
    else:
        for k, (mes, g) in enumerate(ev.groupby("mes")):
            g = g.sort_values("dia")
            cor = SERIES_MES[k % len(SERIES_MES)]
            rot = f"{MESES[mes.month - 1]}/{str(mes.year)[2:]} — hoje {brl(g['total'].iloc[-1])}"
            ax.plot(g["dia"], g["total"], color=cor, lw=2, marker="o", ms=4, label=rot)
        ax.axhline(teto, ls="--", color=COR_TETO, lw=1.2)
        ax.text(1, teto, f" teto {brl(teto)}", transform=ax.get_yaxis_transform(), va="bottom", ha="right",
                fontsize=9, color=COR_TETO)
        n_dias = ev["dia"].nunique()
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, n_dias // 8)))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))
        ax.yaxis.set_major_formatter(FMT_BRL)
        ax.legend(loc="upper left", bbox_to_anchor=(1.0, 1.0), frameon=False, title="Saída em")
    ax.set_title("C · Menor ida+volta encontrado em cada dia de busca, por mês da viagem")
    ax.set_xlabel("Dia em que a busca foi feita")
    ax.set_ylabel("Menor ida+volta")

    fig.savefig(arquivo, dpi=110, bbox_inches="tight")
    plt.show()
    return arquivo


paineis = {}
for i, rota in enumerate(ROTAS):
    if not combos[rota["nome"]].empty:
        paineis[rota["nome"]] = desenhar_painel(rota, f"painel_{i}.png")
