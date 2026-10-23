"""Monta monitor_voos_v4.ipynb a partir dos arquivos em cells/ (ordem pelo prefixo numérico)."""
import glob, os, nbformat

AQUI = os.path.dirname(os.path.abspath(__file__))
nb = nbformat.v4.new_notebook()
nb.metadata = {"kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"},
               "language_info": {"name": "python"}}
for caminho in sorted(glob.glob(os.path.join(AQUI, "cells", "*"))):
    texto = open(caminho, encoding="utf-8").read().rstrip() + "\n"
    if caminho.endswith(".md"):
        nb.cells.append(nbformat.v4.new_markdown_cell(texto))
    else:
        cel = nbformat.v4.new_code_cell(texto)
        if "02_config" in caminho:
            cel.metadata["tags"] = ["parameters"]
        nb.cells.append(cel)
nbformat.write(nb, os.path.join(AQUI, "monitor_voos_v4.ipynb"))
print(f"{len(nb.cells)} células gravadas em monitor_voos_v4.ipynb")
