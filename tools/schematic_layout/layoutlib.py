import sys, os, re, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sheetedit import Sheet, n
from sexp import parse, sym, val, get, getall, at
from conncheck import interior, autojunctions

VERT = dict(ref_off=(3.302,-1.27), val_off=(3.302,1.905))   # vertical part: fields right
VERTL= dict(ref_off=(-3.302,-1.27), val_off=(-3.302,1.905)) # vertical part: fields left
HORZ = dict(ref_off=(0,-2.921), val_off=(0,3.556))          # horizontal part: above / below
HORZU= dict(ref_off=(0,-5.842), val_off=(0,-2.921))         # horizontal part: both fields above
HORZD= dict(ref_off=(0,3.556),  val_off=(0,6.477))          # horizontal part: both fields below

def orig_shapes(path):
    """name -> shape for hierarchical labels in the ORIGINAL sheet (must be preserved)"""
    root = parse(open(path).read()); out = {}
    for l in [c for c in root if sym(c) == 'hierarchical_label']:
        sh = get(l, 'shape')
        out[val(l[1])] = val(sh[1]) if sh else 'input'
    return out

def raw_texts(path):
    """the verbatim escaped strings of every text node, in file order"""
    t = open(path).read()
    return re.findall(r'\(text "((?:[^"\\]|\\.)*)"', t)

class Builder:
    def __init__(self, src):
        self.src = src
        self.s = Sheet(src)
        self.shapes = orig_shapes(src)
        self.texts = raw_texts(src)
        self.s.clear_graphics()
        self.W, self.J, self.L, self.G, self.H, self.NC = [], [], [], [], [], []
    # ---- geometry
    def place(self, *a, **k): self.s.place(*a, **k)
    def pins(self, ref, unit=None): return self.s.pins(ref, unit)
    def wire(self, *pts): self.W.append([(round(x,4), round(y,4)) for x,y in pts])
    def lab(self, t, x, y, r=0, j="left bottom"): self.L.append((t,x,y,r,j))
    def glab(self, t, x, y, r=0, j="left"): self.G.append((t,x,y,r,j))
    def hlab(self, t, x, y, r=0, j="left"): self.H.append((t,x,y,r,j))
    def nc(self, x, y): self.NC.append((x,y))
    def gnd(self, x, y, up=False): self.glab('GND', x, y, 270 if up else 90)
    def stub_gnd(self, x, y, d=2.54, up=False):
        yy = y - d if up else y + d
        self.wire((x,y),(x,yy)); self.gnd(x, yy, up)
    def shunt(self, ref, x, ynode, up=False, netlab=None, glob=False, d=2.54,
              pin1_at_node=True, **kw):
        """vertical 2-pin part hanging off a horizontal node.
        pin1_at_node=False puts pin 1 at the far end (pull-ups: pin1 = the rail)."""
        c = ynode - 3.81 if up else ynode + 3.81
        self.place(ref, x, c, 180 if (up == pin1_at_node) else 0, **(kw or VERT))
        far = ynode - 7.62 if up else ynode + 7.62
        end = far - d if up else far + d
        self.wire((x,far),(x,end))
        if netlab is None: self.gnd(x, end, up)
        elif glob: self.glab(netlab, x, end, 270 if up else 90)
        else: self.lab(netlab, x, end, 0, "left top" if not up else "left bottom")
    # ---- notes
    def notes(self, order, cols, y0, ymax, size=1.27, lead=1.9, gap=4.0):
        cw = [c for c in cols]; y = [y0]*len(cols); ci = 0
        for idx in order:
            t = self.texts[idx]; nl = t.count('\\n') + 1
            h = nl*lead + gap
            if y[ci] + h > ymax and ci < len(cols)-1: ci += 1
            self.s.add_text(t, cw[ci], y[ci], size); y[ci] += h
    # ---- emit
    def save(self, out):
        s = self.s
        segs = [(a,b) for p in self.W for a,b in zip(p, p[1:])]
        segs = [(a,b) for a,b in segs if a != b]
        pins = {}
        for ref in s.symbols:
            if ref is None: continue
            for k,xy in s.pins(ref).items(): pins.setdefault(xy,[]).append(f"{ref}.{k}")
        split=[]
        for a,b in segs:
            pts = sorted((p for p in pins if interior(p,a,b)),
                         key=lambda p:(p[0]-a[0])**2+(p[1]-a[1])**2)
            cur=a
            for p in pts: split.append((cur,p)); cur=p
            split.append((cur,b))
        for a,b in split: s.wire([a,b])
        for jx,jy in sorted(autojunctions(split, pins)): s.junction(jx,jy)
        for t,x,y,r,j in self.L: s.label(t,x,y,rot=r,just=j)
        for t,x,y,r,j in self.G: s.glabel(t,x,y,rot=r,just=j)
        for t,x,y,r,j in self.H: s.hlabel(t,x,y,rot=r,shape=self.shapes.get(t,'input'),just=j)
        for x,y in self.NC: s.nc(x,y)
        s.save(out)
        return len(split), len(self.L)+len(self.G)+len(self.H)
