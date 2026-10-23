# CÉLULA 5 — HISTÓRICO NO PRÓPRIO REPOSITÓRIO (Parquet particionado)
#
# dados/
#   precos/AAAA/MM/<execucao>.parquet    menor preço por (rota, sentido, data do voo) em cada execução
#   ofertas/AAAA/MM/<execucao>.parquet   menor preço de CADA companhia por data (mais detalhe p/ análise)
#   alertas/AAAA/MM/<execucao>.parquet   ofertas enviadas no Telegram (evita repetir)
#   execucoes.csv                        1 linha por execução: modo, fonte, falhas, melhor preço, duração...
#   ultimo/                              painel e tabelas da última varredura completa (sobrescritos)
#
# Cada execução cria arquivos NOVOS e pequenos (append-only): o git guarda só o que mudou,
# o repositório cresce devagar e dá para consultar tudo com pandas ou DuckDB:
#   duckdb.sql("select * from 'dados/precos/**/*.parquet'")
import glob, pathlib

ID_EXECUCAO = AGORA.strftime("%Y%m%dT%H%M%S")
COLS_PRECOS = ["data_busca", "modo"] + list(Oferta.__dataclass_fields__)
COLS_OFERTAS = ["data_busca", "rota", "sentido", "data_voo", "cia", "preco", "origem", "destino",
                "escalas", "duracao_min", "partida", "chegada", "fonte"]
COLS_ALERTAS = ["enviado_em", "rota", "data_ida", "data_volta", "total", "preco_ida", "preco_volta",
                "cia_ida", "cia_volta"]
TIPOS = {"preco": "float64", "total": "float64", "preco_ida": "float64", "preco_volta": "float64",
         "escalas": "float64", "duracao_min": "float64"}


class Historico:
    def __init__(self, pasta=PASTA_DADOS):
        self.raiz = pathlib.Path(pasta)
        self.raiz.mkdir(parents=True, exist_ok=True)

    def _arquivo(self, tabela):
        p = self.raiz / tabela / AGORA.strftime("%Y") / AGORA.strftime("%m") / f"{ID_EXECUCAO}.parquet"
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    def _gravar(self, tabela, colunas, df):
        if df is None or df.empty:
            return
        df = df.reindex(columns=colunas).copy()
        for c in colunas:
            if c in TIPOS:
                df[c] = pd.to_numeric(df[c], errors="coerce").astype(TIPOS[c])
            elif c in ("data_busca", "enviado_em"):
                df[c] = pd.to_datetime(df[c], utc=True)
            elif c.startswith("data_"):
                df[c] = pd.to_datetime(df[c]).dt.date
            else:
                df[c] = df[c].astype("string")
        df.to_parquet(self._arquivo(tabela), index=False)

    def _ler(self, tabela, colunas, desde=None):
        arquivos = sorted(glob.glob(str(self.raiz / tabela / "*" / "*" / "*.parquet")))
        if desde is not None:   # nome do arquivo = AAAAMMDDTHHMMSS → filtra sem abrir
            corte = desde.strftime("%Y%m%dT%H%M%S")
            arquivos = [a for a in arquivos if pathlib.Path(a).stem >= corte]
        if not arquivos:
            return pd.DataFrame(columns=colunas)
        return pd.concat([pd.read_parquet(a) for a in arquivos], ignore_index=True)

    # ---- alto nível
    def ler_precos(self):
        df = self._ler("precos", COLS_PRECOS)
        if df.empty:
            return df
        df["data_busca"] = pd.to_datetime(df["data_busca"], utc=True).dt.tz_convert(TZ)
        df["data_voo"] = pd.to_datetime(df["data_voo"]).dt.date
        return df

    def gravar_precos(self, df):
        self._gravar("precos", COLS_PRECOS, df)

    def gravar_ofertas(self, df):
        self._gravar("ofertas", COLS_OFERTAS, df)

    def ler_alertas(self):
        df = self._ler("alertas", COLS_ALERTAS)
        if not df.empty:
            df["data_ida"] = df["data_ida"].astype(str)
            df["data_volta"] = df["data_volta"].astype(str)
        return df

    def gravar_alertas(self, df):
        self._gravar("alertas", COLS_ALERTAS, df)

    def registrar_execucao(self, linha: dict):
        caminho = self.raiz / "execucoes.csv"
        novo = pd.DataFrame([linha])
        novo.to_csv(caminho, mode="a", index=False, header=not caminho.exists())

    def salvar_ultimo(self, nome, conteudo_df=None, arquivo_origem=None):
        pasta = self.raiz / "ultimo"
        pasta.mkdir(exist_ok=True)
        if conteudo_df is not None:
            conteudo_df.to_csv(pasta / nome, index=False)
        if arquivo_origem is not None:
            import shutil
            shutil.copy(arquivo_origem, pasta / nome)


hist = Historico()
df_hist = hist.ler_precos()
df_alertas_ant = hist.ler_alertas()
n_exec = df_hist["data_busca"].nunique() if not df_hist.empty else 0
print(f"Histórico em '{PASTA_DADOS}/': {len(df_hist)} preços de {n_exec} execuções · "
      f"{len(df_alertas_ant)} alertas já enviados")
