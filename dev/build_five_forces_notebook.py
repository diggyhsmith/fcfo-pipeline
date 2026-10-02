"""Assemble five_forces.ipynb from percent-format cell files in dev/ff_cells/ (sorted by filename).

Same format as dev/build_notebook.py (which builds pipeline.ipynb and is left untouched).
Usage: python dev/build_five_forces_notebook.py            -> writes five_forces.ipynb (unexecuted)
       python dev/build_five_forces_notebook.py --script   -> writes dev/_ff_all_cells.py for debugging
"""
import re, sys, glob, os
import nbformat
from nbformat.v4 import new_notebook, new_markdown_cell, new_code_cell

sys.path.insert(0, os.path.dirname(__file__))
from build_notebook import split_cells, expand_includes

def main():
    all_cells = []
    for f in sorted(glob.glob("dev/ff_cells/*.py")):
        all_cells += split_cells(open(f).read())
    cells = []
    for kind, buf in all_cells:
        body = "\n".join(buf).strip("\n")
        if kind == "md":
            body = "\n".join(re.sub(r"^# ?", "", l) for l in body.split("\n"))
            cells.append(new_markdown_cell(body))
        else:
            cells.append(new_code_cell(expand_includes(body)))
    if "--script" in sys.argv:
        open("dev/_ff_all_cells.py", "w").write("\n\n".join(c.source for c in cells if c.cell_type == "code"))
        print("wrote dev/_ff_all_cells.py"); return
    nb = new_notebook(cells=cells)
    nb.metadata["kernelspec"] = {"display_name": "Python 3", "language": "python", "name": "python3"}
    nbformat.write(nb, "five_forces.ipynb")
    print("wrote five_forces.ipynb with", len(cells), "cells")

if __name__ == "__main__":
    main()
