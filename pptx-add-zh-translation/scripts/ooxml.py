"""Low-level PPTX access with lxml.

python-pptx fails on decks containing mc:AlternateContent / OLE objects
('has_ph_elm' AttributeError), so everything here works on raw XML and
rewrites only the slide parts that changed; all other zip members are
copied byte-for-byte.
"""
import copy
import posixpath
import re
import zipfile

from lxml import etree

NS = {
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "mc": "http://schemas.openxmlformats.org/markup-compatibility/2006",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
}
EMU_PER_PT = 12700
CJK = re.compile(r"[㐀-鿿豈-﫿　-〿＀-￯]")


def q(tag):
    prefix, local = tag.split(":")
    return "{%s}%s" % (NS[prefix], local)


def has_cjk(text):
    return bool(CJK.search(text or ""))


def para_text(p):
    return "".join(t.text or "" for t in p.iter(q("a:t")))


class Deck:
    def __init__(self, path):
        self.path = path
        self.zip = zipfile.ZipFile(path)
        self.parts = {}  # name -> parsed tree (lazily)
        self.dirty = set()
        self.overrides = {}  # part name -> bytes (non-lxml edits, e.g. VML)
        pres = self.xml("ppt/presentation.xml")
        rels = self.rels("ppt/presentation.xml")
        size = pres.find("p:sldSz", NS)
        self.width_pt = int(size.get("cx")) / EMU_PER_PT
        self.height_pt = int(size.get("cy")) / EMU_PER_PT
        self.slides = []  # ordered slide part names
        for sld in pres.find("p:sldIdLst", NS):
            self.slides.append(rels[sld.get(q("r:id"))])

    # ---- parts -------------------------------------------------------
    def xml(self, name):
        if name not in self.parts:
            self.parts[name] = etree.fromstring(self.zip.read(name))
        return self.parts[name]

    def rels(self, name):
        """Return {rId: absolute part name} for a part."""
        folder, base = posixpath.split(name)
        rel_name = posixpath.join(folder, "_rels", base + ".rels")
        if rel_name not in self.zip.namelist():
            return {}
        out = {}
        for r in etree.fromstring(self.zip.read(rel_name)):
            if r.get("TargetMode") == "External":
                continue
            out[r.get("Id")] = posixpath.normpath(posixpath.join(folder, r.get("Target")))
        return out

    def related(self, name, kind):
        """First related part whose type ends with kind (e.g. 'slideLayout')."""
        folder, base = posixpath.split(name)
        rel_name = posixpath.join(folder, "_rels", base + ".rels")
        for r in etree.fromstring(self.zip.read(rel_name)):
            if r.get("Type").endswith("/" + kind):
                return posixpath.normpath(posixpath.join(folder, r.get("Target")))
        return None

    def read(self, name):
        return self.overrides.get(name) or self.zip.read(name)

    def slide(self, number):
        return self.xml(self.slides[number - 1])

    def mark(self, number):
        self.dirty.add(self.slides[number - 1])

    def save(self, out_path):
        with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as out:
            for info in self.zip.infolist():
                if info.filename in self.overrides:
                    out.writestr(info, self.overrides[info.filename])
                elif info.filename in self.dirty:
                    data = etree.tostring(self.parts[info.filename], xml_declaration=True,
                                          encoding="UTF-8", standalone=True)
                    out.writestr(info, data)
                else:
                    out.writestr(info, self.zip.read(info.filename))

    # ---- placeholders / inheritance ---------------------------------
    def layout_and_master(self, number):
        sname = self.slides[number - 1]
        layout = self.related(sname, "slideLayout")
        master = self.related(layout, "slideMaster") if layout else None
        return layout, master

    @staticmethod
    def ph_of(shape):
        ph = shape.find("./*/p:nvPr/p:ph", NS)
        return ph

    def matching_ph(self, part, ph):
        """Find placeholder shape in layout/master matching ph (idx, then type)."""
        root = self.xml(part)
        idx, typ = ph.get("idx"), ph.get("type", "body")
        cands = [s for s in root.iter(q("p:sp")) if self.ph_of(s) is not None]
        if idx is not None:
            for s in cands:
                if self.ph_of(s).get("idx") == idx:
                    return s
        norm = {"ctrTitle": "title", "subTitle": "body"}
        for s in cands:
            if norm.get(self.ph_of(s).get("type", "body"), self.ph_of(s).get("type", "body")) == norm.get(typ, typ):
                return s
        return None

    def ph_chain(self, number, shape):
        """[layout_shape, master_shape] the placeholder inherits from."""
        ph = self.ph_of(shape)
        if ph is None:
            return []
        layout, master = self.layout_and_master(number)
        chain = []
        for part in (layout, master):
            if part:
                s = self.matching_ph(part, ph)
                if s is not None:
                    chain.append(s)
        return chain

    def master_text_style(self, number, shape):
        _, master = self.layout_and_master(number)
        if not master:
            return None
        ph = self.ph_of(shape)
        styles = self.xml(master).find("p:txStyles", NS)
        if styles is None:
            return None
        if ph is None:
            return styles.find("p:otherStyle", NS)
        typ = ph.get("type", "body")
        if typ in ("title", "ctrTitle"):
            return styles.find("p:titleStyle", NS)
        return styles.find("p:bodyStyle", NS)


def own_xfrm(shape):
    for path in ("./p:spPr/a:xfrm", "./p:xfrm", "./p:grpSpPr/a:xfrm"):
        x = shape.find(path, NS)
        if x is not None and x.find("a:off", NS) is not None:
            return x
    return None


def xfrm_box(x):
    off, ext = x.find("a:off", NS), x.find("a:ext", NS)
    return [int(off.get("x")), int(off.get("y")), int(ext.get("cx")), int(ext.get("cy"))]


def shape_id(shape):
    nv = shape.find("./*/p:cNvPr", NS)
    return (int(nv.get("id")), nv.get("name")) if nv is not None else (None, None)


def iter_shapes(tree_root):
    """Yield (shape, group_transforms) for leaf shapes; descends groups and AlternateContent."""
    def walk(node, groups):
        for child in node:
            tag = etree.QName(child).localname
            if tag == "grpSp":
                gx = child.find("./p:grpSpPr/a:xfrm", NS)
                yield child, groups
                yield from walk(child, groups + ([gx] if gx is not None else []))
            elif tag in ("sp", "graphicFrame", "pic", "cxnSp"):
                yield child, groups
            elif tag == "AlternateContent":
                choice = child.find("mc:Choice", NS)
                if choice is not None:
                    yield from walk(choice, groups)
    spTree = tree_root.find("./p:cSld/p:spTree", NS)
    yield from walk(spTree, [])


def absolute_box(box, groups):
    """Map a child box through enclosing group transforms (innermost last)."""
    x, y, w, h = box
    for gx in reversed(groups):
        off, ext = gx.find("a:off", NS), gx.find("a:ext", NS)
        choff, chext = gx.find("a:chOff", NS), gx.find("a:chExt", NS)
        if choff is None or chext is None:
            continue
        sx = int(ext.get("cx")) / max(int(chext.get("cx")), 1)
        sy = int(ext.get("cy")) / max(int(chext.get("cy")), 1)
        x = int(off.get("x")) + (x - int(choff.get("x"))) * sx
        y = int(off.get("y")) + (y - int(choff.get("y"))) * sy
        w, h = w * sx, h * sy
    return [x, y, w, h]


def deep(el):
    return copy.deepcopy(el)


def _lvl_ppr(container, level):
    """a:lvlNpPr inside a lstStyle / txStyle element."""
    if container is None:
        return None
    return container.find("a:lvl%dpPr" % (level + 1), NS)


def style_chain(deck, number, shape, level):
    """lvlNpPr elements from most to least specific for a paragraph level."""
    chain = []
    body = shape.find("./p:txBody", NS)
    if body is not None:
        chain.append(_lvl_ppr(body.find("a:lstStyle", NS), level))
    for inherited in deck.ph_chain(number, shape):
        ib = inherited.find("./p:txBody", NS)
        if ib is not None:
            chain.append(_lvl_ppr(ib.find("a:lstStyle", NS), level))
    chain.append(_lvl_ppr(deck.master_text_style(number, shape), level))
    return [c for c in chain if c is not None]


def resolve_para(deck, number, shape, p):
    """Effective level, marL, indent (EMU) and font size (hundredths pt) of a paragraph."""
    ppr = p.find("a:pPr", NS)
    level = int(ppr.get("lvl", 0)) if ppr is not None else 0
    chain = ([ppr] if ppr is not None else []) + style_chain(deck, number, shape, level)

    def first(attr):
        for c in chain:
            if c.get(attr) is not None:
                return int(c.get(attr))
        return None

    size = None
    for r in p.iter(q("a:rPr")):
        if r.get("sz"):
            size = int(r.get("sz"))
            break
    if size is None:
        for c in chain:
            d = c.find("a:defRPr", NS)
            if d is not None and d.get("sz"):
                size = int(d.get("sz"))
                break
    body = shape.find("./p:txBody", NS)
    scale = 1.0
    if body is not None:
        fit = body.find("a:bodyPr/a:normAutofit", NS)
        if fit is not None and fit.get("fontScale"):
            scale = int(fit.get("fontScale")) / 100000
    return {"level": level, "marL": first("marL") or 0, "indent": first("indent") or 0,
            "sz": size or 1800, "fontScale": scale}


def resolve_box(deck, number, shape, groups):
    x = own_xfrm(shape)
    if x is None:
        for inherited in deck.ph_chain(number, shape):
            x = own_xfrm(inherited)
            if x is not None:
                break
    if x is None:
        return None
    box = absolute_box(xfrm_box(x), groups)
    return [round(v / EMU_PER_PT, 1) for v in box]
