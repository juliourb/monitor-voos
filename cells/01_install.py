# CÉLULA 1 — INSTALAÇÃO
# Instala só o que estiver faltando (no GitHub Actions o requirements.txt já resolve).
# A fli vem do GitHub (versão de setembro/2026), porque a versão do PyPI ainda usa
# um endpoint de calendário que o Google bloqueou em agosto/2026.
import importlib.util, subprocess, sys

def _instalar(pacote_import, spec_pip):
    if importlib.util.find_spec(pacote_import) is None:
        print(f"Instalando {spec_pip} ...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", spec_pip], check=False)

_instalar("fli", "flights @ git+https://github.com/punitarani/fli.git@881aee5ff4321e81ea2157cb44be94ce6a21dc1b")
_instalar("fast_flights", "fast-flights")
_instalar("gspread", "gspread")
_instalar("google.oauth2", "google-auth")
print("Dependências OK.")
