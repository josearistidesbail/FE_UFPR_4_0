import sys, os, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from geom import *
from sexp import *
import re
def key(r):
    m=re.match(r'([A-Za-z#]+)(\d+)',r or ''); return (m.group(1),int(m.group(2))) if m else (r or '',0)
def dump(path, nets_only=False):
    root, lp, comps = sheet_pin_map(path)
    pinat={}
    for ref,c in comps.items():
        for num,xy in c['pins'].items(): pinat.setdefault(xy,[]).append((ref,num))
    net=collections.defaultdict(list); kindof={}
    for kind in ('label','global_label','hierarchical_label'):
        for l in [c for c in root if sym(c)==kind]:
            x,y,_=at(l); k=(round(x,4),round(y,4)); nm=val(l[1]); kindof[nm]=kind[0]
            for rp in pinat.get(k,[]): net[nm].append(rp)
    if not nets_only:
        print(f"### {path}  {len(comps)} components")
        by=collections.defaultdict(list)
        for ref in sorted(comps,key=key):
            c=comps[ref]; by[c['lib_id'].replace('FE_UFPR_4_0:','')].append(f"{ref}={c['props'].get('Value','')}")
        for lib in sorted(by): print(f"  {lib:32s} {'; '.join(by[lib])}")
    print(f"--- {len(net)} nets")
    for n in sorted(net, key=lambda n:(-len(net[n]),n)):
        print(f"  [{kindof[n]}] {n:22s} " + " ".join(f"{r}.{q}" for r,q in sorted(net[n],key=lambda t:key(t[0]))))
    lab={(round(at(l)[0],4),round(at(l)[1],4)) for k in ('label','global_label','hierarchical_label') for l in [c for c in root if sym(c)==k]}
    un=[(xy,v) for xy,v in pinat.items() if xy not in lab]
    if un: print("  unlabelled pins:", sorted(v[0] for xy,v in un))
    print("  texts:", [(round(at(t)[0]),round(at(t)[1]),val(t[1]).count('\\n')+1) for t in [c for c in root if sym(c)=='text']])
if __name__=='__main__': dump(sys.argv[1])
