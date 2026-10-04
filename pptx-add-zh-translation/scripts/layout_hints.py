"""Rendered geometry per slide, so a plan can be written without opening PNGs.

Usage: python3 layout_hints.py rendered.pdf out.md [--pages 4,9]
       python3 layout_hints.py original.pptx out.md [--pages 4,9]   (no PyMuPDF: estimated)
(rendered.pdf = the .render.pdf that render_check.py wrote for the ORIGINAL deck;
PDF points == slide points. With a .pptx, or when PyMuPDF is missing, line positions
are estimated from the XML per paragraph - good to ~10-20 pt, less exact for titles.)

Lists every rendered text line with its bbox [x0, y0, x1, y1] and font size,
picture boxes, and the free horizontal space to the right of the first (title) line.
Text inside pictures is NOT listed - use the visual review notes or the PNG.
"""
import argparse
import re

try:
    import pymupdf
except ImportError:
    pymupdf = None

from inventory import parse_pages

WORD = re.compile(r"[A-Za-z一-鿿]{2,}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("out")
    ap.add_argument("--pages")
    a = ap.parse_args()
    if a.pdf.lower().endswith(".pptx") or pymupdf is None:
        return estimated(a)
    doc = pymupdf.open(a.pdf)
    out = ["# Rendered layout (pt; page %.0fx%.0f)" % (doc[0].rect.width, doc[0].rect.height), ""]
    for n in parse_pages(a.pages, doc.page_count):
        page = doc[n - 1]
        W, H = page.rect.width, page.rect.height
        out.append("## Slide %d" % n)
        lines = []
        for b in page.get_text("dict")["blocks"]:
            for ln in b.get("lines", []):
                t = "".join(s["text"] for s in ln["spans"]).strip()
                if t and WORD.search(t):
                    size = max(s["size"] for s in ln["spans"] if s["text"].strip())
                    lines.append((ln["bbox"], size, t))
        lines.sort(key=lambda l: (round(l[0][1]), l[0][0]))
        for (x0, y0, x1, y1), size, t in lines:
            out.append("- [%d, %d, %d, %d] %gpt %s" % (x0, y0, x1, y1, round(size, 1), t[:90]))
        imgs = [im["bbox"] for im in page.get_image_info()]
        imgs = [b for b in imgs if (b[2] - b[0]) * (b[3] - b[1]) < 0.6 * W * H and (b[2] - b[0]) > 20]
        for b in imgs:
            out.append("- picture [%d, %d, %d, %d]" % tuple(b))
        big = [l for l in lines if l[1] >= 28]
        if big:
            (x0, y0, x1, y1), size, t = big[0]
            right_limit = W - 20
            for (bx0, by0, bx1, by1), _, _ in lines:
                if bx0 > x1 and by0 < y1 and by1 > y0:
                    right_limit = min(right_limit, bx0)
            for b in imgs:
                if b[0] > x1 and b[1] < y1 and b[3] > y0:
                    right_limit = min(right_limit, b[0])
            out.append("- title free space right of title: x %d..%d at y %d..%d" % (x1, right_limit, y0, y1))
        out.append("")
    open(a.out, "w", encoding="utf-8").write("\n".join(out))
    print("wrote", a.out)


def estimated(a):
    from estimate import estimate_shape
    from lxml import etree
    from ooxml import Deck, iter_shapes, resolve_box, shape_id
    src = a.pdf
    if not src.lower().endswith(".pptx"):
        raise SystemExit("PyMuPDF is not installed: pass the original .pptx instead of the PDF")
    deck = Deck(src)
    W, H = deck.width_pt, deck.height_pt
    out = ["# Estimated layout from slide XML (pt; page %.0fx%.0f) - not rendered" % (W, H), ""]
    for n in parse_pages(a.pages, len(deck.slides)):
        out.append("## Slide %d" % n)
        lines, pics = [], []
        for shape, groups in iter_shapes(deck.slide(n)):
            tag = etree.QName(shape).localname
            if tag == "sp":
                est = estimate_shape(deck, n, shape, groups)
                for p in (est or {}).get("paras", []):
                    size = round((p["rect"][3] - p["rect"][1]) / 1.2, 1)
                    lines.append((p["rect"], size, p["text"]))
            elif tag in ("pic", "graphicFrame"):
                box = resolve_box(deck, n, shape, groups)
                if box:
                    pics.append([box[0], box[1], box[0] + box[2], box[1] + box[3]])
        lines.sort(key=lambda l: (round(l[0][1]), l[0][0]))
        for (x0, y0, x1, y1), size, t in lines:
            out.append("- ~[%d, %d, %d, %d] %s" % (x0, y0, x1, y1, t[:90]))
        for b in pics:
            out.append("- picture/object [%d, %d, %d, %d]" % tuple(b))
        if lines:
            (x0, y0, x1, y1), _, t = min(lines, key=lambda l: l[0][1])
            right = W - 20
            for (bx0, by0, bx1, by1), _, _ in lines:
                if bx0 > x1 and by0 < y1 and by1 > y0:
                    right = min(right, bx0)
            for b in pics:
                if b[0] > x1 and b[1] < y1 and b[3] > y0:
                    right = min(right, b[0])
            out.append("- title free space right of top line (estimated): x %d..%d at y %d..%d" % (x1, right, y0, y1))
        out.append("")
    open(a.out, "w", encoding="utf-8").write("\n".join(out))
    print("wrote", a.out, "(estimated)")


if __name__ == "__main__":
    main()
