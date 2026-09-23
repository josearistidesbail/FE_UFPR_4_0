#!/usr/bin/env python3
"""S11 (2026-09-23): hand-fix of the DB37 test-point row after `prefab_s11.py --tp-only --tp-labels=only`.

The six PWM test points (TP14 WH, TP15 WL, TP12 VH, TP13 VL, TP10 UH, TP11 UL) sit on a
2.6-3.25 mm pitch, so only two full net names fitted and they landed 3.5 mm away from the row,
ambiguous.  This script replaces them with one 2-letter label per pad (WH WL VH VL UH UL) plus a
"PWM 15V" legend over the row, and adds short names to the three neighbours that had no room
for a full one (TP19 VBUS_SNS_RAW -> VBUS, TP21 VBUS_RTN -> RTN, TP22 NTC_1_RAW -> NTC).
Every label is a footprint-owned F.SilkS text (moves with its TP); the legend is a board text.

Usage:  python3 tp_db37_labels.py BOARD.kicad_pcb [--report r.json]
BOARD must be a scratch copy with its same-stem .kicad_pro beside it (pcbnew.SaveBoard rewrites
that file - see TOOLING_NOTES.md); the script asserts its md5 is unchanged.  Never point it at
the project directory.  Placement is checked against pads (0.20), silk (0.15) and courtyards
(0.10) with bboxes; the real gate is `kicad-cli pcb drc --severity-all` afterwards.
"""
import hashlib, json, os, sys
import pcbnew

IU = 1e6
BOARD = os.path.abspath(sys.argv[1])
REPORT = sys.argv[sys.argv.index('--report') + 1] if '--report' in sys.argv else None
assert '/Kicad/FE_UFPR_4_0/' not in BOARD + '/', 'refusing to save into the project dir'
pro = os.path.splitext(BOARD)[0] + '.kicad_pro'
assert os.path.exists(pro), 'same-stem .kicad_pro must sit beside the board'
pro_md5 = hashlib.md5(open(pro, 'rb').read()).hexdigest()

b = pcbnew.LoadBoard(BOARD)
fps = {fp.GetReference(): fp for fp in b.GetFootprints()}
REGION = (200.0, 185.0, 265.0, 215.0)   # x0 y0 x1 y1 (mm) - everything here becomes an obstacle

def bx(r): return (r.GetLeft() / IU, r.GetTop() / IU, r.GetRight() / IU, r.GetBottom() / IU)
def bb(x): return bx(x.GetBoundingBox())
def overl(a, c, m): return not (a[2] + m <= c[0] or c[2] + m <= a[0] or a[3] + m <= c[1] or c[3] + m <= a[1])
def inreg(r): return overl(r, REGION, 0)

CLR = {'pad': 0.20, 'silk': 0.15, 'crt': 0.10, 'edge': 0.50}
obst = []   # (kind, bbox, owner, tag)
def rebuild():
    obst.clear()
    for ref, fp in fps.items():
        for p in fp.Pads():
            if p.IsOnLayer(pcbnew.F_Cu) and inreg(bb(p)): obst.append(('pad', bb(p), ref, 'pad'))
        cy = fp.GetCourtyard(pcbnew.F_CrtYd)
        if cy.OutlineCount() and inreg(bx(cy.BBox())): obst.append(('crt', bx(cy.BBox()), ref, 'crt'))
        for f in (fp.Reference(), fp.Value()):
            if f.IsVisible() and f.GetLayer() == pcbnew.F_SilkS and inreg(bb(f)): obst.append(('silk', bb(f), ref, 'field:' + f.GetText()))
        gi = fp.GraphicalItems()
        for i in range(len(gi)):
            g = gi[i]
            if g.GetLayer() == pcbnew.F_SilkS and inreg(bb(g)):
                tag = pcbnew.Cast_to_PCB_TEXT(g).GetText() if g.GetClass() == 'PCB_TEXT' else 'shape'
                obst.append(('silk', bb(g), ref, tag))
    dr = b.Drawings()
    for i in range(len(dr)):
        d = dr[i]
        if d.GetLayer() == pcbnew.F_SilkS and inreg(bb(d)): obst.append(('silk', bb(d), None, 'gr'))
        if d.GetLayer() == pcbnew.Edge_Cuts and inreg(bb(d)): obst.append(('edge', bb(d), None, 'edge'))

def blockers(rect, ignore_owner=None, ignore_tags=(), clr=None):
    out = []
    for kind, r, owner, tag in obst:
        if owner == ignore_owner and (kind in ('crt', 'pad') or tag in ignore_tags): continue
        if overl(rect, r, (clr or CLR)[kind]): out.append((kind, owner, tag))
    return out

def mktext(fp, s, x, y, ang=0, t=None):
    t = t or (pcbnew.PCB_TEXT(fp) if fp else pcbnew.PCB_TEXT(b))
    t.SetText(s); t.SetLayer(pcbnew.F_SilkS)
    t.SetTextSize(pcbnew.VECTOR2I(int(1.0 * IU), int(1.0 * IU))); t.SetTextThickness(int(0.15 * IU))
    t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER); t.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER)
    t.SetTextAngle(pcbnew.EDA_ANGLE(ang, pcbnew.DEGREES_T)); t.SetPosition(pcbnew.VECTOR2I(int(round(x * IU)), int(round(y * IU))))
    return t

report = {'retexted': [], 'hidden': [], 'labels': {}, 'moved_refs': {}, 'conflicts': {}}

# 1. the two ambiguous full names become the WH / WL labels (the objects are re-used: a second
#    fp.Remove() on a footprint text leaves pcbnew's SWIG proxies unresolvable - TOOLING_NOTES.md).
#    TP12 / TP10 lose their TPxx fallback, TP19 its TP19 (VBUS replaces it), and C44's reference
#    is boxed in by TP11 / C45 / C38 / R42 on every side - it joins the hidden passives.
reuse = {}
for ref, txt in (('TP14', 'PWM_WH_15V'), ('TP15', 'PWM_WL_15V')):
    fp = fps[ref]; gi = fp.GraphicalItems()
    victims = [pcbnew.Cast_to_PCB_TEXT(gi[i]) for i in range(len(gi)) if gi[i].GetClass() == 'PCB_TEXT' and pcbnew.Cast_to_PCB_TEXT(gi[i]).GetText() == txt]
    if not victims: raise SystemExit(f'{ref}: {txt} not found - run prefab_s11.py --tp-only --tp-labels=only first')
    reuse[ref] = victims[0]; report['retexted'].append(f'{ref}:{txt}')
for ref in ('TP12', 'TP10', 'TP19', 'C44'):
    fp = fps[ref]
    if fp.Reference().IsVisible(): fp.Reference().SetVisible(False); report['hidden'].append(ref)
rebuild()

def place(fp, s, cands, ignore_tags=(), existing=None, clr=None):
    """cands: list of (x, y, ang).  First free one wins; returns the text or None.
    existing: a footprint text already on the board to re-use (its old box leaves the obstacle list)."""
    ref = fp.GetReference() if fp else None
    if existing is not None:
        old = existing.GetText(); obst[:] = [o for o in obst if not (o[2] == ref and o[3] == old)]
    for x, y, ang in cands:
        t = mktext(fp, s, x, y, ang, existing)
        r = bb(t)
        bl = blockers(r, ref, ignore_tags, clr)
        if not bl:
            if existing is None:
                if fp: fp.Add(t); t.thisown = False
                else: b.Add(t); t.thisown = False
            obst.append(('silk', r, ref, 'label:' + s))
            report['labels'][f'{ref or "board"}:{s}'] = (round(x, 3), round(y, 3), ang, bb(t))
            return t
        report['conflicts'].setdefault(f'{ref or "board"}:{s}', []).append(((round(x, 3), round(y, 3), ang), bl[:4]))
    if existing is not None: raise SystemExit(f'{ref}: no room for the re-used text {s} - {report["conflicts"]}')
    return None

def nudge_ref(ref, dx, dy):
    """move a reference by (dx, dy) mm if the new box is free; returns True on success"""
    f = fps[ref].Reference(); p0 = pcbnew.VECTOR2I(f.GetPosition())
    f.SetPosition(pcbnew.VECTOR2I(p0.x + int(round(dx * IU)), p0.y + int(round(dy * IU))))
    obst[:] = [o for o in obst if not (o[2] == ref and o[3] == 'field:' + ref)]
    if blockers(bb(f), ref): f.SetPosition(p0); obst.append(('silk', bb(f), ref, 'field:' + ref)); return False
    obst.append(('silk', bb(f), ref, 'field:' + ref)); report['moved_refs'][ref] = (dx, dy, bb(f)); return True

# 2. two-letter labels over the six PWM pads (KiCad's box for 1.0 mm text is 1.7 mm tall: centred
#    2.1 mm above the pad it clears the 1.01 mm silk ring by 0.24 mm), then the legend above them
ROW = [('TP14', 'WH'), ('TP15', 'WL'), ('TP12', 'VH'), ('TP13', 'VL'), ('TP10', 'UH'), ('TP11', 'UL')]
for ref, s in ROW:
    fp = fps[ref]; px, py = fp.GetPosition().x / IU, fp.GetPosition().y / IU
    place(fp, s, [(px, py - 2.1, 0), (px - 0.3, py - 2.1, 0), (px, py - 2.2, 0)], existing=reuse.get(ref))
legend = place(None, 'PWM 15V', [(238.7, 199.9, 0), (238.7, 199.7, 0), (238.2, 199.9, 0)])

# 3. short names for the three neighbours that had no room for the full net name.  VBUS takes the
#    TP19 reference's slot (a hair longer, so R57's reference moves up 0.3 mm); RTN sits under TP21
#    (J2's reference moves down 0.2 mm; the box only brushes the empty corner of TP19's round
#    courtyard, so courtyard clearance is waived for it); NTC sits above-left of TP22, clear of NT3.
nudge_ref('R57', 0, -0.3)
place(fps['TP19'], 'VBUS', [(224.09, 202.19, 90), (224.09, 202.1, 90), (224.09, 202.25, 90)], ignore_tags=('field:TP19',))
nudge_ref('J2', 0, 0.2)
place(fps['TP21'], 'RTN', [(219.6, 206.4, 0), (219.6, 206.45, 0), (219.7, 206.4, 0)], clr=dict(CLR, crt=0.0))
place(fps['TP22'], 'NTC', [(215.8, 198.75, 0), (215.8, 198.7, 0), (215.7, 198.75, 0)])

pcbnew.SaveBoard(BOARD, b)
assert hashlib.md5(open(pro, 'rb').read()).hexdigest() == pro_md5, '.kicad_pro changed by SaveBoard'
missing = [s for _, s in ROW if not any(k.endswith(':' + s) for k in report['labels'])]
print('labels', len(report['labels']), 'retexted', report['retexted'], 'hidden', report['hidden'], 'moved refs', report['moved_refs'])
print('legend', 'ok' if legend else 'NO ROOM', '| missing:', missing, '| conflicts:', {k: v[-1][1] for k, v in report['conflicts'].items() if k not in report['labels']})
if REPORT: json.dump(report, open(REPORT, 'w'), indent=1)
