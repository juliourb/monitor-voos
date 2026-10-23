# CÉLULA 2 — PARÂMETROS  (é a única célula que você precisa editar)
import os

# ---------------------------------------------------------------------------
# ROTAS MONITORADAS
# origens/destinos: códigos IATA. Todos os aeroportos de cada lado entram numa
# única consulta (o Google devolve o voo mais barato entre eles).
#   "ida"   = origens → destinos   (aqui: Alagoas/Sergipe → São Paulo)
#   "volta" = destinos → origens   (São Paulo → Alagoas/Sergipe)
# teto_ida_volta: alerta quando preço da ida + preço da volta <= este valor.
# min_noites / max_noites: dias entre o voo de ida e o de volta (estadia).
# teto_trecho:  (opcional) alerta também um trecho avulso <= este valor. None desliga.
# ---------------------------------------------------------------------------
ROTAS = [
    dict(
        nome="Alagoas ⇄ São Paulo",
        origens=["MCZ", "AJU"],
        destinos=["GRU", "CGH", "VCP"],
        teto_ida_volta=1000,
        min_noites=5,
        max_noites=7,
        teto_trecho=None,
    ),
]

HORIZONTE_DIAS = 180          # até quantos dias à frente procurar
ANTECEDENCIA_MIN_DIAS = 1     # não consulta voos para hoje
MAX_ESCALAS = 1               # 0 = só direto; 1 = até 1 escala; None = qualquer
PERMITIR_AEROPORTOS_DIFERENTES = True   # volta por aeroporto diferente da ida

# --- Fontes de preço ---------------------------------------------------------
FONTE = os.environ.get("FONTE", "auto")  # auto | fli | fast_flights | simulada
USAR_AVIASALES = True         # só é usado se existir o segredo TRAVELPAYOUTS_TOKEN
WORKERS = 4                   # consultas simultâneas (não passe de 6)
PAUSA_SEG = 0.4               # pausa por consulta, por worker (anti-bloqueio)

# --- Modo de execução --------------------------------------------------------
MODO = os.environ.get("MODO", "auto")   # auto | completo | rapido
HORAS_ENTRE_COMPLETAS = 20    # no modo auto: completo se a última completa for mais velha
TOP_DATAS_RAPIDO = 25         # no modo rápido: reconsulta as N datas mais baratas de cada sentido
DIAS_PROXIMOS_RAPIDO = 14     # ... e também todas as datas dos próximos N dias

# --- Alertas -----------------------------------------------------------------
MAX_OFERTAS_POR_MSG = 5
QUEDA_MIN_PARA_REALERTAR = 0.03   # só re-alerta a mesma viagem se cair >= 3%
ENVIAR_RESUMO_DIARIO = True       # resumo + painel após a varredura completa
DRY_RUN = os.environ.get("DRY_RUN", "0") == "1"   # 1 = imprime em vez de enviar

# --- Histórico ---------------------------------------------------------------
HIST_BACKEND = os.environ.get("HIST_BACKEND", "auto")  # auto | sheets | csv
# URL da planilha: lida do segredo URL_PLANILHA (não fica escrita no código).
ABA_PRECOS = "v4_precos"
ABA_ALERTAS = "v4_alertas"
PASTA_DADOS = os.environ.get("PASTA_DADOS", "dados")   # usado no modo csv
FUSO = "America/Sao_Paulo"

print(f"{len(ROTAS)} rota(s) · horizonte {HORIZONTE_DIAS} dias · modo={MODO} · fonte={FONTE} · dry_run={DRY_RUN}")
