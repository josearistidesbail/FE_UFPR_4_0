"""Interactive hand-assembly tracker for FE_UFPR 4.0: one self-contained HTML page (map + checklist,
progress kept in the browser's localStorage, Export/Import as JSON).
Run from the project dir:  python3 tools/fab/hand_assembly_tracker.py
  -> fab/FE_UFPR_4_0_hand_assembly_tracker.html
Reads a temporary copy of the board (never saves anything). Stage lists / notes: STAGES below."""
import sys, os, csv, json, html, shutil, tempfile
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
brd_path = sys.argv[1] if len(sys.argv) > 1 else 'FE_UFPR_4_0.kicad_pcb'
bom_path = sys.argv[2] if len(sys.argv) > 2 else 'fab/FE_UFPR_4_0_HANDSOLDER_BOM.csv'
out = sys.argv[3] if len(sys.argv) > 3 else 'fab/FE_UFPR_4_0_hand_assembly_tracker.html'
tmpd = tempfile.mkdtemp()
shutil.copy(brd_path, os.path.join(tmpd, 'board.kicad_pcb'))
b = pcbnew.LoadBoard(os.path.join(tmpd, 'board.kicad_pcb'))
shutil.rmtree(tmpd)
MM = 1e6

STAGES = [
    dict(n=0, name='Before you start', col='#7f7f7f', refs='',
         note='JLC never confirmed the CPL rotations: look before adding anything.',
         tasks=[('T0a', 'Inspect JLC-placed polarised parts: LEDs D4-D9, diodes, IC pin 1'),
                ('T0b', 'Meter GND vs +24V_PROT, +5V, +3V3, +13V5_GATE, +/-15V_ISO: no shorts')]),
    dict(n=1, name='Bottom-side SMD', col='#E69F00',
         refs='R2 R3 D17 C119 C25 C26 C27 C28 R118 R119 C113 C120',
         note='Do these before J3/J4/J5 go in (the connectors sit over them). D17: the band on the part goes on the black pad (cathode).', tasks=[]),
    dict(n=2, name='Power path + first power-on', col='#D55E00',
         refs='F1 F2 F3 Q1 C1 U4 J1',
         note='Q1 tab: big chisel tip, no preheat needed. C1: the black stripe on the can goes on the black pad (−, GND); cut corners of the base = + side.',
         tasks=[('T2a', 'Recommended: wire strap F1 pad 2 to Q1 tab, over the 0.25 mm track'),
                ('T2b', 'Bring-up A (S12 §5): current-limited 24 V, check TP1 > TP5 > TP2 13.5 V > TP3 5 V > TP4 3.3 V > TP6/TP7 vs TP8, record idle current')]),
    dict(n=3, name='Logic + analog ICs (rails good)', col='#0072B2',
         refs='U8 U5 U6 U7 L3 R57 R105 R58 R129 U12 U13 U14 U15 U16 U17',
         note='Pin 1 = dot; check it before soldering the second side. R57/R105 = 3.00k, R58/R129 = 2.20k, 0.1 %, UNMARKED: one tape at a time, measure each.',
         tasks=[]),
    dict(n=4, name='Solder jumpers', col='#009E73', refs='JP1 JP2 JP3 JP4 JP5 JP6',
         note='JP1, JP3, JP4, JP5: bridge 1-2 (never leave open). JP2: leave open. JP6: check it is bridged.', tasks=[]),
    dict(n=5, name='Connectors', col='#CC79A7', refs='J20 J21 J22 J23 J3 J4 J5 J2',
         note='Solder J20-J23 while plugged onto the LaunchPad. J3-J5 DT15: #4-20 screws from the underside. GND pins: extra dwell.',
         tasks=[]),
]
JP_NOTE = {'JP1': 'bridge 1-2', 'JP3': 'bridge 1-2', 'JP4': 'bridge 1-2', 'JP5': 'bridge 1-2',
           'JP2': 'leave OPEN', 'JP6': 'check bridged'}
STRIPE = {'C1': '2', 'D17': '1'}  # pad that gets the part's stripe: C1 minus, D17 cathode
NO_DOT = set('C1 D17 L3 R57 R105 R58 R129 R2 R3 R118 R119 C25 C26 C27 C28 C119 C113 C120 F1 F2 F3'.split())
LEFT = {'R105', 'R57', 'R3', 'F1'}
NUDGE = {'R57': (0, -1.3), 'R58': (0, 1.3)}

stage_of = {r: s for s in STAGES for r in s['refs'].split()}
bom = {}
for row in csv.DictReader(open(bom_path)):
    for r in row['Designators'].split(','):
        bom[r.strip()] = row
fps = {fp.GetReference(): fp for fp in b.GetFootprints()}
assert all(r in fps for r in stage_of)

def pts_of(ps):
    res = []
    for i in range(ps.OutlineCount()):
        o = ps.Outline(i)
        res.append([(o.CPoint(k).x / MM, o.CPoint(k).y / MM) for k in range(o.PointCount())])
    return res

outl = pcbnew.SHAPE_POLY_SET(); b.GetBoardPolygonOutlines(outl, False)
outlines = []
for i in range(outl.OutlineCount()):
    o = outl.Outline(i); outlines.append([(o.CPoint(k).x / MM, o.CPoint(k).y / MM) for k in range(o.PointCount())])

def courtyard(fp, back):
    p = pts_of(fp.GetCourtyard(pcbnew.B_CrtYd if back else pcbnew.F_CrtYd))
    if p: return p
    bb = fp.GetBoundingBox(False)
    x0, y0, x1, y1 = bb.GetX() / MM, bb.GetY() / MM, bb.GetRight() / MM, bb.GetBottom() / MM
    return [[(x0, y0), (x1, y0), (x1, y1), (x0, y1)]]

def svg_side(back):
    X = (lambda x: -x) if back else (lambda x: x)
    cu = pcbnew.B_Cu if back else pcbnew.F_Cu
    def P(pts): return ' '.join(f'{X(x):.2f},{y:.2f}' for x, y in pts)
    out = []
    for o in outlines:
        out.append(f'<polygon class="edge" points="{P(o)}"/>')
    ctx = []
    for ref, fp in fps.items():
        on_side = fp.IsFlipped() == back
        if on_side and ref not in stage_of:
            for p in courtyard(fp, back):
                ctx.append(f'<polygon class="cy" points="{P(p)}"/>')
        if ref in stage_of and on_side:
            continue
        for pad in fp.Pads():
            if not pad.IsOnLayer(cu) and pad.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH:
                continue
            lay = cu if pad.IsOnLayer(cu) else pcbnew.F_Cu
            for p in pts_of(pad.GetEffectivePolygon(lay, pcbnew.ERROR_INSIDE)):
                ctx.append(f'<polygon class="pad0" points="{P(p)}"/>')
    out.append('<g class="ctx">' + ''.join(ctx) + '</g>')
    parts = []
    for ref, st in stage_of.items():
        fp = fps[ref]
        if fp.IsFlipped() != back:
            continue
        cys = courtyard(fp, back)
        g = [f'<g class="part" data-ref="{ref}" data-stage="{st["n"]}" style="--c:{st["col"]}">']
        for p in cys:
            g.append(f'<polygon class="body" points="{P(p)}"/>')
        for pad in fp.Pads():
            if pad.IsOnLayer(cu):
                stripe = STRIPE.get(ref) == pad.GetNumber()
                for p in pts_of(pad.GetEffectivePolygon(cu, pcbnew.ERROR_INSIDE)):
                    g.append(f'<polygon class="pad{" stripe" if stripe else ""}" points="{P(p)}"/>')
                if stripe and ref == 'C1':
                    c = pad.GetPosition()
                    g.append(f'<text class="minus" x="{X(c.x / MM):.2f}" y="{c.y / MM:.2f}">−</text>')
        p1 = [pd for pd in fp.Pads() if pd.GetNumber() == '1']
        if p1 and not ref.startswith('JP') and ref not in NO_DOT:
            c = p1[0].GetPosition()
            g.append(f'<circle class="p1" cx="{X(c.x / MM):.2f}" cy="{c.y / MM:.2f}" r="0.55"/>')
        if JP_NOTE.get(ref) == 'bridge 1-2':
            pads = {pd.GetNumber(): pd.GetPosition() for pd in fp.Pads()}
            a, c = pads['1'], pads['2']
            g.append(f'<line class="bridge" x1="{X(a.x / MM):.2f}" y1="{a.y / MM:.2f}" x2="{X(c.x / MM):.2f}" y2="{c.y / MM:.2f}"/>')
        xs = [X(x) for p in cys for x, _ in p]; ys = [y for p in cys for _, y in p]
        val = fp.GetValue()
        txt = f'{ref} {JP_NOTE[ref]}' if ref in JP_NOTE else (f'{ref} {val}' if ref in bom and len(val) <= 14 else ref)
        dx, dy = NUDGE.get(ref, (0, 0))
        left = ref in LEFT
        tx = (min(xs) - 0.6 if left else max(xs) + 0.6) + dx
        ty = (min(ys) + max(ys)) / 2 + dy
        g.append(f'<text x="{tx:.2f}" y="{ty:.2f}" text-anchor="{"end" if left else "start"}">{html.escape(txt)}</text>')
        g.append(f'<text class="tick" x="{(min(xs)+max(xs))/2:.2f}" y="{(min(ys)+max(ys))/2:.2f}">✓</text>')
        g.append('</g>')
        parts.append(''.join(g))
    out.append(''.join(parts))
    xs = [X(x) for o in outlines for x, _ in o]; ys = [y for o in outlines for _, y in o]
    vb = (min(xs) - 2, min(ys) - 2, max(xs) - min(xs) + 16, max(ys) - min(ys) + 4)
    return vb, ''.join(out)

sides = {}
for name, back in (('top', False), ('bottom', True)):
    vb, body = svg_side(back)
    sides[name] = f'<svg id="svg-{name}" viewBox="{vb[0]:.2f} {vb[1]:.2f} {vb[2]:.2f} {vb[3]:.2f}" data-vb="{vb[0]:.2f} {vb[1]:.2f} {vb[2]:.2f} {vb[3]:.2f}">{body}</svg>'

items = []
for st in STAGES:
    rows = []
    for r in st['refs'].split():
        fp = fps[r]
        rows.append(dict(id=r, kind='part', ref=r, val=fp.GetValue(), lcsc=bom.get(r, {}).get('LCSC', ''),
                         side='bottom' if fp.IsFlipped() else 'top', note=JP_NOTE.get(r, '')))
    tasks = [dict(id=t, kind='task', text=x) for t, x in st['tasks']]
    items.append(dict(n=st['n'], name=st['name'], col=st['col'], note=st['note'],
                      rows=(tasks + rows) if st['n'] == 0 else (rows + tasks)))

TEMPLATE = open(os.path.join(HERE, 'hand_assembly_template.html')).read()
page = (TEMPLATE.replace('/*DATA*/', json.dumps(items))
        .replace('<!--SVG_TOP-->', sides['top']).replace('<!--SVG_BOTTOM-->', sides['bottom']))
open(out, 'w').write(page)
print('wrote', out, len(page) // 1024, 'KiB')
