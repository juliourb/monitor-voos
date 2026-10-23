# CÉLULA 3 — UTILITÁRIOS (segredos, datas, formatação)
import json, time, hashlib, random, warnings
from dataclasses import dataclass, asdict, field
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
from urllib.parse import quote

import pandas as pd
import requests

warnings.filterwarnings("ignore", category=FutureWarning)
TZ = ZoneInfo(FUSO)
AGORA = datetime.now(TZ)
HOJE = AGORA.date()


def segredo(nome, padrao=None):
    """Lê um segredo de: variável de ambiente → Kaggle Secrets → Colab userdata."""
    v = os.environ.get(nome)
    if v:
        return v
    try:
        from kaggle_secrets import UserSecretsClient
        return UserSecretsClient().get_secret(nome)
    except Exception:
        pass
    try:
        from google.colab import userdata
        return userdata.get(nome)
    except Exception:
        pass
    return padrao


TELEGRAM_TOKEN = segredo("TELEGRAM_TOKEN")
TELEGRAM_CHAT_IDS = [c.strip() for c in (segredo("TELEGRAM_CHAT_IDS") or "").split(",") if c.strip()]
TRAVELPAYOUTS_TOKEN = segredo("TRAVELPAYOUTS_TOKEN")

DIAS_SEMANA = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]
MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
CIAS = {"JJ": "LATAM", "LA": "LATAM", "G3": "GOL", "AD": "Azul", "2Z": "Voepass",
        "TP": "TAP", "AR": "Aerolíneas", "CM": "Copa"}


def brl(v):
    """1234.5 → 'R$ 1.235'"""
    if v is None or pd.isna(v):
        return "—"
    return "R$ " + f"{v:,.0f}".replace(",", ".")


def fmt_data(d, com_dia=True):
    d = pd.Timestamp(d).date()
    txt = f"{d.day:02d}/{d.month:02d}"
    return f"{DIAS_SEMANA[d.weekday()]} {txt}" if com_dia else txt


def fmt_dur(minutos):
    if minutos is None or pd.isna(minutos):
        return "—"
    minutos = int(minutos)
    return f"{minutos // 60}h{minutos % 60:02d}"


def fmt_escalas(n):
    if n is None or pd.isna(n):
        return "—"
    return "direto" if int(n) == 0 else f"{int(n)} escala" + ("s" if int(n) > 1 else "")


def link_google(origem, destino, d):
    """Busca genérica no Google Flights (usada quando a fonte não dá deep link)."""
    q = quote(f"Flights from {origem} to {destino} on {pd.Timestamp(d).date()} one way")
    return f"https://www.google.com/travel/flights?q={q}&curr=BRL&hl=pt-BR&gl=BR"


def datas_horizonte(dias_extras=0):
    ini = HOJE + timedelta(days=ANTECEDENCIA_MIN_DIAS)
    return [ini + timedelta(days=i) for i in range(HORIZONTE_DIAS + dias_extras)]


@dataclass
class Oferta:
    rota: str
    sentido: str          # "ida" (origens→destinos) ou "volta"
    data_voo: str         # YYYY-MM-DD
    preco: float
    cia: str
    origem: str
    destino: str
    escalas: int | None
    duracao_min: int | None
    partida: str          # HH:MM
    chegada: str          # HH:MM
    fonte: str
    link: str


print(f"Agora: {AGORA:%d/%m/%Y %H:%M} ({FUSO})")
print(f"Telegram: {len(TELEGRAM_CHAT_IDS)} destinatário(s) · "
      f"Travelpayouts: {'sim' if TRAVELPAYOUTS_TOKEN else 'não'}")
