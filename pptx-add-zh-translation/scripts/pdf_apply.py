"""PDF mode, step 2: apply a translation plan to a PDF and write a new bilingual PDF.

Usage: python3 pdf_apply.py lecture.pdf plan.json out.pdf [--report rep.json] [--merge b2.json b3.json ...]
(--merge adds the pages of further batch plans; a page listed twice takes the last one.)

Plan format: references/pdf-mode.md. The original stays vector: edited pages are
rebuilt from clipped pieces of the original page (show_pdf_page), so English text
remains selectable. Room for Chinese under a paragraph is opened by cutting the page
(full width, or per column) below it and shifting what follows down; the opened gap
is filled by stretching a thin slice at the cut, so backgrounds, boxes and table
borders continue. If a column no longer fits, it is scaled down evenly from just
above its first translated paragraph (below defaults.min_en_scale = 0.75 the page is
reported as an error). Pages without ops are copied unchanged; links on edited pages
are dropped.
"""
import argparse
import json
import sys
from pathlib import Path

from pdfmodel import ensure_pymupdf

ensure_pymupdf()
import pymupdf  # noqa: E402

from pdfmodel import (cut_for, draw_lines, find_cut, fit, font,  # noqa: E402
                      below_right, footer_top, free_below, free_right, mark_footer, page_objects,
                      paragraphs, rgb, text_height)

DEFAULTS = {"min_pt": 12, "scale": 0.75, "title_scale": 0.5, "color": None, "font": None,
            "pad": 2, "min_en_scale": 0.75}


ALIGN = {"l": "l", "left": "l", "ctr": "ctr", "c": "ctr", "center": "ctr", "centre": "ctr", "r": "r", "right": "r"}
ANCHOR = {"t": "t", "top": "t", "ctr": "ctr", "c": "ctr", "center": "ctr", "centre": "ctr", "middle": "ctr",
          "b": "b", "bottom": "b"}


def normalize(op, errs):
    """Accept left/center/right and top/middle/bottom spellings; anything else is an error, not a silent centre."""
    for key, table in (("align", ALIGN), ("anchor", ANCHOR)):
        if key in op:
            v = table.get(str(op[key]).lower())
            if v is None:
                errs.append({"level": "error", "type": "bad_value", "op": op.get("op"),
                             "why": "%s=%r; use %s" % (key, op[key], "l/ctr/r" if key == "align" else "t/ctr/b")})
                v = "l" if key == "align" else "t"
            op[key] = v


class Flow:
    """A column (x0..x1) whose content below `origin` moves down by the gaps and is scaled by s."""

    def __init__(self, x0, x1, bottom):
        self.x0, self.x1, self.bottom = x0, x1, bottom
        self.cuts = {}  # source y -> gap height (source units)
        self.s = 1.0
        self.top = None  # clean cut just above the first translated paragraph
        self.reqs = []

    def origin(self):
        if not self.cuts:
            return None
        c = min(self.cuts)
        return min(c, self.top) if self.top is not None else c

    def off(self, y):
        return sum(g for c, g in self.cuts.items() if c <= y)

    def inside(self, x, y):
        return bool(self.cuts) and self.x0 - 0.5 <= x <= self.x1 + 0.5 and self.origin() <= y < self.bottom - 0.5

    def map(self, x, y):
        c1 = self.origin()
        return self.x0 + (x - self.x0) * self.s, c1 + (y + self.off(y) - c1) * self.s


class Layout:
    def __init__(self, flows):
        self.flows = flows

    def at(self, x, y):
        return next((f for f in self.flows if f.inside(x, y)), None)

    def map(self, x, y):
        f = self.at(x, y)
        return f.map(x, y) if f else (x, y)

    def s(self, x, y):
        f = self.at(x, y)
        return f.s if f else 1.0


def boxes_of(ctx):
    return [ln["bbox"] for P in ctx["paras"] for ln in P["lines"]] + \
        [o["bbox"] for o in ctx["imgs"] + ctx["draws"] if not o["bg"]]


def make_flows(ctx, cut_req, errs):
    """Group cut requests into columns that move independently."""
    W = ctx["W"]
    ok = [r for r in cut_req if r["y"] is not None]
    for r in cut_req:
        if r["y"] is None:
            errs.append({"level": "error", "type": "no_room", "p": r["P"]["id"],
                         "why": "nothing below can move (picture/shape/other column in the way): "
                                "use right, a textbox beside it, move, or a smaller pt"})
    if not ok:
        return []
    if all(r["xr"] is None for r in ok):
        clusters = [ok]
    else:
        clusters = []
        for r in sorted(ok, key=lambda r: r["P"]["tx"]):
            if clusters and r["P"]["tx"] - clusters[-1][0]["P"]["tx"] < 0.25 * W:
                clusters[-1].append(r)
            else:
                clusters.append([r])
    flows = []
    for cl in clusters:
        x0, x1 = 0.0, W
        for r in cl:
            if r["xr"]:
                x0, x1 = max(x0, r["xr"][0]), min(x1, r["xr"][1])
        f = Flow(x0, x1, ctx["ft"])
        f.reqs = cl
        flows.append(f)
    # neighbouring columns must not overlap: split between their paragraphs
    for a, b in zip(flows, flows[1:]):
        if a.reqs and b.reqs and a.x1 > b.x0:
            a_right = max(r["P"]["bbox"][2] for r in a.reqs)
            b_left = min(r["P"]["bbox"][0] for r in b.reqs)
            if a_right < b_left:
                mid = (a_right + b_left) / 2
                a.x1, b.x0 = min(a.x1, mid), max(b.x0, mid)
            else:
                for r in b.reqs:
                    errs.append({"level": "error", "type": "no_room", "p": r["P"]["id"],
                                 "why": "overlaps the column to its left; use right/textbox"})
                b.reqs = []
    flows = [f for f in flows if f.reqs]
    for f in flows:
        if f.x0 <= 0.5 and f.x1 >= W - 0.5:
            continue
        # anything straddling the column's side edges stops the column above it
        ytop = min(r["y"] for r in f.reqs)
        for b in boxes_of(ctx):
            if b[3] > ytop + 0.5 and b[1] < f.bottom and b[2] > f.x0 and b[0] < f.x1 \
                    and (b[0] < f.x0 - 0.5 or b[2] > f.x1 + 0.5) and b[1] > ytop:
                f.bottom = min(f.bottom, b[1] - 0.5)
        keep = []
        for r in f.reqs:
            if r["y"] > f.bottom - 1:
                errs.append({"level": "error", "type": "no_room", "p": r["P"]["id"],
                             "why": "something below it spans into the next column; use right/textbox"})
            else:
                keep.append(r)
        f.reqs = keep
    flows = [f for f in flows if f.reqs]
    # scale origin: just above the first translated paragraph of the column
    for f in flows:
        P0 = min((r["P"] for r in f.reqs), key=lambda P: P["bbox"][1])
        xr = None if (f.x0 <= 0.5 and f.x1 >= W - 0.5) else [f.x0, f.x1]
        lo = max([P["bbox"][3] for P in ctx["paras"] if P["bbox"][3] <= P0["bbox"][1] + 0.5
                  and (xr is None or (P["bbox"][2] > xr[0] and P["bbox"][0] < xr[1]))], default=0)
        f.top = find_cut(max(lo, P0["bbox"][1] - P0["size"]), P0["bbox"][1] - 0.5,
                         ctx["paras"], ctx["imgs"], ctx["draws"], xr, from_top=False)
        if f.top is not None and xr is not None and any(
                b[3] > f.top and b[1] < f.bottom and b[2] > xr[0] and b[0] < xr[1]
                and (b[0] < xr[0] - 0.5 or b[2] > xr[1] + 0.5) for b in boxes_of(ctx)):
            f.top = None
        if f.top is not None and xr is None:
            # the scale origin must not run through a table/frame: lines above it would keep their
            # size while the rest shrinks. Lift it to just above whatever line art it crosses.
            y = f.top
            for _ in range(10):
                cross = [d["bbox"] for d in ctx["draws"] if not d["bg"] and d["bbox"][1] < y - 0.5 < d["bbox"][3] - 1]
                if not cross:
                    break
                y = min(b[1] for b in cross) - 1
            solid = [ln["bbox"] for P in ctx["paras"] for ln in P["lines"]] + [o["bbox"] for o in ctx["imgs"] if not o["bg"]]
            if 0 < y < f.top and not any(b[1] < y < b[3] for b in solid):
                f.top = y
    return flows


def plan_page(src_page, entry, d, fnt, errs):
    W, H = src_page.rect.width, src_page.rect.height
    paras = paragraphs(src_page)
    byid = {P["id"]: P for P in paras}
    imgs, draws = page_objects(src_page)
    ft = footer_top(src_page, paras, imgs, draws)
    mark_footer(paras, ft)
    ctx = {"W": W, "H": H, "paras": paras, "imgs": imgs, "draws": draws, "ft": ft}
    covered, skipped, moves, cut_req = set(), set(), [], []

    def para(pid, op):
        P = byid.get(pid)
        if P is None:
            errs.append({"level": "error", "type": "bad_id", "op": op.get("op"), "p": pid})
        return P

    for op in entry["ops"]:
        kind = op["op"]
        normalize(op, errs)
        covered.update(op.get("covers", []))
        if kind == "skip":
            skipped.update(op["p"] if isinstance(op["p"], list) else [op["p"]])
        elif kind == "existing":
            covered.add(op["p"])
        elif kind == "move":
            P = para(op["p"], op) if "p" in op else None
            rect = [v + e for v, e in zip(P["bbox"], (-1, -1, 1, 1))] if P else op.get("rect")
            if rect:
                moves.append({"rect": rect, "dx": op.get("dx", 0), "dy": op.get("dy", 0), "scale": op.get("scale", 1)})
        elif kind in ("below", "right", "gap"):
            P = para(op.get("p") or op.get("after"), op)
            if P is None:
                continue
            if kind != "gap":
                covered.add(P["id"])
            if kind == "right" or op.get("room", "auto") == "none":
                continue
            free, top = free_below(P, paras, imgs, draws, W, ft, below_right(P, paras, imgs, draws, W))
            y, xr = cut_for(P, top, paras, imgs, draws, W)
            cut_req.append({"op": op, "P": P, "free": free, "top": top, "y": y, "xr": xr})
        elif kind != "textbox":
            errs.append({"level": "error", "type": "unknown_op", "op": kind})

    flows = make_flows(ctx, cut_req, errs)
    lay = Layout(flows)

    def zh_pt(op, P, s):
        if "pt" in op:
            return op["pt"]
        k = op.get("scale", d["title_scale"] if op["op"] == "right" and P["size"] >= 28 else d["scale"])
        return max(d["min_pt"], round(P["size"] * s * k * 2) / 2)

    def flow_of(P):
        return next((f for f in flows if f.x0 - 0.5 <= P["tx"] <= f.x1 + 0.5
                     and (f.top if f.top is not None else min([r["y"] for r in f.reqs] or [1e9])) <= P["bbox"][3]), None)

    def below_width(op, P):
        if "w" in op:
            return op["w"]
        f = flow_of(P)
        right = below_right(P, paras, imgs, draws, W)
        if f:
            right = min(right, f.x1 - 4)
        return max(right - P["tx"] - op.get("dx", 0), 60)

    def content_bottom(f, c1):
        bs = [b for b in boxes_of(ctx) if b[1] >= c1 - 0.5 and b[3] <= f.bottom + 0.5
              and b[0] >= f.x0 - 0.5 and b[2] <= f.x1 + 0.5]
        return max([b[3] for b in bs] or [c1])

    # requests whose cuts fall in the same blank band (e.g. cells of one table row) share one gap
    for f in flows:
        f.reqs.sort(key=lambda r: r["y"])
        inner = [b for b in boxes_of(ctx) if b[2] > f.x0 and b[0] < f.x1]
        groups = []
        for r in f.reqs:
            if groups and not any(groups[-1][-1]["y"] < (b[1] + b[3]) / 2 < r["y"] for b in inner):
                groups[-1].append(r)
            else:
                groups.append([r])
        for g in groups:  # the lowest cut is clean for all of them (nothing sits between)
            y = max(r["y"] for r in g)
            for r in g:
                r["y"] = y

    # per column: gaps depend on the Chinese height, which depends on the shrink factor s
    for f in flows:
        for _ in range(8):
            cuts, chinese = {}, []
            for r in f.reqs:
                op, P = r["op"], r["P"]
                if op["op"] == "gap":
                    cuts[r["y"]] = cuts.get(r["y"], 0) + op["h"]
                    continue
                pt = zh_pt(op, P, f.s)
                _, lines, h, _ = fit(resolve_text(op), below_width(op, P) * f.s, pt, pt, None, fnt)
                need = h + 2 * d["pad"] + op.get("dy", 0)
                g = max(0.0, need / f.s - r["free"])
                if g > 0:
                    cuts[r["y"]] = max(cuts.get(r["y"], 0), g + 0.5)
                chinese.append((P["bbox"][3], need))
            f.cuts = {c: g for c, g in cuts.items() if g > 0}
            if not f.cuts:
                break
            c1, B = f.origin(), f.bottom - 2
            cb, G = content_bottom(f, c1), sum(f.cuts.values())
            s_new = 1.0 if cb + G <= B else (B - c1) / (cb - c1 + G)
            for yb, need in chinese:  # Chinese under a shifted paragraph must still end above the bottom
                span = yb + f.off(yb) - c1
                if yb >= c1 and span > 0:
                    s_new = min(s_new, (B - need - c1) / span)
            s_new = max(s_new, 0.3)
            if abs(s_new - f.s) < 0.002:
                break
            f.s = s_new
        if f.cuts:
            f.content_bottom = content_bottom(f, f.origin())
            if f.s < d["min_en_scale"] - 0.005:
                errs.append({"level": "error", "type": "too_full",
                             "why": "column x %d..%d would shrink to %d%% (< %d%%): shorter Chinese, right/textbox, or report"
                                    % (f.x0, f.x1, f.s * 100, d["min_en_scale"] * 100)})
            elif f.s < 0.999:
                errs.append({"level": "info", "type": "shrunk", "why": "column x %d..%d from y=%d shrunk to %d%%%s" % (
                    f.x0, f.x1, f.origin(), f.s * 100,
                    "; right side gets a white margin" if f.x0 <= 0.5 and f.x1 >= W - 0.5 else "")})
    flows[:] = [f for f in flows if f.cuts]

    # Chinese boxes in final page coordinates
    boxes = []
    for op in entry["ops"]:
        kind = op["op"]
        color = op.get("color") or d["color"]
        if kind == "below":
            P = byid.get(op["p"])
            if P is None:
                continue
            s = lay.s(P["tx"], P["bbox"][3])
            x, y = lay.map(P["tx"], P["bbox"][3])
            x += op.get("dx", 0) * s
            y += d["pad"] + op.get("dy", 0)
            w = below_width(op, P) * s
            _, top = free_below(P, paras, imgs, draws, W, ft, P["tx"] + w / s)
            max_h = max(lay.map(P["tx"], top)[1] - y - d["pad"], 0)
            size, lines, h, ok = fit(resolve_text(op), w, zh_pt(op, P, s), d["min_pt"], max_h, fnt)
            if not ok:
                errs.append({"level": "error", "type": "overflow", "p": P["id"],
                             "why": "Chinese needs %d pt height, only %d free under it" % (h, max_h)})
            boxes.append({"x": x, "y": y, "w": w, "lines": lines, "pt": size,
                          "color": color or ("%06X" % P["color"]), "align": op.get("align", "l"), "fill": op.get("fill")})
        elif kind == "right":
            P = byid.get(op["p"])
            if P is None:
                continue
            first = P["lines"][0]["bbox"]
            x0, xr = free_right(P, paras, imgs, draws, W)
            s = lay.s(x0, first[1])
            x = lay.map(x0, first[1])[0] + op.get("gap", 10)
            w = op.get("w", lay.map(xr, first[1])[0] - x - 4)
            pt = zh_pt(op, P, s)
            size, lines, h, ok = fit(resolve_text(op), w, pt, d["min_pt"], pt * 1.3, fnt)
            if not ok:
                errs.append({"level": "error", "type": "no_room_right", "p": P["id"],
                             "why": "only %d pt to the right; use below" % w})
            cy = (lay.map(x0, first[1])[1] + lay.map(x0, first[3] - 0.01)[1]) / 2
            boxes.append({"x": x, "y": cy - h / 2 + op.get("dy", 0), "w": w, "lines": lines, "pt": size,
                          "color": color or ("%06X" % P["color"]), "align": "l", "fill": op.get("fill")})
        elif kind == "textbox":
            x, y = lay.map(op["x"], op["y"])
            k = lay.s(op["x"], op["y"])
            max_h = op["h"] * k if "h" in op else None
            size, lines, h, ok = fit(resolve_text(op), op["w"] * k, op.get("pt", 16), d["min_pt"], max_h, fnt)
            if not ok:
                errs.append({"level": "error", "type": "overflow", "box": op.get("name", "textbox"),
                             "why": "text needs %d pt height, box is %d" % (h, max_h)})
            if max_h and op.get("anchor", "t") != "t":
                y += (max_h - h) / (2 if op["anchor"] == "ctr" else 1)
            boxes.append({"x": x, "y": y, "w": op["w"] * k, "lines": lines, "pt": size, "color": color or "000000",
                          "align": op.get("align", "l"), "fill": op.get("fill")})
    uncovered = [P["id"] + " " + P["text"][:50] for P in paras
                 if P["kind"] == "en" and P["id"] not in covered and P["id"] not in skipped]
    return lay, moves, boxes, uncovered


def resolve_text(op):
    return "\n".join(op["lines"]) if "lines" in op else op["zh"]


def drop_pictures_inside(page, rects):
    """Remove (not just blank) non-background pictures lying inside rects, so no invisible copy keeps
    reporting the old position; background pictures are blanked by the later pixel redaction."""
    imgs, _ = page_objects(page)
    hit = [im["bbox"] for im in imgs if not im["bg"] and any(
        im["bbox"][0] >= r[0] - 1 and im["bbox"][1] >= r[1] - 1 and im["bbox"][2] <= r[2] + 1 and im["bbox"][3] <= r[3] + 1
        for r in rects)]
    if hit:
        for b in hit:
            page.add_redact_annot(pymupdf.Rect(b) + (1, 1, -1, -1), fill=False, cross_out=False)
        page.apply_redactions(images=1, graphics=0, text=1)


def build_page(out, src, n, W, H, lay, moves):
    """New page in `out` = original page n with the columns shifted/scaled and moved pieces re-placed."""
    page = out.new_page(width=W, height=H)
    strip_doc = pymupdf.open()
    strip_doc.insert_pdf(src, from_page=n - 1, to_page=n - 1)
    # a full-page background picture (scan) is cut pixel-wise; otherwise pictures and line art only
    # partly inside a moved rect (logo, footer bar) stay where they are and are not carried along
    has_bg = any(im["bg"] for im in page_objects(src[n - 1])[0])
    if moves:
        sp = strip_doc[0]
        drop_pictures_inside(sp, [m["rect"] for m in moves])
        for m in moves:
            sp.add_redact_annot(pymupdf.Rect(m["rect"]), fill=False, cross_out=False)
        sp.apply_redactions(images=2 if has_bg else 0, graphics=1, text=0)
    flows = lay.flows
    full = len(flows) == 1 and flows[0].x0 <= 0.5 and flows[0].x1 >= W - 0.5
    if full:
        f = flows[0]
        c1 = f.origin()
        page.show_pdf_page(pymupdf.Rect(0, 0, W, c1), strip_doc, 0, clip=pymupdf.Rect(0, 0, W, c1))
        if f.bottom < H:
            r = pymupdf.Rect(0, f.bottom, W, H)
            page.show_pdf_page(r, strip_doc, 0, clip=r)
    else:
        base = pymupdf.open()
        base.insert_pdf(strip_doc)
        if flows:
            drop_pictures_inside(base[0], [[f.x0, f.origin(), f.x1, f.bottom] for f in flows])
            for f in flows:
                base[0].add_redact_annot(pymupdf.Rect(f.x0, f.origin(), f.x1, f.bottom), fill=False, cross_out=False)
            base[0].apply_redactions(images=2, graphics=1, text=0)
        page.show_pdf_page(page.rect, base, 0)
    for f in flows:
        # a copy without pictures lying outside this column, so clipped-away copies don't count as images
        col = pymupdf.open()
        col.insert_pdf(strip_doc)
        c1 = f.origin()
        imgs, _ = page_objects(col[0])
        outside = [im["bbox"] for im in imgs if not im["bg"] and (
            im["bbox"][2] <= f.x0 + 0.5 or im["bbox"][0] >= f.x1 - 0.5
            or im["bbox"][3] <= c1 + 0.5 or im["bbox"][1] >= f.bottom - 0.5)]
        if outside:
            for b in outside:
                col[0].add_redact_annot(pymupdf.Rect(b) + (1, 1, -1, -1), fill=False, cross_out=False)
            col[0].apply_redactions(images=1, graphics=0, text=1)
        cuts = sorted(set(f.cuts) | {c1})
        s, x0, x1 = f.s, f.x0, f.x1
        tw = (x1 - x0) * s
        end = max(min(f.bottom, c1 + (f.bottom - c1) / s - f.off(f.bottom)), f.content_bottom)
        for i, c in enumerate(cuts):
            g = f.cuts.get(c, 0)
            t0 = f.map(x0, c)[1]  # top of the strip below the cut (after the gap)
            if g > 0:
                page.show_pdf_page(pymupdf.Rect(x0, t0 - g * s, x0 + tw, t0), col, 0,
                                   clip=pymupdf.Rect(x0, c - 0.1, x1, c + 0.1), keep_proportion=False)
            nxt = cuts[i + 1] if i + 1 < len(cuts) else end
            if nxt - c >= 0.2:
                page.show_pdf_page(pymupdf.Rect(x0, t0, x0 + tw, t0 + (nxt - c) * s), col, 0,
                                   clip=pymupdf.Rect(x0, c, x1, nxt), keep_proportion=False)
    for m in moves:
        r = pymupdf.Rect(m["rect"])
        tx, ty = r.x0 + m["dx"], r.y0 + m["dy"]
        x, y = lay.map(tx, ty)
        k = m["scale"] * lay.s(tx, ty)
        piece = pymupdf.open()
        piece.insert_pdf(src, from_page=n - 1, to_page=n - 1)
        pp = piece[0]
        for o in (pymupdf.Rect(0, 0, W, r.y0), pymupdf.Rect(0, r.y1, W, H),
                  pymupdf.Rect(0, r.y0, r.x0, r.y1), pymupdf.Rect(r.x1, r.y0, W, r.y1)):
            if not o.is_empty:
                pp.add_redact_annot(o, fill=False, cross_out=False)
        pp.apply_redactions(images=0 if has_bg else 1, graphics=2, text=1)
        page.show_pdf_page(pymupdf.Rect(x, y, x + r.width * k, y + r.height * k), piece, 0, clip=r)
    return page


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf", type=Path)
    ap.add_argument("plan", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--report", type=Path)
    ap.add_argument("--merge", type=Path, nargs="*", default=[], help="more plan files (batches) to apply together")
    a = ap.parse_args()
    if a.out.resolve() == a.pdf.resolve():
        sys.exit("refusing to overwrite the original PDF")
    plan = json.loads(a.plan.read_text(encoding="utf-8"))
    d = dict(DEFAULTS, **plan.get("defaults", {}))
    fnt = font(d["font"])
    src = pymupdf.open(a.pdf)
    entries = {e["page"]: e for e in plan["pages"]}
    for extra in a.merge:
        entries.update({e["page"]: e for e in json.loads(extra.read_text(encoding="utf-8"))["pages"]})
    out = pymupdf.open()
    report = []
    for n in range(1, src.page_count + 1):
        e = entries.get(n)
        if not e:
            out.insert_pdf(src, from_page=n - 1, to_page=n - 1)
            continue
        sp = src[n - 1]
        errs = []
        lay, moves, boxes, uncovered = plan_page(sp, e, d, fnt, errs)
        if lay.flows or moves:
            page = build_page(out, src, n, sp.rect.width, sp.rect.height, lay, moves)
        else:
            out.insert_pdf(src, from_page=n - 1, to_page=n - 1)
            page = out[-1]
        for b in boxes:
            draw_lines(page, b["x"], b["y"], b["w"], b["lines"], b["pt"], rgb(int(b["color"], 16)),
                       b["align"], fnt, b.get("fill"))
        cols = [{"x": [round(f.x0), round(f.x1)], "from_y": round(f.origin()), "en_scale": round(f.s, 3),
                 "gaps": {round(c, 1): round(g, 1) for c, g in f.cuts.items()}} for f in lay.flows]
        report.append({"page": n, "chinese_boxes": len(boxes), "columns_moved": cols,
                       "uncovered": uncovered, "issues": errs})
        n_err = sum(1 for i in errs if i["level"] == "error")
        print("page %d: %d Chinese box(es), English scale %s, %d error(s)%s" % (
            n, len(boxes), "/".join("%.2f" % f.s for f in lay.flows) or "1.00", n_err,
            ", %d uncovered" % len(uncovered) if uncovered else ""))
        for i in errs:
            print("   ", i)
        for u in uncovered:
            print("    uncovered:", u)
    toc = src.get_toc(simple=False)
    if toc:
        try:
            out.set_toc(toc)
        except Exception:  # noqa: BLE001 - a broken outline must not block the output
            pass
    out.set_metadata(src.metadata)
    out.subset_fonts()
    out.ez_save(a.out, garbage=4, deflate=True)
    if a.report:
        a.report.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print("wrote", a.out)


if __name__ == "__main__":
    main()
