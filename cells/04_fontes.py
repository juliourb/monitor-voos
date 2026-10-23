# CÉLULA 4 — FONTES DE PREÇO
# Cada fonte recebe (origens, destinos, data) e devolve a Oferta mais barata ou None.
#   fli          → Google Flights, multi-aeroporto numa consulta, deep link do voo exato
#   fast_flights → Google Flights (biblioteca da v3), 1 consulta por par de aeroportos
#   simulada     → preços falsos e determinísticos, para testar o notebook sem internet
#   aviasales    → cache do Travelpayouts (1 chamada devolve o mês inteiro); radar extra
from concurrent.futures import ThreadPoolExecutor, as_completed


def _nome_cia(codigo, nome=None):
    return CIAS.get(codigo, nome or codigo)


# ---------------------------------------------------------------- fli
def buscar_fli(origens, destinos, d):
    from fli.models import (Airport, FlightSearchFilters, FlightSegment,
                            PassengerInfo, SeatType, MaxStops, SortBy)
    from fli.search import SearchFlights

    paradas = {0: MaxStops.NON_STOP, 1: MaxStops.ONE_STOP_OR_FEWER,
               2: MaxStops.TWO_OR_FEWER_STOPS}.get(MAX_ESCALAS, MaxStops.ANY)
    filtros = FlightSearchFilters(
        passenger_info=PassengerInfo(adults=1),
        flight_segments=[FlightSegment(
            departure_airport=[[Airport[o], 0] for o in origens],
            arrival_airport=[[Airport[x], 0] for x in destinos],
            travel_date=d.isoformat())],
        seat_type=SeatType.ECONOMY, stops=paradas, sort_by=SortBy.CHEAPEST)
    busca = SearchFlights()
    voos = busca.search(filtros, currency="BRL", language="pt-BR", country="BR")
    voos = [v for v in (voos or []) if v.price]
    if not voos:
        return None
    v = min(voos, key=lambda x: x.price)
    l0, l1 = v.legs[0], v.legs[-1]
    cias = sorted({_nome_cia(l.airline.name, l.airline.value) for l in v.legs})
    try:
        link = busca.build_flight_booking_url(v, currency="BRL", language="pt-BR", country="BR")
    except Exception:
        link = link_google(l0.departure_airport.name, l1.arrival_airport.name, d)
    return dict(preco=float(v.price), cia=" + ".join(cias),
                origem=l0.departure_airport.name, destino=l1.arrival_airport.name,
                escalas=int(v.stops), duracao_min=int(v.duration),
                partida=l0.departure_datetime.strftime("%H:%M"),
                chegada=l1.arrival_datetime.strftime("%H:%M"), link=link)


# ---------------------------------------------------------------- fast-flights
def buscar_fast_flights(origens, destinos, d):
    from fast_flights import create_query, FlightQuery, Passengers, get_flights
    melhor = None
    for o in origens:
        for x in destinos:
            q = create_query(
                flights=[FlightQuery(date=d.isoformat(), from_airport=o, to_airport=x)],
                trip="one-way", seat="economy", passengers=Passengers(adults=1),
                language="pt-BR", currency="BRL", max_stops=MAX_ESCALAS)
            try:
                res = get_flights(q)
            except Exception:
                continue
            for f in (res or []):
                if f.price and (melhor is None or f.price < melhor["preco"]):
                    s0, s1 = f.flights[0], f.flights[-1]
                    melhor = dict(
                        preco=float(f.price), cia=" + ".join(_nome_cia(c) for c in f.airlines),
                        origem=s0.from_airport.code, destino=s1.to_airport.code,
                        escalas=max(0, len(f.flights) - 1),
                        duracao_min=sum(s.duration or 0 for s in f.flights),
                        partida="%02d:%02d" % tuple(s0.departure.time),
                        chegada="%02d:%02d" % tuple(s1.arrival.time), link=q.url())
            time.sleep(PAUSA_SEG)
    return melhor


# ---------------------------------------------------------------- simulada
def buscar_simulada(origens, destinos, d):
    """Preço plausível e estável por data (varia um pouco a cada hora), sem internet."""
    semente = int(hashlib.md5(f"{origens}{destinos}{d}".encode()).hexdigest(), 16)
    rnd = random.Random(semente)
    if rnd.random() < 0.03:
        return None
    base = 430 + (180 if d.month in (12, 1, 7) else 0) + (60 if d.weekday() in (4, 6) else 0)
    antecedencia = (d - HOJE).days
    base += max(0, 25 - antecedencia) * 18            # perto da data fica caro
    ruido = random.Random(semente + AGORA.hour).uniform(-0.06, 0.06)
    preco = round(base * rnd.uniform(0.62, 1.45) * (1 + ruido))
    o, x = rnd.choice(origens), rnd.choice(destinos)
    h = rnd.randint(5, 21)
    dur = rnd.choice([180, 195, 240, 330, 410])
    return dict(preco=float(preco), cia=rnd.choice(["LATAM", "GOL", "Azul"]), origem=o, destino=x,
                escalas=0 if dur < 200 else 1, duracao_min=dur, partida=f"{h:02d}:{rnd.choice([0, 15, 30, 45]):02d}",
                chegada=f"{(h + dur // 60) % 24:02d}:{dur % 60:02d}", link=link_google(o, x, d))


FONTES = {"fli": buscar_fli, "fast_flights": buscar_fast_flights, "simulada": buscar_simulada}


def escolher_fonte(rota):
    """Testa as fontes em ordem com 3 datas e fica com a primeira que responde."""
    if FONTE != "auto":
        return FONTE
    teste = [HOJE + timedelta(days=n) for n in (20, 45, 75)]
    for nome in ("fli", "fast_flights"):
        try:
            if any(FONTES[nome](rota["origens"], rota["destinos"], d) for d in teste):
                print(f"[fonte] {nome} respondeu — usando {nome}.")
                return nome
            print(f"[fonte] {nome} não trouxe preços nas datas de teste.")
        except Exception as e:
            print(f"[fonte] {nome} falhou: {type(e).__name__}: {str(e)[:120]}")
    raise RuntimeError("Nenhuma fonte do Google Flights respondeu (possível bloqueio).")


def _consultar(fonte, origens, destinos, d, tentativas=2):
    for t in range(tentativas):
        try:
            r = FONTES[fonte](origens, destinos, d)
            time.sleep(PAUSA_SEG)
            return r, None
        except Exception as e:
            erro = f"{type(e).__name__}: {str(e)[:100]}"
            time.sleep(1.5 * (t + 1))
    return None, erro


def varrer(rota, sentido, datas, fonte):
    """Consulta todas as datas em paralelo. Devolve (lista de Oferta, estatísticas)."""
    ori, dst = (rota["origens"], rota["destinos"]) if sentido == "ida" else (rota["destinos"], rota["origens"])
    ofertas, stats = [], {"consultas": len(datas), "sem_voo": 0, "falhas": 0, "erros": []}
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futuros = {ex.submit(_consultar, fonte, ori, dst, d): d for d in datas}
        for i, fut in enumerate(as_completed(futuros), 1):
            d = futuros[fut]
            r, erro = fut.result()
            if erro:
                stats["falhas"] += 1
                stats["erros"].append(erro)
            elif r is None:
                stats["sem_voo"] += 1
            else:
                ofertas.append(Oferta(rota=rota["nome"], sentido=sentido, data_voo=d.isoformat(),
                                      fonte=fonte, **r))
            if i % 40 == 0 or i == len(datas):
                print(f"  {sentido}: {i}/{len(datas)} consultas · {len(ofertas)} com preço · {stats['falhas']} falhas")
    return ofertas, stats


# ---------------------------------------------------------------- aviasales (radar)
def buscar_aviasales(rota, sentido, meses):
    """Preço mais barato por dia, mês a mês, do cache do Aviasales (pode ter até 48 h)."""
    if not (USAR_AVIASALES and TRAVELPAYOUTS_TOKEN):
        return []
    ori, dst = (rota["origens"], rota["destinos"]) if sentido == "ida" else (rota["destinos"], rota["origens"])
    melhores = {}
    for o in ori:
        for x in dst:
            for mes in meses:
                try:
                    r = requests.get(
                        "https://api.travelpayouts.com/aviasales/v3/grouped_prices",
                        params=dict(origin=o, destination=x, departure_at=mes, group_by="departure_at",
                                    currency="brl", market="br", direct=str(MAX_ESCALAS == 0).lower()),
                        headers={"X-Access-Token": TRAVELPAYOUTS_TOKEN, "Accept-Encoding": "gzip"},
                        timeout=20)
                    dados = r.json().get("data") or {}
                except Exception as e:
                    print(f"  [aviasales] {o}->{x} {mes}: {e}")
                    continue
                for dia, it in dados.items():
                    if MAX_ESCALAS is not None and (it.get("transfers") or 0) > MAX_ESCALAS:
                        continue
                    preco = float(it["price"])
                    if dia not in melhores or preco < melhores[dia].preco:
                        dep = pd.Timestamp(it["departure_at"])
                        dur = it.get("duration_to") or it.get("duration")
                        melhores[dia] = Oferta(
                            rota=rota["nome"], sentido=sentido, data_voo=dia, preco=preco,
                            cia=_nome_cia(it.get("airline", "?")),
                            origem=it.get("origin_airport", o), destino=it.get("destination_airport", x),
                            escalas=it.get("transfers"), duracao_min=dur, partida=dep.strftime("%H:%M"),
                            chegada=(dep + pd.Timedelta(minutes=dur or 0)).strftime("%H:%M") if dur else "—",
                            fonte="aviasales", link="https://www.aviasales.com" + it.get("link", ""))
                time.sleep(0.15)
    return list(melhores.values())

print("Fontes prontas:", ", ".join(FONTES) + (" + aviasales" if TRAVELPAYOUTS_TOKEN else ""))
