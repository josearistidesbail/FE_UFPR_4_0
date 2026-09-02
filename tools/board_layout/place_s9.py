#!/usr/bin/env python3
"""S9 placement generator for FE_UFPR_4_0.

Produces a JSON map {ref: {x, y, rotation[, layer]}} in ABSOLUTE KiCad board
coordinates from a floorplan expressed in board-local millimetres (origin = top-left
corner of the outline, x right, y down).  The map is applied with the MCP
`batch_move_components` tool; this script never touches the .kicad_pcb itself.

Floorplan (S9_BOARD_SETUP.md):
  - left edge   = analog edge: J4 (encoder, top) and J3 (LEM, bottom), mating faces at x=1
  - top edge    = service edge: J5 (vehicle DTM 8-way, vertical flange), J1 (24 V entry)
  - bottom edge = module edge: J2 DB37, gate/fault pins at its right end
  - right column = power region top-down (entry, 13.5 V, 5 V, 3V3) then the gate drivers
  - bottom-left = isolated +/-15 V island (U4) beside the LEM connector
  - BoosterPack sockets J20..J23 on B.Cu on the 43.18 x 63.5 grid, J1-pin-1 at (XG, YG)

Block membership is derived from the golden netlist (net families), not guessed from
reference numbers.  Packing inside a block is a shelf packer over courtyard boxes: a
starting placement for S10/S11, not a finished one.
"""
import json, re, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.abspath(os.path.join(HERE, '..', '..'))
OUT = sys.argv[1] if len(sys.argv) > 1 else HERE

# ----------------------------------------------------------------------------- inputs
def load_net_components():
    s = open(os.path.join(PROJ, 'tools/schematic_layout/golden.net')).read()
    comps = {}
    for b in re.split(r'\n\t\t\(comp\n', s.split('(nets')[0])[1:]:
        ref = re.search(r'\(ref "([^"]+)"', b).group(1)
        fp = re.search(r'\(footprint "([^"]*)"', b)
        val = re.search(r'\(value "([^"]*)"', b)
        sh = re.search(r'\(sheetpath\s*\(names "([^"]+)"', b)
        comps[ref] = dict(fp=(fp.group(1) if fp else '').split(':')[-1],
                          val=val.group(1) if val else '', sheet=sh.group(1) if sh else '?')
    nets = {}
    for n in re.split(r'\n\t\t\(net\n', s.split('(nets')[1])[1:]:
        name = re.search(r'\(name "([^"]+)"', n).group(1)
        if name.startswith('unconnected'):
            continue
        nets[name] = re.findall(r'\(ref "([^"]+)"\)\s*\(pin "([^"]+)"\)', n)
    return comps, nets

def courtyards():
    """footprint name -> (xmin, xmax, ymin, ymax) of its F.CrtYd graphics at rotation 0."""
    out = {}
    lib = os.path.join(PROJ, 'FE_UFPR_4_0.pretty')
    for f in os.listdir(lib):
        if not f.endswith('.kicad_mod'):
            continue
        s = open(os.path.join(lib, f)).read()
        xs, ys = [], []
        for m in re.finditer(r'\(fp_(line|rect|circle|poly)\b', s):
            end = s.find('\n\t)', m.start())
            blk = s[m.start():end]
            if '"F.CrtYd"' not in blk and '"B.CrtYd"' not in blk:
                continue
            if m.group(1) == 'circle':
                c = re.search(r'\(center\s+([-\d.]+)\s+([-\d.]+)\)', blk)
                e = re.search(r'\(end\s+([-\d.]+)\s+([-\d.]+)\)', blk)
                r = ((float(e.group(1)) - float(c.group(1))) ** 2 + (float(e.group(2)) - float(c.group(2))) ** 2) ** .5
                xs += [float(c.group(1)) - r, float(c.group(1)) + r]
                ys += [float(c.group(2)) - r, float(c.group(2)) + r]
            else:
                for x, y in re.findall(r'\((?:start|end|xy)\s+([-\d.]+)\s+([-\d.]+)\)', blk):
                    xs.append(float(x)); ys.append(float(y))
        out[f[:-10]] = (min(xs), max(xs), min(ys), max(ys)) if xs else (-0.5, 0.5, -0.5, 0.5)
    return out

COMPS, NETS = load_net_components()
CY = courtyards()
NETS_OF = {}
for n, nodes in NETS.items():
    for r, p in nodes:
        NETS_OF.setdefault(r, set()).add(n)

def box(ref, rot=0):
    """courtyard (w, h, cx, cy) at rotation rot; (cx, cy) = centre offset from the origin."""
    x0, x1, y0, y1 = CY[COMPS[ref]['fp']]
    if rot % 180 == 90:                       # KiCad CCW: (x, y) -> (y, -x)
        x0, x1, y0, y1 = y0, y1, -x1, -x0
    elif rot % 360 == 180:
        x0, x1, y0, y1 = -x1, -x0, -y1, -y0
    return (x1 - x0, y1 - y0, (x0 + x1) / 2, (y0 + y1) / 2)

def on(pattern, exclude=('J2', 'J3', 'J4', 'J5', 'J20', 'J21', 'J22', 'J23')):
    """refs having at least one net whose name matches pattern, in refdes order."""
    rx = re.compile(pattern)
    refs = {r for n, nodes in NETS.items() if rx.search(n) for r, p in nodes}
    return sorted((r for r in refs if r not in exclude),
                  key=lambda r: (r.rstrip('0123456789'), int(re.sub(r'\D', '', r) or 0)))

def sheet(name):
    return sorted((r for r, c in COMPS.items() if c['sheet'] == f'/{name}/'),
                  key=lambda r: (r.rstrip('0123456789'), int(re.sub(r'\D', '', r) or 0)))

# ----------------------------------------------------------------------------- floorplan
W, H = 146.0, 130.0          # board outline (board-local)
X0, Y0 = 50.0, 50.0          # KiCad coordinates of the outline's top-left corner
XG, YG = 66.0, 14.0          # LaunchPad J1 pin 1 = socket J20 pad 1
DX, DY = 43.18, 63.5         # BoosterPack grid (1.700 x 2.500 in), verified S1/S8/S9

placed = {}                  # ref -> (x, y, rot, layer)
def fix(ref, x, y, rot=0, layer='F.Cu'):
    placed[ref] = (x, y, rot, layer)

# sockets on the bottom, unrotated: J1 outer-left, pin 1 at the USB (service) end,
# handedness read from SPRUI77 Fig. 12 and matching 3.0's as-built grid.
fix('J20', XG, YG, 0, 'B.Cu')
fix('J21', XG + DX, YG, 0, 'B.Cu')
fix('J22', XG, YG + DY, 0, 'B.Cu')
fix('J23', XG + DX, YG + DY, 0, 'B.Cu')
fix('J4', 30.6, 29.7, -90)            # encoder, mating face at x = 1.0
fix('J3', 30.6, 78.8, -90)            # LEM
fix('J5', 72.0, 6.35, 180)            # vehicle 8-way; its Dwgs.User edge line lies on y = 0
fix('J1', 129.0, 5.0, 0)              # 24 V entry, Mini-Fit
fix('J2', 116.0, H - 9.40, 0)         # DB37; pin-row-1-to-edge 9.40 mm puts the edge on y = H
fix('U4', 28.0, 114.0, 180)           # isolated DC/DC; rot 180 puts the 24 V input pins on its right

# mounting holes (placed by the MCP as footprints H1..H9, listed here for the record)
HOLES = {
    'H1': (5, 5), 'H2': (W - 5, 5), 'H3': (5, H - 5), 'H4': (W - 5, H - 5),
    'H5': (5, 54), 'H6': (W - 5, 62.5),
    # LaunchPad standoffs, measured from SPRUI77 Fig. 12/14 relative to J1 pin 1 (+/-0.3 mm)
    'H7': (XG + 22.77, YG - 2.75), 'H8': (XG + 25.26, YG + 64.60), 'H9': (XG - 3.87, YG + 95.30),
}

# ----------------------------------------------------------------------------- block packer
class Block:
    def __init__(self, name, x0, y0, x1, y1, gap=0.6, rot=0, sort=False):
        self.name, self.x0, self.y0, self.x1, self.y1, self.gap, self.rot = name, x0, y0, x1, y1, gap, rot
        self.parts, self.rots, self.sort = [], {}, sort
    def add(self, *refs, rot=None):
        for r in refs:
            if isinstance(r, (list, tuple)):
                self.add(*r, rot=rot)
            elif r in COMPS and r not in placed and r not in self.parts and r not in CLAIMED:
                self.parts.append(r); CLAIMED.add(r)
                if rot is not None:
                    self.rots[r] = rot
        return self
    def pack(self):
        x, y, rowh, over = self.x0, self.y0, 0.0, []
        order = self.parts
        if self.sort:   # tallest first: dense blocks pack far better, at the cost of functional adjacency
            order = sorted(self.parts, key=lambda r: -box(r, self.rots.get(r, self.rot))[1])
        for ref in order:
            rot = self.rots.get(ref, self.rot)
            w, h, cx, cy = box(ref, rot)
            if x + w > self.x1 + 1e-6 and x > self.x0:
                x, y, rowh = self.x0, y + rowh + self.gap, 0.0
            if y + h > self.y1 + 1e-6:
                over.append(ref)
            placed[ref] = (x + w / 2 - cx, y + h / 2 - cy, rot, 'F.Cu')
            x += w + self.gap
            rowh = max(rowh, h)
        if over:
            print(f'!! {self.name}: {len(over)} parts overflow the region: {over}')
        return y + rowh

CLAIMED = set()
blocks = []
def B(*a, **k):
    b = Block(*a, **k); blocks.append(b); return b

# ---- power column (x 115..145), top-down ------------------------------------------
entry = B('entry', 115, 15, 145, 41)
entry.add('TP9', 'F1', 'Q1', 'D2', 'R1', 'D1', 'C1', 'C2', 'C3', 'C4', 'NT2', 'D4', 'R13', 'TP1')
buck1 = B('buck1', 115, 42, 145, 58)
buck1.add('U1', 'C6', 'C8', 'L1', on(r'PWR_U1_'), 'C9', 'C10', 'C11', 'D5', 'R14')
buck2 = B('buck2', 115, 59, 137, 72)                       # H6 sits at (141, 62.5)
buck2.add('U2', 'C12', 'L2', on(r'PWR_U2_'), 'C14', 'C15', 'C16', 'C17', 'D6', 'R15')
ldo = B('ldo', 115, 73, 145, 84)
ldo.add('U3', 'C18', 'C19', 'C20', 'C21', 'C22', 'D7', 'R16')
gate_drv = B('gate_drv', 115, 85, 145, 102)                # right of J23 (PWM on its odd pads)
gate_drv.add('U5', 'C29', 'C30', 'U6', 'C31', 'C32', 'U7', 'C33', 'C34', 'C36')
# ---- isolated island (beside U4, bottom-left) -------------------------------------
iso = B('iso', 43, 103, 58, 118.5)
iso.add('C23', 'C24', 'C25', 'C26', 'C27', 'C28', 'NT1', 'D8', 'R17', 'TP6', 'TP7', 'TP8')
# ---- bottom band along the DB37 ----------------------------------------------------
ms_ov = B('ms_ov', 66, 102.6, 77, 111.5)                       # FLT_OV: pin 16 (x 74.5) -> J22-15
ms_ov.add(on(r'FLT_OV_'))
ms_div = B('ms_div', 78, 102.6, 89.5, 111.5)                     # Vbus / NTC dividers at pins 7, 29, 11
ms_div.add('R57', 'R58', 'C58', 'NT3', 'TP19', 'TP21', 'R60', 'R61', 'C60', 'TP22')
ms_flt = B('ms_flt', 90, 102.6, 126, 110.5, sort=True)                  # OC_A/B/C + OT receivers at pins 2/22/5/6
ms_flt.add(on(r'FLT_OC_A_'), on(r'FLT_OC_B_'), on(r'FLT_OC_C_'), on(r'FLT_OT_'))
db_misc = B('db_misc', 66, 111.5, 99, 119)                 # EMC caps, RTN tie, aux-15 V TPs, module-aux fuse
db_misc.add('C64', 'C70', 'C77', 'NT4', 'TP17', 'TP18', 'F2', 'C5', 'TP5')
db_in = B('db_in', 100, 110.8, 126.5, 118.8, gap=0.4, sort=True)         # series 100 R + datasheet 10k/1nF at the gate pins
db_in.add(on(r'PWM_[UVW][HL]_15V'))
db_shield = B('db_shield', 127, 112, 137, 119)
db_shield.add(on(r'SHIELD_DB37'))
# ---- module-status charge buckets at J20 even pads 8 (NTC) and 14 (Vbus) -----------
ms_bucket = B('ms_bucket', 71, 19, 78, 31)
ms_bucket.add('R62', 'C61', 'TP23', 'R59', 'C59', 'TP20')
# ---- gate logic at J23 ----------------------------------------------------------------
gate_pd = B('gate_pd', 103, 76, 106.8, 98, rot=90)         # PWM pull-downs beside J23 odd pads
gate_pd.add(on(r'PWM_[UVW][HL]_3V3'))
gate_logic = B('gate_logic', 87, 84, 102, 101)
gate_logic.add('U8', 'C35', 'JP1', on(r'DRV_EN|GATE_ILOCK|GATE_EN_3V3|LED_GATE'))
# ---- current sense: left strip below the encoder, LEM side first, buckets last ---------
cs = B('cs', 41, 47, 64, 102)
cs.add('C92', 'C93', 'C94', 'C95', 'TP37', 'R103', 'R104', 'C96')
for ch, u in (('A', 'U12'), ('B', 'U13'), ('C', 'U14')):
    lem = on(rf'LEM_{ch}_M'); lemst = on(rf'ISNS_{ch}_LEM'); intst = on(rf'ISNS_{ch}_INT'); raw = on(rf'ISNS_{ch}_RAW')
    cs.add([r for r in lem if r[0] in 'RC'], [r for r in lemst if r[0] in 'RC'], u,
           [r for r in raw + intst if r[0] in 'RC' and r not in ('C64', 'C70', 'C77')])
for ch in 'ABC':
    cs.add(on(rf'ISNS_{ch}_SEL'), on(rf'ISNS_{ch}_ADC'), on(rf'ISNS_{ch}_INT$'), on(rf'ISNS_{ch}_LEM$'))
cs_ref = B('cs_ref', 71, 85, 86, 101)                      # VREF buffer; ref buckets at J22 pads 10/18
cs_ref.add('R101', 'C85', 'R102', 'C86', 'U15', on(r'ISNS_VREF_DIV'), 'TP36', 'C87', 'C88', 'C89', 'C90', 'C91')
# ---- encoder: left strip top, input side first, ADC clamps/buckets last -------------------
enc = B('enc', 41, 12.2, 64, 46)
enc.add('FB1', 'C97', 'C98', 'C99', 'C100', 'TP38', 'TP39', 'R108', 'R113',
        'U16', 'C103', 'C104', on(r'ENC_(SIN|COS)_[PN]$'), on(r'ENC_(SIN|COS)_OUT'),
        'D10', 'C107', 'TP40', 'D11', 'C110', 'TP41',
        'U17', 'C111', 'C112', on(r'ENC_VREF'), 'TP44', on(r'SHIELD_ENC'))
# ---- LaunchPad 5 V feed, between J20-2 and J22-2 ------------------------------------------
lp = B('lp', 71, 46, 84, 56)
lp.add('D12', 'C114', 'C115', 'TP45', 'TP46', 'TP47', 'TP48')
# ---- vehicle I/O under J5, CAN end first (J5 pins 1/8 are at x = 78.3) --------------------
vio = B('vio', 78.6, 15, 106, 44, sort=True)
vio.add('D13', 'R122', 'JP6', 'TP49', 'TP50', 'L3', 'U18', 'R120', 'R121', 'C116', 'C117',
        'U19', 'D14', 'R123', 'R124', 'R125', 'U20', 'D15', 'R126', 'R127', 'R128',
        'U21', 'C118', 'TP51', 'TP52', 'D16', 'F3', 'D17', 'C119')

# ----------------------------------------------------------------------------- fallback
RAIL_BLOCK = {'+24V_PROT': entry, '+13V5_GATE': buck1, '+5V': buck2, '+3V3': ldo,
              '+15V_ISO': iso, '-15V_ISO': iso, 'ISO_COM': iso}
block_of = {r: b for b in blocks for r in b.parts}
for ref in [r for r in COMPS if r not in placed and r not in CLAIMED]:
    score = {}
    for n in NETS_OF.get(ref, ()):
        if len(NETS[n]) > 12:
            continue
        for r, p in NETS[n]:
            if r in block_of:
                score[block_of[r]] = score.get(block_of[r], 0) + 1
    if score:
        b = max(score, key=score.get)
    else:
        rails = [n for n in NETS_OF.get(ref, ()) if n in RAIL_BLOCK]
        b = RAIL_BLOCK[rails[0]] if rails else None
    if b is None:
        continue
    b.add(ref); block_of[ref] = b
    print(f'   fallback: {ref} ({COMPS[ref]["val"][:16]}) -> {b.name}')

# ----------------------------------------------------------------------------- run
for b in blocks:
    b.pack()

missing = [r for r in COMPS if r not in placed]
if missing:
    print('!! unplaced (dropped into a scrap row at the top-left):', missing)
    scrap = Block('scrap', 12, 1, 60, 8); scrap.add(*missing); scrap.pack()

moves = {}
for ref, (x, y, rot, layer) in placed.items():
    m = {'x': round(X0 + x, 3), 'y': round(Y0 + y, 3), 'rotation': rot, 'unit': 'mm'}
    if layer != 'F.Cu':
        m['layer'] = layer
    moves[ref] = m
json.dump(moves, open(os.path.join(OUT, 'moves.json'), 'w'), indent=1)
json.dump({h: {'x': round(X0 + x, 3), 'y': round(Y0 + y, 3)} for h, (x, y) in HOLES.items()},
          open(os.path.join(OUT, 'holes.json'), 'w'), indent=1)
print(f'{len(moves)} placements -> {OUT}/moves.json ; {len(HOLES)} holes -> holes.json')
for b in blocks:
    used = sum(box(r, b.rots.get(r, b.rot))[0] * box(r, b.rots.get(r, b.rot))[1] for r in b.parts)
    area = (b.x1 - b.x0) * (b.y1 - b.y0)
    print(f'  {b.name:11s} {len(b.parts):3d} parts  courtyard {used:5.0f} / region {area:5.0f} mm2  ({100 * used / area:3.0f} %)')
