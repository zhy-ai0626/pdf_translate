"""Shared PDF-mode helpers: paragraph extraction (stable ids P1..Pn), content boxes,
clean horizontal cuts, CJK text layout. Needs PyMuPDF.

When the running Python has no PyMuPDF (DeepSeek Harness' bundled Python), the
scripts re-run themselves with another interpreter that has it: env
PPTX_ZH_PDF_PY, then python3 on PATH and common install locations.
"""
import os
import re
import shutil
import subprocess
import sys

PUA = re.compile(r"^[-•▪◦●■□◆◇►▶➢➤✓✔\-–—·*]+\s*")
WORD = re.compile(r"[A-Za-z]{2,}")
CJK = re.compile(r"[㐀-鿿豈-﫿]")
CLOSE_PUNCT = set("，。、；：？！）》」』】”’,.;:?!)]}%")


def ensure_pymupdf(need_lxml=False):
    """Import pymupdf or re-exec this script under a Python that has it."""
    try:
        import pymupdf  # noqa: F401
        if need_lxml:
            import lxml  # noqa: F401
        return
    except ImportError:
        pass
    if os.environ.get("PPTX_ZH_REEXEC"):
        raise SystemExit("PyMuPDF not importable in %s either" % sys.executable)
    test = "import pymupdf" + (", lxml" if need_lxml else "")
    cands = [os.environ.get("PPTX_ZH_PDF_PY"), shutil.which("python3"), "/opt/homebrew/bin/python3",
             "/usr/local/bin/python3", "/usr/bin/python3"]
    for c in cands:
        if not c or not os.path.exists(c) or os.path.realpath(c) == os.path.realpath(sys.executable):
            continue
        try:
            ok = subprocess.run([c, "-c", test], capture_output=True, timeout=60).returncode == 0
        except (OSError, subprocess.TimeoutExpired):
            ok = False
        if ok:
            print("(PyMuPDF missing here; re-running with %s)" % c, file=sys.stderr)
            env = dict(os.environ, PPTX_ZH_REEXEC="1")
            os.execve(c, [c] + sys.argv, env)
    raise SystemExit(
        "PDF mode needs PyMuPDF, and no Python with it was found.\n"
        "Set PPTX_ZH_PDF_PY=/path/to/python3 (one that can `import pymupdf`), or run this step in "
        "Claude Code / Codex. Do not pip-install inside DeepSeek Harness.")


def parse_pages(spec, total):
    if not spec:
        return list(range(1, total + 1))
    pages = []
    for part in spec.split(","):
        if "-" in part:
            a, b = part.split("-")
            pages.extend(range(int(a), int(b) + 1))
        else:
            pages.append(int(part))
    return [p for p in pages if 1 <= p <= total]


def has_cjk(s):
    return bool(CJK.search(s or ""))


def rgb(c):
    return ((c >> 16) & 255) / 255, ((c >> 8) & 255) / 255, (c & 255) / 255


def area(r):
    return max(r[2] - r[0], 0) * max(r[3] - r[1], 0)


def inter(a, b):
    w = min(a[2], b[2]) - max(a[0], b[0])
    h = min(a[3], b[3]) - max(a[1], b[1])
    return w * h if w > 0 and h > 0 else 0.0


# ---------------------------------------------------------------- extraction

def _lines(page):
    out = []
    for bi, b in enumerate(page.get_text("dict")["blocks"]):
        if b.get("type") != 0:
            continue
        for ln in b["lines"]:
            spans = [s for s in ln["spans"] if s["text"].strip()]
            if not spans:
                continue
            raw = "".join(s["text"] for s in ln["spans"])
            m = PUA.match(raw.lstrip())
            bullet = bool(m and m.group(0).strip())
            text = raw.strip()
            text = PUA.sub("", text, count=1) if bullet else text
            # x where the words start (after the bullet glyph)
            first = next((s for s in spans if not PUA.fullmatch(s["text"].strip())), None)
            tx = ln["bbox"][0]
            if first is not None:  # where the words start: skip bullet glyph and spaces (estimated widths)
                t = first["text"]
                body = t.lstrip()
                m2 = PUA.match(body) if bullet else None
                skip_chars = len(t) - len(body) + (len(m2.group(0)) if m2 else 0)
                tx = first["bbox"][0] + skip_chars * 0.3 * first["size"]
            big = max(spans, key=lambda s: len(s["text"].strip()))
            colors = {}
            for s_ in spans:
                colors[s_["color"]] = colors.get(s_["color"], 0) + len(s_["text"].strip())
            out.append({"block": bi, "bbox": list(ln["bbox"]), "tx": tx, "text": text.strip(),
                        "bullet": bullet, "size": max(s["size"] for s in spans),
                        "color": big["color"], "colors": colors, "font": big["font"], "dir": ln.get("dir", (1, 0))})
    return out


def _merge_bullets(lines):
    """A bullet glyph extracted as its own line (Beamer, some exporters) joins the text right of it."""
    out, used = [], set()
    for i, ln in enumerate(lines):
        if i in used:
            continue
        if ln["bullet"] and not ln["text"]:
            best = None
            for j, o in enumerate(lines):
                if j == i or j in used or not o["text"]:
                    continue
                dx = o["bbox"][0] - ln["bbox"][2]
                if abs(o["bbox"][1] - ln["bbox"][1]) < 0.5 * o["size"] and -1 <= dx < 3 * o["size"]:
                    if best is None or dx < best[0]:
                        best = (dx, j)
            if best:
                o = dict(lines[best[1]])
                used.add(best[1])
                o["bbox"] = [ln["bbox"][0], min(ln["bbox"][1], o["bbox"][1]), o["bbox"][2], max(ln["bbox"][3], o["bbox"][3])]
                o["bullet"] = True
                out.append(o)
                continue
        out.append(ln)
    return out


def paragraphs(page):
    """Group rendered lines into paragraphs. Ids P1..Pn follow content order."""
    paras = []
    prev = None
    for ln in _merge_bullets(_lines(page)):
        if abs(ln["dir"][1]) > 0.1:  # rotated text: own paragraph
            cont = False
        elif prev is None:
            cont = False
        else:
            p = prev
            gap = ln["bbox"][1] - p["bbox"][3]
            # justified text can split one visual line into pieces with wide word gaps
            same_line = abs(ln["bbox"][1] - p["bbox"][1]) < 0.3 * p["size"] and 0 <= ln["bbox"][0] - p["bbox"][2] < 2 * p["size"]
            # a line starting exactly at the text start of a bullet line above is its wrapped continuation,
            # even when the deck uses loose line spacing
            hanging = paras[-1]["bullet"] and abs(ln["bbox"][0] - paras[-1]["row_x"][1]) < 0.3 * p["size"] \
                and abs(ln["bbox"][0] - paras[-1]["row_x"][0]) > 0.3 * p["size"]
            cont = (not ln["bullet"] and ln["block"] - p["block"] <= 1 and abs(ln["size"] - p["size"]) < 0.6
                    and ((-0.4 * p["size"] < gap < 0.3 * p["size"] and min(abs(ln["bbox"][0] - x) for x in paras[-1]["row_x"]) < 0.6 * p["size"])
                         or (hanging and -0.4 * p["size"] < gap < 0.9 * p["size"])
                         or same_line))
        if cont:
            P = paras[-1]
            if not same_line:
                P["row_x"] = (ln["bbox"][0], ln["tx"])
            P["lines"].append(ln)
            P["text"] += (" " if not (has_cjk(P["text"][-1:]) or has_cjk(ln["text"][:1])) else "") + ln["text"]
            P["bbox"] = [min(P["bbox"][0], ln["bbox"][0]), min(P["bbox"][1], ln["bbox"][1]),
                         max(P["bbox"][2], ln["bbox"][2]), max(P["bbox"][3], ln["bbox"][3])]
        else:
            paras.append({"lines": [ln], "text": ln["text"], "bbox": list(ln["bbox"]), "tx": ln["tx"], "row_x": (ln["bbox"][0], ln["tx"]),
                          "size": ln["size"], "color": ln["color"], "bullet": ln["bullet"], "font": ln["font"]})
        prev = ln
    for i, P in enumerate(paras, 1):
        P["id"] = "P%d" % i
        tally = {}
        for ln in P["lines"]:
            for c, n in ln.get("colors", {}).items():
                tally[c] = tally.get(c, 0) + n
        if tally:  # Chinese follows the colour of most of the English, not of a coloured lead-in term
            P["color"] = max(tally, key=tally.get)
        t = P["text"]
        P["kind"] = "zh" if has_cjk(t) else ("en" if WORD.search(t) else "misc")
    return paras


def page_objects(page):
    """Images and vector drawings with a 'background' flag (covers most of the page)."""
    W, H = page.rect.width, page.rect.height
    imgs = []
    for im in page.get_image_info():
        b = list(im["bbox"])
        b = [max(b[0], 0), max(b[1], 0), min(b[2], W), min(b[3], H)]
        if area(b) < 30:
            continue
        imgs.append({"bbox": b, "bg": area(b) > 0.5 * W * H})
    draws = []
    for d in page.get_drawings():
        r = d["rect"]
        b = [max(r.x0, 0), max(r.y0, 0), min(r.x1, W), min(r.y1, H)]
        if b[2] < b[0] or b[3] < b[1]:
            continue
        draws.append({"bbox": b, "items": d["items"], "bg": area(b) > 0.5 * W * H, "fill": d.get("fill")})
    return imgs, draws


def mark_footer(paras, ft):
    """English in the footer zone (course code, lecturer name) is kind 'footer': no Chinese required."""
    for P in paras:
        if P["kind"] == "en" and P["bbox"][1] >= ft - 0.5:
            P["kind"] = "footer"


def footer_top(page, paras, imgs, draws):
    """Top of the footer zone (page number, logos in the bottom 15%); content there never moves."""
    H = page.rect.height
    lim = 0.85 * H
    def footer_like(P):  # page numbers, course codes, lecturer names: short and small
        return len(P["text"]) <= 12 or P["size"] <= 14
    boxes = [(P["bbox"], footer_like(P)) for P in paras] + [(o["bbox"], True) for o in imgs + draws if not o["bg"]]
    body = [b for b, ok in boxes if b[1] < lim or not ok]
    foot = [b for b, ok in boxes if b[1] >= lim and ok]
    if not foot:
        return H
    ft = min(b[1] for b in foot)
    low = max([b[3] for b in body] or [0])
    return ft if low <= ft else H


# ---------------------------------------------------------------- cuts

def _boundaries(draws, xr=None):
    ys = []
    for d in draws:
        if not _in_x(d["bbox"], xr):
            continue
        for it in d["items"]:
            kind = it[0]
            if kind == "re":
                r = it[1]
                ys += [r.y0, r.y1]
            elif kind == "l":
                p, q = it[1], it[2]
                if abs(p.y - q.y) < 0.5:
                    ys.append(p.y)
            elif kind == "qu":
                q = it[1]
                ys += [q.rect.y0, q.rect.y1]
    return ys


def _in_x(b, xr):
    return xr is None or (b[2] > xr[0] + 0.5 and b[0] < xr[1] - 0.5)


def cut_problems(y, paras, imgs, draws, xr=None):
    """Why a cut at y across x-range xr (None = full width) would look wrong. The opened
    gap is filled by stretching a thin slice at y, so rects/vertical lines continue."""
    bad = []
    for P in paras:
        for ln in P["lines"]:
            b = ln["bbox"]
            if b[1] + 0.5 < y < b[3] - 0.5 and _in_x(b, xr):
                bad.append("text %s" % P["id"])
                break
    for im in imgs:
        b = im["bbox"]
        if not im["bg"] and b[1] + 0.5 < y < b[3] - 0.5 and _in_x(b, xr):
            bad.append("picture [%d,%d,%d,%d]" % tuple(b))
    for d in draws:
        if not _in_x(d["bbox"], xr):
            continue
        for it in d["items"]:
            if it[0] == "c":
                ys = [pt.y for pt in it[1:5]]
                if min(ys) + 0.5 < y < max(ys) - 0.5:
                    bad.append("curve [%d,%d,%d,%d]" % tuple(d["bbox"]))
                    break
            elif it[0] == "l":
                p, q = it[1], it[2]
                if min(p.y, q.y) + 0.5 < y < max(p.y, q.y) - 0.5 and abs(p.x - q.x) > 0.5:
                    bad.append("slanted line [%d,%d,%d,%d]" % tuple(d["bbox"]))
                    break
    return bad


def find_cut(lo, hi, paras, imgs, draws, xr=None, from_top=True):
    """A y in [lo, hi] where a cut across xr is clean and >=1pt from horizontal edges; None if none.
    Searches downward from lo (from_top) or upward from hi."""
    edges = _boundaries(draws, xr)
    steps = int(max(hi - lo, 0) / 0.5) + 1
    for i in range(steps):
        y = lo + i * 0.5 if from_top else hi - i * 0.5
        if all(abs(y - e) >= 1.0 for e in edges) and not cut_problems(y, paras, imgs, draws, xr):
            return round(y, 2)
    return None


def column_at(y, P, paras, imgs, draws, W):
    """x-range around paragraph P that a cut at y can span without crossing anything; None if blocked."""
    x0, x1 = 0.0, W
    obstacles = [ln["bbox"] for o in paras if o is not P for ln in o["lines"]]
    obstacles += [o["bbox"] for o in imgs + draws if not o["bg"]]
    for b in obstacles:
        if not (b[1] + 0.5 < y < b[3] - 0.5):
            continue
        if b[0] >= P["lines"][-1]["bbox"][2] - 0.5:  # beside the last line (the cut is under it)
            x1 = min(x1, b[0] - 1)
        elif b[2] <= P["bbox"][0] + 0.5:
            x0 = max(x0, b[2] + 1)
        else:
            return None
    return [x0, x1]


def cut_for(P, top, paras, imgs, draws, W):
    """Where room can be opened under P: (y, x-range or None for full width), or (None, None)."""
    lo, hi = P["bbox"][3] + 0.5, max(P["bbox"][3] + 0.5, top - 0.5)
    y = find_cut(lo, hi, paras, imgs, draws)
    if y is not None:
        return y, None
    yy = lo
    while yy <= hi + 1e-6:
        xr = column_at(yy, P, paras, imgs, draws, W)
        if xr and xr[1] - xr[0] > 0.3 * W:
            y = find_cut(yy, hi, paras, imgs, draws, xr)
            if y is not None:
                return y, xr
        yy += 0.5
    return None, None


def below_right(P, paras, imgs, draws, W):
    """Right edge for Chinese placed under P: stop before text/pictures/rules beside or just below it."""
    right = W - 20
    for o in paras:
        for ln in o["lines"]:
            b = ln["bbox"]
            # only things beside P (starting above its bottom) narrow it; content starting below is moved down
            if o is not P and b[0] > P["tx"] + 20 and b[1] < P["bbox"][3] - 1 and b[3] > P["bbox"][3] - 1:
                right = min(right, b[0] - 6)
    for o in imgs + draws:
        b = o["bbox"]
        if not o["bg"] and b[0] > P["tx"] + 20 and b[1] < P["bbox"][3] - 1 and b[3] > P["bbox"][3] - 1:
            right = min(right, b[0] - 6)  # includes vertical cell borders
    return right


def free_below(P, paras, imgs, draws, W, limit, x1=None):
    """Free vertical space under paragraph P within x tx..x1 (default: to the right margin)."""
    x0, x1 = P["tx"], (x1 if x1 is not None else W - 20)
    top = limit
    for o in paras:
        if o is P:
            continue
        b = o["bbox"]
        if b[1] >= P["bbox"][3] - 1 and b[2] > x0 and b[0] < x1:
            top = min(top, b[1])
    for o in imgs + draws:
        if o["bg"]:
            continue
        b = o["bbox"]
        if b[1] >= P["bbox"][3] - 1 and b[2] > x0 and b[0] < x1:  # thin rules count too (table borders)
            top = min(top, b[1])
    return top - P["bbox"][3], top


def free_right(P, paras, imgs, draws, W):
    """x range free to the right of P's first line."""
    b = P["lines"][0]["bbox"]
    right = W - 20
    for o in paras:
        if o is P:
            continue
        for ln in o["lines"]:
            c = ln["bbox"]
            if c[0] >= b[2] - 1 and c[1] < b[3] and c[3] > b[1]:
                right = min(right, c[0])
    for o in imgs + draws:
        c = o["bbox"]
        # a picture beside the line, or one the line already runs into (logo with blank margin)
        if not o["bg"] and c[2] > b[2] and c[0] > b[0] + 2 and c[1] < b[3] and c[3] > b[1] and (c[2] - c[0]) > 2:
            right = min(right, max(c[0], b[2]))
    return b[2], right


# ---------------------------------------------------------------- text layout

_FONTS = {}


def font(path=None):
    import pymupdf
    key = path or "cjk"
    if key not in _FONTS:
        _FONTS[key] = pymupdf.Font(fontfile=path) if path else pymupdf.Font("cjk")
    return _FONTS[key]


def _tokens(text):
    toks = re.findall(r"[A-Za-z0-9_.+\-/%=×()]+|\s+|.", text)
    out = []
    for t in toks:
        if out and (t[0] in CLOSE_PUNCT) and not out[-1].isspace():
            out[-1] += t
        else:
            out.append(t)
    return out


def wrap(text, width, pt, fnt):
    lines = []
    for para in text.split("\n"):
        cur = ""
        for tok in _tokens(para):
            if fnt.text_length(cur + tok, pt) <= width or not cur.strip():
                cur += tok
            else:
                lines.append(cur.rstrip())
                cur = tok.lstrip()
        lines.append(cur.rstrip())
    return lines


def text_height(n, pt):
    return n * pt * 1.25


def fit(text, width, pt, min_pt, max_h, fnt):
    """Largest size from pt down to min_pt whose wrapped height fits max_h (None = no limit)."""
    size = pt
    while True:
        lines = wrap(text, width, size, fnt)
        h = text_height(len(lines), size)
        if max_h is None or h <= max_h + 0.5 or size - 0.5 < min_pt:
            return size, lines, h, (max_h is None or h <= max_h + 0.5)
        size -= 0.5


def draw_lines(page, x, y, width, lines, pt, color, align, fnt, fill=None):
    import pymupdf
    h = text_height(len(lines), pt)
    if fill:
        page.draw_rect(pymupdf.Rect(x - 2, y - 1, x + width + 2, y + h + 1), color=None, fill=rgb(int(fill, 16)), overlay=True)
    tw = pymupdf.TextWriter(page.rect)
    asc = fnt.ascender
    lead = (1.25 - (fnt.ascender - fnt.descender)) * pt / 2
    for i, s in enumerate(lines):
        if not s:
            continue
        L = fnt.text_length(s, pt)
        dx = 0 if align == "l" else (width - L if align == "r" else (width - L) / 2)
        tw.append((x + dx, y + i * pt * 1.25 + lead + asc * pt), s, font=fnt, fontsize=pt)
    tw.write_text(page, color=color)
    return [x, y, x + width, y + h]
