"""Assemble learning_curve.ipynb from the percent-format cell file dev/cells.py.
Usage (from learning-curve/):
    python dev/build_notebook.py
    jupyter nbconvert --to notebook --execute --inplace learning_curve.ipynb
"""
import re
from pathlib import Path
import nbformat
from nbformat.v4 import new_notebook, new_markdown_cell, new_code_cell

HERE = Path(__file__).resolve().parent.parent
cells, kind, buf = [], None, []
for line in (HERE / "dev" / "cells.py").read_text().split("\n") + ["# %%"]:
    m = re.match(r"^# %%( \[markdown\])?\s*$", line)
    if m:
        if kind is not None:
            body = "\n".join(buf).strip("\n")
            cells.append(new_markdown_cell("\n".join(re.sub(r"^# ?", "", l) for l in body.split("\n"))) if kind == "md" else new_code_cell(body))
        kind, buf = ("md" if m.group(1) else "code"), []
    else:
        buf.append(line)
nb = new_notebook(cells=cells, metadata={"kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"}})
nbformat.write(nb, HERE / "learning_curve.ipynb")
print(f"wrote learning_curve.ipynb ({len(cells)} cells)")
