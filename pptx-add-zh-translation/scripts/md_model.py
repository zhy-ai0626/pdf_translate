"""Markdown block parser / editor for doc_inventory.py / doc_apply.py.

Line-based (CommonMark + Obsidian habits): front matter, fenced code, $$ math,
HTML, headings, lists, tables, block quotes / callouts, paragraphs.
Ids: B<n> per block in order; table cells are B<n>.r<row>c<col> (header row = r0).
Edits insert lines after a block (or change table cells / append to a line);
all other lines are kept byte-for-byte.
"""
import re

from codetext import code_runs, looks_like_code
from doc_common import classify

QUOTE = re.compile(r"^((?:[ \t]{0,3}>[ \t]?)+)")
FENCE = re.compile(r"^(\s*)(`{3,}|~{3,})")
HEADING = re.compile(r"^(\s{0,3})(#{1,6})\s+(.*?)\s*#*\s*$")
LIST = re.compile(r"^(\s*)([-*+]|\d{1,9}[.)])(\s+)(\[[^\]]\]\s+)?(.*)$")
HR = re.compile(r"^\s{0,3}([-*_])(\s*\1){2,}\s*$")
TABLE_SEP = re.compile(r"^\s*\|?\s*:?-{1,}:?\s*(\|\s*:?-{1,}:?\s*)*\|?\s*$")
CALLOUT = re.compile(r"^\[!([\w-]+)\][+-]?\s*(.*)$")
IMAGE_ONLY = re.compile(r"^\s*(!\[\[[^\]]*\]\]|!\[[^\]]*\]\([^)]*\))\s*$")
NOT_REQUIRED = {"code", "math", "html", "meta", "image"}


def plain(text):
    """Strip markup so classify() sees only prose."""
    t = re.sub(r"`[^`]*`", " ", text)
    t = re.sub(r"\$[^$]+\$", " ", t)
    t = re.sub(r"!?\[\[([^\]|]*\|)?([^\]]*)\]\]", r"\2", t)
    t = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", t)
    t = re.sub(r"<[^>]+>|https?://\S+", " ", t)
    return t


def split_cells(line):
    """[(start, end)] spans of cell contents in a table row (pipes excluded)."""
    spans, start, i, in_code = [], 0, 0, False
    s = line
    lead = len(s) - len(s.lstrip())
    if s.lstrip().startswith("|"):
        start = lead + 1
        i = start
    while i < len(s):
        ch = s[i]
        if ch == "\\":
            i += 2
            continue
        if ch == "`":
            in_code = not in_code
        elif ch == "|" and not in_code:
            spans.append((start, i))
            start = i + 1
        i += 1
    tail = s[start:]
    if tail.strip():
        spans.append((start, len(s)))
    return spans


class Markdown:
    def __init__(self, path):
        raw = open(path, encoding="utf-8").read()
        self.newline = "\r\n" if "\r\n" in raw else "\n"
        self.trailing = raw.endswith(("\n", "\r\n"))
        body = raw[:-len(self.newline)] if self.trailing else raw
        self.lines = body.split(self.newline) if body else []
        self.after = {}    # line index -> lines to insert after it
        self.replace = {}  # line index -> new line text
        self._blocks = self._parse()

    # ---- parsing ------------------------------------------------------
    def _parse(self):
        L, out, i, n = self.lines, [], 0, len(self.lines)
        bid = 0

        def add(role, start, end, text, **kw):
            nonlocal bid
            bid += 1
            b = {"id": "B%d" % bid, "role": role, "start": start, "end": end, "text": text}
            b.update(kw)
            if role in NOT_REQUIRED:
                b["kind"] = role
            else:
                b["kind"] = classify(plain(text)) if text.strip() else "misc"
                if b["kind"] == "en" and role in ("para", "list") and looks_like_code(plain(text).split("\n")):
                    b["kind"] = "code"  # unfenced code / program output
            out.append(b)
            return b

        if n and L[0].strip() == "---":
            for j in range(1, n):
                if L[j].strip() in ("---", "..."):
                    add("meta", 0, j, "\n".join(L[1:j]))
                    i = j + 1
                    break
        in_list = False
        while i < n:
            line = L[i]
            m = QUOTE.match(line)
            qp = m.group(1) if m else ""
            rest = line[len(qp):]
            if not rest.strip():
                i += 1
                continue
            indent = len(rest) - len(rest.lstrip(" "))
            fm = FENCE.match(rest)
            if fm:
                mark = fm.group(2)
                j = i + 1
                while j < n:
                    r = L[j][len(qp):] if L[j].startswith(qp) else L[j]
                    if r.strip().startswith(mark[0] * len(mark)) and not r.strip().strip(mark[0]):
                        break
                    j += 1
                add("code", i, min(j, n - 1), "\n".join(L[i:j + 1]))
                i = j + 1
                continue
            if rest.strip().startswith("$$"):
                j = i
                if not (rest.strip().endswith("$$") and len(rest.strip()) > 2):
                    j = i + 1
                    while j < n and "$$" not in L[j]:
                        j += 1
                add("math", i, min(j, n - 1), "\n".join(L[i:j + 1]))
                i = j + 1
                continue
            if indent >= 4 and not in_list and not qp:
                j = i
                while j + 1 < n and (L[j + 1].startswith("    ") or not L[j + 1].strip()):
                    j += 1
                add("code", i, j, "\n".join(L[i:j + 1]))
                i = j + 1
                continue
            if rest.lstrip().startswith("<") and re.match(r"\s*</?[A-Za-z!]", rest):
                j = i
                while j + 1 < n and L[j + 1].strip():
                    j += 1
                add("html", i, j, "\n".join(L[i:j + 1]))
                i = j + 1
                continue
            hm = HEADING.match(rest)
            if hm:
                add("heading", i, i, hm.group(3), level=len(hm.group(2)), qp=qp, indent="")
                in_list = False
                i += 1
                continue
            if HR.match(rest):
                i += 1
                continue
            if "|" in rest and i + 1 < n and TABLE_SEP.match(L[i + 1][len(qp):]) and "-" in L[i + 1]:
                j = i + 2
                while j < n and "|" in L[j] and L[j].strip():
                    j += 1
                bid += 1
                tid = "B%d" % bid
                for r_i, li in enumerate([i] + list(range(i + 2, j))):
                    row = L[li]
                    for c_i, (a, b) in enumerate(split_cells(row)):
                        txt = row[a:b].strip()
                        if not txt:
                            continue
                        kind = classify(plain(txt))
                        out.append({"id": "%s.r%dc%d" % (tid, r_i, c_i), "role": "cell", "start": li,
                                    "end": li, "text": txt, "kind": kind, "row": r_i, "col": c_i,
                                    "table": tid})
                i = j
                continue
            if IMAGE_ONLY.match(rest):
                add("image", i, i, rest.strip())
                i += 1
                continue
            cm = CALLOUT.match(rest.strip()) if qp else None
            if cm:
                add("callout", i, i, cm.group(2), qp=qp, indent="", callout=cm.group(1))
                i += 1
                continue
            lm = LIST.match(rest)
            if lm:
                col = len(lm.group(1)) + len(lm.group(2)) + len(lm.group(3))
                j = i
                while j + 1 < n and self._continues(L[j + 1], qp):
                    j += 1
                text = "\n".join([lm.group(5)] + [L[k][len(qp):].strip() for k in range(i + 1, j + 1)])
                add("list", i, j, text, qp=qp, indent=" " * col, level=len(lm.group(1)) // 2)
                in_list = True
                i = j + 1
                continue
            j = i
            while j + 1 < n and self._continues(L[j + 1], qp):
                j += 1
            text = "\n".join(L[k][len(qp):].strip() for k in range(i, j + 1))
            add("para", i, j, text, qp=qp, indent=" " * indent)
            if indent == 0:
                in_list = False
            i = j + 1
        code_runs(out, lambda a, b: a["role"] == b["role"] == "para" and b["start"] - a["end"] <= 2)
        return out

    def _continues(self, line, qp):
        """Is `line` a lazy continuation of the paragraph / list item above?"""
        m = QUOTE.match(line)
        if (m.group(1) if m else "") != qp:
            return False
        rest = line[len(qp):]
        if not rest.strip():
            return False
        if (FENCE.match(rest) or HEADING.match(rest) or LIST.match(rest) or HR.match(rest)
                or rest.strip().startswith("$$") or IMAGE_ONLY.match(rest)):
            return False
        return True

    def blocks(self):
        return self._blocks

    # ---- editing ------------------------------------------------------
    def add_below(self, b, zh, cfg):
        role, qp = b["role"], b.get("qp", "")
        indent = b.get("indent", "")
        zl = [qp + indent + z for z in zh.split("\n")]
        blank = qp.rstrip()
        mode = cfg.get("md_list", "soft") if role == "list" else "paragraph"
        if role == "callout":
            new = zl
        elif mode == "soft":
            new = zl
        elif mode == "br":
            last = self.replace.get(b["end"], self.lines[b["end"]])
            self.replace[b["end"]] = last.rstrip() + "<br>"
            new = zl
        else:
            new = [blank] + zl
            nxt = b["end"] + 1
            if nxt < len(self.lines) and self.lines[nxt].strip() and self.lines[nxt].strip() != qp.strip():
                new.append(blank)
        self.after.setdefault(b["end"], []).extend(new)

    def add_inline(self, b, zh, cfg, sep):
        li = b["end"]
        line = self.replace.get(li, self.lines[li])
        self.replace[li] = line.rstrip() + sep + zh.replace("\n", " ")

    def add_cell(self, b, zh, cfg):
        li = b["start"]
        line = self.replace.get(li, self.lines[li])
        spans = split_cells(line)
        a, e = spans[b["col"]]
        cell = line[a:e]
        lead = cell[:len(cell) - len(cell.lstrip())]
        trail = cell[len(cell.rstrip()):]
        new = lead + cell.strip() + "<br>" + zh.replace("|", "\\|").replace("\n", "<br>") + (trail or " ")
        self.replace[li] = line[:a] + new + line[e:]

    def save(self, out):
        res = []
        for i, line in enumerate(self.lines):
            res.append(self.replace.get(i, line))
            res.extend(self.after.get(i, []))
        text = self.newline.join(res) + (self.newline if self.trailing else "")
        open(out, "w", encoding="utf-8", newline="").write(text)
