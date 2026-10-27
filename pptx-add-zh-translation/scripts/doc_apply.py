"""Apply a translation plan to a Word (.docx) or Markdown (.md) file.

Usage: python3 doc_apply.py in.docx plan.json out.docx [--report rep.json]
                            [--review pairs.md] [--merge plan_b2.json ...]
Plan format: references/doc-mode.md. Always apply to the original file.
"""
import argparse
import json
import sys

from doc_inventory import load

DEFAULTS = {"scale": 1.0, "min_pt": 10, "color": None, "ea_font": None, "tight": True,
            "heading": None, "md_list": "soft", "sep": "  "}


def as_list(v):
    return v if isinstance(v, list) else [v]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source")
    ap.add_argument("plan")
    ap.add_argument("out")
    ap.add_argument("--report")
    ap.add_argument("--review", help="write an English/Chinese pair list for proofreading")
    ap.add_argument("--merge", nargs="*", default=[])
    a = ap.parse_args()
    if a.source == a.out:
        sys.exit("refusing to overwrite the source; write <name>_双语.<ext>")
    is_md = not a.source.lower().endswith(".docx")
    plan = json.load(open(a.plan, encoding="utf-8"))
    items = list(plan.get("items", []))
    for extra in a.merge:
        items += json.load(open(extra, encoding="utf-8")).get("items", [])
    cfg = dict(DEFAULTS, **plan.get("defaults", {}))
    if cfg["heading"] is None:
        cfg["heading"] = "below" if is_md else "inline"
    doc = load(a.source)
    blocks = doc.blocks()
    by_id = {b["id"]: b for b in blocks}
    errors, notes, covered, pairs, seen = [], [], set(), [], set()

    def check(bid, where):
        if bid not in by_id:
            errors.append("%s: unknown block id %s (re-run doc_inventory.py on the original file?)" % (where, bid))
            return False
        return True

    for n, it in enumerate(items):
        where = "item %d" % (n + 1)
        if "skip" in it:
            if not it.get("why"):
                errors.append("%s: skip needs a why" % where)
            for bid in as_list(it["skip"]):
                if check(bid, where):
                    covered.add(bid)
            continue
        if "existing" in it:
            if check(it["existing"], where) and by_id[it["existing"]]["kind"] != "zh":
                notes.append("%s: existing %s is not Chinese (kind %s)" % (where, it["existing"], by_id[it["existing"]]["kind"]))
            for bid in as_list(it.get("covers", [])):
                if check(bid, where):
                    covered.add(bid)
            continue
        bid, zh = it.get("b"), (it.get("zh") or "").strip()
        if not bid or not zh:
            errors.append("%s: needs b and zh (or skip / existing)" % where)
            continue
        if not check(bid, where):
            continue
        if bid in seen:
            errors.append("%s: %s translated twice" % (where, bid))
            continue
        seen.add(bid)
        b = by_id[bid]
        if b["kind"] != "en":
            notes.append("%s: %s is kind %s, translated anyway" % (where, bid, b["kind"]))
        place = it.get("place") or (cfg["heading"] if b["role"] == "heading"
                                    else "inline" if b["role"] == "callout" else "below")
        sep = it.get("sep", cfg["sep"])
        if is_md and b["role"] == "cell":
            doc.add_cell(b, zh, cfg)
        elif place == "inline":
            doc.add_inline(b, zh, cfg, sep)
            if is_md and b["role"] == "heading":
                notes.append("%s: inline Chinese changes the heading anchor; links like [[file#%s]] break" % (bid, b["text"][:40]))
        elif place == "below":
            doc.add_below(b, zh, cfg)
        else:
            errors.append("%s: place must be below or inline" % where)
            continue
        covered.add(bid)
        for c in as_list(it.get("covers", [])):
            if check(c, where):
                covered.add(c)
        pairs.append((bid, b["text"], zh))

    optional_roles = {"header", "toc"}
    uncovered = [b for b in blocks if b["kind"] == "en" and b["id"] not in covered
                 and b["role"] not in optional_roles]
    optional = [b for b in blocks if b["kind"] == "en" and b["id"] not in covered
                and b["role"] in optional_roles]
    if errors:
        for e in errors:
            print("ERROR:", e)
        sys.exit(1)
    doc.save(a.out)
    if a.report:
        json.dump({"errors": errors, "notes": notes,
                   "uncovered": [{"id": b["id"], "text": b["text"]} for b in uncovered],
                   "optional_uncovered": [{"id": b["id"], "role": b["role"], "text": b["text"]} for b in optional],
                   "translated": len(pairs)},
                  open(a.report, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if a.review:
        lines = ["# 对照校读：%s" % a.out, ""]
        for bid, en, zh in pairs:
            lines += ["**%s** %s" % (bid, en.replace("\n", " ")), "", "> " + zh.replace("\n", "\n> "), ""]
        open(a.review, "w", encoding="utf-8").write("\n".join(lines))
    for line in notes:
        print("note:", line)
    for b in uncovered:
        print("uncovered: %s %s: %s" % (b["id"], b["role"], b["text"].replace("\n", " ")[:70]))
    if optional:
        print("optional (header/footer/TOC, not required): %s" % ", ".join(b["id"] for b in optional))
    print("wrote %s (%d translated, %d uncovered)" % (a.out, len(pairs), len(uncovered)))


if __name__ == "__main__":
    main()
