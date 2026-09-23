#!/usr/bin/env python3
"""S11 pre-fab pass (2026-09-23), run once.

  python3 prefab_s11.py SRC.kicad_pcb DST.kicad_pcb [--report report.json] [--no-silk]
  python3 prefab_s11.py SRC.kicad_pcb DST.kicad_pcb --tp-only --tp-labels=only|both [--report r.json]
      (second form: SRC is the already-processed board; adds a silk net-name label to every test
       point - 'only' replaces the TPxx reference on silk and falls back to it where the name does
       not fit, 'both' keeps the reference and adds the name beside it)

DST must be a *scratch* path whose directory is NOT the project directory; the script copies
the project's .kicad_pro / .kicad_dru next to DST (same stem) before loading, because
pcbnew.LoadBoard only picks up the design rules from a same-stem .kicad_pro and
pcbnew.SaveBoard ALWAYS rewrites the same-stem .kicad_pro next to the board it saves
(with KiCad defaults if none was loaded - the .kicad_pro rollback signature).  Only the
.kicad_pcb is meant to be copied back into the project.

Phase A (text, exact substitutions):
  * H1-H4: MountingHole_3.2mm_M3 -> MountingHole_4.3mm_M4_ISO7380 (user: M4; the button-head
    variant's 4.05 mm courtyard is the largest that clears Q1 at H2 - 4.26 mm), attr board_only
    (no schematic symbol -> stops the 4 extra_footprint parity warnings)
  * the spare +5V via at (208.335, 181.4) (via_dangling) is deleted
  * the two "MOTOR CONTROLLER V3" silk texts (F/B) become the board name
Phase B (pcbnew): every visible reference designator is re-placed on its silk layer so it
  overlaps no pad, no silk graphic, no other reference, no other courtyard and stays 0.5 mm
  from the edge; when nothing fits within 3 mm (4 mm for J/U/TP/JP/D) of the courtyard the
  reference is hidden (JLC places from the CPL; the fab-layer ${REFERENCE} text stays).
  Footprint silk texts that clash are nudged; unfixable solder-jumper pad-number labels are removed,
  connector pin marks are left where they are. 'Under a part' = the neighbour's fab-layer body.
pcbnew.SaveBoard's round-trip of the untouched source is byte-identical, so the diff of the
result against SRC is exactly this script's changes.
"""
import sys, re, json, math, collections, os, shutil, hashlib
IU = 1e6

SRC, DST = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
REPORT = sys.argv[sys.argv.index('--report') + 1] if '--report' in sys.argv else None
DO_SILK = '--no-silk' not in sys.argv
TP_ONLY = '--tp-only' in sys.argv   # board already processed: skip phase A and the reference pass, add labels only
sdir, ddir = os.path.dirname(SRC), os.path.dirname(DST)
assert sdir != ddir, 'DST must live in a scratch directory (SaveBoard rewrites the .kicad_pro next to it)'
stem_s = os.path.basename(SRC)[:-len('.kicad_pcb')]; stem_d = os.path.basename(DST)[:-len('.kicad_pcb')]
for ext in ('.kicad_pro', '.kicad_dru'):
    shutil.copy(os.path.join(sdir, stem_s + ext), os.path.join(ddir, stem_d + ext))
pro_md5 = hashlib.md5(open(os.path.join(ddir, stem_d + '.kicad_pro'), 'rb').read()).hexdigest()

t = open(SRC).read()
n0 = len(t)
holes = []
if TP_ONLY:
    open(DST, 'w').write(t)
else:

    def sub1(block, old, new):
        assert block.count(old) == 1, (old, block.count(old))
        return block.replace(old, new)

    # ---- H1-H4 --------------------------------------------------------------------------
    HEAD = '\t(footprint "FE_UFPR_4_0:MountingHole_3.2mm_M3"\n'
    holes = []
    pos = 0
    while True:
        s = t.find(HEAD, pos)
        if s < 0: break
        e = t.find('\n\t)\n', s) + 4
        blk = t[s:e]
        for old, new in [
            ('"FE_UFPR_4_0:MountingHole_3.2mm_M3"', '"FE_UFPR_4_0:MountingHole_4.3mm_M4_ISO7380"'),
            ('(descr "Mounting Hole 3.2mm, M3, no annular', '(descr "Mounting Hole 4.3mm, M4, no annular'),
            ('(tags "mountinghole M3")', '(tags "mountinghole M4 ISO7380")'),
            ('(at 0 -4.15 0)', '(at 0 -4.75 0)'),
            ('(at 0 4.15 0)', '(at 0 4.75 0)'),
            ('"M3 board mount"', '"M4 board mount (ISO 7380 button head)"'),
            ('(end 3.2 0)', '(end 3.8 0)'),
            ('(end 3.45 0)', '(end 4.05 0)'),
            ('(size 3.2 3.2)', '(size 4.3 4.3)'),
            ('(drill 3.2)', '(drill 4.3)'),
            ('(attr exclude_from_pos_files exclude_from_bom)', '(attr board_only exclude_from_pos_files exclude_from_bom)'),
        ]:
            blk = sub1(blk, old, new)
        holes.append(re.search(r'\(property "Reference" "(H\d)"', blk)[1])
        t = t[:s] + blk + t[e:]
        pos = s + len(blk)
    assert sorted(holes) == ['H1', 'H2', 'H3', 'H4'], holes

    # ---- spare +5V via ------------------------------------------------------------------
    VIA = '\t(via\n\t\t(at 208.335 181.4)\n'
    s = t.find(VIA); assert s >= 0 and t.find(VIA, s + 1) < 0
    e = t.find('\n\t)\n', s) + 4
    assert '264201b6-1b58-4561-9d1a-daa8b2ad2c16' in t[s:e] and '(net "+5V")' in t[s:e]
    t = t[:s] + t[e:]

    # ---- silk title texts ---------------------------------------------------------------
    F_TEXT = 'FE_UFPR 4.0 - FSAE - 2026-09'          # 28 chars: fits the free run of the right edge
    B_TEXT = 'FE_UFPR 4.0 - FORMULA UFPR'
    t = sub1(t, '\t(gr_text "MOTOR CONTROLLER V3\\n"\n\t\t(at 268.8 199.6 90)',
                f'\t(gr_text "{F_TEXT}"\n\t\t(at 268.8 199.6 90)')
    t = sub1(t, '\t(gr_text "MOTOR CONTROLLER V3\\n"\n\t\t(at 131.4 99.4 90)',
                f'\t(gr_text "{B_TEXT}"\n\t\t(at 131.4 99.4 90)')

    open(DST, 'w').write(t)
    print(f'phase A: {n0} -> {len(t)} chars, holes {holes}, via deleted, 2 texts')

# ---- Phase B: reference designators ---------------------------------------------------
import pcbnew
b = pcbnew.LoadBoard(DST)
assert abs(b.GetDesignSettings().m_TrackMinWidth / IU - 0.127) < 1e-6, 'project rules not loaded'
fps = list(b.GetFootprints())

def mm(v): return v / IU
def bb2t(bb): return (mm(bb.GetLeft()), mm(bb.GetTop()), mm(bb.GetRight()), mm(bb.GetBottom()))
def overl(a, c, m):  # bbox tuples, margin m (mm)
    return not (a[2] + m <= c[0] or c[2] + m <= a[0] or a[3] + m <= c[1] or c[3] + m <= a[1])

SIDES = {'F': (pcbnew.F_Cu, pcbnew.F_SilkS, pcbnew.F_CrtYd), 'B': (pcbnew.B_Cu, pcbnew.B_SilkS, pcbnew.B_CrtYd)}
CLR_PAD, CLR_SILK, CLR_REF, CLR_CRT, EDGE = 0.20, 0.15, 0.15, 0.10, 0.5   # CRT = other parts' fab bodies
GAPS = [0.2, 0.4, 0.7, 1.0, 1.5, 2.0, 2.5, 3.0]
GAPS_HI = GAPS + [3.5, 4.0]
HI = ('J', 'U', 'TP', 'JP', 'D')

class Grid:
    def __init__(self, cell=4.0): self.cell = cell; self.d = collections.defaultdict(list)
    def keys(self, bb, m=0.5):
        c = self.cell
        for ix in range(int((bb[0] - m) // c), int((bb[2] + m) // c) + 1):
            for iy in range(int((bb[1] - m) // c), int((bb[3] + m) // c) + 1):
                yield (ix, iy)
    def add(self, bb, item):
        for k in self.keys(bb): self.d[k].append((bb, item))
    def remove(self, item):
        for lst in self.d.values():
            lst[:] = [x for x in lst if x[1] is not item]
    def near(self, bb):
        seen = set()
        for k in self.keys(bb):
            for e in self.d.get(k, ()):
                if id(e) not in seen: seen.add(id(e)); yield e

obst = {'F': Grid(), 'B': Grid()}   # items: ('pad', shape, ref) ('silk', poly, ref) ('crt', poly, ref) ('ref', None, ref) ('text', None, id)
for fp in fps:
    for side, (cu, silk, crt) in SIDES.items():
        for pad in fp.Pads():
            if pad.IsOnLayer(cu):   # keep the pad, not its cached shape: fp.Add() invalidates the cache
                obst[side].add(bb2t(pad.GetEffectiveShape(cu).BBox()), ('pad', (pad, cu), fp.GetReference()))
        poly = pcbnew.SHAPE_POLY_SET()
        fp.TransformFPShapesToPolySet(poly, silk, 0, 5000, pcbnew.ERROR_INSIDE, False, True, False)
        if poly.OutlineCount():
            obst[side].add(bb2t(poly.BBox()), ('silk', poly, fp.GetReference()))
        body = pcbnew.SHAPE_POLY_SET()
        fp.TransformFPShapesToPolySet(body, pcbnew.F_Fab if side == 'F' else pcbnew.B_Fab, 0, 5000, pcbnew.ERROR_INSIDE, False, True, False)
        if not body.OutlineCount(): body = pcbnew.SHAPE_POLY_SET(fp.GetCourtyard(crt))   # a copy: the cached one is rebuilt on fp.Add()
        if body.OutlineCount():
            obst[side].add(bb2t(body.BBox()), ('crt', body, fp.GetReference()))
dr = b.Drawings()
for i in range(len(dr)):
    d = dr[i]
    if d.GetClass() == 'PCB_TEXT' and d.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS):
        side = 'F' if d.GetLayer() == pcbnew.F_SilkS else 'B'
        obst[side].add(bb2t(d.GetBoundingBox()), ('text', None, 'gr_text'))
# footprint silk texts (e.g. solder-jumper pad-number labels) are obstacles too, and get their own pass
fptexts = []
for fp in fps:
    gi = fp.GraphicalItems()
    for i in range(len(gi)):
        g = gi[i]
        if g.GetClass() == 'PCB_TEXT' and g.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS):
            g = pcbnew.Cast_to_PCB_TEXT(g)
            if g.IsVisible():
                side = 'F' if g.GetLayer() == pcbnew.F_SilkS else 'B'
                it = ('text', None, f'{fp.GetReference()}:{g.GetText()}')
                obst[side].add(bb2t(g.GetBoundingBox()), it); fptexts.append((fp, g, side, it))
refitems = {}
for fp in fps:
    r = fp.Reference()
    if r.IsVisible():
        side = 'F' if fp.GetLayer() == pcbnew.F_Cu else 'B'
        it = ('ref', None, fp.GetReference()); refitems[fp.GetReference()] = it
        obst[side].add(bb2t(r.GetBoundingBox()), it)
eb = bb2t(b.GetBoardEdgesBoundingBox())
board_in = (eb[0] + EDGE, eb[1] + EDGE, eb[2] - EDGE, eb[3] - EDGE)

def blocked(side, bb, rect, me, self_item=None):
    if bb[0] < board_in[0] or bb[1] < board_in[1] or bb[2] > board_in[2] or bb[3] > board_in[3]:
        return 'edge'
    for obb, item in obst[side].near(bb):
        if item is self_item: continue
        kind, shape, who = item
        if kind == 'ref':
            if who != me and overl(bb, obb, CLR_REF): return 'ref ' + who
        elif kind == 'text':
            if overl(bb, obb, CLR_REF): return 'text ' + who
        elif kind == 'pad':
            if overl(bb, obb, CLR_PAD) and shape[0].GetEffectiveShape(shape[1]).Collide(rect, int(CLR_PAD * IU)): return 'pad ' + who
        elif kind == 'silk':
            if overl(bb, obb, CLR_SILK) and shape.Collide(rect, int(CLR_SILK * IU)): return 'silk ' + who
        elif kind == 'crt':
            if who != me and overl(bb, obb, CLR_CRT) and shape.Collide(rect, int(CLR_CRT * IU)): return 'crt ' + who
    return None

PRIO = {'J': 0, 'U': 1, 'TP': 2, 'JP': 3, 'H': 4, 'D': 5, 'Q': 6, 'L': 7, 'FB': 8, 'SW': 9, 'F': 10, 'NT': 11, 'C': 12, 'R': 13}
def pfx(ref): m = re.match(r'[A-Z]+', ref); return m[0] if m else ''
def prio(fp):
    p = PRIO.get(pfx(fp.GetReference()), 20)
    cy = fp.GetCourtyard(pcbnew.F_CrtYd if fp.GetLayer() == pcbnew.F_Cu else pcbnew.B_CrtYd)
    return (p, -cy.Area() if cy.OutlineCount() else 0)

report = {'placed': {}, 'hidden': {}, 'kept_hidden': [], 'holes': holes, 'fp_texts': {}}
if DO_SILK and not TP_ONLY:
    for fp in sorted(fps, key=prio):
        ref = fp.GetReference(); r = fp.Reference()
        if not r.IsVisible():
            report['kept_hidden'].append(ref); continue
        side = 'F' if fp.GetLayer() == pcbnew.F_Cu else 'B'
        cu, silk, crt = SIDES[side]
        cy = fp.GetCourtyard(crt)
        C = bb2t(cy.BBox()) if cy.OutlineCount() else bb2t(fp.GetBoundingBox(False, False))
        cx, cyy = (C[0] + C[2]) / 2, (C[1] + C[3]) / 2
        obst[side].remove(refitems[ref])
        r.SetTextSize(pcbnew.VECTOR2I(int(1.0 * IU), int(1.0 * IU))); r.SetTextThickness(int(0.15 * IU))
        r.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER); r.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER)
        r.SetMirrored(side == 'B')
        found = None; tried = 0
        dims = {}
        for ang in (0, 90):
            r.SetTextAngle(pcbnew.EDA_ANGLE(ang, pcbnew.DEGREES_T)); r.SetPosition(pcbnew.VECTOR2I(int(cx * IU), int(cyy * IU)))
            tb = bb2t(r.GetBoundingBox()); dims[ang] = (tb[2] - tb[0], tb[3] - tb[1], (tb[0] + tb[2]) / 2 - cx, (tb[1] + tb[3]) / 2 - cyy)
        gaps = GAPS_HI if pfx(ref) in HI else GAPS
        for g in gaps:
            if found: break
            for ang in ((0, 90) if (C[2] - C[0]) >= (C[3] - C[1]) else (90, 0)):
                if found: break
                w, h, dx, dy = dims[ang]
                sides = ['top', 'bottom', 'left', 'right'] if ang == 0 else ['left', 'right', 'top', 'bottom']
                cands = []
                for sd in sides:
                    span = (C[2] - C[0]) if sd in ('top', 'bottom') else (C[3] - C[1])
                    ext = (w if sd in ('top', 'bottom') else h)   # allow the text to hang past the corner
                    slides = [0.0]
                    for k in range(1, int((span + ext) / 2 / 0.5) + 2): slides += [k * 0.5, -k * 0.5]
                    for s_ in slides:
                        if sd == 'top':    x, y = cx + s_, C[1] - g - h / 2
                        elif sd == 'bottom': x, y = cx + s_, C[3] + g + h / 2
                        elif sd == 'left': x, y = C[0] - g - w / 2, cyy + s_
                        else:              x, y = C[2] + g + w / 2, cyy + s_
                        cands.append((abs(s_), sides.index(sd), x, y, sd))
                for _, _, x, y, sd in sorted(cands):
                    r.SetTextAngle(pcbnew.EDA_ANGLE(ang, pcbnew.DEGREES_T))
                    r.SetPosition(pcbnew.VECTOR2I(int(round((x - dx) * IU)), int(round((y - dy) * IU))))
                    bbI = r.GetBoundingBox(); bb = bb2t(bbI); tried += 1
                    if blocked(side, bb, pcbnew.SHAPE_RECT(bbI), ref) is None:
                        found = (round(x, 3), round(y, 3), ang, sd, g); break
        if found:
            obst[side].add(bb2t(r.GetBoundingBox()), refitems[ref])
            report['placed'][ref] = found
        else:
            r.SetVisible(False)
            report['hidden'][ref] = tried
    # footprint silk texts (solder-jumper pad-number labels, connector pin-1 marks): nudge, else remove
    for fp, g, side, it in fptexts:
        bbI = g.GetBoundingBox(); why = blocked(side, bb2t(bbI), pcbnew.SHAPE_RECT(bbI), fp.GetReference(), it)
        if why is None: continue
        p0 = pcbnew.VECTOR2I(g.GetPosition().x, g.GetPosition().y); ok = None
        for d in (0.3, 0.6, 0.9, 1.2, 1.5):
            for ddx, ddy in ((0, -d), (0, d), (-d, 0), (d, 0), (-d, -d), (d, -d), (-d, d), (d, d)):
                g.SetPosition(pcbnew.VECTOR2I(p0.x + int(ddx * IU), p0.y + int(ddy * IU)))
                bbI = g.GetBoundingBox()
                if blocked(side, bb2t(bbI), pcbnew.SHAPE_RECT(bbI), fp.GetReference(), it) is None: ok = (ddx, ddy); break
            if ok: break
        if ok:
            obst[side].remove(it); obst[side].add(bb2t(g.GetBoundingBox()), it)
            report['fp_texts'][it[2]] = ('moved', ok, why)
        elif pfx(fp.GetReference()) == 'JP':
            obst[side].remove(it); fp.Remove(g)
            report['fp_texts'][it[2]] = ('removed', why)
        else:
            g.SetPosition(p0)
            report['fp_texts'][it[2]] = ('left', why)

# ---- optional: net-name silk labels on the test points (--tp-labels) --------------------
TP_LABELS = next((a.split('=', 1)[1] if '=' in a else 'both' for a in sys.argv if a.startswith('--tp-labels')), None)  # both | only
report['tp_labels'] = {}
base_placed = {r: 'as-is' for r in refitems} if TP_ONLY else dict(report['placed'])
if DO_SILK and TP_LABELS:
    for fp in sorted(fps, key=prio):
        ref = fp.GetReference()
        if pfx(ref) != 'TP': continue
        pads = list(fp.Pads()); net = pads[0].GetNetname() if pads else ''
        label = net.split('/')[-1]
        if not label: continue
        side = 'F' if fp.GetLayer() == pcbnew.F_Cu else 'B'
        cu, silk, crt = SIDES[side]
        if TP_LABELS == 'only' and fp.Reference().IsVisible():   # the net name replaces the TPxx on silk
            fp.Reference().SetVisible(False); obst[side].remove(refitems[ref]); report['placed'].pop(ref, None); report['hidden'].pop(ref, None)
        txt = pcbnew.PCB_TEXT(fp); txt.SetText(label); txt.SetLayer(silk)
        txt.SetTextSize(pcbnew.VECTOR2I(int(1.0 * IU), int(1.0 * IU))); txt.SetTextThickness(int(0.15 * IU))
        txt.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER); txt.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER)
        txt.SetMirrored(side == 'B')
        fp.Add(txt); txt.thisown = False   # the footprint owns it now (double free otherwise)
        cy = fp.GetCourtyard(crt)
        C = bb2t(cy.BBox()) if cy.OutlineCount() else bb2t(fp.GetBoundingBox(False, False))
        cx, cyy = (C[0] + C[2]) / 2, (C[1] + C[3]) / 2
        it = ('text', None, f'{ref}:{label}')
        found = None
        dims = {}
        for ang in (0, 90):
            txt.SetTextAngle(pcbnew.EDA_ANGLE(ang, pcbnew.DEGREES_T)); txt.SetPosition(pcbnew.VECTOR2I(int(cx * IU), int(cyy * IU)))
            tb = bb2t(txt.GetBoundingBox()); dims[ang] = (tb[2] - tb[0], tb[3] - tb[1], (tb[0] + tb[2]) / 2 - cx, (tb[1] + tb[3]) / 2 - cyy)
        for g in GAPS_HI:
            if found: break
            for ang in (0, 90):
                if found: break
                w, h, dx, dy = dims[ang]
                cands = []
                for sd in ('top', 'bottom', 'left', 'right'):
                    span = (C[2] - C[0]) if sd in ('top', 'bottom') else (C[3] - C[1])
                    ext = (w if sd in ('top', 'bottom') else h)
                    slides = [0.0]
                    for k in range(1, int((span + ext) / 2 / 0.5) + 2): slides += [k * 0.5, -k * 0.5]
                    for s_ in slides:
                        if sd == 'top':    x, y = cx + s_, C[1] - g - h / 2
                        elif sd == 'bottom': x, y = cx + s_, C[3] + g + h / 2
                        elif sd == 'left': x, y = C[0] - g - w / 2, cyy + s_
                        else:              x, y = C[2] + g + w / 2, cyy + s_
                        cands.append((abs(s_), x, y, sd))
                for _, x, y, sd in sorted(cands):
                    txt.SetTextAngle(pcbnew.EDA_ANGLE(ang, pcbnew.DEGREES_T))
                    txt.SetPosition(pcbnew.VECTOR2I(int(round((x - dx) * IU)), int(round((y - dy) * IU))))
                    bbI = txt.GetBoundingBox(); bb = bb2t(bbI)
                    if blocked(side, bb, pcbnew.SHAPE_RECT(bbI), None, it) is None:   # me=None: its own TPxx reference counts too
                        found = (round(x, 3), round(y, 3), ang, sd, g); break
        if found:
            obst[side].add(bb2t(txt.GetBoundingBox()), it); report['tp_labels'][ref] = (label,) + found
        else:
            fp.Remove(txt); txt.thisown = True; report['tp_labels'][ref] = (label, 'NO ROOM')
            if TP_LABELS == 'only' and ref in base_placed:   # fall back to the TPxx reference where it fitted
                r = fp.Reference(); r.SetVisible(True); obst[side].add(bb2t(r.GetBoundingBox()), refitems[ref]); report['placed'][ref] = base_placed[ref]
    n_ok = sum(1 for v in report['tp_labels'].values() if v[1] != 'NO ROOM')
    print('TP labels placed', n_ok, 'of', len(report['tp_labels']), 'no room:', [k for k, v in report['tp_labels'].items() if v[1] == 'NO ROOM'])

pcbnew.SaveBoard(DST, b)
assert hashlib.md5(open(os.path.join(ddir, stem_d + '.kicad_pro'), 'rb').read()).hexdigest() == pro_md5, '.kicad_pro changed by SaveBoard'
summ = collections.Counter()
for ref in report['placed']: summ[pfx(ref) + ' placed'] += 1
for ref in report['hidden']: summ[pfx(ref) + ' hidden'] += 1
report['summary'] = dict(sorted(summ.items()))
print('placed', len(report['placed']), 'hidden', len(report['hidden']), 'kept hidden', len(report['kept_hidden']), 'fp texts', report['fp_texts'])
print(report['summary'])
if REPORT: json.dump(report, open(REPORT, 'w'), indent=1)
