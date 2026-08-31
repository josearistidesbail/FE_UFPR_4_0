"""Compute absolute schematic pin positions for symbol instances."""
import sys, os, math, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sexp import *

def lib_pins(root):
    """lib_id -> {unit: {pin_number: (x, y, angle)}}   unit 0 = common to all units"""
    out = {}
    ls = get(root, 'lib_symbols')
    if not ls: return out
    for s in getall(ls, 'symbol'):
        name = val(s[1]); units = {}
        for sub in getall(s, 'symbol'):
            sn = val(sub[1])
            m = re.match(r'.*_(\d+)_(\d+)$', sn)
            u = int(m.group(1)) if m else 1
            d = units.setdefault(u, {})
            for p in getall(sub, 'pin'):
                a = get(p, 'at'); num = get(p, 'number')
                if not num: continue
                d[val(num[1])] = (float(val(a[1])), float(val(a[2])),
                                  float(val(a[3])) if len(a) > 3 else 0.0)
        d = units.setdefault(1, {})
        for p in getall(s, 'pin'):
            a = get(p, 'at'); num = get(p, 'number')
            if num: d[val(num[1])] = (float(val(a[1])), float(val(a[2])),
                                      float(val(a[3])) if len(a)>3 else 0.0)
        out[name] = units
    return out

def inst_pin_positions(inst, libpins):
    """Return {pin_number: (X, Y)} in schematic coords."""
    lib_id = val(get(inst, 'lib_id')[1])
    a = get(inst, 'at')
    X, Y = float(val(a[1])), float(val(a[2]))
    rot = float(val(a[3])) if len(a) > 3 else 0.0
    m = get(inst, 'mirror')
    mirror = val(m[1]) if m else None
    units = libpins.get(lib_id, {})
    un = get(inst, 'unit')
    u = int(val(un[1])) if un else 1
    pins = dict(units.get(0, {}))
    pins.update(units.get(u, {}))
    res = {}
    for num, (px, py, pang) in pins.items():
        # library Y-up -> schematic Y-down
        x, y = px, -py
        r = math.radians(rot)
        # KiCad rotates FIRST, then applies the mirror in schematic space.
        cx = x * math.cos(r) + y * math.sin(r)
        cy = -x * math.sin(r) + y * math.cos(r)
        if mirror == 'y':   cx = -cx
        elif mirror == 'x': cy = -cy
        res[num] = (round(X + cx, 4), round(Y + cy, 4))
    return res

def sheet_pin_map(path):
    root = parse(open(path).read())
    lp = lib_pins(root)
    comps = {}
    for inst in [c for c in root if sym(c) == 'symbol']:
        props = {val(p[1]): val(p[2]) for p in getall(inst, 'property')}
        ref = props.get('Reference', '?')
        e = comps.setdefault(ref, dict(node=inst, props=props,
                                       lib_id=val(get(inst,'lib_id')[1]),
                                       pos=at(inst), pins={}))
        e['pins'].update(inst_pin_positions(inst, lp))
    return root, lp, comps
