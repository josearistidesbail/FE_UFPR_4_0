"""In-place KiCad schematic editor: move symbols, rebuild the graphical layer.
Symbol blocks are preserved verbatim except (at ...), (mirror ...) and field positions,
so UUIDs, properties, LCSC fields and instance paths survive untouched."""
import re, uuid, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sexp import parse, sym, val, get, getall
from geom import lib_pins, inst_pin_positions

def U(): return str(uuid.uuid4())
def n(v):
    """format a number the way KiCad does"""
    s = f"{round(float(v), 4):.4f}".rstrip('0').rstrip('.')
    return s if s not in ('', '-0') else '0'

class Sheet:
    def __init__(self, path):
        self.path = path
        self.text = open(path).read()
        self.root = parse(self.text)
        self.libpins = lib_pins(self.root)
        self._split()

    def _split(self):
        t = self.text
        # spans of every top-level node
        spans = []
        i, depth = 0, 0
        start = None
        # find top-level '(' at indent 1 tab
        for m in re.finditer(r'^\t\(', t, re.M):
            p = m.start() + 1
            d = 0; j = p; instr = False
            while j < len(t):
                c = t[j]
                if instr:
                    if c == '\\': j += 2; continue
                    if c == '"': instr = False
                elif c == '"': instr = True
                elif c == '(': d += 1
                elif c == ')':
                    d -= 1
                    if d == 0: break
                j += 1
            spans.append((p, j + 1))
        head_end = spans[0][0]
        self.header = t[:head_end].rstrip('\t')
        self.blocks = []           # (kind, text, ref_or_None)
        for (a, b) in spans:
            seg = t[a:b]
            kind = re.match(r'\((\w+)', seg).group(1)
            ref = None
            if kind == 'symbol':
                m = re.search(r'\(property "Reference" "([^"]+)"', seg)
                u = re.search(r'(?m)^\t\t\(unit (\d+)\)$', seg)
                ref = (m.group(1) if m else None, int(u.group(1)) if u else 1)
            self.blocks.append([kind, seg, ref])
        self.trailer = t[spans[-1][1]:]
        self.symbols = {}
        for b in self.blocks:
            if b[0] == 'symbol': self.symbols.setdefault(b[2][0], {})[b[2][1]] = b

    # ---------- symbol placement ----------
    def place(self, ref, x, y, rot=0, mirror=None, ref_off=(0, -2.54), val_off=(0, 2.54),
              field_rot=None, hide_value=False, unit=None):
        if field_rot is None: field_rot = {0:0, 90:270, 180:0, 270:90}[int(rot) % 360]
        assert mirror in (None,'x','y'), f"bad mirror {mirror!r} for {ref}"
        us = self.symbols[ref]
        if unit is None:
            assert len(us) == 1, f"{ref} has units {sorted(us)} - pass unit="
            unit = next(iter(us))
        blk = us[unit]
        seg = blk[1]
        seg = re.sub(r'(?m)^\t\t\(at [-\d.]+ [-\d.]+(?: [-\d.]+)?\)$',
                     f"\t\t(at {n(x)} {n(y)} {n(rot)})", seg, count=1)
        seg = re.sub(r'(?m)^\t\t\(mirror [xy]\)\n', '', seg)
        if mirror:
            seg = re.sub(r'(?m)^(\t\t\(at [^\n]*\)\n)', r'\1' + f"\t\t(mirror {mirror})\n", seg, count=1)
        def setprop(s, name, px, py, prot, just=None):
            pat = re.compile(r'(\(property "' + re.escape(name) + r'" "(?:[^"\\]|\\.)*"\n\t\t\t\(at )[-\d.]+ [-\d.]+ [-\d.]+(\))')
            s2, k = pat.subn(lambda m: m.group(1) + f"{n(px)} {n(py)} {n(prot)}" + m.group(2), s, count=1)
            if just:
                head = re.search(r'\(property "' + re.escape(name) + r'" "(?:[^"\\]|\\.)*"\n', s2)
                if head:
                    seg = s2[head.end():]
                    cut = seg.find("\n\t\t\t)\n")          # end of this property node
                    body = seg[:cut]
                    if "(justify" in body:          # MCP-written fields carry one already (S8)
                        body = re.sub(r'\(justify [^)]*\)', '(justify ' + just + ')', body, count=1)
                    else:                           # body ends with the font block's closing paren
                        body = body + "\n\t\t\t\t(justify " + just + ")"
                    s2 = s2[:head.end()] + body + seg[cut:]
            return s2
        rj = 'left' if ref_off[0] > 0.5 else ('right' if ref_off[0] < -0.5 else None)
        vj = 'left' if val_off[0] > 0.5 else ('right' if val_off[0] < -0.5 else None)
        if (mirror == 'y') != (int(rot) % 360 == 180):   # KiCad transforms a field's justification
            flip = {'left':'right','right':'left',None:None} # with the symbol: mirror-y and 180 flip it
            rj, vj = flip[rj], flip[vj]
        seg = setprop(seg, 'Reference', x + ref_off[0], y + ref_off[1], field_rot, rj)
        seg = setprop(seg, 'Value',     x + val_off[0], y + val_off[1], field_rot, vj)
        for h in ('Footprint', 'Datasheet', 'Description', 'LCSC'):
            seg = setprop(seg, h, x, y, 0)
        if hide_value:
            seg = re.sub(r'(\(property "Value"(?:[^()]|\([^()]*\))*?\(effects\n\t\t\t\t\(font\n\t\t\t\t\t\(size [\d.]+ [\d.]+\)\n\t\t\t\t\)\n)(\t\t\t\))',
                         r'\1\t\t\t\t(hide yes)\n\2', seg, count=1)
        blk[1] = seg

    def pins(self, ref, unit=None):
        """absolute pin coords using the CURRENT placement in the block text"""
        us = self.symbols[ref]
        out = {}
        for u, blk in us.items():
            if unit is not None and u != unit: continue
            out.update(inst_pin_positions(parse(blk[1]), self.libpins))
        return out

    # ---------- graphical layer ----------
    GFX = ('wire','junction','label','global_label','hierarchical_label',
           'text','text_box','no_connect','bus','bus_entry','polyline','rectangle',
           'netclass_flag','image','arc','circle')
    def clear_graphics(self):
        self.blocks = [b for b in self.blocks if b[0] not in self.GFX]
        self.symbols = {}
        for b in self.blocks:
            if b[0] == 'symbol': self.symbols.setdefault(b[2][0], {})[b[2][1]] = b
        self.gfx = []

    def wire(self, pts):
        for a, b in zip(pts, pts[1:]):
            self.gfx.append(
                f"\t(wire\n\t\t(pts\n\t\t\t(xy {n(a[0])} {n(a[1])}) (xy {n(b[0])} {n(b[1])})\n\t\t)\n"
                f"\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type default)\n\t\t)\n\t\t(uuid \"{U()}\")\n\t)\n")

    def junction(self, x, y):
        self.gfx.append(f"\t(junction\n\t\t(at {n(x)} {n(y)})\n\t\t(diameter 0)\n\t\t(color 0 0 0 0)\n\t\t(uuid \"{U()}\")\n\t)\n")

    def _lbl(self, kind, text, x, y, rot, just, extra="", size=1.27):
        return (f"\t({kind} \"{text}\"\n{extra}\t\t(at {n(x)} {n(y)} {n(rot)})\n"
                f"\t\t(effects\n\t\t\t(font\n\t\t\t\t(size {size} {size})\n\t\t\t)\n\t\t\t(justify {just})\n\t\t)\n"
                f"\t\t(uuid \"{U()}\")\n\t)\n")

    def label(self, text, x, y, rot=0, just="left bottom"):
        self.gfx.append(self._lbl('label', text, x, y, rot, just))

    def glabel(self, text, x, y, rot=0, just="left"):
        self.gfx.append(self._lbl('global_label', text, x, y, rot, just))

    def hlabel(self, text, x, y, rot=0, shape="output", just="left"):
        self.gfx.append(self._lbl('hierarchical_label', text, x, y, rot, just,
                                  extra=f"\t\t(shape {shape})\n"))

    def nc(self, x, y):
        self.gfx.append(f"\t(no_connect\n\t\t(at {n(x)} {n(y)})\n\t\t(uuid \"{U()}\")\n\t)\n")

    def add_text(self, s, x, y, size=1.27, just="left top"):
        self.gfx.append(f"\t(text \"{s}\"\n\t\t(exclude_from_sim no)\n\t\t(at {n(x)} {n(y)} 0)\n"
                        f"\t\t(effects\n\t\t\t(font\n\t\t\t\t(size {size} {size})\n\t\t\t)\n\t\t\t(justify {just})\n\t\t)\n"
                        f"\t\t(uuid \"{U()}\")\n\t)\n")

    def save(self, out=None):
        TAIL = ('sheet_instances', 'embedded_fonts', 'embedded_files')
        parts = [self.header]
        for b in self.blocks:
            if b[0] not in TAIL: parts.append("\t" + b[1] + "\n")
        parts.extend(self.gfx)
        for b in self.blocks:
            if b[0] in TAIL: parts.append("\t" + b[1] + "\n")
        parts.append(self.trailer.lstrip('\n'))
        txt = ''.join(parts)
        # header ends without newline handling
        open(out or self.path, 'w').write(txt)
