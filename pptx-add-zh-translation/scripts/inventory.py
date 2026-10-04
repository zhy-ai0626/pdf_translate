"""Extract what needs translating: text shapes, paragraphs, table cells, geometry,
existing Chinese, animations and objects that can't be read as text.

Usage: python3 inventory.py deck.pptx out_dir [--pages 4,9,38-40]
Writes out_dir/inventory.json (full detail) and out_dir/inventory.md (for reading).
"""
import argparse
import json
import re
from pathlib import Path

from lxml import etree

from ooxml import (NS, Deck, has_cjk, iter_shapes, para_text, q, resolve_box,
                   resolve_para, shape_id)


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


def para_animated_ids(slide):
    """Shape ids built 'by paragraph' (inserting paragraphs would break their animation)."""
    ids = set()
    for b in slide.iter(q("p:bldP")):
        if b.get("build") in ("p", "cust"):
            ids.add(int(b.get("spid")))
    for t in slide.iter(q("p:txEl")):
        sp = t.getparent().find("p:spTgt", NS) if t.getparent() is not None else None
        if sp is not None:
            ids.add(int(sp.get("spid")))
    return ids


def slide_record(deck, number):
    slide = deck.slide(number)
    animated = para_animated_ids(slide)
    shapes, objects = [], []
    for shape, groups in iter_shapes(slide):
        tag = etree.QName(shape).localname
        sid, name = shape_id(shape)
        if tag == "grpSp":
            continue
        box = resolve_box(deck, number, shape, groups)
        ph = deck.ph_of(shape)
        rec = {"id": sid, "name": name, "kind": tag, "box_pt": box,
               "placeholder": ph.get("type", "body") if ph is not None else None,
               "in_group": bool(groups)}
        if tag == "sp" and shape.find("p:txBody", NS) is not None:
            paras = []
            for i, p in enumerate(shape.find("p:txBody", NS).findall("a:p", NS)):
                text = para_text(p)
                if not text.strip():
                    continue
                st = resolve_para(deck, number, shape, p)
                paras.append({"p": i, "lvl": st["level"], "sz_pt": st["sz"] / 100,
                              "zh": has_cjk(text), "text": text})
            if not paras:
                continue
            rec["paragraphs"] = paras
            rec["all_zh"] = all(x["zh"] for x in paras)
            rec["para_animated"] = sid in animated
            shapes.append(rec)
        elif tag == "graphicFrame" and shape.find(".//a:tbl", NS) is not None:
            cells = []
            for r, tr in enumerate(shape.iter(q("a:tr"))):
                for c, tc in enumerate(tr.findall("a:tc", NS)):
                    text = " / ".join(para_text(p) for p in tc.iter(q("a:p")) if para_text(p).strip())
                    if text.strip():
                        cells.append({"r": r, "c": c, "zh": has_cjk(text), "text": text})
            rec["table_cells"] = cells
            shapes.append(rec)
        else:
            kind = tag
            if shape.find(".//p:oleObj", NS) is not None:
                kind = "ole(equation/embedded object)"
            elif shape.find(".//a:videoFile", NS) is not None or shape.find(".//p:videoFile", NS) is not None:
                kind = "video"
            elif tag == "pic":
                kind = "picture"
            rec["kind"] = kind
            objects.append(rec)
    return {"slide": number, "part": deck.slides[number - 1],
            "hidden": slide.get("show") == "0", "shapes": shapes, "objects": objects,
            "has_zh": any(any(p["zh"] for p in s.get("paragraphs", [])) for s in shapes)}


def to_markdown(deck, records):
    lines = ["# Inventory: %s" % Path(deck.path).name,
             "slide size %.0fx%.0f pt; box = [x, y, w, h] pt" % (deck.width_pt, deck.height_pt), ""]
    for rec in records:
        flags = [f for f, on in (("HIDDEN", rec["hidden"]), ("has-zh", rec["has_zh"])) if on]
        lines.append("## Slide %d %s" % (rec["slide"], " ".join("[%s]" % f for f in flags)))
        for s in rec["shapes"]:
            tag = "zh-box " if s.get("all_zh") else ""
            anim = " PARA-ANIMATED" if s.get("para_animated") else ""
            lines.append("- %sshape %s `%s` %s box=%s%s" % (tag, s["id"], s["name"], s["placeholder"] or s["kind"], s["box_pt"], anim))
            for p in s.get("paragraphs", []):
                lines.append("    - p%d L%d %gpt%s: %s" % (p["p"], p["lvl"], p["sz_pt"], " ZH" if p["zh"] else "", p["text"]))
            for c in s.get("table_cells", []):
                lines.append("    - cell r%d c%d%s: %s" % (c["r"], c["c"], " ZH" if c["zh"] else "", c["text"]))
        for o in rec["objects"]:
            lines.append("- object %s `%s` %s box=%s" % (o["id"], o["name"], o["kind"], o["box_pt"]))
        lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("deck")
    ap.add_argument("out_dir", type=Path)
    ap.add_argument("--pages")
    a = ap.parse_args()
    deck = Deck(a.deck)
    pages = parse_pages(a.pages, len(deck.slides))
    records = [slide_record(deck, n) for n in pages]
    a.out_dir.mkdir(parents=True, exist_ok=True)
    payload = {"deck": a.deck, "slide_w_pt": deck.width_pt, "slide_h_pt": deck.height_pt,
               "total_slides": len(deck.slides), "slides": records}
    (a.out_dir / "inventory.json").write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    (a.out_dir / "inventory.md").write_text(to_markdown(deck, records), encoding="utf-8")
    zh = [r["slide"] for r in records if r["has_zh"]]
    print("%d slides inventoried; with Chinese: %s" % (len(records), zh or "none"))


if __name__ == "__main__":
    main()
