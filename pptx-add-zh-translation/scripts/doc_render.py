"""Render a .docx to PDF + PNG pages for a visual check (Word mode).

Usage: python3 doc_render.py out.docx chk_dir [--pages 1-3] [--dpi 80]
Renderer: WPS `wpscli word2pdf` (staged inside the WPS sandbox container),
else LibreOffice `soffice`. PNGs need PyMuPDF; without it only the PDF is written.
"""
import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from render_check import WPS_STAGE, WPSCLI


def to_pdf(docx, pdf):
    if WPSCLI.exists():
        WPS_STAGE.mkdir(parents=True, exist_ok=True)
        stage = Path(tempfile.mkdtemp(prefix="zhdoc_", dir=WPS_STAGE))
        s_in, s_out = stage / "render_input.docx", stage / "render_output.pdf"
        try:
            shutil.copyfile(docx, s_in)
            r = subprocess.run([str(WPSCLI), "word2pdf", str(s_in), "-o", str(s_out), "--json"],
                               capture_output=True, text=True, timeout=400)
            if r.returncode == 0 and s_out.exists():
                shutil.move(str(s_out), str(pdf))
                return "wps"
            print("WPS export failed:", (r.stdout + r.stderr).strip()[-300:], file=sys.stderr)
        finally:
            shutil.rmtree(stage, ignore_errors=True)
    office = shutil.which("soffice") or shutil.which("libreoffice")
    if office:
        subprocess.run([office, "--headless", "--convert-to", "pdf", "--outdir", str(pdf.parent), str(docx)],
                       capture_output=True, timeout=400)
        made = pdf.parent / (Path(docx).stem + ".pdf")
        if made.exists():
            made.rename(pdf)
            return "libreoffice (approximate)"
    sys.exit("no renderer (WPS / LibreOffice) found; open the file in Word/WPS to check")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("docx")
    ap.add_argument("out_dir")
    ap.add_argument("--pages")
    ap.add_argument("--dpi", type=int, default=80)
    a = ap.parse_args()
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    pdf = out / (Path(a.docx).stem + ".pdf")
    how = to_pdf(a.docx, pdf)
    try:
        import pymupdf
    except ImportError:
        print("rendered with %s -> %s (no PyMuPDF: open the PDF to look)" % (how, pdf))
        return
    doc = pymupdf.open(pdf)
    pages = range(1, len(doc) + 1)
    if a.pages:
        pages = []
        for part in a.pages.split(","):
            x, _, y = part.partition("-")
            pages += range(int(x), int(y or x) + 1)
    for n in pages:
        if 1 <= n <= len(doc):
            doc[n - 1].get_pixmap(dpi=a.dpi).save(out / ("page%02d.png" % n))
    print("rendered with %s -> %s (%d pages), PNG in %s" % (how, pdf, len(doc), out))


if __name__ == "__main__":
    main()
