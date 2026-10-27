"""Shared helpers for Word / Markdown mode (doc_inventory.py, doc_apply.py)."""
import re

CJK = re.compile(r"[㐀-鿿豈-﫿　-〿＀-￯]")
LATIN = re.compile(r"[A-Za-z]")


def classify(text):
    """en = needs Chinese; zh = already Chinese; misc = numbers/symbols only.
    'mixed' en blocks (English with a few Chinese words) still count as en."""
    t = text or ""
    cjk = len(CJK.findall(t))
    lat = len(LATIN.findall(t))
    if cjk and cjk * 2 >= lat:
        return "zh"
    if lat >= 2:
        return "en"
    return "misc"


def has_cjk(text):
    return bool(CJK.search(text or ""))


def out_name(src, suffix="_双语"):
    from pathlib import Path
    p = Path(src)
    return str(p.with_name(p.stem + suffix + p.suffix))
