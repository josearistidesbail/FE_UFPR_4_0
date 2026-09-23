#!/usr/bin/env python3
"""S11 GND stitching / thermal via generator for FE_UFPR_4_0 (2026-09-23).

Verified on commit cbd091b: 327 vias + 154 stubs, DRC starved_thermal 33 -> 0 (with the .kicad_dru
single-spoke waiver for C11/C13/L2/U17), unconnected 14 -> 6 (all pre-existing routing gaps), no new
violation of any type.  See S11_PREFAB_REVIEW.md section 3.

Usage:  python3 stitch.py <board.kicad_pcb> <out.kicad_pcb> [--plan plan.json]

Reads the board with pcbnew (in-memory zone refill), decides via positions with
exact shape collision tests, then writes the result as *text* (via/segment
blocks appended before the file's closing paren; the 6 net-less vias get
(net "GND")).  Nothing else in the file is touched.  Verification is the real
`kicad-cli pcb drc --refill-zones` on the output.
"""
import sys, json, math, uuid, re
import pcbnew

SRC, DST = sys.argv[1], sys.argv[2]
PLAN = sys.argv[sys.argv.index("--plan") + 1] if "--plan" in sys.argv else None
NM = lambda mm: int(round(mm * 1e6))
MM = lambda nm: nm / 1e6

VIA_D, VIA_DRILL = 0.6, 0.3
CLR = 0.30            # clearance to any other-net copper (Analog/Power_3A max)
HOLE2HOLE = 0.50      # board rule
EDGE = 1.5            # distance from board bbox edge
STUB_W = 0.30
PAD_NEAR = 2.0        # pad needs a GND via within this radius, else we add one
GRID = 7.0            # open-area grid pitch
GRID_MIN = 4.5        # grid via only if no GND via closer than this
FENCE = 6.0           # edge fence pitch

import os
if os.path.exists(DST + ".stitched.json") and "--force" not in sys.argv:
    sys.exit(f"{DST} already stitched ({DST}.stitched.json exists) - refusing to add vias twice; use --force to override")
b = pcbnew.LoadBoard(SRC)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
F, B = pcbnew.F_Cu, pcbnew.B_Cu
LAY = {F: "F.Cu", B: "B.Cu"}

gnd_zone = [z for z in b.Zones() if z.GetNetname() == "GND" and len(z.GetLayerSet().Seq()) >= 3][0]
fill = {l: gnd_zone.GetFilledPolysList(l) for l in (F, B, pcbnew.In1_Cu)}
gfills = {l: [z.GetFilledPolysList(l) for z in b.Zones() if z.GetNetname() == "GND" and z.IsOnLayer(l)] for l in (F, B)}
def in_gnd_fill(l, x, y, r=0.2):
    return any(all(poly.Contains(pcbnew.VECTOR2I(NM(x + ex), NM(y + ey))) for ex, ey in ((0, 0), (r, 0), (-r, 0), (0, r), (0, -r))) for poly in gfills[l])
p33_in2 = [z for z in b.Zones() if z.GetNetname() == "+3V3" and b.GetLayerName(z.GetLayerSet().Seq()[0]) == "In2.Cu"]

# ---------------- obstacles ----------------
pads = []
for fp in b.GetFootprints():
    for p in fp.Pads():
        pads.append(p)
tracks = []  # via/segments parsed from text (pcbnew Tracks() iteration is broken on py3.14)
txt = open(SRC).read()
segs = []
for m in re.finditer(r"\n\t\(segment\n(.*?)\n\t\)", txt, re.S):
    g = lambda pat: re.search(pat, m.group(1))
    s = g(r"\(start ([-\d.]+) ([-\d.]+)\)"); e = g(r"\(end ([-\d.]+) ([-\d.]+)\)")
    segs.append(dict(x1=float(s.group(1)), y1=float(s.group(2)), x2=float(e.group(1)), y2=float(e.group(2)),
                     w=float(g(r"\(width ([\d.]+)\)").group(1)), layer=g(r'\(layer "([^"]+)"\)').group(1),
                     net=g(r'\(net "([^"]*)"\)').group(1)))
vias = []
for m in re.finditer(r"\n\t\(via\n(.*?)\n\t\)", txt, re.S):
    g = lambda pat: re.search(pat, m.group(1))
    a = g(r"\(at ([-\d.]+) ([-\d.]+)\)")
    vias.append(dict(x=float(a.group(1)), y=float(a.group(2)), size=float(g(r"\(size ([\d.]+)\)").group(1)),
                     drill=float(g(r"\(drill ([\d.]+)\)").group(1)), net=g(r'\(net "([^"]*)"\)').group(1)))
bb = b.GetBoardEdgesBoundingBox()
BX0, BY0, BX1, BY1 = MM(bb.GetLeft()), MM(bb.GetTop()), MM(bb.GetRight()), MM(bb.GetBottom())

def pseg(px, py, s):
    x1, y1, x2, y2 = s["x1"], s["y1"], s["x2"], s["y2"]
    dx, dy = x2 - x1, y2 - y1
    L2 = dx * dx + dy * dy
    t = 0 if L2 == 0 else max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / L2))
    return math.hypot(px - (x1 + t * dx), py - (y1 + t * dy))

def pad_layers(p):
    return [l for l in (F, B) if p.IsOnLayer(l)]

def via_ok(x, y, net="GND", layers=(F, B), need_fill=True, allow_pads=(), fill_layers=None, edge=None):
    """Can a VIA_D/VIA_DRILL via of `net` sit at (x,y)?  Returns True or a reason string."""
    edge = EDGE if edge is None else edge
    if not (BX0 + edge <= x <= BX1 - edge and BY0 + edge <= y <= BY1 - edge):
        return "edge"
    pt = pcbnew.VECTOR2I(NM(x), NM(y))
    r = VIA_D / 2
    for p in pads:
        if p in allow_pads:
            continue
        # hole-to-hole for PTH / NPTH
        if p.GetDrillSizeX() > 0:
            if math.hypot(x - MM(p.GetPosition().x), y - MM(p.GetPosition().y)) < VIA_DRILL / 2 + MM(p.GetDrillSizeX()) / 2 + HOLE2HOLE:
                return "hole2hole " + p.GetParentFootprint().GetReference()
        same = (p.GetNetname() == net)
        for l in pad_layers(p):
            if l not in layers and not p.GetDrillSizeX():
                continue
            shp = p.GetEffectiveShape(l)
            # same-net SMD pad: keep the via out of the pad copper (no via-in-pad)
            clr = 0.10 if same else CLR
            if shp.Collide(pt, NM(r + clr)):
                return "pad " + p.GetParentFootprint().GetReference() + "." + p.GetNumber()
    for s in segs:
        if s["net"] == net:
            continue
        l = {"F.Cu": F, "B.Cu": B}.get(s["layer"])
        if l is None and s["layer"] != "In2.Cu":
            continue
        if pseg(x, y, s) < r + s["w"] / 2 + CLR:
            return "track " + s["net"]
    for v in vias + new_vias:
        d = math.hypot(x - v["x"], y - v["y"])
        if d < VIA_DRILL / 2 + v["drill"] / 2 + HOLE2HOLE:
            return "via hole2hole"
        if v["net"] != net and d < r + v["size"] / 2 + CLR:
            return "via " + v["net"]
    if need_fill and net == "GND":
        # the via must sit in GND pour on at least one outer layer (else it stitches nothing)
        ok_any = False
        for l in (fill_layers or (F, B)):
            poly = fill[l]
            if all(poly.Contains(pcbnew.VECTOR2I(NM(x + dx), NM(y + dy))) for dx, dy in ((0, 0), (r + 0.15, 0), (-r - 0.15, 0), (0, r + 0.15), (0, -r - 0.15))):
                ok_any = True
        if not ok_any:
            return "no GND fill"
    return True

def stub_ok(x1, y1, x2, y2, layer, net="GND", allow_pads=()):
    """0.3 mm track from pad centre to via: clearance to every other-net item on that layer."""
    seg = dict(x1=x1, y1=y1, x2=x2, y2=y2)
    n = 6
    for i in range(n + 1):
        px, py = x1 + (x2 - x1) * i / n, y1 + (y2 - y1) * i / n
        pt = pcbnew.VECTOR2I(NM(px), NM(py))
        for p in pads:
            if p in allow_pads or p.GetNetname() == net or not p.IsOnLayer(layer):
                continue
            if p.GetEffectiveShape(layer).Collide(pt, NM(STUB_W / 2 + CLR)):
                return False
        for s in segs:
            if s["net"] == net or s["layer"] != LAY[layer]:
                continue
            if pseg(px, py, s) < STUB_W / 2 + s["w"] / 2 + CLR:
                return False
        for v in vias + new_vias:
            if v["net"] != net and math.hypot(px - v["x"], py - v["y"]) < STUB_W / 2 + v["size"] / 2 + CLR:
                return False
    return True

new_vias, new_segs, notes = [], [], []
def add_via(x, y, net="GND", why=""):
    new_vias.append(dict(x=round(x, 3), y=round(y, 3), size=VIA_D, drill=VIA_DRILL, net=net, why=why))
def add_seg(x1, y1, x2, y2, layer, net="GND"):
    new_segs.append(dict(x1=round(x1, 3), y1=round(y1, 3), x2=round(x2, 3), y2=round(y2, 3), w=STUB_W, layer=LAY[layer], net=net))

gvias = lambda: [v for v in vias + new_vias if v["net"] == "GND"]
def nearest_gnd_via(x, y):
    return min((math.hypot(v["x"] - x, v["y"] - y) for v in gvias()), default=99)

# ---------------- 1. U1 exposed pad: vias at the footprint's 8 thermal sub-pads ----------------
# (U1's Texas_HSOP-8 ThermalVias footprint already carries 8 PTH thermal vias as pads — nothing to add)

# ---------------- 2. U3 (AMS1117) tab -> In2 +3V3 pour ----------------
u3 = [f for f in b.GetFootprints() if f.GetReference() == "U3"][0]
tab = [p for p in u3.Pads() if p.GetNumber() == "2" and MM(p.GetSizeY()) > 3][0]
tx, ty = MM(tab.GetPosition().x), MM(tab.GetPosition().y)
for dy in (-1.1, 0.0, 1.1):
    x, y = tx, ty + dy
    pt = pcbnew.VECTOR2I(NM(x), NM(y))
    if p33_in2 and p33_in2[0].Outline().Contains(pt) and via_ok(x, y, "+3V3", need_fill=False, allow_pads=(tab,)) is True:
        add_via(x, y, "+3V3", "U3 tab thermal -> In2 +3V3")
    else:
        notes.append(f"U3 tab via at ({x:.2f},{y:.2f}) skipped (outside In2 +3V3 pour or blocked)")

# ---------------- 3. net-less vias inside GND copper -> GND ----------------
fix_net = []
for v in vias:
    if v["net"] == "":
        pt = pcbnew.VECTOR2I(NM(v["x"]), NM(v["y"]))
        if gnd_zone.Outline().Contains(pt):
            fix_net.append((v["x"], v["y"]))
            v["net"] = "GND"

# ---------------- 4. one via per SMD GND pad that has none within PAD_NEAR ----------------
DEBUG = set(sys.argv[sys.argv.index("--debug") + 1].split(",")) if "--debug" in sys.argv else set()
# pads DRC reported as starved_thermal on cbd091b (2026-09-23) - they always get a stub even if a via is near
starved = set(['C11.2', 'C110.2', 'C112.2', 'C114.2', 'C122.2', 'C13.2', 'C21.2', 'C41.2', 'C44.2', 'C54.2', 'C59.2', 'C60.2', 'C68.2', 'C75.2', 'C82.2', 'C83.2', 'C85.2', 'C87.2', 'C89.2', 'C91.2', 'R26.2', 'R29.2', 'R32.2', 'R77.2', 'U11.2', 'U11.3', 'U17.4', 'U18.2', 'U21.2', 'U8.2'])
if "--starved" in sys.argv:
    starved = set(json.load(open(sys.argv[sys.argv.index("--starved") + 1])))
pad_rows = []
for fp in b.GetFootprints():
    cx, cy = MM(fp.GetPosition().x), MM(fp.GetPosition().y)
    for p in fp.Pads():
        if p.GetNetname() != "GND" or p.GetAttribute() != pcbnew.PAD_ATTRIB_SMD:
            continue
        layer = F if p.IsOnLayer(F) else B
        px, py = MM(p.GetPosition().x), MM(p.GetPosition().y)
        key = f"{fp.GetReference()}.{p.GetNumber()}"
        force = key in starved
        if not force and nearest_gnd_via(px, py) <= PAD_NEAR:
            continue
        # candidate directions: away from the part centre first, then the perpendiculars, then the diagonals
        ax, ay = px - cx, py - cy
        L = math.hypot(ax, ay)
        ax, ay = (ax / L, ay / L) if L > 0.05 else (1.0, 0.0)
        base = math.atan2(ay, ax)
        dirs = [(math.cos(base + k * math.pi / 8), math.sin(base + k * math.pi / 8)) for k in (0, 1, -1, 2, -2, 3, -3, 4, -4, 5, -5, 6, -6, 7, -7, 8)]
        placed = False; last = ""
        half = max(MM(p.GetSizeX()), MM(p.GetSizeY())) / 2
        for dist in (half + 0.75, half + 0.95, half + 1.2, half + 1.5, half + 1.9, half + 2.4, half + 3.0):
            for dx, dy in dirs:
                n = math.hypot(dx, dy); dx, dy = dx / n, dy / n
                x, y = px + dx * dist, py + dy * dist
                r_ = via_ok(x, y, "GND", need_fill=False, allow_pads=(p,), edge=1.0)
                if r_ is True and not stub_ok(px, py, x, y, layer, allow_pads=(p,)):
                    r_ = "stub blocked"
                if r_ is True:
                    add_via(x, y, "GND", f"pad {key}")
                    add_seg(px, py, x, y, layer)
                    placed = True
                    break
                last = r_
                if key in DEBUG:
                    print(f"  dbg {key} cand ({x:.2f},{y:.2f}) d={dist:.2f}: {r_}")
            if placed:
                break
        if not placed:
            for dist in (half + 0.45, half + 0.6, half + 0.8, half + 1.0):
                for dx, dy in dirs:
                    x, y = px + dx * dist, py + dy * dist
                    end_in_fill = in_gnd_fill(layer, x, y)
                    if end_in_fill and stub_ok(px, py, x, y, layer, allow_pads=(p,)):
                        add_seg(px, py, x, y, layer); new_segs[-1]["why"] = f"bare stub {key}"
                        placed = True; last = "bare stub"
                        break
                if placed:
                    break
        if not placed:
            # L-shaped stub: pad -> leg1 (along the pad axis) -> leg2 (perpendicular) -> via, searched on a 0.4 mm grid within 4 mm
            best = None
            for gx_ in range(-10, 11):
                for gy_ in range(-10, 11):
                    vx, vy = px + gx_ * 0.4, py + gy_ * 0.4
                    dvia = math.hypot(vx - px, vy - py)
                    if dvia < half + 0.7 or dvia > 4.0 or (best and dvia >= best[0]):
                        continue
                    if via_ok(vx, vy, "GND", need_fill=False, allow_pads=(p,), edge=1.0) is not True:
                        continue
                    for corner in ((px, vy), (vx, py)):
                        if stub_ok(px, py, corner[0], corner[1], layer, allow_pads=(p,)) and stub_ok(corner[0], corner[1], vx, vy, layer, allow_pads=(p,)):
                            best = (dvia, vx, vy, corner)
                            break
            if best:
                dvia, vx, vy, corner = best
                add_via(vx, vy, "GND", f"pad {key} (L)")
                if (corner[0], corner[1]) != (px, py):
                    add_seg(px, py, corner[0], corner[1], layer)
                add_seg(corner[0], corner[1], vx, vy, layer)
                placed = True; last = "L-stub"
        pad_rows.append((key, placed, last))
unplaced = [f"{k} ({why})" for k, ok, why in pad_rows if not ok]

# ---------------- 4b. hand-designed connections the search cannot find ----------------
# U8.2 (SN74LVC1G11 GND) is fenced in by the DRV_EN tracks and the +3V3 feed: run 0.25 mm up the
# 0.9 mm gap between R30.1 and R31.1 to R30.2 (GND pull-down pad), which sits in the GND pour.
MANUAL = [  # (x1,y1,x2,y2,width,layer,net,why)
    (236.9, 152.95, 236.8, 152.55, 0.14, "F.Cu", "GND", "manual U8.2"),   # 0.75 mm corridor between R30.1/R31.1 -> 0.30 clearance each side
    (236.8, 152.55, 236.8, 150.45, 0.14, "F.Cu", "GND", "manual U8.2"),
    (236.8, 150.45, 235.95, 149.55, 0.25, "F.Cu", "GND", "manual U8.2"),  # to R31.2 (GND pull-down pad, in the pour)
]
for x1, y1, x2, y2, w, layer, net, why in MANUAL:
    new_segs.append(dict(x1=x1, y1=y1, x2=x2, y2=y2, w=w, layer=layer, net=net, why=why))
unplaced = [u for u in unplaced if not u.startswith("U8.2")]

# ---------------- 5. edge fence + open-area grid ----------------
fence_pts = []
x = BX0 + EDGE
while x <= BX1 - EDGE + 1e-6:
    fence_pts += [(x, BY0 + EDGE), (x, BY1 - EDGE)]
    x += FENCE
y = BY0 + EDGE
while y <= BY1 - EDGE + 1e-6:
    fence_pts += [(BX0 + EDGE, y), (BX1 - EDGE, y)]
    y += FENCE
for x, y in fence_pts:
    if nearest_gnd_via(x, y) > FENCE * 0.6 and via_ok(x, y) is True:
        add_via(x, y, "GND", "edge fence")
gx = BX0 + EDGE + GRID / 2
while gx < BX1 - EDGE:
    gy = BY0 + EDGE + GRID / 2
    while gy < BY1 - EDGE:
        if nearest_gnd_via(gx, gy) > GRID_MIN:
            for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
                if via_ok(gx + dx, gy + dy) is True:
                    add_via(gx + dx, gy + dy, "GND", "grid")
                    break
        gy += GRID
    gx += GRID

# ---------------- write ----------------
def via_block(v):
    return ('\t(via\n\t\t(at %g %g)\n\t\t(size %g)\n\t\t(drill %g)\n\t\t(layers "F.Cu" "B.Cu")\n\t\t(net "%s")\n\t\t(uuid "%s")\n\t)\n'
            % (v["x"], v["y"], v["size"], v["drill"], v["net"], uuid.uuid4()))
def seg_block(s):
    return ('\t(segment\n\t\t(start %g %g)\n\t\t(end %g %g)\n\t\t(width %g)\n\t\t(layer "%s")\n\t\t(net "%s")\n\t\t(uuid "%s")\n\t)\n'
            % (s["x1"], s["y1"], s["x2"], s["y2"], s["w"], s["layer"], s["net"], uuid.uuid4()))
out = txt
MOVE_13V5 = {(249.6,142.6):(259.2,142.6),(249.6,143.4):(259.2,143.4),(249.6,144.2):(259.2,144.2),(250.4,142.6):(260.0,142.6),(250.4,143.4):(260.0,143.4),(250.4,144.2):(260.0,144.2)}
moved = 0
for (x, y), (nx, ny) in MOVE_13V5.items():
    out, k = re.subn(r'\(via\n\t\t\(at %g %g\)(?=\n\t\t\(size 0\.6\)\n\t\t\(drill 0\.3\)\n\t\t\(layers "F\.Cu" "B\.Cu"\)\n\t\t\(free yes\)\n\t\t\(net "\+13V5_GATE"\))' % (x, y), '(via\n\t\t(at %g %g)' % (nx, ny), out)
    moved += k
for x, y in fix_net:
    pat = re.compile(r'(\(via\n\t\t\(at %g %g\)\n\t\t\(size [\d.]+\)\n\t\t\(drill [\d.]+\)\n\t\t\(layers "F.Cu" "B.Cu"\)\n\t\t\(net )""' % (x, y))
    out, n = pat.subn(r'\1"GND"', out)
    assert n == 1, (x, y, n)
body = "".join(via_block(v) for v in new_vias) + "".join(seg_block(s) for s in new_segs)
assert out.rstrip().endswith(")")
idx = out.rstrip().rfind(")")
out = out[:idx] + body + out[idx:]
open(DST, "w").write(out)

summary = dict(new_vias=len(new_vias), new_stubs=len(new_segs), bare_stubs=sum(1 for q in new_segs if q.get("why","").startswith("bare")), netless_fixed=len(fix_net), vias_13v5_moved=moved, unplaced_pads=unplaced, notes=notes,
               by_reason={k: sum(1 for v in new_vias if v["why"].split(" ")[0] == k) for k in ("U1", "U3", "pad", "edge", "grid")})
print(json.dumps(summary, indent=1))
json.dump(dict(vias=new_vias, segs=new_segs, fix_net=fix_net, summary=summary), open(DST + ".stitched.json", "w"), indent=1)
if PLAN:
    json.dump(dict(vias=new_vias, segs=new_segs, fix_net=fix_net, summary=summary), open(PLAN, "w"), indent=1)
