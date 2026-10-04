"""PDF mode, step 1: what is on each page and where Chinese can go.

Usage: python3 pdf_inventory.py lecture.pdf out_dir [--pages 3,5-9] [--dpi 110]
Writes out_dir/inventory.md (read this), inventory.json and pageNN.png (original pages).
inventory.md carries the full English text; the printed page index gives each page's line
range in it, so a batch can be read with offset/limit instead of the whole file.

Per page: paragraphs P1..Pn (ids used by the plan) with bbox [x0,y0,x1,y1] in pt,
font size, kind (en = needs Chinese, zh = existing Chinese, misc = numbers/symbols),
free space under each paragraph and whether the page can be opened up there
(clean cut), free space right of the first line, pictures, footer zone.
Pages with pictures but no text are flagged SCANNED/IMAGE-ONLY: read the PNG.
"""
import argparse
import json
from pathlib import Path

from pdfmodel import ensure_pymupdf

ensure_pymupdf()
import pymupdf  # noqa: E402

from pdfmodel import (below_right, cut_for, footer_top, free_below, free_right,  # noqa: E402
                      mark_footer, page_objects, paragraphs, parse_pages)


def inside(a, b):
    return a[0] >= b[0] - 2 and a[1] >= b[1] - 2 and a[2] <= b[2] + 2 and a[3] <= b[3] + 2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf", type=Path)
    ap.add_argument("out_dir", type=Path)
    ap.add_argument("--pages")
    ap.add_argument("--dpi", type=int, default=110)
    a = ap.parse_args()
    a.out_dir.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(a.pdf)
    pages = parse_pages(a.pages, doc.page_count)
    W0, H0 = doc[0].rect.width, doc[0].rect.height
    md = ["# PDF inventory: %s (%d pages, %.0fx%.0f pt)" % (a.pdf.name, doc.page_count, W0, H0), "",
          "ids P1..Pn are per page; kind en = needs Chinese, zh = existing Chinese, footer = in the footer zone "
          "(optional), misc = numbers/symbols. `below: free N` = empty pt under the paragraph; "
          "`cut ok@y` = page can be opened up there, full width; `column cut` = only that column moves "
          "(pdf_apply adds room automatically); "
          "`no cut` = Chinese under it needs a textbox/move instead. `box` = a vector frame/shape "
          "(diagram box, callout): Chinese must stay clear of its border.", ""]
    data, index = [], []
    for n in pages:
        page = doc[n - 1]
        W, H = page.rect.width, page.rect.height
        paras = paragraphs(page)
        imgs, draws = page_objects(page)
        ft = footer_top(page, paras, imgs, draws)
        mark_footer(paras, ft)
        png = a.out_dir / ("page%02d.png" % n)
        page.get_pixmap(dpi=a.dpi).save(png)
        en = [P for P in paras if P["kind"] == "en"]
        flags = []
        if not paras and imgs:
            flags.append("SCANNED/IMAGE-ONLY (no text layer: read the PNG, use textbox ops)")
        if any(P["kind"] == "zh" for P in paras):
            flags.append("HAS CHINESE")
        start = len(md) + 1
        md.append("## Page %d%s" % (n, (" - " + "; ".join(flags)) if flags else ""))
        md.append("png: %s; footer zone y>=%d" % (png.name, ft) if ft < H else "png: %s" % png.name)
        rows = []
        for P in paras:
            b = [round(v) for v in P["bbox"]]
            free, top = free_below(P, paras, imgs, draws, W, ft, below_right(P, paras, imgs, draws, W))
            cut, xr_cut = cut_for(P, top, paras, imgs, draws, W)
            xr = free_right(P, paras, imgs, draws, W)
            row = {"id": P["id"], "kind": P["kind"], "bbox": b, "tx": round(P["tx"]), "size": round(P["size"], 1),
                   "lines": len(P["lines"]), "bullet": P["bullet"], "text": P["text"],
                   "free_below": round(free), "cut": cut, "cut_x": xr_cut, "free_right": [round(xr[0]), round(xr[1])]}
            rows.append(row)
            if P["kind"] == "misc" and len(P["text"]) < 4:
                md.append("- %s misc [%d,%d,%d,%d] %s" % (P["id"], *b, P["text"]))
                continue
            md.append("- %s %s [%d,%d,%d,%d] %gpt%s %dL | below: free %d, %s | right: x %d..%d | %s" % (
                P["id"], P["kind"], *b, row["size"], " bullet" if P["bullet"] else "", row["lines"], row["free_below"],
                ("no cut" if cut is None else "cut ok@%g" % cut if xr_cut is None
                 else "column cut x%d..%d @%g" % (xr_cut[0], xr_cut[1], cut)), *row["free_right"], P["text"]))
        for im in imgs:
            md.append("- picture%s [%d,%d,%d,%d]" % (" (background)" if im["bg"] else "", *[round(v) for v in im["bbox"]]))
        frames = [[round(v) for v in d["bbox"]] for d in draws if not d["bg"]
                  and d["bbox"][2] - d["bbox"][0] > 40 and d["bbox"][3] - d["bbox"][1] > 15
                  and d["bbox"][1] < ft and any(inside(P["bbox"], d["bbox"]) for P in paras)]
        for b in frames:
            md.append("- box [%d,%d,%d,%d]" % tuple(b))
        md.append("")
        index.append("%d:%d-%d" % (n, start, len(md)))
        data.append({"page": n, "width": W, "height": H, "footer_top": ft, "png": str(png), "flags": flags,
                     "paragraphs": rows, "pictures": [im["bbox"] for im in imgs], "boxes": frames,
                     "english_paragraphs": len(en)})
    (a.out_dir / "inventory.md").write_text("\n".join(md), encoding="utf-8")
    (a.out_dir / "inventory.json").write_text(json.dumps({"pdf": str(a.pdf), "pages": data}, ensure_ascii=False, indent=1),
                                              encoding="utf-8")
    print("wrote", a.out_dir / "inventory.md", "-", sum(d["english_paragraphs"] for d in data), "English paragraphs on",
          len(data), "pages;", sum(1 for d in data if d["flags"] and d["flags"][0].startswith("SCANNED")), "image-only pages")
    print("inventory.md lines per page (page:first-last):", " ".join(index))


if __name__ == "__main__":
    main()
