"""Layout checks estimated from the slide XML, for environments without PyMuPDF
(e.g. DeepSeek Harness' bundled Python, which only ships lxml).

Text size is estimated from character classes (CJK = 1 em, Latin ~0.52 em,
monospace 0.6 em), so results are approximate: they catch Chinese boxes that
clearly overflow, overlap other text, leave the slide or are too small, not
1-2 pt collisions. Prefer the rendered PDF check when PyMuPDF is available.
"""
import re

from lxml import etree

from ooxml import (CJK, EMU_PER_PT, NS, has_cjk, iter_shapes, para_text, q,
                   resolve_box, resolve_para, shape_id)

MONO = ("consolas", "courier", "mono", "menlo")


def char_em(ch, mono):
    if CJK.match(ch):
        return 1.0
    if mono:
        return 0.55  # Consolas / Menlo advance width
    if ch in "il.,:;'!|ftjI ":
        return 0.3
    if ch.isupper() or ch in "mwMW@%":
        return 0.68
    return 0.52


def text_width(text, size_pt, mono=False):
    tabs = text.count("\t")
    text = re.sub(r" {2,}", " ", text.replace("\t", ""))
    return sum(char_em(c, mono) for c in text) * size_pt + tabs * 36  # ~0.5 inch per tab stop


def theme_fonts(deck, n):
    """{'+mj-lt': major latin typeface, '+mn-lt': minor} from the slide master's theme."""
    _, master = deck.layout_and_master(n)
    theme = deck.related(master, "theme") if master else None
    out = {}
    if theme:
        fs = deck.xml(theme).find(".//a:fontScheme", NS)
        for key, tag in (("+mj-lt", "a:majorFont"), ("+mn-lt", "a:minorFont")):
            el = fs.find(tag + "/a:latin", NS) if fs is not None else None
            if el is not None:
                out[key] = el.get("typeface")
    return out


def para_font(deck, n, shape, p, level):
    """Latin typeface a paragraph's runs inherit (run -> pPr defRPr -> list styles -> theme)."""
    from ooxml import style_chain
    ppr = p.find("a:pPr", NS)
    for c in ([ppr] if ppr is not None else []) + style_chain(deck, n, shape, level):
        d = c.find("a:defRPr/a:latin", NS)
        if d is not None and d.get("typeface"):
            face = d.get("typeface")
            return theme_fonts(deck, n).get(face, face)
    ph = deck.ph_of(shape)
    key = "+mj-lt" if ph is not None and ph.get("type") in ("title", "ctrTitle") else "+mn-lt"
    return theme_fonts(deck, n).get(key, "")


def run_sizes(p, default, inherited_mono=False):
    out = []
    runs = p.findall("a:r", NS)
    for k, r in enumerate(runs):
        rpr = r.find("a:rPr", NS)
        sz = int(rpr.get("sz")) / 100 if rpr is not None and rpr.get("sz") else default
        latin = rpr.find("a:latin", NS) if rpr is not None else None
        mono = any(m in (latin.get("typeface") or "").lower() for m in MONO) if latin is not None else inherited_mono
        text = "".join(t.text or "" for t in r.iter(q("a:t")))
        if k == len(runs) - 1:
            text = text.rstrip()  # trailing spaces take no visible width
        out.append((text, sz, mono))
    return out


def estimate_shape(deck, n, shape, groups):
    """Box plus one estimated text rectangle per paragraph [x0, y0, x1, y1] and min Chinese size."""
    box = resolve_box(deck, n, shape, groups)
    body = shape.find("p:txBody", NS)
    if box is None or body is None:
        return None
    bpr = body.find("a:bodyPr", NS)
    ins = lambda k, d: int(bpr.get(k, d)) / EMU_PER_PT if bpr is not None else d / EMU_PER_PT
    lI, rI, tI, bI = ins("lIns", 91440), ins("rIns", 91440), ins("tIns", 45720), ins("bIns", 45720)
    wrap = bpr is None or bpr.get("wrap") != "none"
    paras, y, zh_min = [], 0.0, None
    for p in body.findall("a:p", NS):
        st = resolve_para(deck, n, shape, p)
        scale = st["fontScale"]
        face = para_font(deck, n, shape, p, st["level"]).lower()
        runs = run_sizes(p, st["sz"] / 100, any(m in face for m in MONO))
        size = max([s for _, s, _ in runs] or [st["sz"] / 100]) * scale
        left = lI + st["marL"] / EMU_PER_PT
        avail = max(box[2] - left - rI, 20)
        width = sum(text_width(t, s * scale, m) for t, s, m in runs)
        lines = max(1, -(-int(width) // int(avail * 1.05))) if wrap and width > avail * 1.05 else 1
        h = lines * size * 1.2
        text = para_text(p)
        if text.strip():
            line_h = size * 1.2
            if lines > 1:  # full-width block for the wrapped lines + the shorter last line
                last_w = max(width - (lines - 1) * avail, size)
                rels = [[left, y, left + avail, y + h - line_h], [left, y + h - line_h, left + last_w, y + h]]
            else:
                rels = [[left, y, left + (min(width, avail) if wrap else width), y + h]]
            for rel in rels:
                paras.append({"rel": rel, "zh": has_cjk(text), "text": text[:60]})
        y += h
        for t, s, _ in runs:
            if has_cjk(t):
                zh_min = s * scale if zh_min is None else min(zh_min, s * scale)
    anchor = bpr.get("anchor") if bpr is not None else None
    for inherited in ([] if anchor else deck.ph_chain(n, shape)):  # placeholders inherit anchoring
        ib = inherited.find("p:txBody/a:bodyPr", NS)
        if ib is not None and ib.get("anchor"):
            anchor = ib.get("anchor")
            break
    anchor = anchor or "t"
    text_h = y + tI + bI
    top = box[1] + tI if anchor == "t" else box[1] + tI + (box[3] - text_h) / (2 if anchor == "ctr" else 1)
    for pr in paras:
        r = pr.pop("rel")
        pr["rect"] = [box[0] + r[0], top + r[1], box[0] + r[2], top + r[3]]
    return {"box": box, "paras": paras, "text_h": text_h, "zh_min": zh_min}


def inter(a, b):
    w = min(a[2], b[2]) - max(a[0], b[0])
    h = min(a[3], b[3]) - max(a[1], b[1])
    return w * h if w > 0 and h > 0 else 0.0


def area(r):
    return max(r[2] - r[0], 0) * max(r[3] - r[1], 0)


def check_slide(deck, n, min_pt, prefix="ZH "):
    slide = deck.slide(n)
    items = []
    for shape, groups in iter_shapes(slide):
        if etree.QName(shape).localname != "sp":
            continue
        est = estimate_shape(deck, n, shape, groups)
        if not est or not est["paras"]:
            continue
        sid, name = shape_id(shape)
        est.update(id=sid, added=(name or "").startswith(prefix), zh=est["zh_min"] is not None,
                   text=" / ".join(p["text"] for p in est["paras"])[:60])
        items.append(est)
    issues = []
    W, H = deck.width_pt, deck.height_pt
    for it in items:
        if not it["zh"]:
            continue
        if it["zh_min"] < min_pt - 0.3:
            issues.append({"level": "error", "type": "too_small", "size": round(it["zh_min"], 1), "text": it["text"]})
        for pr in it["paras"]:
            r = pr["rect"]
            beyond = max(-r[1], r[3] - H, r[2] - W)
            if pr["zh"] and beyond > 1:  # estimates are +-10-20 pt: only clear cases are errors
                issues.append({"level": "error" if beyond > 20 else "warn", "type": "out_of_slide(est)",
                               "by_pt": round(beyond), "text": pr["text"]})
        if it["text_h"] > it["box"][3] * 1.15 + 6:
            issues.append({"level": "warn", "type": "overflows_box(est)", "text": it["text"],
                           "est_h": round(it["text_h"]), "box_h": round(it["box"][3])})
    for i, a in enumerate(items):
        for b in items[i + 1:]:
            for pa in a["paras"]:
                for pb in b["paras"]:
                    if not (pa["zh"] or pb["zh"]):
                        continue
                    ov = inter(pa["rect"], pb["rect"])
                    small = min(area(pa["rect"]), area(pb["rect"]))
                    if ov > 0.25 * small:
                        level = "error" if (a["added"] or b["added"]) and ov > 0.5 * small else "warn"
                        issues.append({"level": level, "type": "text_overlap(est)", "a": pa["text"], "b": pb["text"]})
    return issues
