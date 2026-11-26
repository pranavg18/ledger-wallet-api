#!/usr/bin/env python3
"""Export docs/srs.md to docs/srs.tex and docs/srs.pdf (the submission copy of the SRS).

Usage (from the repo root):  python3 scripts/export_srs.py
Needs pandoc (converts the Markdown body) and tectonic (compiles the PDF). On macOS:
  brew install pandoc tectonic
Without tectonic it still writes docs/srs.tex; compile it with pdflatex or xelatex (run twice).

The title page, contents page, page header, table column widths and the three diagrams (redrawn
in TikZ) are added here. The use case diagram must stay in step with docs/diagrams/use-case.tex.
"""

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRS_MD = REPO / "docs/srs.md"
SRS_TEX = REPO / "docs/srs.tex"

# --------------------------------------------------------------------------- figures (TikZ)
FIG_CONTEXT = r"""
\begin{figure}[!htbp]
\centering
\begin{tikzpicture}[font=\small,
    box/.style={draw, rounded corners=2pt, align=center, inner sep=5pt, fill=white},
    flow/.style={-{Stealth[length=2.2mm]}},
    lbl/.style={font=\footnotesize, fill=white, inner sep=1.5pt}]
  \node[box] (client) at (0,0)
    {API client\\{\footnotesize (curl / Bruno / Postman /}\\{\footnotesize tests / skills)}};
  \node[box] (admin) at (0,-2.4) {Administrator};
  \node[box] (api) at (8.4,0) {REST controllers};
  \node[box, text width=5.7cm] (service) at (8.4,-1.7)
    {Services\\{\footnotesize transfer $\cdot$ idempotency $\cdot$ reversal $\cdot$ reconciliation}};
  \node[box] (domain) at (6.5,-3.5) {Domain rules\\{\footnotesize (Money, balancing)}};
  \node[box] (repo) at (10.3,-3.5) {Repository interfaces};
  \coordinate (top) at (8.4,0.95);
  \node[draw, dashed, rounded corners=4pt, inner sep=9pt, fit=(top)(api)(service)(domain)(repo),
    label={[anchor=north west, font=\footnotesize\bfseries, inner sep=6pt]north west:Ledger Wallet API (Spring Boot)}] {};
  \node[draw, cylinder, shape border rotate=90, aspect=0.18, align=center, minimum height=1.6cm,
    inner sep=4pt, fill=white] (db) at (10.3,-6.4)
    {PostgreSQL 17\\{\footnotesize wallets $\cdot$ ledger $\cdot$ idempotency keys}};
  \draw[flow] (client.east) -- node[lbl, above=2pt, pos=0.4] {HTTP JSON (REST)} (api.west);
  \draw[flow] (admin.east) -- node[lbl, sloped, above=2pt, pos=0.32] {X-Admin-Token} (api.south west);
  \draw[flow] (api) -- (service);
  \draw[flow] (service) -- (domain);
  \draw[flow] (service) -- (repo);
  \draw[flow] (repo) -- node[lbl, right=3pt, pos=0.72] {JDBC / SQL transactions} (db);
\end{tikzpicture}
\caption{Product context: the API, its clients and its database.}
\label{fig:context}
\end{figure}
"""

FIG_USE_CASE = r"""
\begin{figure}[!htbp]
\centering
\resizebox{\linewidth}{!}{%
\begin{tikzpicture}[font=\small,
    usecase/.style={ellipse, draw, minimum width=3.9cm, minimum height=0.95cm, inner sep=1pt,
      align=center, fill=white},
    generalize/.style={draw, -{Triangle[open, length=3mm, width=3mm]}},
    stereo/.style={font=\scriptsize, fill=white, inner sep=1pt},
    actor/.pic={
      \draw[thick] (0,0.55) circle (0.22);
      \draw[thick] (0,0.33) -- (0,-0.25);
      \draw[thick] (-0.35,0.12) -- (0.35,0.12);
      \draw[thick] (0,-0.25) -- (-0.28,-0.72) (0,-0.25) -- (0.28,-0.72);
    }]
  \draw[thick] (2.3,0.75) rectangle (13.0,-15.0);
  \node[anchor=north, font=\bfseries] at (7.65,0.7) {Ledger Wallet API};
  \pic at (0.6,-4.4) {actor};
  \node[align=center] (clientlabel) at (0.6,-5.55) {API client /\\wallet user};
  \pic at (0.6,-11.8) {actor};
  \node[align=center] at (0.6,-12.95) {Administrator /\\auditor};
  \pic at (14.6,-14.0) {actor};
  \node[align=center] at (14.6,-15.15) {Developer /\\AI agent};
  \node[usecase] (create-user)   at (5.5,-0.75) {Create user\\[-2pt]\scriptsize (FR-1.1)};
  \node[usecase] (create-wallet) at (5.5,-2.0)  {Create wallet\\[-2pt]\scriptsize (FR-1.2)};
  \node[usecase] (view-wallet)   at (5.5,-3.25) {View wallet and balance\\[-2pt]\scriptsize (FR-1.4)};
  \node[usecase] (statement)     at (5.5,-4.5)  {View statement\\[-2pt]\scriptsize (FR-1.5)};
  \node[usecase] (view-tx)       at (5.5,-5.75) {View transaction\\[-2pt]\scriptsize (FR-4.7)};
  \node[usecase] (deposit)       at (5.5,-7.0)  {Deposit funds\\[-2pt]\scriptsize (FR-1.6)};
  \node[usecase] (transfer)      at (5.5,-8.25) {Transfer funds\\[-2pt]\scriptsize (FR-2)};
  \node[usecase] (reverse)       at (5.5,-11.0) {Reverse transaction\\[-2pt]\scriptsize (FR-4.2)};
  \node[usecase] (reconcile)     at (5.5,-12.7) {Run reconciliation\\[-2pt]\scriptsize (FR-5)};
  \node[usecase] (idempotency)   at (10.5,-9.4)  {Apply idempotency key\\[-2pt]\scriptsize (FR-2.2 to FR-2.7)};
  \node[usecase] (token)         at (10.5,-12.2) {Verify admin token\\[-2pt]\scriptsize (NFR-SEC-4)};
  \node[usecase] (health)        at (10.5,-14.0) {Check service health\\[-2pt]\scriptsize (NFR-OBS-1)};
  \foreach \uc in {create-user, create-wallet, view-wallet, statement, view-tx, deposit, transfer}
    \draw (1.0,-4.3) -- (\uc.west);
  \foreach \uc in {reverse, reconcile}
    \draw (1.0,-11.7) -- (\uc.west);
  \draw (14.2,-13.9) -- (health.east);
  \draw[generalize] (0.6,-11.0) -- (clientlabel.south);
  \foreach \from/\to in {deposit.east/idempotency.north west, transfer.east/idempotency.west,
      reverse.north east/idempotency.south west, reverse.east/token.north west,
      reconcile.east/token.west} {
    \draw[dashed] (\from) -- node[stereo, sloped, pos=0.45] {\guillemotleft include\guillemotright} (\to);
    \draw[-{To[length=2.2mm]}] ($(\to)!1.5mm!(\from)$) -- (\to);
  }
\end{tikzpicture}}
\caption{Use case diagram. The administrator inherits every API client use case (generalisation arrow).}
\label{fig:use-case}
\end{figure}
"""

FIG_ER = r"""
\begin{figure}[!htbp]
\centering
\begin{tikzpicture}[font=\small,
    entity/.style={draw, thick, minimum width=2.4cm, minimum height=0.9cm, inner xsep=8pt, font=\small\bfseries,
      fill=white},
    mult/.style={font=\footnotesize, inner sep=2pt},
    rel/.style={font=\footnotesize\itshape, inner sep=2pt}]
  \node[entity] (user)   at (0,0)       {USER};
  \node[entity] (wallet) at (5.0,0)     {WALLET};
  \node[entity] (entry)  at (10.6,0)    {LEDGER\_ENTRY};
  \node[entity] (tx)     at (10.6,-3.6) {LEDGER\_TRANSACTION};
  \node[entity] (key)    at (3.6,-3.6)  {IDEMPOTENCY\_KEY};
  \draw (user) -- node[rel, above] {owns}
    node[mult, below, pos=0.12] {0..1} node[mult, below, pos=0.86] {0..*} (wallet);
  \draw (wallet) -- node[rel, above] {posted to}
    node[mult, below, pos=0.12] {1} node[mult, below, pos=0.86] {0..*} (entry);
  \draw (tx) -- node[rel, right] {consists of (sum = 0)}
    node[mult, left, pos=0.15] {1} node[mult, left, pos=0.85] {1..*} (entry);
  \draw (key) -- node[rel, above] {result of}
    node[mult, below, pos=0.12] {0..1} node[mult, below, pos=0.86] {0..1} (tx);
  \draw ($(tx.south)+(1.0,0)$) -- ++(0,-0.9) -| node[rel, below=1.5pt, pos=0.25] {reverses} ($(tx.south)+(-1.0,0)$);
  \node[mult, anchor=south west] at ($(tx.south)+(1.05,-0.45)$) {0..1};
  \node[mult, anchor=south east] at ($(tx.south)+(-1.05,-0.45)$) {0..1};
\end{tikzpicture}
\caption{Preliminary conceptual data model (multiplicities in UML notation).}
\label{fig:er}
\end{figure}
"""

# Relative column widths, keyed by each table's header row (pandoc reads them from the dashes).
TABLE_WIDTHS = {
    "| Name | Date | Reason For Changes | Version |": [22, 11, 57, 8],
    "| Reader | Read first | Then |": [30, 40, 30],
    "| User class | Description | Privileges | Importance |": [21, 34, 33, 12],
    "| Interface | Detail |": [18, 82],
    "| Method | Path | Purpose | Idempotency-Key |": [9, 44, 30, 17],
    "| Term | Definition |": [20, 80],
    "| ID | Item | Owner | Due |": [8, 68, 10, 10],
}

UNICODE_TO_LATEX = {
    "\u00b9\u00b2": r"\textsuperscript{12}",
    "\u2192": r"\ensuremath{\rightarrow}",
    "\u00b7": r"\ensuremath{\cdot}",
    "\u2264": r"\ensuremath{\le}",
    "\u2013": "--",
    "\u00ab": r"\guillemotleft{}",
    "\u00bb": r"\guillemotright{}",
    "\u2212": r"\ensuremath{-}",
    "\u03a3": r"\ensuremath{\Sigma}",
}


def raw(latex: str) -> str:
    return "\n```{=latex}\n" + latex.strip("\n") + "\n```\n"


def cover_field(md: str, pattern: str) -> str:
    match = re.search(pattern, md, re.M)
    if not match:
        sys.exit(f"export_srs: cover field not found in docs/srs.md: {pattern}")
    return match.group(1).strip()


def preprocess(md: str) -> str:
    """Drop the cover and contents list, map figures and rules to LaTeX, set table widths."""
    lines = md.split("\n")
    lines = lines[lines.index("## Revision History"):]
    out, i, mermaid_seen, rule_seen = [], 0, 0, 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("```mermaid"):
            j = i + 1
            while not lines[j].startswith("```"):
                j += 1
            out.append(raw(FIG_CONTEXT if mermaid_seen == 0 else FIG_ER))
            mermaid_seen += 1
            i = j + 1
            continue
        if line.startswith("![Use case diagram"):
            out.append(raw(FIG_USE_CASE))
            i += 1
            continue
        if line == "---":
            if rule_seen == 0:
                out.append(raw("\\clearpage\n\\pagenumbering{arabic}"))
            rule_seen += 1
            i += 1
            continue
        if line.startswith("#"):
            line = line[1:]  # ## -> # so the numbered sections become \section
        out.append(line)
        if line in TABLE_WIDTHS:
            out.append("|" + "|".join("-" * w for w in TABLE_WIDTHS[line]) + "|")
            i += 2  # skip the original separator row
            continue
        i += 1
    if mermaid_seen != 2:
        sys.exit(f"export_srs: expected 2 Mermaid diagrams in docs/srs.md, found {mermaid_seen}")
    return "\n".join(out)


def allow_code_breaks(text: str) -> str:
    """Allow line breaks after / and _ inside \\texttt{...} (code spans can be long)."""
    res, k = [], 0
    while True:
        s = text.find(r"\texttt{", k)
        if s < 0:
            res.append(text[k:])
            return "".join(res)
        res.append(text[k:s + 8])
        depth, p = 1, s + 8
        while depth:
            c = text[p]
            if c == "\\":
                p += 2
                continue
            depth += {"{": 1, "}": -1}.get(c, 0)
            p += 1
        inner = text[s + 8:p - 1]
        inner = inner.replace("/", r"/\allowbreak{}").replace(r"\_", r"\_\allowbreak{}")
        res.append(inner + "}")
        k = p


def body_latex(md: str) -> str:
    with tempfile.TemporaryDirectory() as tmp:
        pre = Path(tmp) / "srs_pre.md"
        pre.write_text(preprocess(md), encoding="utf-8")
        body = subprocess.run(
            ["pandoc", str(pre), "-f", "markdown+autolink_bare_uris-implicit_figures", "-t", "latex",
             "--wrap=preserve", "--columns=40"],
            check=True, capture_output=True, text=True).stdout
    body = allow_code_breaks(body)
    for char, latex in UNICODE_TO_LATEX.items():
        body = body.replace(char, latex)
    body = re.sub(r"\b(e\.g\.|vs\.) ", r"\1\\ ", body)
    leftover = sorted({c for c in body if ord(c) > 127})
    if leftover:
        sys.exit(f"export_srs: add LaTeX replacements for these characters: {leftover}")
    return body


def preamble(md: str) -> str:
    cover = cover_field(md, r"^\*\*(Version .*?)\*\*$")  # e.g. "Version 1.3 (Stage 1)"
    version = cover_field(md, r"^\*\*Version ([\d.]+)")
    stage = cover_field(md, r"^\*\*Version .*?Stage (\d+)")
    names = [n.strip() for n in cover_field(md, r"^\*\*Prepared by:\*\* (.+)$").split(",")]
    organization = cover_field(md, r"^\*\*Organization:\*\* (.+)$")
    created = cover_field(md, r"^\*\*Date created:\*\* (.+)$")
    return r"""% Software Requirements Specification for Ledger Wallet API, version @VERSION@.
% LaTeX version of docs/srs.md (the Markdown file in the repository is the working copy).
% Build:  tectonic docs/srs.tex   (or run pdflatex / xelatex twice so the contents page is filled in)
\documentclass[11pt,a4paper]{article}

\usepackage{iftex}
\ifPDFTeX
  \usepackage[T1]{fontenc}
  \usepackage[utf8]{inputenc}
  \usepackage{newtxtext,newtxmath}
  \usepackage[varqu,scaled=0.95]{zi4}
\else
  \usepackage{newtxtext,newtxmath}
  \setmonofont{Inconsolatazi4}[Extension=.otf, UprightFont=*-Regular, BoldFont=*-Bold, Scale=0.95]
\fi
\usepackage[a4paper,margin=2.5cm,headheight=14pt]{geometry}
\usepackage{microtype}
\usepackage{longtable,booktabs,array,calc}
\usepackage{etoolbox}
\usepackage{needspace}
\usepackage{tocloft}
\usepackage{float}
\usepackage[font=small,labelfont=bf,skip=6pt]{caption}
\usepackage{graphicx}
\usepackage{tikz}
\usetikzlibrary{shapes.geometric,arrows.meta,calc,fit}
\usepackage{fancyhdr}
\usepackage{xcolor}
\usepackage{xurl}
\usepackage{hyperref}
\hypersetup{
  colorlinks=true, linkcolor=black, urlcolor=blue!55!black,
  pdftitle={Software Requirements Specification for Ledger Wallet API},
  pdfauthor={@AUTHORS@},
  pdfsubject={SRS version @VERSION@, Stage @STAGE@},
}

% Section titles already carry their numbers (1., 1.1, 4.1.1 ...), as in the IEEE template.
\setcounter{secnumdepth}{-\maxdimen}
\setcounter{tocdepth}{2}
\setlength{\cftbeforesecskip}{0.45em}
\renewcommand{\cfttoctitlefont}{\Large\bfseries}
\pretocmd{\section}{\needspace{8\baselineskip}}{}{}
\pretocmd{\subsection}{\needspace{6\baselineskip}}{}{}
\pretocmd{\subsubsection}{\needspace{5\baselineskip}}{}{}

\setlength{\parindent}{0pt}
\setlength{\parskip}{0.55em}
\setlength{\emergencystretch}{3em}
\providecommand{\tightlist}{\setlength{\itemsep}{2pt}\setlength{\parskip}{0pt}}
\newcounter{none} % lets uncaptioned tables skip the table counter
\AtBeginEnvironment{longtable}{\small}
\renewcommand{\arraystretch}{1.2}

\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{\small Software Requirements Specification for Ledger Wallet API}
\fancyhead[R]{\small Page \thepage}
\renewcommand{\headrulewidth}{0.4pt}

\begin{document}
\pagenumbering{roman}

\begin{titlepage}
  \centering
  \vspace*{3.5cm}
  {\Huge\bfseries Software Requirements Specification\par}
  \vspace{0.8cm}
  {\LARGE for\par}
  \vspace{0.8cm}
  {\Huge\bfseries Ledger Wallet API\par}
  \vspace{1.5cm}
  {\Large @COVER@\par}
  \vspace{2.5cm}
  {\large Prepared by\par}
  \vspace{0.3cm}
  {\large @NAMES@\par}
  \vspace{1.2cm}
  {\large @ORG@\par}
  \vspace{1.2cm}
  {\large Date created: @CREATED@\par}
  \vfill
\end{titlepage}

\tableofcontents
\clearpage

""".replace("@VERSION@", version).replace("@STAGE@", stage).replace("@COVER@", cover) \
        .replace("@AUTHORS@", ", ".join(names)).replace("@NAMES@", "\\\\ ".join(names)) \
        .replace("@ORG@", organization).replace("@CREATED@", created)


def main() -> None:
    md = SRS_MD.read_text(encoding="utf-8")
    tex = preamble(md) + body_latex(md).strip() + "\n\n\\end{document}\n"
    SRS_TEX.write_text(tex, encoding="utf-8")
    print(f"wrote {SRS_TEX.relative_to(REPO)}")
    if shutil.which("tectonic"):
        subprocess.run(["tectonic", SRS_TEX.name], cwd=SRS_TEX.parent, check=True,
                       stdout=subprocess.DEVNULL)
        print(f"wrote {SRS_TEX.with_suffix('.pdf').relative_to(REPO)}")
    else:
        print("tectonic not found: compile docs/srs.tex with pdflatex or xelatex (run it twice)")


if __name__ == "__main__":
    main()
