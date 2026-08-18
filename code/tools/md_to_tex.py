#!/usr/bin/env python3
"""Convert a generated survey from Markdown to LaTeX, with real references.

main.py writes two files per run:

    <topic>.md     the survey; its reference list is titles only
    <topic>.json   {"survey": ..., "reference": {"1": "2005.11401v4", ...}}

The arxiv ids only live in the .json, and everything else about a paper (URL,
authors, date, category) only lives in the local arxiv database. This script
joins the three so the .tex comes out with a usable bibliography instead of a
list of bare titles.

Output:

    <topic>.tex    ready for pdflatex; carries an inline thebibliography
    <topic>.bib    the same entries as BibTeX, if you would rather use natbib

The inline bibliography is what the .tex uses by default because it reproduces
the source numbering exactly -- [17] in the Markdown stays [17] in the PDF.
BibTeX styles renumber by citation order or alphabetically, which silently
breaks any cross-reference to the original run.

Usage:
    python code/tools/md_to_tex.py <run_dir>            # dir holding .md + .json
    python code/tools/md_to_tex.py <survey.md>
    python code/tools/md_to_tex.py <run_dir> --compile  # also produce the PDF
"""

import argparse
import json
import os
import re
import subprocess
import sys

DATA_ROOT = os.environ.get("SURVEYFORGE_DATA",
                           "/data2/chanjoong/survey-agent/SurveyForge_data")
DEFAULT_DB = os.path.join(DATA_ROOT, "database", "arxiv_paper_db_with_cc.json")


def db_for_run(run_dir):
    """산출물 경로에서 그 실행이 쓴 스냅샷을 되짚는다.

    run_demo.py 는 출력 경로에 스냅샷을 넣는다 —
    `output/res/<model>__<db_dir>/<topic>/exp_N`. 기본 스냅샷이면 접미사가 없다.
    이걸 안 보고 배포본을 물리면 최신 논문의 제목·저자가 전부 빠진 참고문헌이
    나오므로, 경로가 알려 줄 수 있는 것은 경로에서 읽는다.
    """
    try:
        slug = os.path.basename(os.path.dirname(os.path.dirname(
            os.path.abspath(run_dir.rstrip("/")))))
    except (OSError, ValueError):
        return DEFAULT_DB
    if "__" not in slug:
        return DEFAULT_DB
    candidate = os.path.join(DATA_ROOT, slug.rsplit("__", 1)[1],
                             "arxiv_paper_db_with_cc.json")
    return candidate if os.path.exists(candidate) else DEFAULT_DB

# The full paper database is ~880MB of JSON and takes about a minute to parse,
# but a survey only cites ~100 papers. Extract those into a small cache next to
# the output so re-runs are instant.
CACHE_NAME = "reference_metadata.json"

SECTION_CMD = ["section", "subsection", "subsubsection", "paragraph"]

# pdflatex with inputenc cannot digest these directly. Everything the generator
# actually emits is listed here; anything else is reported rather than mangled.
UNICODE_MAP = {
    "\u2011": "-",             # non-breaking hyphen -- by far the most common
    "\u2013": "--",            # en dash
    "\u2014": "---",           # em dash
    "\u2018": "`",
    "\u2019": "'",
    "\u201c": "``",
    "\u201d": "''",
    "\u00d7": r"$\times$",
    "\u2192": r"$\rightarrow$",
    "\u00b2": r"$^{2}$",
    "\u00b3": r"$^{3}$",
    "\u2074": r"$^{4}$",
    "\u0131": r"\i{}",        # dotless i -- arrives in Turkish author names
    "\u0142": r"\l{}",        # l with stroke -- Polish author names
    "\u0141": r"\L{}",
    "\u2026": r"\ldots{}",
    "\u00a0": "~",
    # Characters that look like ASCII punctuation but are not, so they slip
    # past review and then stop pdflatex dead. The minus sign is the common one:
    # models write it for a range ("scales to -3") where a hyphen was meant.
    "\u2010": "-",             # hyphen (the real U+2010, not U+002D)
    "\u2212": "$-$",           # minus sign
    "\u2032": r"$'$",          # prime
    "\u201a": ",",             # single low quote
    "\u201e": ",,",            # double low quote
    "\u2039": r"$<$",
    "\u203a": r"$>$",
    "\u00ad": "",              # soft hyphen -- invisible, drop it
    "\u200b": "",              # zero-width space
    "\ufeff": "",              # BOM
    # Math prose. The model writes formulas inline as running text
    # ("the system computes P(y|x) = \u03a3 ..."), so these arrive in the body, not in
    # any math environment. One unmapped \u03a3 aborted a whole run at pdflatex pass 1,
    # and a pass-1 abort leaves every citation number unresolved -- the PDF renders
    # but its bibliography references are broken, which looks like a data problem
    # rather than a compile one.
    "\u00b7": r"$\cdot$",      # middle dot
    "\u2248": r"$\approx$",
    "\u2264": r"$\leq$",
    "\u2265": r"$\geq$",
    "\u2260": r"$\neq$",
    "\u00b1": r"$\pm$",
    "\u221e": r"$\infty$",
    "\u2208": r"$\in$",
    "\u2211": r"$\sum$",
    "\u220f": r"$\prod$",
    "\u221a": r"$\sqrt{}$",
    "\u00b0": r"$^{\circ}$",
    "\u2205": r"$\emptyset$",
    "\u2229": r"$\cap$",
    "\u222a": r"$\cup$",
    "\u2200": r"$\forall$",
    "\u2203": r"$\exists$",
    "\u00a7": r"\S{}",           # section sign
    "\u00df": r"\ss{}",          # NFD 분해가 없어 deaccent 로는 안 잡힌다 (Nie\u00dfner)
    "\u1d40": r"$^{T}$",         # 전치. 모델이 산문에 S\u1d40 R\u1d40 처럼 쓴다
    "\u00b9": r"$^{1}$",        # \u00b2\u00b3\u2074 만 있고 \u00b9 이 빠져 있었다
    "\u207a": r"$^{+}$",
    "\u207b": r"$^{-}$",        # 10\u207b\u00b3 표기
    "\u02e3": r"$^{x}$",
    "\u2097": r"$_{l}$",
    "\u2098": r"$_{m}$",
    "\u2099": r"$_{n}$",
    "\u2093": r"$_{x}$",
    # 흑판체. amssymb 가 프리앰블에 있으므로 \mathbb 을 쓸 수 있다.
    "\u211d": r"$\mathbb{R}$",
    "\u2115": r"$\mathbb{N}$",
    "\u2124": r"$\mathbb{Z}$",
    "\u211a": r"$\mathbb{Q}$",
    "\u2102": r"$\mathbb{C}$",
}

# 아래첨자. 위첨자 \u00b9\u00b2\u00b3\u2074 는 위에 있지만 나머지 자리와 아래첨자 전체가 비어 있었다.
# 모델이 L\u2081 / x\u2080 처럼 본문에 그대로 쓴다.
UNICODE_MAP.update({c: rf"$^{{{d}}}$" for c, d in zip("\u2070\u2075\u2076\u2077\u2078\u2079", "056789")})
UNICODE_MAP.update({c: rf"$_{{{d}}}$" for c, d in zip("\u2080\u2081\u2082\u2083\u2084\u2085\u2086\u2087\u2088\u2089", "0123456789")})

# Greek. Enumerable, unlike the accented Latin range, but not uniform: the
# uppercase letters that look like Latin ones (\u0391 \u0392 \u0395 ...) have **no** LaTeX macro
# -- \Alpha does not exist -- so they map to the Latin letter they are drawn as.
# A rule that derived every macro from the character name would compile-error on
# exactly those.
UNICODE_MAP.update({c: rf"$\{n}$" for c, n in zip(
    "\u03b1\u03b2\u03b3\u03b4\u03b5\u03b6\u03b7\u03b8\u03b9\u03ba\u03bb\u03bc\u03bd\u03be\u03c0\u03c1\u03c3\u03c4\u03c5\u03c6\u03c7\u03c8\u03c9",
    ("alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu nu xi "
     "pi rho sigma tau upsilon phi chi psi omega").split())})
UNICODE_MAP.update({c: rf"$\{n}$" for c, n in zip(
    "\u0393\u0394\u0398\u039b\u039e\u03a0\u03a3\u03a5\u03a6\u03a8\u03a9",
    "Gamma Delta Theta Lambda Xi Pi Sigma Upsilon Phi Psi Omega".split())})
UNICODE_MAP.update(dict(zip(
    "\u0391\u0392\u0395\u0396\u0397\u0399\u039a\u039c\u039d\u039f\u03a1\u03a4\u03a7",  # Latin-lookalike uppercase
    "ABEZHIKMNOPTX")))
UNICODE_MAP["\u03bf"] = "o"    # omicron -- likewise indistinguishable from Latin o

# Accented letters are not enumerable in advance -- they arrive with author names
# from the database (K\u00fchn, M\u00fcller, P\u00e9rez, ...). Decomposing to base letter plus
# combining mark covers the whole Latin range with one rule instead of a list
# that is always one name short.
COMBINING_TO_LATEX = {
    "\u0300": "`", "\u0301": "'", "\u0302": "^", "\u0303": "~",
    "\u0308": '"', "\u030a": "r", "\u0327": "c", "\u0304": "=",
    "\u030c": "v", "\u0306": "u", "\u0307": ".",
}


def deaccent(text):
    """Rewrite accented characters as LaTeX accent commands (\u00fc -> \\"{u})."""
    import unicodedata
    out = []
    for ch in unicodedata.normalize("NFD", text):
        if ch in COMBINING_TO_LATEX and out:
            out[-1] = "\\%s{%s}" % (COMBINING_TO_LATEX[ch], out[-1])
        elif unicodedata.combining(ch):
            continue  # a mark with no LaTeX equivalent: drop it, keep the letter
        else:
            out.append(ch)
    return "".join(out)


def clean_title(title):
    """Database titles carry hard line wraps ('Adaptive-RAG\\n  Learning to')."""
    return re.sub(r"\s+", " ", title).strip()


# src.utils.arxiv_month does the same parse, but importing it would pull in
# faiss, langchain and pandas for six lines of regex -- this converter should
# run anywhere the .md and .json are.
_NEW_ID = re.compile(r"^(\d{2})(\d{2})\.\d{4,5}")
_OLD_ID = re.compile(r"^[a-zA-Z][\w.-]*/(\d{2})(\d{2})\d+")


def citation_year(aid, rec):
    """The year a reader would cite: when v1 was announced.

    The database's `date` is the date of the *version named in the id*, which is
    deliberate -- it matches the base corpus and is what check_oai_schema.py
    verifies against. But it is the wrong number for a bibliography: a paper
    posted 2024-04 and revised 2025-03 is cited as 2024, not 2025. Taken from
    `date`, this misdated 36% of the 3DGS bibliography and 26% of Multi-Agent's.

    The arXiv id's YYMM is the v1 announcement month and never changes, so read
    the year from there, falling back to `date` only for an unparseable id.
    """
    m = _NEW_ID.match(aid or "")
    if m:
        return str(2000 + int(m.group(1)))
    m = _OLD_ID.match(aid or "")
    if m:
        yy = int(m.group(1))
        return str(1900 + yy if yy >= 91 else 2000 + yy)
    return ((rec or {}).get("date") or "")[:4]


# Order matters: the backslash has to be consumed first or it would be applied
# again to the replacements produced for the other characters.
LATEX_SPECIALS = [
    ("\\", "\x00BS\x00"),
    ("&", r"\&"), ("%", r"\%"), ("$", r"\$"), ("#", r"\#"),
    ("_", r"\_"), ("{", r"\{"), ("}", r"\}"),
    ("~", r"\textasciitilde{}"), ("^", r"\textasciicircum{}"),
]


def protect(text, store):
    """Replace math and inline code with opaque tokens.

    Escaping must not touch math -- `\\alpha_1` is meaningful there and would be
    destroyed. Display math is matched first because `\\[` also starts with a
    backslash that the inline pattern would otherwise not see past. Both are
    handled before the document is split into lines, since `\\[...\\]` spans
    several of them.
    """
    def sub(pattern, kind, flags=0):
        def repl(m):
            store.append((kind, m.group(0)))
            return f"\x00{kind}{len(store) - 1}\x00"
        return lambda s: re.sub(pattern, repl, s, flags=flags)

    for step in (
        sub(r"\\\[.*?\\\]", "MATH", re.S),   # display
        sub(r"\\\(.*?\\\)", "MATH", re.S),   # inline
        # 줄바꿈을 넘지 않는다. Markdown 코드 스팬은 한 줄 안에서 닫히는데, 모델이
        # 백틱을 짝 없이 흘리면 `[^`]+` 가 **산문 한 뭉치를 통째로** 삼킨다. 그러면
        # 문단 경계를 품은 \texttt{...} 가 만들어져 "Paragraph ended before
        # \text@command was complete" 로 죽는다 (실측: 산문 블록 하나에 em dash 66개).
        sub(r"`[^`\n]+`", "CODE"),
    ):
        text = step(text)
    return text


def _map_only(text, math_mode=False):
    """UNICODE_MAP + deaccent 만 적용한다 (LaTeX 특수문자 이스케이프는 하지 않는다).

    보호 구간(MATH/CODE)은 escape() 를 안 거치므로 여기서 따로 태워야 한다. 안 그러면
    맵에 **있는** 문자도 그대로 남아 pdflatex 이 죽는다 -- 실측으로 `\u2014` 151개 중 66개,
    `\u03b8` 3개 전부가 보호 구간 안이었다.

    `math_mode=True` 면 치환값의 `$` 를 벗긴다. 이미 수식 안이라 `$` 를 그대로 넣으면
    수식이 닫혔다 열리면서 깨진다.
    """
    for ch, esc in UNICODE_MAP.items():
        if ch not in text:
            continue
        if math_mode and len(esc) > 1 and esc.startswith("$") and esc.endswith("$"):
            esc = esc[1:-1]
        text = text.replace(ch, esc)
    return deaccent(text)


def restore(text, store):
    for i, (kind, raw) in enumerate(store):
        if kind == "MATH":
            raw = _map_only(raw, math_mode=True)
        if kind == "CODE":
            # Strip the backticks and make the content verbatim-ish. The only
            # occurrence in practice is an HTML-looking tag such as `<read>`,
            # which must not reach LaTeX as markup.
            body = raw[1:-1]
            for ch, esc in LATEX_SPECIALS:
                body = body.replace(ch, esc)
            body = body.replace("\x00BS\x00", r"\textbackslash{}")
            body = _map_only(body)
            raw = r"\texttt{" + body + "}"
        text = text.replace(f"\x00{kind}{i}\x00", raw)
    return text


def escape(text):
    for ch, esc in LATEX_SPECIALS:
        text = text.replace(ch, esc)
    text = text.replace("\x00BS\x00", r"\textbackslash{}")
    for ch, esc in UNICODE_MAP.items():
        text = text.replace(ch, esc)
    return deaccent(text)


def inline_markup(text):
    # Bold before italic: a lone `*` pattern would otherwise bite into `**`.
    text = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", text, flags=re.S)
    text = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"\\emph{\1}", text, flags=re.S)
    return text


def convert_citations(text, keys, unknown):
    """Turn the generator's `[3]` / `[3; 17]` markers into \\cite commands."""
    def repl(m):
        nums = [n.strip() for n in m.group(1).split(";")]
        resolved = []
        for n in nums:
            if n in keys:
                resolved.append(keys[n])
            else:
                unknown.add(n)
        if not resolved:
            return m.group(0)
        return r"\cite{" + ",".join(resolved) + "}"

    return re.sub(r"\[(\d+(?:\s*;\s*\d+)*)\]", repl, text)


def inline(text, keys, unknown):
    return convert_citations(inline_markup(escape(text)), keys, unknown)


def load_metadata(ids, db_path, cache_path):
    """arxiv id -> record, via a cache so the 880MB database is read once."""
    cached = {}
    if os.path.exists(cache_path):
        with open(cache_path) as f:
            cached = json.load(f)
    missing = [i for i in ids if i not in cached]
    if not missing:
        print(f"  metadata: {len(ids)} ids, all from cache")
        return cached

    if not os.path.exists(db_path):
        print(f"  WARNING: database not found at {db_path}", file=sys.stderr)
        print("  entries will fall back to title-only", file=sys.stderr)
        return cached

    print(f"  metadata: {len(missing)} ids not cached, scanning {db_path} "
          "(~1 min)...", flush=True)
    with open(db_path) as f:
        table = json.load(f)["cs_paper_info"]
    wanted = set(missing)
    for rec in table.values():
        if rec.get("id") in wanted:
            cached[rec["id"]] = rec
            wanted.discard(rec["id"])
            if not wanted:
                break
    if wanted:
        # 거의 항상 스냅샷을 잘못 짚은 것이다. 신 스냅샷으로 만든 산출물에 배포본을
        # 물리면 최신 논문 전부가 여기 걸리고, 참고문헌이 제목·저자 없는 껍데기가 된다.
        print(f"  WARNING: {len(wanted)}/{len(ids)} ids absent from {db_path}",
              file=sys.stderr)
        print("  these become bare arXiv links with no title or authors. If the run "
              "used a different snapshot, pass --db <그 스냅샷>/arxiv_paper_db_with_cc.json",
              file=sys.stderr)

    with open(cache_path, "w") as f:
        json.dump(cached, f, indent=1)
    print(f"  metadata: cached to {os.path.basename(cache_path)}")
    return cached


def bib_key(arxiv_id):
    return "arxiv:" + arxiv_id


def format_authors(rec, limit):
    authors = rec.get("authors") or []
    if not authors:
        return None
    if len(authors) > limit:
        return ", ".join(escape(a) for a in authors[:limit]) + r" \emph{et al.}"
    return ", ".join(escape(a) for a in authors)


def build_bibliography(order, refmap, meta, max_authors):
    """Inline thebibliography, emitted in the survey's own numbering order."""
    lines = [r"\begin{thebibliography}{%d}" % len(order),
             r"\setlength{\itemsep}{2pt}", ""]
    for num in order:
        aid = refmap[num]
        rec = meta.get(aid)
        lines.append(r"\bibitem{%s}" % bib_key(aid))
        if rec:
            parts = []
            authors = format_authors(rec, max_authors)
            if authors:
                parts.append(authors + ".")
            parts.append(r"\newblock \emph{%s}." % escape(clean_title(rec.get("title", aid))))
            year = citation_year(aid, rec)
            tail = "arXiv:%s" % escape(aid)
            if year:
                tail += ", %s" % year
            parts.append(r"\newblock %s." % tail)
            parts.append(r"\newblock \url{https://arxiv.org/abs/%s}" % aid)
            lines.append("\n".join(parts))
        else:
            # Better a visible placeholder than a silently missing entry.
            lines.append(r"\newblock arXiv:%s. \url{https://arxiv.org/abs/%s}"
                         % (escape(aid), aid))
        lines.append("")
    lines.append(r"\end{thebibliography}")
    return "\n".join(lines)


def bib_escape(s):
    for ch, esc in [("\\", r"\textbackslash{}"), ("&", r"\&"), ("%", r"\%"),
                    ("$", r"\$"), ("#", r"\#"), ("_", r"\_"),
                    ("{", r"\{"), ("}", r"\}"), ("~", r"\textasciitilde{}")]:
        s = s.replace(ch, esc)
    for ch, esc in UNICODE_MAP.items():
        s = s.replace(ch, esc)
    return deaccent(s)


def build_bibtex(order, refmap, meta):
    out = ["% Generated by code/tools/md_to_tex.py",
           "% Only needed if you switch the .tex to natbib/biblatex. Note that",
           "% BibTeX styles renumber the references, so [17] here will not match",
           "% [17] in the original Markdown.", ""]
    for num in order:
        aid = refmap[num]
        rec = meta.get(aid)
        out.append("@article{%s," % bib_key(aid))
        if rec:
            # Double braces keep the title's capitalization under styles that
            # would otherwise lowercase it.
            out.append("  title         = {{%s}}," % bib_escape(clean_title(rec.get("title", ""))))
            authors = rec.get("authors") or []
            if authors:
                out.append("  author        = {%s},"
                           % " and ".join(bib_escape(a) for a in authors))
            year = citation_year(aid, rec)
            if year:
                out.append("  year          = {%s}," % year)
            if rec.get("cat"):
                out.append("  primaryClass  = {%s}," % rec["cat"])
        out.append("  eprint        = {%s}," % aid)
        out.append("  archivePrefix = {arXiv},")
        out.append("  url           = {https://arxiv.org/abs/%s}," % aid)
        out.append("}")
        out.append("")
    return "\n".join(out)


PREAMBLE = r"""\documentclass[11pt,a4paper]{article}
\usepackage[utf8]{inputenc}
% lmodern must precede fontenc: without a scalable Type1 font the T1 encoding
% falls back to bitmap fonts, and microtype's expansion then aborts the run
% with "auto expansion is only possible with scalable fonts".
\usepackage{lmodern}
\usepackage[T1]{fontenc}
\usepackage[margin=1in]{geometry}
\usepackage{amsmath,amssymb}
\usepackage{graphicx}
\usepackage{microtype}
\usepackage[hidelinks,breaklinks]{hyperref}
\usepackage{url}
\urlstyle{same}

% Generated by code/tools/md_to_tex.py from the SurveyForge Markdown output.
% Citation numbers match the source .md exactly.

\title{@@TITLE@@}
\author{Generated by SurveyForge}
\date{}

\begin{document}
\maketitle
\tableofcontents
\newpage

"""


def convert(md_path, json_path, out_dir, db_path, max_authors):
    text = open(md_path).read()

    refmap = {}
    if os.path.exists(json_path):
        refmap = json.load(open(json_path)).get("reference", {})
    else:
        print(f"  WARNING: {os.path.basename(json_path)} missing -- citations "
              "cannot be resolved to arxiv ids", file=sys.stderr)

    # The Markdown reference list is titles only; the bibliography replaces it.
    body = re.split(r"\n#+\s*References\s*\n", text, maxsplit=1)[0]

    keys = {num: bib_key(aid) for num, aid in refmap.items()}

    store = []
    body = protect(body, store)

    unknown = set()
    title, out = None, []
    for line in body.split("\n"):
        m = re.match(r"^(#{1,4})\s+(.*)$", line)
        if m:
            level, heading = len(m.group(1)), m.group(2).strip()
            # Strip the generator's own numbering ("2.1 Foo") so LaTeX does not
            # print it a second time next to its own counter.
            heading = re.sub(r"^\d+(\.\d+)*\s+", "", heading)
            heading = inline(heading, keys, unknown)
            if level == 1 and title is None:
                title = heading
            else:
                out.append("\n\\%s{%s}\n" % (SECTION_CMD[min(level - 2, 3)], heading))
            continue
        out.append(inline(line, keys, unknown) if line.strip() else "")

    tex_body = restore("\n".join(out), store)

    if unknown:
        print(f"  WARNING: {len(unknown)} citation numbers had no entry in the "
              f".json and were left as plain text: {sorted(unknown)[:10]}",
              file=sys.stderr)

    order = sorted(refmap, key=int)
    meta = load_metadata([refmap[n] for n in order], db_path,
                         os.path.join(out_dir, CACHE_NAME)) if order else {}

    stem = os.path.splitext(os.path.basename(md_path))[0]
    tex_path = os.path.join(out_dir, stem + ".tex")
    bib_path = os.path.join(out_dir, stem + ".bib")

    # Plain replace rather than %-formatting: the preamble is full of LaTeX
    # comments, and every one of their `%` would read as a format specifier.
    doc = PREAMBLE.replace("@@TITLE@@", title or escape(stem))
    doc += tex_body.rstrip() + "\n\n"
    if order:
        doc += build_bibliography(order, refmap, meta, max_authors) + "\n"
    doc += "\n\\end{document}\n"

    with open(tex_path, "w") as f:
        f.write(doc)
    if order:
        with open(bib_path, "w") as f:
            f.write(build_bibtex(order, refmap, meta))

    leftover = sorted({c for c in doc if ord(c) > 127})
    if leftover:
        print("  WARNING: unmapped non-ASCII characters remain: "
              + " ".join(f"U+{ord(c):04X}({c})" for c in leftover)
              + "\n  -> xelatex 으로 컴파일합니다. 자주 나오는 문자면 UNICODE_MAP 에 넣으세요",
              file=sys.stderr)

    return tex_path, bib_path, len(order), bool(leftover)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("target", help="run directory, or the survey .md itself")
    ap.add_argument("-o", "--out-dir", help="default: alongside the input")
    ap.add_argument("--db", default=None,
                    help="arxiv_paper_db_with_cc.json. 기본값은 산출물 경로에 박힌 "
                         "스냅샷에서 되짚고, 없으면 배포본")
    ap.add_argument("--max-authors", type=int, default=6,
                    help="authors listed before 'et al.' (default: 6)")
    ap.add_argument("--compile", action="store_true",
                    help="run latexmk -pdf on the result")
    args = ap.parse_args()

    if os.path.isdir(args.target):
        mds = [f for f in os.listdir(args.target)
               if f.endswith(".md") and not f.startswith("README")]
        if len(mds) != 1:
            sys.exit(f"expected exactly one .md in {args.target}, found {len(mds)}: {mds}")
        md_path = os.path.join(args.target, mds[0])
    else:
        md_path = args.target
    if not os.path.exists(md_path):
        sys.exit(f"no such file: {md_path}")

    json_path = os.path.splitext(md_path)[0] + ".json"
    out_dir = args.out_dir or os.path.dirname(os.path.abspath(md_path))
    os.makedirs(out_dir, exist_ok=True)

    print(f"converting {os.path.basename(md_path)}")
    db_path = args.db or db_for_run(os.path.dirname(os.path.abspath(md_path)))
    snapshot = os.path.basename(os.path.dirname(db_path))
    if args.db:
        print(f"  snapshot: {snapshot} (--db 로 지정)")
    elif db_path != DEFAULT_DB:
        print(f"  snapshot: {snapshot} (산출물 경로에서 되짚음)")
    else:
        # 되짚기가 실패해도 조용히 배포본을 물면 최신 논문의 제목·저자가 통째로 빠진
        # 참고문헌이 나오고, 그건 컴파일도 되고 그럴듯해 보입니다. 경로에 스냅샷
        # 접미사가 없는 배치(예: 실험 arm 하위 디렉터리)가 실제로 여기에 걸립니다.
        print(f"  snapshot: {snapshot} (기본값 — 경로에서 되짚지 못했습니다)")
        print( "  WARNING: 이 실행이 다른 스냅샷을 썼다면 --db <그 스냅샷>/"
               "arxiv_paper_db_with_cc.json 을 주세요. 안 주면 최신 논문의 "
               "제목·저자가 빠진 채로 조용히 진행됩니다")
    tex, bib, n, needs_xetex = convert(md_path, json_path, out_dir, db_path,
                                       args.max_authors)
    print(f"  wrote {tex}")
    if n:
        print(f"  wrote {bib}  ({n} references)")

    if args.compile:
        # pdflatex directly rather than latexmk: the bibliography is inline, so
        # there is no bibtex pass to sequence, and latexmk is not always a
        # working install (on this box it is a perl wrapper that needs a GUI).
        # Two passes resolve \cite and the table of contents; a third settles
        # page numbers if the ToC changed pagination.
        # 모델이 내놓는 문자를 미리 다 열거할 수는 없다. 남은 게 있으면 engine 을 바꾼다 --
        # 경고만 띄우던 판에서는 그 경고가 두 번 다 무시됐고, 두 번 다 pass 1 에서 죽어
        # **인용 번호가 전부 미해소된 PDF** 가 남았다. 열려서 데이터 문제로 보이는 종류다.
        engine = "xelatex" if needs_xetex else "pdflatex"
        print(f"  compiling (3 {engine} passes)...")
        for i in range(1, 4):
            # errors="replace": pdflatex echoes source bytes into its log, and a
            # font-encoding warning can carry a byte that is not valid UTF-8.
            # Without this the decode raises and the traceback buries the actual
            # LaTeX error we were trying to report.
            r = subprocess.run(
                [engine, "-interaction=nonstopmode", os.path.basename(tex)],
                cwd=out_dir, capture_output=True, text=True,
                encoding="utf-8", errors="replace")
            if r.returncode != 0:
                errs = [l for l in r.stdout.splitlines()
                        if l.startswith("!") or l.startswith("l.")]
                sys.exit("  %s failed on pass %d:\n    %s"
                         % (engine, i, "\n    ".join(errs[:15] or r.stdout.splitlines()[-15:])))
        pdf = os.path.splitext(tex)[0] + ".pdf"
        print(f"  wrote {pdf} ({os.path.getsize(pdf) / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
