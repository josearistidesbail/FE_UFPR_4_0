"""Reproduce KiCad schematic connectivity from geometry, and flag bad crossings.

KiCad rules implemented:
  * a wire's two endpoints are connected
  * a pin / label anchor lying anywhere on a wire (endpoint or interior) joins it
  * two wires crossing at a point interior to BOTH are NOT connected (no junction)
  * a wire endpoint touching another wire's interior IS connected
"""
import sys, os, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sexp import parse, sym, val, get, getall, at
from geom import lib_pins, inst_pin_positions

EPS = 1e-6
def onseg(p, a, b):
    (px,py),(ax,ay),(bx,by) = p,a,b
    if abs((bx-ax)*(py-ay) - (by-ay)*(px-ax)) > 1e-4: return False
    return (min(ax,bx)-EPS <= px <= max(ax,bx)+EPS) and (min(ay,by)-EPS <= py <= max(ay,by)+EPS)
def interior(p,a,b):
    return onseg(p,a,b) and p != a and p != b

class DSU:
    def __init__(self): self.p={}
    def find(self,x):
        self.p.setdefault(x,x)
        while self.p[x]!=x: self.p[x]=self.p[self.p[x]]; x=self.p[x]
        return x
    def union(self,a,b): 
        ra,rb=self.find(a),self.find(b)
        if ra!=rb: self.p[ra]=rb

def analyze(path):
    root = parse(open(path).read())
    lps  = lib_pins(root)
    pins = {}   # (x,y) -> [ "REF.N" ]
    for inst in [c for c in root if sym(c)=='symbol']:
        props={val(p[1]):val(p[2]) for p in getall(inst,'property')}
        ref=props.get('Reference','?')
        if ref.startswith('#'): pass
        for num,xy in inst_pin_positions(inst,lps).items():
            pins.setdefault(xy,[]).append(f"{ref}.{num}")
    segs=[]
    for w in [c for c in root if sym(c)=='wire']:
        q=getall(get(w,'pts'),'xy')
        a=(round(float(val(q[0][1])),4),round(float(val(q[0][2])),4))
        b=(round(float(val(q[1][1])),4),round(float(val(q[1][2])),4))
        segs.append((a,b))
    labels=[]
    for kind in ('label','global_label','hierarchical_label'):
        for l in [c for c in root if sym(c)==kind]:
            x,y,_=at(l); labels.append(((round(x,4),round(y,4)), val(l[1]), kind))
    d=DSU()
    for i,(a,b) in enumerate(segs):
        d.union(('s',i),('p',a)); d.union(('s',i),('p',b))
    pois = set(pins) | {p for p,_,_ in labels} | {p for s in segs for p in s}
    for i,(a,b) in enumerate(segs):
        for p in pois:
            if onseg(p,a,b): d.union(('p',p),('s',i))
    # groups
    groups=collections.defaultdict(lambda: {'pins':set(),'names':set()})
    for xy,refs in pins.items():
        g=groups[d.find(('p',xy))]; g['pins'].update(refs)
    for xy,name,kind in labels:
        groups[d.find(('p',xy))]['names'].add(name)
    nets={}
    problems=[]
    for root_key,g in groups.items():
        if not g['pins'] and not g['names']: continue
        if len(g['names'])>1:
            problems.append(f"SHORT: nets {sorted(g['names'])} merged, pins {sorted(g['pins'])}")
        name=sorted(g['names'])[0] if g['names'] else f"<unnamed:{sorted(g['pins'])[:2]}>"
        nets.setdefault(name,set()).update(g['pins'])
    # visual crossings: perpendicular segs meeting at a point interior to both
    cross=[]
    for i in range(len(segs)):
        for j in range(i+1,len(segs)):
            a1,b1=segs[i]; a2,b2=segs[j]
            h1 = abs(a1[1]-b1[1])<EPS; h2 = abs(a2[1]-b2[1])<EPS
            v1 = abs(a1[0]-b1[0])<EPS; v2 = abs(a2[0]-b2[0])<EPS
            if h1 and v2: p=(a2[0],a1[1])
            elif v1 and h2: p=(a1[0],a2[1])
            else: continue
            if interior(p,a1,b1) and interior(p,a2,b2): cross.append(p)
    return nets, problems, cross, pins, segs

def autojunctions(segs, pins):
    """points needing an explicit junction dot"""
    endpoints=collections.Counter()
    for a,b in segs: endpoints[a]+=1; endpoints[b]+=1
    js=set()
    for p,c in endpoints.items():
        if c>=3: js.add(p)
    for a,b in segs:
        for p in list(endpoints):
            if interior(p,a,b): js.add(p)
    return js
