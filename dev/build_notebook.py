"""Assemble pipeline.ipynb from percent-format cell files in dev/cells/ (sorted by filename).

`# @@INCLUDE path@@` inside a code cell is replaced by the text of that file (up to a `# --- CLI ---` marker), so verify.py
is a real standalone script *and* fully visible in the notebook.
Usage: python dev/build_notebook.py            -> writes pipeline.ipynb (unexecuted)
       python dev/build_notebook.py --script   -> writes dev/_all_cells.py for debugging
"""
import re, sys, glob, json
import nbformat
from nbformat.v4 import new_notebook, new_markdown_cell, new_code_cell

def split_cells(text):
    cells, kind, buf = [], None, []
    for line in text.split("\n"):
        m = re.match(r"^# %%( \[markdown\])?\s*$", line)
        if m:
            if kind is not None: cells.append((kind, buf))
            kind, buf = ("md" if m.group(1) else "code"), []
        else:
            buf.append(line)
    if kind is not None: cells.append((kind, buf))
    return cells

def expand_includes(code):
    def rep(m):
        src = open(m.group(1)).read().split("# --- CLI ---")[0].rstrip() + "\n"
        return src
    return re.sub(r"# @@INCLUDE ([^@]+)@@", rep, code)

def main():
    all_cells = []
    for f in sorted(glob.glob("dev/cells/*.py")):
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
        open("dev/_all_cells.py", "w").write("\n\n".join(c.source for c in cells if c.cell_type == "code"))
        print("wrote dev/_all_cells.py"); return
    nb = new_notebook(cells=cells)
    nb.metadata["kernelspec"] = {"display_name": "Python 3", "language": "python", "name": "python3"}
    nbformat.write(nb, "pipeline.ipynb")
    print("wrote pipeline.ipynb with", len(cells), "cells")

if __name__ == "__main__":
    main()
