"""Apply a translation plan (JSON) to a deck, writing a NEW pptx.

Usage: python3 apply_plan.py source.pptx plan.json out.pptx [--report report.json]

Only slide XML parts touched by the plan are rewritten; everything else
(media, OLE equations, animations, other slides) is copied unchanged.
See references/plan-schema.md for the op list.
"""
import argparse
import json
import re
import sys

from lxml import etree

from ooxml import (EMU_PER_PT, NS, Deck, deep, has_cjk, iter_shapes, own_xfrm,
                   para_text, q, resolve_box, resolve_para, shape_id)
from inventory import para_animated_ids

DEFAULTS = {"scale": 0.75, "title_scale": 0.5, "cell_scale": 0.85, "min_pt": 12,
            "color": None, "ea_font": None, "name_prefix": "ZH "}
TRIVIAL = re.compile(r"^[^A-Za-z]*([A-Za-z][^A-Za-z]*)?$")  # no 2-letter word -> nothing to translate


class PlanError(Exception):
    pass


def find_shape(slide, sid):
    for shape, groups in iter_shapes(slide):
        if shape_id(shape)[0] == sid:
            return shape, groups
    raise PlanError("shape id %s not found" % sid)


def zh_rpr(size_hundredths, cfg, base_rpr=None):
    rpr = etree.Element(q("a:rPr"), lang="zh-CN", altLang="en-US", dirty="0")
    rpr.set("sz", str(int(size_hundredths)))
    if base_rpr is not None:
        if base_rpr.get("b"):
            rpr.set("b", base_rpr.get("b"))
        fill = base_rpr.find("a:solidFill", NS)
        if fill is not None and not cfg.get("color"):
            rpr.append(deep(fill))
    if cfg.get("color"):
        fill = etree.SubElement(rpr, q("a:solidFill"))
        etree.SubElement(fill, q("a:srgbClr"), val=cfg["color"].lstrip("#"))
    if cfg.get("ea_font"):
        etree.SubElement(rpr, q("a:ea"), typeface=cfg["ea_font"])
    return rpr


def zh_size(base_sz, scale, font_scale, cfg):
    """Explicit sz (hundredths pt) so the rendered size >= min_pt."""
    sz = base_sz * scale
    floor = cfg["min_pt"] * 100 / font_scale
    return round(max(sz, floor) / 50) * 50


def make_para(text, ppr, rpr):
    p = etree.Element(q("a:p"))
    p.append(ppr)
    r = etree.SubElement(p, q("a:r"))
    r.append(rpr)
    etree.SubElement(r, q("a:t")).text = text
    return p


def op_para_after(deck, n, slide, op, cfg, log):
    shape, _ = find_shape(slide, op["shape"])
    if op["shape"] in para_animated_ids(slide):
        raise PlanError("shape %s is animated by paragraph; use a textbox op instead" % op["shape"])
    paras = cfg["_ctx"]["orig"].get(op["shape"]) or shape.find("p:txBody", NS).findall("a:p", NS)  # original indices
    is_title = (deck.ph_of(shape) is not None and deck.ph_of(shape).get("type") in ("title", "ctrTitle")) \
        or op.get("title")
    scale = op.get("scale", cfg["title_scale"] if is_title else cfg["scale"])
    for item in op["items"]:
        src = paras[item["p"]]
        nxt = src.getnext()
        if nxt is not None and etree.QName(nxt).localname == "p" and has_cjk(para_text(nxt)):
            log.append("slide %d shape %s p%d already followed by Chinese; skipped" % (n, op["shape"], item["p"]))
            continue
        st = resolve_para(deck, n, shape, src)
        if item.get("inline"):  # same line: append a run after the English text
            if has_cjk(para_text(src)):
                log.append("slide %d shape %s p%d already contains Chinese; skipped" % (n, op["shape"], item["p"]))
                continue
            size = zh_size(st["sz"], item.get("scale", scale), st["fontScale"], cfg)
            r = etree.Element(q("a:r"))
            r.append(zh_rpr(size, cfg))
            etree.SubElement(r, q("a:t")).text = item.get("sep", "  ") + item["zh"]
            end = src.find("a:endParaRPr", NS)
            (end.addprevious(r) if end is not None else src.append(r))
            item["_done"] = True
            continue
        ppr = etree.Element(q("a:pPr"), marL=str(st["marL"]), indent="0")
        if st["level"]:
            ppr.set("lvl", str(st["level"]))
        sppr = src.find("a:pPr", NS)
        if sppr is not None and sppr.get("algn"):
            ppr.set("algn", sppr.get("algn"))
        bef = etree.SubElement(ppr, q("a:spcBef"))
        etree.SubElement(bef, q("a:spcPts"), val=str(op.get("space_before_pt", 0) * 100))
        etree.SubElement(ppr, q("a:buNone"))
        size = zh_size(st["sz"], item.get("scale", scale), st["fontScale"], cfg)
        zp = make_para(item["zh"], ppr, zh_rpr(size, cfg))
        src.addnext(zp)
        cfg["_ctx"]["inserted"].add(zp)
        item["_done"] = True


def op_cells(deck, n, slide, op, cfg, log):
    frame, _ = find_shape(slide, op["shape"])
    tbl = frame.find(".//a:tbl", NS)
    rows = tbl.findall("a:tr", NS)
    if op.get("table_scale"):
        for rpr in tbl.iter(q("a:rPr"), q("a:endParaRPr")):
            rpr.set("sz", str(round(int(rpr.get("sz", 1800)) * op["table_scale"] / 50) * 50))
        for tr in rows:
            tr.set("h", str(int(int(tr.get("h")) * op["table_scale"])))
    if op.get("table_box"):  # move/resize the table frame; columns scale proportionally
        tb = op["table_box"]
        xf = frame.find("p:xfrm", NS)
        off, ext = xf.find("a:off", NS), xf.find("a:ext", NS)
        old_w = int(ext.get("cx"))
        if "x" in tb:
            off.set("x", str(int(tb["x"] * EMU_PER_PT)))
        if "y" in tb:
            off.set("y", str(int(tb["y"] * EMU_PER_PT)))
        if "w" in tb:
            ext.set("cx", str(int(tb["w"] * EMU_PER_PT)))
            ratio = tb["w"] * EMU_PER_PT / old_w
            for col in tbl.find("a:tblGrid", NS):
                col.set("w", str(int(int(col.get("w")) * ratio)))
    for item in op["items"]:
        tc = rows[item["r"]].findall("a:tc", NS)[item["c"]]
        body = tc.find("a:txBody", NS)
        ps = [p for p in body.findall("a:p", NS)]
        if any(has_cjk(para_text(p)) for p in ps):
            log.append("slide %d cell r%d c%d already has Chinese; skipped" % (n, item["r"], item["c"]))
            continue
        first_run = next(iter(body.iter(q("a:rPr"))), None)
        base = int(first_run.get("sz")) if first_run is not None and first_run.get("sz") else 1800
        ppr = etree.Element(q("a:pPr"))
        sppr = ps[0].find("a:pPr", NS)
        if sppr is not None and sppr.get("algn"):
            ppr.set("algn", sppr.get("algn"))
        size = zh_size(base, item.get("scale", op.get("scale", cfg["cell_scale"])), 1.0, cfg)
        last = ps[-1]
        last.addnext(make_para(item["zh"], ppr, zh_rpr(size, cfg, first_run)))
        item["_done"] = True


def next_id(slide):
    ids = [int(e.get("id")) for e in slide.iter(q("p:cNvPr")) if e.get("id", "").isdigit()]
    return max(ids + [0]) + 1


def op_textbox(deck, n, slide, op, cfg, log):
    lines = op["lines"] if "lines" in op else [op["zh"]]
    emu = lambda v: str(int(round(v * EMU_PER_PT)))
    sid = next_id(slide)
    sp = etree.Element(q("p:sp"))
    nv = etree.SubElement(sp, q("p:nvSpPr"))
    etree.SubElement(nv, q("p:cNvPr"), id=str(sid), name=cfg["name_prefix"] + op.get("name", "译文 %d" % sid))
    etree.SubElement(etree.SubElement(nv, q("p:cNvSpPr")), q("a:spLocks")).set("noGrp", "1")
    nv.find("p:cNvSpPr", NS).set("txBox", "1")
    etree.SubElement(nv, q("p:nvPr"))
    sppr = etree.SubElement(sp, q("p:spPr"))
    x = etree.SubElement(sppr, q("a:xfrm"))
    etree.SubElement(x, q("a:off"), x=emu(op["x"]), y=emu(op["y"]))
    etree.SubElement(x, q("a:ext"), cx=emu(op["w"]), cy=emu(op["h"]))
    etree.SubElement(etree.SubElement(sppr, q("a:prstGeom"), prst="rect"), q("a:avLst"))
    if op.get("fill"):
        etree.SubElement(etree.SubElement(sppr, q("a:solidFill")), q("a:srgbClr"), val=op["fill"].lstrip("#"))
    else:
        etree.SubElement(sppr, q("a:noFill"))
    body = etree.SubElement(sp, q("p:txBody"))
    bpr = etree.SubElement(body, q("a:bodyPr"), wrap="square", lIns="45720", tIns="22860",
                           rIns="45720", bIns="22860", rtlCol="0", anchor=op.get("anchor", "t"))
    etree.SubElement(bpr, q("a:noAutofit"))
    etree.SubElement(body, q("a:lstStyle"))
    size = max(op.get("pt", 16), cfg["min_pt"]) * 100
    for line in lines:
        ppr = etree.Element(q("a:pPr"), algn=op.get("align", "l"))
        etree.SubElement(ppr, q("a:buNone"))
        body.append(make_para(line, ppr, zh_rpr(size, cfg)))
    slide.find("./p:cSld/p:spTree", NS).append(sp)
    op["_done"] = True


def move_vml(deck, n, shape, x, y, w, h):
    """Legacy OLE objects (mc:Choice Requires="v") are drawn from the slide's VML part."""
    spids = [o.get("spid") for o in shape.iter(q("p:oleObj")) if o.get("spid")]
    if not spids:
        return
    vml = deck.related(deck.slides[n - 1], "vmlDrawing")
    if not vml:
        return
    text = deck.read(vml).decode("utf-8")
    for spid in spids:
        m = re.search(r'(<v:shape\b[^>]*o:spid="%s"[^>]*style=")([^"]*)(")' % re.escape(spid), text)
        if not m:
            continue
        style = m.group(2)
        for key, val in (("left", x), ("top", y), ("width", w), ("height", h)):
            style = re.sub(r"(?<![-\w])%s:[^;]*" % key, "%s:%.2fpt" % (key, val), style)
        text = text[:m.start(2)] + style + text[m.end(2):]
    deck.overrides[vml] = text.encode("utf-8")


def op_adjust(deck, n, slide, op, cfg, log):
    shape, groups = find_shape(slide, op["shape"])
    if groups and any(k in op for k in ("x", "y", "w", "h", "dx", "dy", "dw", "dh")):
        raise PlanError("shape %s is inside a group; move the group instead" % op["shape"])
    if any(k in op for k in ("x", "y", "w", "h", "dx", "dy", "dw", "dh")):
        box = resolve_box(deck, n, shape, groups)
        if box is None:
            raise PlanError("shape %s has no resolvable position" % op["shape"])
        x, y, w, h = box
        x, y, w, h = op.get("x", x + op.get("dx", 0)), op.get("y", y + op.get("dy", 0)), \
            op.get("w", w + op.get("dw", 0)), op.get("h", h + op.get("dh", 0))
        xf = own_xfrm(shape)
        if xf is None:  # placeholder inheriting position: give it its own
            sppr = shape.find("p:spPr", NS) if shape.find("p:spPr", NS) is not None else shape.find("p:xfrm/..", NS)
            xf = etree.Element(q("a:xfrm"))
            etree.SubElement(xf, q("a:off"))
            etree.SubElement(xf, q("a:ext"))
            sppr.insert(0, xf)
        old_box = [xf.find("a:off", NS).get("x"), xf.find("a:off", NS).get("y"),
                   xf.find("a:ext", NS).get("cx"), xf.find("a:ext", NS).get("cy")]
        xf.find("a:off", NS).set("x", str(int(x * EMU_PER_PT)))
        xf.find("a:off", NS).set("y", str(int(y * EMU_PER_PT)))
        xf.find("a:ext", NS).set("cx", str(int(w * EMU_PER_PT)))
        xf.find("a:ext", NS).set("cy", str(int(h * EMU_PER_PT)))
        # OLE objects keep copies of the position inside mc:Choice / mc:Fallback (p:pic);
        # move every copy that sat exactly where the frame was, or PowerPoint draws a ghost
        alts = list(shape.iterancestors(q("mc:AlternateContent")))[:1]
        scopes = [shape] + [a.find("mc:Fallback", NS) for a in alts if a.find("mc:Fallback", NS) is not None]
        for scope in scopes:
            for fx in list(scope.iter(q("a:xfrm"))) + list(scope.iter(q("p:xfrm"))):
                if fx is xf or fx.find("a:off", NS) is None or fx.find("a:ext", NS) is None:
                    continue
                if [fx.find("a:off", NS).get("x"), fx.find("a:off", NS).get("y"),
                        fx.find("a:ext", NS).get("cx"), fx.find("a:ext", NS).get("cy")] == old_box:
                    fx.find("a:off", NS).attrib.update(xf.find("a:off", NS).attrib)
                    fx.find("a:ext", NS).attrib.update(xf.find("a:ext", NS).attrib)
        move_vml(deck, n, shape, x, y, w, h)
    if op.get("font_scale"):
        body = shape.find("p:txBody", NS)
        for p in body.findall("a:p", NS):
            st = resolve_para(deck, n, shape, p)
            for el in list(p.iter(q("a:rPr"), q("a:endParaRPr"))):
                cur = int(el.get("sz")) if el.get("sz") else st["sz"]
                el.set("sz", str(round(cur * op["font_scale"] / 50) * 50))
            if not list(p.iter(q("a:rPr"))):
                continue
            for r in p.findall("a:r", NS):
                if r.find("a:rPr", NS) is None:
                    r.insert(0, etree.Element(q("a:rPr"), sz=str(round(st["sz"] * op["font_scale"] / 50) * 50)))
    op["_done"] = True


OPS = {"para_after": op_para_after, "cells": op_cells, "textbox": op_textbox, "adjust": op_adjust,
       "skip": None, "existing": None}


def mostly_zh(text):
    cjk = sum(1 for ch in text if has_cjk(ch))
    latin = sum(1 for ch in text if ch.isascii() and ch.isalpha())
    return cjk > 0 and cjk >= latin / 2


def snapshot(slide):
    """Original paragraph elements per shape id, taken before any op runs."""
    orig = {}
    for shape, _ in iter_shapes(slide):
        body = shape.find("p:txBody", NS)
        if body is not None and etree.QName(shape).localname == "sp":
            orig[shape_id(shape)[0]] = body.findall("a:p", NS)
    return orig


def coverage(deck, n, slide, ops, ctx):
    """English paragraphs / cells with no Chinese counterpart and no skip reason.
    Paragraph numbers in covers/skip always refer to the ORIGINAL deck."""
    covered, covered_el = set(), set()
    orig = ctx["orig"]

    def add(sid, p):
        if p == "all":
            covered.add((sid, "all"))
        elif isinstance(p, int):
            if sid in orig and p < len(orig[sid]):
                covered_el.add(orig[sid][p])
        else:
            covered.add((sid, p))
    for op in ops:
        for c in op.get("covers", []):
            add(c["shape"], c.get("p", "all"))
        if op["op"] == "skip":
            for p in op.get("p", ["all"]):
                add(op["shape"], p)
    missing = []
    for shape, _ in iter_shapes(slide):
        sid, name = shape_id(shape)
        if (sid, "all") in covered or (name or "").startswith(DEFAULTS["name_prefix"]):
            continue
        body = shape.find("p:txBody", NS)
        if body is not None and etree.QName(shape).localname == "sp":
            ps = body.findall("a:p", NS)
            for i, p in enumerate(ps):
                t = para_text(p)
                if not t.strip() or has_cjk(t) or TRIVIAL.match(t) or p in covered_el or p in ctx["inserted"]:
                    continue
                nxt = ps[i + 1] if i + 1 < len(ps) else None
                if nxt is not None and (nxt in ctx["inserted"] or mostly_zh(para_text(nxt))):
                    continue
                num = orig[sid].index(p) if sid in orig and p in orig[sid] else i
                missing.append({"shape": sid, "p": num, "text": t})
        tbl = shape.find(".//a:tbl", NS)
        if tbl is not None:
            for r, tr in enumerate(tbl.findall("a:tr", NS)):
                for c, tc in enumerate(tr.findall("a:tc", NS)):
                    t = " ".join(para_text(p) for p in tc.iter(q("a:p")))
                    if t.strip() and not has_cjk(t) and not TRIVIAL.match(t) and (sid, "r%dc%d" % (r, c)) not in covered:
                        missing.append({"shape": sid, "cell": [r, c], "text": t})
    return missing


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source")
    ap.add_argument("plan")
    ap.add_argument("out")
    ap.add_argument("--report")
    ap.add_argument("--force", action="store_true", help="re-apply on slides that already have ZH shapes")
    a = ap.parse_args()
    if a.source == a.out:
        sys.exit("refusing to overwrite the source deck; write a new file")
    plan = json.load(open(a.plan, encoding="utf-8"))
    cfg = dict(DEFAULTS, **plan.get("defaults", {}))
    deck = Deck(a.source)
    log, errors, report = [], [], {"slides": []}
    for entry in plan["slides"]:
        n = entry["slide"]
        slide = deck.slide(n)
        done_before = [shape_id(sh)[1] for sh, _ in iter_shapes(slide)
                       if (shape_id(sh)[1] or "").startswith(cfg["name_prefix"])]
        if done_before and not a.force:
            log.append("slide %d already processed (has %s); skipped. Apply plans to the original deck, or --force" % (n, done_before[0]))
            continue
        cfg["_ctx"] = {"orig": snapshot(slide), "inserted": set()}
        for op in entry["ops"]:
            fn = OPS.get(op["op"], "unknown")
            if fn == "unknown":
                errors.append("slide %d: unknown op %s" % (n, op["op"]))
                continue
            if fn is None:
                continue
            try:
                fn(deck, n, slide, op, cfg, log)
            except PlanError as e:
                errors.append("slide %d: %s" % (n, e))
        deck.mark(n)
        missing = coverage(deck, n, slide, entry["ops"], cfg["_ctx"])
        report["slides"].append({"slide": n, "uncovered": missing})
    deck.save(a.out)
    report.update(log=log, errors=errors)
    if a.report:
        json.dump(report, open(a.report, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for line in log:
        print("note:", line)
    for line in errors:
        print("ERROR:", line)
    for s in report["slides"]:
        for m in s["uncovered"]:
            print("uncovered: slide %d shape %s %s: %s" % (s["slide"], m["shape"], m.get("p", m.get("cell")), m["text"][:70]))
    print("wrote %s (%d slides changed, %d errors)" % (a.out, len(plan["slides"]), len(errors)))
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
