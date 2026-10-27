"""Word (.docx) access with lxml for doc_inventory.py / doc_apply.py.

Blocks are paragraphs (w:p). Ids: B = body, F = footnotes, N = endnotes,
H = headers/footers; the number is the paragraph's position among all
paragraphs of that part (empty ones included), so ids stay stable.
Paragraphs inside mc:Fallback are not listed; edits to the matching
mc:Choice paragraph are mirrored into them. Only changed parts are
rewritten; everything else in the zip is copied byte-for-byte.
"""
import copy
import re
import zipfile

from lxml import etree

from codetext import code_runs, looks_like_code
from doc_common import classify

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {
    "w": W,
    "m": "http://schemas.openxmlformats.org/officeDocument/2006/math",
    "mc": "http://schemas.openxmlformats.org/markup-compatibility/2006",
}
MONO = re.compile(r"courier|consolas|menlo|monaco|mono|source code|fira code|lucida console|jetbrains", re.I)
XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"


def q(tag):
    prefix, local = tag.split(":")
    return "{%s}%s" % (NS[prefix], local)


def wattr(el, name):
    return el.get(q("w:" + name))


# pPr children whose order matters (ECMA-376 CT_PPrBase sequence)
PPR_ORDER = ["pStyle", "keepNext", "keepLines", "pageBreakBefore", "framePr", "widowControl",
             "numPr", "suppressLineNumbers", "pBdr", "shd", "tabs", "suppressAutoHyphens", "kinsoku",
             "wordWrap", "overflowPunct", "topLinePunct", "autoSpaceDE", "autoSpaceDN", "bidi",
             "adjustRightInd", "snapToGrid", "spacing", "ind", "contextualSpacing", "mirrorIndents",
             "suppressOverlap", "jc", "textDirection", "textAlignment", "textboxTightWrap",
             "outlineLvl", "divId", "cnfStyle", "rPr", "sectPr", "pPrChange"]
RPR_ORDER = ["rStyle", "rFonts", "b", "bCs", "i", "iCs", "caps", "smallCaps", "strike", "dstrike",
             "outline", "shadow", "emboss", "imprint", "noProof", "snapToGrid", "vanish", "webHidden",
             "color", "spacing", "w", "kern", "position", "sz", "szCs", "highlight", "u", "effect",
             "bdr", "shd", "fitText", "vertAlign", "rtl", "cs", "em", "lang", "eastAsianLayout",
             "specVanish", "oMath"]


def set_child(parent, local, order, attrs):
    """Get-or-create w:<local> under parent at its schema position, set attrs."""
    el = parent.find(q("w:" + local))
    if el is None:
        el = etree.Element(q("w:" + local))
        idx = order.index(local)
        pos = len(parent)
        for i, ch in enumerate(parent):
            name = etree.QName(ch).localname
            if name in order and order.index(name) > idx:
                pos = i
                break
        parent.insert(pos, el)
    for k, v in attrs.items():
        el.set(q("w:" + k), str(v))
    return el


def para_text(p):
    """Text of p itself (not of text boxes anchored in it); math is returned separately."""
    out, math = [], []

    def walk(el):
        for ch in el:
            tag = ch.tag
            if not isinstance(tag, str):
                continue
            if tag in (q("w:txbxContent"), q("mc:Fallback")):
                continue
            if tag == q("w:t"):
                out.append(ch.text or "")
            elif tag == q("w:tab"):
                out.append(" ")
            elif tag in (q("w:br"), q("w:cr")):
                out.append("\n")
            elif tag == q("m:t"):
                math.append(ch.text or "")
            elif tag == q("w:delText"):
                pass
            else:
                walk(ch)
    walk(p)
    return "".join(out), "".join(math)


class Docx:
    def __init__(self, path):
        self.path = path
        self.zip = zipfile.ZipFile(path)
        self.trees = {}
        self.dirty = set()
        names = self.zip.namelist()
        self.part_names = [("B", "word/document.xml")]
        for pref, name in (("F", "word/footnotes.xml"), ("N", "word/endnotes.xml")):
            if name in names:
                self.part_names.append((pref, name))
        for name in sorted(n for n in names if re.match(r"word/(header|footer)\d*\.xml$", n)):
            self.part_names.append(("H", name))
        self.styles = self._styles()
        self.numbering = self.xml("word/numbering.xml") if "word/numbering.xml" in names else None

    def xml(self, name):
        if name not in self.trees:
            self.trees[name] = etree.fromstring(self.zip.read(name))
        return self.trees[name]

    def _styles(self):
        out = {}
        if "word/styles.xml" not in self.zip.namelist():
            return out
        for st in self.xml("word/styles.xml").iter(q("w:style")):
            sid = wattr(st, "styleId")
            name_el = st.find("w:name", NS)
            ppr = st.find("w:pPr", NS)
            num = ppr.find("w:numPr", NS) if ppr is not None else None
            out[sid] = {
                "num": num,
                "name": wattr(name_el, "val") if name_el is not None else sid,
                "outline": ppr is not None and ppr.find("w:outlineLvl", NS) is not None,
                "based": wattr(st.find("w:basedOn", NS), "val") if st.find("w:basedOn", NS) is not None else None,
                "type": wattr(st, "type"),
            }
        return out

    def mono_share(self, p):
        """Share of p's text set in a monospace font (code listings)."""
        total = mono = 0
        for r in p.iter(q("w:r")):
            n = sum(len(t.text or "") for t in r.findall("w:t", NS))
            if not n:
                continue
            total += n
            f = r.find("w:rPr/w:rFonts", NS)
            fonts = " ".join(filter(None, (wattr(f, "ascii"), wattr(f, "hAnsi")))) if f is not None else ""
            if MONO.search(fonts):
                mono += n
        return mono / total if total else 0

    def style_num(self, p):
        """numPr inherited from the paragraph style chain (e.g. 'List Bullet'), or None."""
        ps = p.find("w:pPr/w:pStyle", NS)
        sid, hops = (wattr(ps, "val") if ps is not None else None), 0
        while sid and sid in self.styles and hops < 10:
            if self.styles[sid]["num"] is not None:
                return self.styles[sid]["num"]
            sid, hops = self.styles[sid]["based"], hops + 1
        return None

    def num_pr(self, p):
        own = p.find("w:pPr/w:numPr", NS)
        if own is not None:
            nid = own.find("w:numId", NS)
            return None if nid is not None and wattr(nid, "val") == "0" else own
        return self.style_num(p)

    def style_name(self, p):
        ps = p.find("w:pPr/w:pStyle", NS)
        if ps is None:
            return ""
        sid = wattr(ps, "val")
        return self.styles.get(sid, {}).get("name", sid) or sid

    def role(self, prefix, p):
        if prefix == "H":
            return "header"
        if prefix in "FN":
            return "footnote"
        name = self.style_name(p).lower()
        sid_el = p.find("w:pPr/w:pStyle", NS)
        sid = wattr(sid_el, "val") if sid_el is not None else None
        instr = " ".join(t.text or "" for t in p.iter(q("w:instrText")))
        instr += " ".join(wattr(f, "instr") or "" for f in p.iter(q("w:fldSimple")))
        if name.startswith("toc") or re.search(r"\bTOC\b|PAGEREF\s+_Toc", instr):
            return "toc"
        if (name.startswith("heading") or name in ("title", "subtitle")
                or p.find("w:pPr/w:outlineLvl", NS) is not None
                or (sid and self.styles.get(sid, {}).get("outline"))):
            return "heading"
        if re.search(r"code|preformatted|source", name) or self.mono_share(p) >= 0.7:
            return "code"
        if name == "caption":
            return "caption"
        if self.num_pr(p) is not None:
            return "list"
        return "para"

    # ---- blocks --------------------------------------------------------
    def blocks(self):
        """All paragraphs in reading order with id, role, kind, text, location."""
        out, counters = [], {}
        for prefix, name in self.part_names:
            root = self.xml(name)
            tables = {t: i + 1 for i, t in enumerate(root.iter(q("w:tbl")))}
            mirrors = self._fallback_map(root)
            idx = counters.get(prefix, 0)
            for p in root.iter(q("w:p")):
                if any(a.tag == q("mc:Fallback") for a in p.iterancestors()):
                    continue
                idx += 1
                text, math = para_text(p)
                if not text.strip() and not math.strip():
                    continue
                n = idx
                role = self.role(prefix, p)
                loc = []
                for a in p.iterancestors():
                    if a.tag == q("w:txbxContent"):
                        loc.append("textbox")
                        break
                tc = next((a for a in p.iterancestors() if a.tag == q("w:tc")), None)
                if tc is not None:
                    tr = tc.getparent()
                    tbl = tr.getparent()
                    r = [x for x in tbl if x.tag == q("w:tr")].index(tr)
                    c = [x for x in tr if x.tag == q("w:tc")].index(tc)
                    loc.append("table%d r%dc%d" % (tables.get(tbl, 0), r, c))
                    if role == "para":
                        role = "cell"
                if prefix == "H":
                    loc.append(name.split("/")[-1])
                kind = "code" if role == "code" else classify(text) if text.strip() else "misc"
                out.append({
                    "id": "%s%d" % (prefix, n), "role": role, "kind": kind,
                    "style": self.style_name(p), "loc": " ".join(loc),
                    "text": text, "math": math, "el": p, "part": name,
                    "mirror": mirrors.get(p),
                    "level": self.list_level(p),
                })
            counters[prefix] = idx
        # code typeset in a normal font (C listings, program output in a lab sheet): recognised from the text
        for b in out:
            if b["kind"] == "en" and b["role"] in ("para", "cell", "list") and looks_like_code(b["text"].split("\n")):
                b["kind"] = "code"
        code_runs(out, lambda a, b: a["part"] == b["part"] and a["role"] == b["role"] == "para"
                  and int(b["id"][1:]) - int(a["id"][1:]) <= 2)  # consecutive paragraphs, one blank between at most
        return out

    def _fallback_map(self, root):
        """mc:Choice text-box paragraph -> matching mc:Fallback paragraph."""
        out = {}
        for ac in root.iter(q("mc:AlternateContent")):
            ch, fb = ac.find("mc:Choice", NS), ac.find("mc:Fallback", NS)
            if ch is None or fb is None:
                continue
            a = [list(t.iter(q("w:p"))) for t in ch.iter(q("w:txbxContent"))]
            b = [list(t.iter(q("w:p"))) for t in fb.iter(q("w:txbxContent"))]
            for pa, pb in zip(a, b):
                if len(pa) == len(pb):
                    out.update(zip(pa, pb))
        return out

    def list_level(self, p):
        num = self.num_pr(p)
        if num is None:
            return None
        il = num.find("w:ilvl", NS)
        return int(wattr(il, "val")) if il is not None else 0

    def list_indent(self, p):
        """Left text indent (twips) of p's numbering level, or None."""
        if self.numbering is None:
            return None
        num_pr = self.num_pr(p)
        num = num_pr.find("w:numId", NS) if num_pr is not None else None
        if num is None:
            return None
        ilvl = self.list_level(p) or 0
        num_id = wattr(num, "val")
        for n in self.numbering.iter(q("w:num")):
            if wattr(n, "numId") != num_id:
                continue
            for ov in n.findall("w:lvlOverride", NS):
                if wattr(ov, "ilvl") == str(ilvl):
                    ind = ov.find("w:lvl/w:pPr/w:ind", NS)
                    if ind is not None:
                        return wattr(ind, "left") or wattr(ind, "start")
            abs_el = n.find("w:abstractNumId", NS)
            abs_id = wattr(abs_el, "val") if abs_el is not None else None
            for an in self.numbering.iter(q("w:abstractNum")):
                if wattr(an, "abstractNumId") != abs_id:
                    continue
                for lvl in an.findall("w:lvl", NS):
                    if wattr(lvl, "ilvl") == str(ilvl):
                        ind = lvl.find("w:pPr/w:ind", NS)
                        if ind is not None:
                            return wattr(ind, "left") or wattr(ind, "start")
        return None

    # ---- editing -------------------------------------------------------
    def main_rpr(self, p):
        """rPr of the run carrying the most text (the paragraph's 'body' formatting)."""
        best, best_len = None, -1
        for r in p.iter(q("w:r")):
            if any(a.tag in (q("w:txbxContent"), q("mc:Fallback")) for a in r.iterancestors()):
                continue
            n = sum(len(t.text or "") for t in r.findall("w:t", NS))
            if n > best_len:
                best, best_len = r, n
        rpr = best.find("w:rPr", NS) if best is not None else None
        rpr = copy.deepcopy(rpr) if rpr is not None else etree.Element(q("w:rPr"))
        rs = rpr.find("w:rStyle", NS)
        if rs is not None and "hyperlink" in self.styles.get(wattr(rs, "val"), {}).get("name", wattr(rs, "val")).lower():
            rpr.remove(rs)
            for tag in ("w:u", "w:color"):
                el = rpr.find(tag, NS)
                if el is not None:
                    rpr.remove(el)
        for tag in ("w:vertAlign", "w:highlight", "w:rPrChange", "w:vanish", "w:webHidden"):
            el = rpr.find(tag, NS)
            if el is not None:
                rpr.remove(el)
        return rpr

    def zh_run(self, rpr, text, cfg):
        rpr = copy.deepcopy(rpr)
        if cfg.get("ea_font"):
            set_child(rpr, "rFonts", RPR_ORDER, {"eastAsia": cfg["ea_font"], "hint": "eastAsia"})
        if cfg.get("color"):
            set_child(rpr, "color", RPR_ORDER, {"val": cfg["color"]})
        scale = cfg.get("scale", 1.0)
        if scale != 1.0:
            for tag in ("sz", "szCs"):
                el = rpr.find("w:" + tag, NS)
                if el is not None:
                    el.set(q("w:val"), str(max(int(cfg["min_pt"] * 2), round(int(wattr(el, "val")) * scale))))
        set_child(rpr, "lang", RPR_ORDER, {"eastAsia": "zh-CN"})
        r = etree.Element(q("w:r"))
        if len(rpr):
            r.append(rpr)
        for i, line in enumerate(text.split("\n")):
            if i:
                etree.SubElement(r, q("w:br"))
            t = etree.SubElement(r, q("w:t"))
            t.text = line
            t.set(XML_SPACE, "preserve")
        return r

    def add_below(self, block, zh, cfg):
        p = block["el"]
        self._below(p, zh, cfg, block["role"])
        if block["mirror"] is not None:
            self._below(block["mirror"], zh, cfg, block["role"])
        self.dirty.add(block["part"])

    def _below(self, p, zh, cfg, role):
        new = etree.Element(q("w:p"))
        old_ppr = p.find("w:pPr", NS)
        ppr = copy.deepcopy(old_ppr) if old_ppr is not None else etree.Element(q("w:pPr"))
        for tag in ("numPr", "sectPr", "pageBreakBefore", "framePr", "pPrChange"):
            el = ppr.find("w:" + tag, NS)
            if el is not None:
                ppr.remove(el)
        if role == "heading":
            for tag in ("pStyle", "outlineLvl"):
                el = ppr.find("w:" + tag, NS)
                if el is not None:
                    ppr.remove(el)
            set_child(ppr, "keepLines", PPR_ORDER, {})
        if role == "list" and self.style_num(p) is not None:  # style-level bullets: switch off
            num = set_child(ppr, "numPr", PPR_ORDER, {})
            etree.SubElement(num, q("w:numId")).set(q("w:val"), "0")
        left = self.list_indent(p) if role == "list" else None
        ind = ppr.find("w:ind", NS)
        if left is not None and (ind is None or not (wattr(ind, "left") or wattr(ind, "start"))):
            ind = set_child(ppr, "ind", PPR_ORDER, {"left": left})
        if ind is not None:
            for a in ("hanging", "hangingChars", "firstLine", "firstLineChars"):
                ind.attrib.pop(q("w:" + a), None)
            if role == "list" and left is not None and not (wattr(ind, "left") or wattr(ind, "start")):
                ind.set(q("w:left"), left)
        if cfg.get("tight", True):
            sp = set_child(ppr, "spacing", PPR_ORDER, {"before": 0})
            sp.attrib.pop(q("w:beforeAutospacing"), None)
            sp.attrib.pop(q("w:beforeLines"), None)
            if old_ppr is None:
                old_ppr = etree.Element(q("w:pPr"))
                p.insert(0, old_ppr)
            osp = set_child(old_ppr, "spacing", PPR_ORDER, {"after": 0})
            osp.attrib.pop(q("w:afterAutospacing"), None)
            osp.attrib.pop(q("w:afterLines"), None)
        new.append(ppr)
        rpr = self.main_rpr(p)
        if role == "heading" and rpr.find("w:b", NS) is None:
            set_child(rpr, "b", RPR_ORDER, {})
        new.append(self.zh_run(rpr, zh, cfg))
        sect = old_ppr.find("w:sectPr", NS) if old_ppr is not None else None
        if sect is not None:  # section break stays at the end of the section
            old_ppr.remove(sect)
            ppr.append(sect)
        if not len(ppr):
            new.remove(ppr)
        p.addnext(new)

    def add_inline(self, block, zh, cfg, sep):
        for p in (block["el"], block["mirror"]):
            if p is None:
                continue
            rpr = self.main_rpr(p)
            p.append(self.zh_run(rpr, sep + zh, cfg))
        self.dirty.add(block["part"])

    def save(self, out):
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
            for info in self.zip.infolist():
                if info.filename in self.dirty:
                    data = etree.tostring(self.trees[info.filename], xml_declaration=True,
                                          encoding="UTF-8", standalone=True)
                    z.writestr(info, data)
                else:
                    z.writestr(info, self.zip.read(info.filename))
