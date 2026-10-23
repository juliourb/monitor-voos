# CÉLULA 5 — HISTÓRICO (Google Sheets ou CSV)
# Uma linha por (execução, rota, sentido, data do voo) com o preço mais barato encontrado.
# Alertas enviados ficam numa tabela à parte, para não repetir a mesma oferta.
COLS_PRECOS = ["data_busca", "modo"] + list(Oferta.__dataclass_fields__)
COLS_ALERTAS = ["enviado_em", "rota", "data_ida", "data_volta", "total"]


class Historico:
    def __init__(self):
        b = HIST_BACKEND
        if b == "auto":
            b = "sheets" if (GOOGLE_SHEETS_CREDS and URL_PLANILHA) else "csv"
        self.backend = b
        if b == "sheets":
            import gspread
            from google.oauth2.service_account import Credentials
            creds = Credentials.from_service_account_info(
                json.loads(GOOGLE_SHEETS_CREDS),
                scopes=["https://www.googleapis.com/auth/spreadsheets",
                        "https://www.googleapis.com/auth/drive"])
            self.sh = gspread.authorize(creds).open_by_url(URL_PLANILHA)
        else:
            os.makedirs(PASTA_DADOS, exist_ok=True)
        print(f"Histórico em: {self.backend}")

    # ---- baixo nível
    def _aba(self, nome, colunas):
        import gspread
        try:
            ws = self.sh.worksheet(nome)
        except gspread.exceptions.WorksheetNotFound:
            ws = self.sh.add_worksheet(title=nome, rows=1000, cols=len(colunas))
            ws.append_row(colunas)
        return ws

    def _ler(self, nome, colunas):
        if self.backend == "sheets":
            vals = self._aba(nome, colunas).get_all_values()
            df = pd.DataFrame(vals[1:], columns=vals[0]) if len(vals) > 1 else pd.DataFrame(columns=colunas)
        else:
            caminho = os.path.join(PASTA_DADOS, f"{nome}.csv.gz")
            df = pd.read_csv(caminho, dtype=str) if os.path.exists(caminho) else pd.DataFrame(columns=colunas)
        return df

    def _gravar(self, nome, colunas, df):
        if df.empty:
            return
        df = df[colunas].astype(object).where(df[colunas].notna(), "")
        if self.backend == "sheets":
            self._aba(nome, colunas).append_rows(df.astype(str).values.tolist(), value_input_option="RAW")
        else:
            caminho = os.path.join(PASTA_DADOS, f"{nome}.csv.gz")
            antigo = pd.read_csv(caminho, dtype=str) if os.path.exists(caminho) else pd.DataFrame(columns=colunas)
            pd.concat([antigo, df.astype(str)], ignore_index=True).to_csv(caminho, index=False)

    # ---- alto nível
    def ler_precos(self):
        df = self._ler(ABA_PRECOS, COLS_PRECOS)
        if df.empty:
            return df
        df["data_busca"] = pd.to_datetime(df["data_busca"], utc=True).dt.tz_convert(TZ)
        df["data_voo"] = pd.to_datetime(df["data_voo"]).dt.date
        for c in ("preco", "escalas", "duracao_min"):
            df[c] = pd.to_numeric(df[c], errors="coerce")
        return df

    def gravar_precos(self, df):
        df = df.copy()
        df["data_busca"] = df["data_busca"].map(lambda t: pd.Timestamp(t).isoformat())
        df["data_voo"] = df["data_voo"].astype(str)
        self._gravar(ABA_PRECOS, COLS_PRECOS, df)

    def ler_alertas(self):
        df = self._ler(ABA_ALERTAS, COLS_ALERTAS)
        df["total"] = pd.to_numeric(df["total"], errors="coerce")
        return df

    def gravar_alertas(self, df):
        self._gravar(ABA_ALERTAS, COLS_ALERTAS, df)


hist = Historico()
df_hist = hist.ler_precos()
df_alertas_ant = hist.ler_alertas()
print(f"Histórico: {len(df_hist)} linhas de preço · {len(df_alertas_ant)} alertas já enviados")
