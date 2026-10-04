"""Render a deck, rasterize pages and check the layout of the Chinese text.

Usage: python3 render_check.py deck.pptx out_dir [--pages 4,9] [--min-pt 12] [--dpi 110]
       [--renderer auto|powerpoint|lok|soffice|none] [--lok-node N --lok-cli C]
       python3 render_check.py bilingual.pdf out_dir [--pages ...]   (PDF mode: checks the PDF itself)

Renderers (auto order): Microsoft PowerPoint via AppleScript (macOS, most faithful);
DeepSeek Harness' bundled LibreOffice Kit (pass --lok-node/--lok-cli, or env
PPTX_ZH_LOK_NODE / PPTX_ZH_LOK_CLI, or auto-detected in the DSH app bundle);
system soffice. LibreOffice layout is approximate (fonts such as Consolas may be missing).
Hidden slides are unhidden in a temporary copy so PDF page N == slide N.

Checks: with PyMuPDF installed, on the rendered PDF (Chinese text < --min-pt, text
outside the slide, overlapping / touching text, Chinese on pictures). Without PyMuPDF
(e.g. DSH bundled Python), the same checks are ESTIMATED from the slide XML
(estimate.py) and PNGs come from the LibreOffice Kit renderer when available.
Always look at the PNGs too when the user wants visual review.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    import pymupdf
except ImportError:  # DSH bundled Python ships lxml only
    pymupdf = None

from inventory import parse_pages
from ooxml import Deck, has_cjk

HERE = Path(__file__).resolve().parent
WORD = re.compile(r"[A-Za-z]{3,}")
DSH_APP = Path("/Applications/DeepSeek Harness.app/Contents/Resources")
DSH_NODE = DSH_APP / "runtime/primary-runtime/dependencies/node/bin/node"
DSH_CLI = DSH_APP / "app.asar.unpacked/dsh/node_modules/@deepseek-ai/libreoffice-kit/lib/cli.js"
POWERPOINT = Path("/Applications/Microsoft PowerPoint.app")


def unhidden_copy(src, dst):
    deck = Deck(str(src))
    for i in range(1, len(deck.slides) + 1):
        s = deck.slide(i)
        if s.get("show") == "0":
            del s.attrib["show"]
            deck.mark(i)
    deck.save(str(dst))
    return len(deck.slides)


def lok_paths(a):
    node = a.lok_node or os.environ.get("PPTX_ZH_LOK_NODE")
    cli = a.lok_cli or os.environ.get("PPTX_ZH_LOK_CLI")
    if not (node and cli) and DSH_NODE.exists() and DSH_CLI.exists():
        node, cli = str(DSH_NODE), str(DSH_CLI)
    return (node, cli) if node and cli else None


def run_lok(lok, *args):
    r = subprocess.run([lok[0], lok[1], *args], capture_output=True, text=True, timeout=600)
    if r.returncode != 0:
        raise RuntimeError((r.stdout + r.stderr).strip()[-500:])
    try:
        return json.loads(r.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        return {}


def export_pdf(pptx, pdf, a):
    order = [a.renderer] if a.renderer != "auto" else ["powerpoint", "lok", "soffice"]
    for kind in order:
        if kind == "powerpoint" and sys.platform == "darwin" and POWERPOINT.exists():
            r = subprocess.run(["osascript", str(HERE / "export_pdf.applescript"), str(pptx), str(pdf)],
                               capture_output=True, text=True, timeout=400)
            if r.returncode == 0 and pdf.exists():
                return "powerpoint"
            print("PowerPoint export failed:", r.stderr.strip(), file=sys.stderr)
        elif kind == "lok" and lok_paths(a):
            try:
                info = run_lok(lok_paths(a), "convert", "--input", str(pptx), "--output", str(pdf))
            except RuntimeError as e:
                print("LibreOffice Kit export failed:", e, file=sys.stderr)
                continue
            if pdf.exists():
                missing = info.get("missingFonts")
                return "libreoffice-kit (approximate layout%s)" % (
                    "; missing fonts: " + ", ".join(missing) if missing else "")
        elif kind == "soffice":
            office = shutil.which("soffice") or shutil.which("libreoffice")
            if not office:
                continue
            subprocess.run([office, "--headless", "--convert-to", "pdf", "--outdir", str(pdf.parent), str(pptx)],
                           capture_output=True, timeout=400)
            produced = pdf.parent / (pptx.stem + ".pdf")
            if produced.exists():
                produced.rename(pdf)
                return "libreoffice (approximate layout)"
    return None


def inter(a, b):
    w = min(a[2], b[2]) - max(a[0], b[0])
    h = min(a[3], b[3]) - max(a[1], b[1])
    return w * h if w > 0 and h > 0 else 0.0


def area(r):
    return max(r[2] - r[0], 0) * max(r[3] - r[1], 0)


def check_page(page, min_pt):
    W, H = page.rect.width, page.rect.height
    lines = []
    words = page.get_text("words")  # line bboxes include trailing spaces; tighten with word boxes

    def tighten(bb, text):
        inside = [w for w in words if w[4] in text and bb[0] - 1 <= (w[0] + w[2]) / 2 <= bb[2] + 1 and bb[1] - 1 <= (w[1] + w[3]) / 2 <= bb[3] + 1]
        if not inside:
            return list(bb)
        return [min(w[0] for w in inside), min(w[1] for w in inside), max(w[2] for w in inside), max(w[3] for w in inside)]
    for bi, b in enumerate(page.get_text("dict")["blocks"]):
        if b.get("type") != 0:
            continue
        for li, ln in enumerate(b["lines"]):
            text = "".join(s["text"] for s in ln["spans"]).strip()
            if not text:
                continue
            sizes = [s["size"] for s in ln["spans"] if has_cjk(s["text"])] or [s["size"] for s in ln["spans"] if s["text"].strip()]
            fonts = sorted({s["font"] for s in ln["spans"] if has_cjk(s["text"])})
            # shrink bbox slightly: glyph boxes include leading
            x0, y0, x1, y1 = tighten(ln["bbox"], text)
            pad = (y1 - y0) * 0.15
            lines.append({"text": text, "bbox": [x0, y0 + pad, x1, y1 - pad], "raw": [x0, y0, x1, y1],
                          "block": bi, "size": min(sizes) if sizes else 0, "zh": has_cjk(text), "fonts": fonts})
    issues = []
    for ln in lines:
        x0, y0, x1, y1 = ln["raw"]
        if x0 < -1 or y0 < -1 or x1 > W + 1 or y1 > H + 1:
            issues.append({"level": "error", "type": "out_of_slide", "text": ln["text"][:60]})
        if ln["zh"] and ln["size"] < min_pt - 0.3:
            issues.append({"level": "error", "type": "too_small", "size": round(ln["size"], 1), "text": ln["text"][:60]})
    wordy = [ln for ln in lines if has_cjk(ln["text"]) or WORD.search(ln["text"])]  # drop equation glyph junk
    for i, a in enumerate(wordy):
        for b in wordy[i + 1:]:
            ov = inter(a["bbox"], b["bbox"])
            if ov and ov > 0.15 * min(area(a["bbox"]), area(b["bbox"])):
                level = "error" if (a["zh"] or b["zh"]) else "warn(pre-existing?)"
                issues.append({"level": level, "type": "text_overlap", "a": a["text"][:50], "b": b["text"][:50]})
            elif (a["zh"] or b["zh"]) and a["block"] != b["block"] and inter(a["raw"], b["raw"]) > 0:
                issues.append({"level": "warn", "type": "tight", "a": a["text"][:50], "b": b["text"][:50]})
    imgs = [im["bbox"] for im in page.get_image_info()
            if 400 < area(im["bbox"]) < 0.6 * W * H]  # skip slide backgrounds
    for ln in lines:
        if not ln["zh"]:
            continue
        for im in imgs:
            if inter(ln["bbox"], im) > 0.05 * area(ln["bbox"]):
                issues.append({"level": "warn", "type": "zh_on_image", "text": ln["text"][:60],
                               "image": [round(v) for v in im]})
                break
    fonts = sorted({f for ln in lines for f in ln["fonts"]})
    return issues, fonts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("deck", type=Path)
    ap.add_argument("out_dir", type=Path)
    ap.add_argument("--pages")
    ap.add_argument("--min-pt", type=float, default=12)
    ap.add_argument("--dpi", type=int, default=110)
    ap.add_argument("--pdf", type=Path, help="reuse an already exported PDF")
    ap.add_argument("--renderer", default="auto", choices=["auto", "powerpoint", "lok", "soffice", "none"])
    ap.add_argument("--lok-node")
    ap.add_argument("--lok-cli")
    a = ap.parse_args()
    a.out_dir.mkdir(parents=True, exist_ok=True)
    if a.deck.suffix.lower() == ".pdf":
        return check_pdf(a)
    tmp = Path(tempfile.mkdtemp(prefix="zhrender_"))
    copy = tmp / "render_input.pptx"
    unhidden_copy(a.deck.resolve(), copy)
    pdf = a.pdf
    if pdf is None and a.renderer != "none":
        pdf = (a.out_dir / (a.deck.stem + ".render.pdf")).resolve()
        how = export_pdf(copy, pdf, a)
        if how:
            print("rendered with", how)
        else:
            print("no renderer available (PowerPoint / DSH LibreOffice Kit / soffice); geometry is estimated only")
            pdf = None
    deck = Deck(str(a.deck))
    total = len(deck.slides)
    pages = parse_pages(a.pages, total)
    results = []
    if pdf is not None and pymupdf is not None:
        doc = pymupdf.open(pdf)
        for n in pages:
            page = doc[n - 1]
            png = a.out_dir / ("slide%02d.png" % n)
            page.get_pixmap(dpi=a.dpi).save(png)
            issues, fonts = check_page(page, a.min_pt)
            results.append({"slide": n, "png": str(png), "zh_fonts": fonts, "issues": issues})
        mode = "rendered-pdf"
    else:
        from estimate import check_slide
        pngs = {}
        lok = lok_paths(a) if a.renderer in ("auto", "lok") else None
        if lok and pdf is not None:  # rasterize the exported PDF (pdfium); rendering the pptx directly gives blank pages
            try:
                info = run_lok(lok, "render", "--input", str(pdf), "--output-dir", str(a.out_dir / "png"),
                               "--pages", ",".join(map(str, pages)), "--dpi", str(a.dpi))
                if not info:
                    info = json.loads((a.out_dir / "png" / "manifest.json").read_text())
                for im in info.get("images", []):
                    pngs[im["page"]] = im["path"]
            except (RuntimeError, OSError, ValueError) as e:
                print("PNG rendering failed:", e, file=sys.stderr)
        for n in pages:
            results.append({"slide": n, "png": pngs.get(n), "zh_fonts": [], "issues": check_slide(deck, n, a.min_pt)})
        mode = "estimated-from-xml (no PyMuPDF)"
    (a.out_dir / "check.json").write_text(json.dumps({"mode": mode, "pdf": str(pdf) if pdf else None,
                                                      "slides": results}, ensure_ascii=False, indent=1), encoding="utf-8")
    bad = 0
    print("check mode:", mode)
    for r in results:
        errs = [i for i in r["issues"] if i["level"] == "error"]
        bad += bool(errs)
        print("slide %d: %d error(s), %d warning(s); zh fonts %s -> %s" % (
            r["slide"], len(errs), len(r["issues"]) - len(errs), r["zh_fonts"] or "-", r["png"] or "no png"))
        for i in r["issues"]:
            print("   ", i)
    print("%d/%d pages with errors" % (bad, len(results)))


def check_pdf(a):
    from pdfmodel import ensure_pymupdf
    ensure_pymupdf(need_lxml=True)
    import pymupdf as fitz
    doc = fitz.open(a.deck)
    results, bad = [], 0
    for n in parse_pages(a.pages, doc.page_count):
        page = doc[n - 1]
        png = a.out_dir / ("page%02d.png" % n)
        page.get_pixmap(dpi=a.dpi).save(png)
        issues, fonts = check_page(page, a.min_pt)
        results.append({"page": n, "png": str(png), "zh_fonts": fonts, "issues": issues})
    (a.out_dir / "check.json").write_text(json.dumps({"mode": "pdf", "pdf": str(a.deck), "pages": results},
                                                     ensure_ascii=False, indent=1), encoding="utf-8")
    print("check mode: pdf")
    for r in results:
        errs = [i for i in r["issues"] if i["level"] == "error"]
        bad += bool(errs)
        print("page %d: %d error(s), %d warning(s) -> %s" % (r["page"], len(errs), len(r["issues"]) - len(errs), r["png"]))
        for i in r["issues"]:
            print("   ", i)
    print("%d/%d pages with errors" % (bad, len(results)))


if __name__ == "__main__":
    main()
