"""Canonical, order-insensitive netlist fingerprint."""
import sys, subprocess, hashlib, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sexp import parse, sym, val, getall, get

def fingerprint(netfile):
    root = parse(open(netfile).read())
    nets = {}
    for n in getall(get(root, 'nets'), 'net'):
        name = val(get(n, 'name')[1])
        nodes = set()
        for nd in getall(n, 'node'):
            r = val(get(nd, 'ref')[1]); p = val(get(nd, 'pin')[1])
            nodes.add(f"{r}.{p}")
        nets[name] = nodes
    return nets

def report(a, b):
    ka, kb = set(a), set(b)
    ok = True
    for n in sorted(ka - kb): print(f"  NET REMOVED: {n} {sorted(a[n])}"); ok = False
    for n in sorted(kb - ka): print(f"  NET ADDED:   {n} {sorted(b[n])}"); ok = False
    for n in sorted(ka & kb):
        if a[n] != b[n]:
            ok = False
            print(f"  NET CHANGED: {n}")
            print(f"     lost:  {sorted(a[n]-b[n])}")
            print(f"     gained:{sorted(b[n]-a[n])}")
    return ok

if __name__ == '__main__':
    a = fingerprint(sys.argv[1]); b = fingerprint(sys.argv[2])
    print(f"A: {len(a)} nets, {sum(len(v) for v in a.values())} nodes")
    print(f"B: {len(b)} nets, {sum(len(v) for v in b.values())} nodes")
    print("IDENTICAL" if report(a,b) else "*** DIFFERENCES ABOVE ***")
