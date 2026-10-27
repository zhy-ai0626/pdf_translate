"""Recognise code, commands and program input/output lines: they stay as they are (no Chinese).

Used by inventory.py / apply_plan.py (PPTX) and pdfmodel.py (PDF). Conservative on purpose:
a prose line wrongly taken as code would silently lose its translation, while a missed code
line only shows up as `uncovered` and gets a skip in the plan.
"""
import re

MONO = ("consolas", "courier", "mono", "menlo", "monaco", "lucida console", "lucidaconsole",
        "source code", "sourcecode", "fira code", "inconsolata", "andale", "sfmono", "jetbrains")

TYPES = r"(?:int|float|double|char|void|unsigned|bool|boolean|String|struct|const|public|private)"
OPND = r"(\$\w{1,6}|-?\d*\(\$?\w{1,6}\)|[A-Z0-9#+\-]{1,8})"  # assembly operand: R1, A, $t0, 0(R2), #5
CODE_RE = [
    re.compile(r"^(#include|#define|#ifn?def|#endif|#pragma|%\{|%\}|%%|%token|%left|%right|%type|%start|%union)"),
    re.compile(r"^(import|from\s+[\w.]+\s+import|package)\s+[\w.*]+;?\s*$"),
    re.compile(r"^(def|class)\s+\w+\s*[(:]"),
    re.compile(r"^(return\b.*;|break;|continue;|else\s*\{|\}\s*else\b)"),
    re.compile(r"^(//|/\*|\*/|<!--)"),
    re.compile(r"\{[^{}]*;\s*\}"),                                         # inline action { return NUM; }
    re.compile(r"^[{}()\[\];]+$"),                                         # a lone brace
    re.compile(r"^(if|for|while|switch|catch)\s*\(.*\)\s*\{?$"),
    re.compile(r"^" + TYPES + r"(\s+[\w*&<>\[\],]+){0,3}\s+[*&]?\w+\s*(\(.*\)\s*\{?|=.*;|;|\[.*\]\s*;)$"),  # declarations
    re.compile(r"^[\w.\[\]>*-]+\s*(=|\+=|-=|\*=|/=|\+\+|--)\s*.*;$"),        # x = ...;
    re.compile(r"^[\w.]+\(.*\)\s*;$"),                                       # call(...);
    re.compile(r"^(\$\s+|>>>\s*|[A-Z]:\\)\S"),                                # shell / REPL prompt, Windows path
    re.compile(r"^(sudo|pip3?|python3?|gcc|g\+\+|cc|make|flex|bison|lex|yacc|javac|java|hadoop|hdfs|spark-submit|"
               r"pyspark|mvn|git|docker|kubectl|ssh|scp|chmod|mkdir|cd|ls|cat|echo|wget|curl|apt|brew|conda|npm)"
               r"\s+(-{1,2}\w|\S*[./\\]\S*|\w+\s+-)"),                       # command with a flag or a path
    re.compile(r"^\.?[A-Z]{2,6}(\.[A-Z0-9]{1,3})?\s+(?!\d+\s*,)" + OPND + r"(\s*,\s*" + OPND + r"){1,3}\s*([;#@].*)?$"),  # SUB R1, A, B
    re.compile(r"^\.?[A-Z]{2,6}(\.[A-Z0-9]{1,3})?\s+" + OPND + r"\s*[;#@]"),                                       # LDA D ; comment
    re.compile(r"^\w[\w.]*\s*(<-|:=)\s*.+$"),                               # R: x <- c(1, 2)
    re.compile(r"^([\w.]+ ?){0,3}:?\s*[A-Z][A-Z0-9]*(_[A-Z0-9]+)+[;,]?$"),     # "Lexical Error: MALFORMED_FLOAT"
    re.compile(r"^\w[\w ]{0,20}: \S+ {3,15}\w[\w ]{0,20}: \S+$"),               # "Valid Token: ID      Lexeme: x"
]
# only in a monospace font (in a normal font these are formulas such as "CPU time = IC x CPI", which do get Chinese)
MONO_RE = [
    re.compile(r"^(for|while|if|elif|else|with|try|except|finally|def|class|async)\b.*:$"),   # Python blocks
    re.compile(r"^[\w.\[\]'\"]+\s*(=|\+=|-=)(?![=>])\s*\S"),                                       # x = df.groupby(...)
    re.compile(r"^[\w.]+\(.*\)$"),                                                          # print(x), df.show()
    re.compile(r"^(SELECT|FROM|WHERE|GROUP BY|ORDER BY|INSERT|UPDATE|CREATE|JOIN)\b"),        # SQL
]
PROSE_WORD = re.compile(r"\b[a-z]{3,}\b")


def is_mono(face):
    face = (face or "").lower()
    return any(m in face for m in MONO)


def prose(t):
    """An ordinary sentence: 8+ plain words and few code symbols."""
    return len(PROSE_WORD.findall(t)) >= 8 and len(re.findall(r"[{}()\[\];=<>*&|$#%\\]", t)) <= 2


def code_line(line, mono=False):
    t = line.strip()
    if not t:
        return False
    if prose(t) and not re.match(r"^(//|/\*|#\s)", t):  # matched by accident: still a sentence
        return False
    return any(r.search(t) for r in CODE_RE) or (mono and any(r.search(t) for r in MONO_RE))


def looks_like_code(lines, mono=False):
    """lines: the visual lines of one paragraph (PPTX: split at <a:br/>; PDF: rendered lines).
    mono: all of the text is in a monospace font."""
    lines = [ln.strip() for ln in lines if ln.strip() and not re.fullmatch(r"\s*<!--.*-->\s*", ln)]  # page markers
    if not lines or any(prose(ln) and not re.match(r"^(//|/\*|#\s)", ln) for ln in lines):
        return False  # a sentence in it (e.g. a title merged with the first code line) needs Chinese
    # monospace alone is not enough (some decks set explanations in Consolas); it only adds MONO_RE
    return sum(code_line(ln, mono) for ln in lines) * 2 >= len(lines)


def code_runs(items, same):
    """Spread 'code' over a block of short lines: in a run of 3+ consecutive non-prose one-liners that
    `same(a, b)` says belong together, if at least 30% are code, all are (program output such as
    'Lexeme: 12.3.4' between 'Lexical Error: MALFORMED_FLOAT' lines).
    items: dicts with 'kind' ('code', 'en', ...) and 'text'. Changes 'en' to 'code' in place."""
    run = []

    def flush():
        if len(run) >= 3 and sum(x["kind"] == "code" for x in run) >= 0.3 * len(run):
            for x in run:  # only lines with digits/symbols: a plain label such as "Expected output" keeps its Chinese
                sentence = len(PROSE_WORD.findall(x["text"])) >= 3 and x["text"].rstrip(" )\"'").endswith(".")
                if x["kind"] == "en" and not sentence and re.search(r"[0-9\\'\"(){}\[\];=<>*&|$#%_/.+-]", x["text"].rstrip(":")):
                    x["kind"] = "code"
        run.clear()
    for x in items:
        ok = x["kind"] in ("en", "code", "misc") and not prose(x["text"]) and len(x["text"]) <= 80
        if ok and run and not same(run[-1], x):
            flush()
        if ok:
            run.append(x)
        else:
            flush()
    flush()
