"""Export a kit's documents to Word (.docx) and LaTeX (.tex, compiled to .pdf).

Usage (from the repository root):
    python tools/export/export_docs.py kits/qae_european

Reads kits/<kit>/README.md and kits/<kit>/docs/{circuit,benchmarks,tests}.md and writes
kits/<kit>/docs/export/<name>.docx, <name>.tex and <name>.pdf. Markdown stays the source of truth.
Needs pandoc and xelatex (TeX Live with fontspec, tcolorbox, sectsty) and the DejaVu fonts.
"""
import os, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
DOCS = [("README.md", "user-guide"), ("docs/circuit.md", "1-circuit"), ("docs/benchmarks.md", "2-benchmarks"), ("docs/tests.md", "3-tests")]
HEADER = r"""
\usepackage{xcolor}
\definecolor{plblue}{HTML}{1F3864}
\usepackage{sectsty}
\allsectionsfont{\sffamily\color{plblue}}
\usepackage{fvextra}
\DefineVerbatimEnvironment{Highlighting}{Verbatim}{breaklines,commandchars=\\\{\},fontsize=\footnotesize}
\usepackage{etoolbox}
\AtBeginEnvironment{longtable}{\footnotesize}
"""


def run(cmd, cwd):
    env = dict(os.environ, TEXINPUTS=os.path.join(HERE, "texinputs") + os.pathsep)
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=env)
    if r.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd[:2])} failed:\n{r.stdout[-3000:]}\n{r.stderr[-3000:]}")


def main(kit):
    kit = os.path.abspath(kit)
    out = os.path.join(kit, "docs", "export")
    os.makedirs(out, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", suffix=".tex", delete=False) as h:
        h.write(HEADER)
    for src, name in DOCS:
        path = os.path.join(kit, src)
        base = os.path.dirname(path)                                       # images are relative to the source
        common = ["pandoc", path, "--from", "gfm", "--resource-path", base, "--lua-filter", os.path.join(HERE, "tablewidths.lua")]
        run(common + ["--reference-doc", os.path.join(HERE, "reference.docx"), "-o", os.path.join(out, name + ".docx")], base)
        tex = os.path.join(out, name + ".tex")
        run(common + ["--standalone", "--pdf-engine=xelatex", "-H", h.name,
                      "-V", "geometry:margin=2.2cm", "-V", "fontsize=10pt", "-V", "colorlinks=true",
                      "-V", "mainfont=DejaVu Sans", "-V", "monofont=DejaVu Sans Mono", "-V", "mathfont=DejaVu Sans",
                      "-o", tex], base)
        # images: copy next to the .tex so it compiles on its own
        img_src = os.path.join(base, "img") if os.path.isdir(os.path.join(base, "img")) else os.path.join(kit, "docs", "img")
        shutil.copytree(img_src, os.path.join(out, "img"), dirs_exist_ok=True)
        with open(tex) as f:
            t = f.read().replace("{docs/img/", "{img/")
        with open(tex, "w") as f:
            f.write(t)
        for _ in range(2):
            run(["xelatex", "-interaction=nonstopmode", "-halt-on-error", os.path.basename(tex)], out)
        for ext in (".aux", ".log", ".out", ".toc"):  # keep .docx, .tex, .pdf
            p = os.path.join(out, name + ext)
            if os.path.exists(p):
                os.remove(p)
        print("exported", name)
    os.remove(h.name)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "kits/qae_european")
