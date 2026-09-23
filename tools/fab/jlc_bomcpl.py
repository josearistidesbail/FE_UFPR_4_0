#!/usr/bin/env python3
"""S12: turn kicad-cli's BOM + position exports into JLCPCB's BOM and CPL files.

  kicad-cli sch export bom --fields 'Reference,Value,Footprint,LCSC,${QUANTITY}' --labels 'Reference,Value,Footprint,LCSC,Qty' \
      --group-by 'Value,Footprint,LCSC' -o SCRATCH/bom.csv FE_UFPR_4_0.kicad_sch
  kicad-cli pcb export pos --format csv --units mm --side both --use-drill-file-origin -o SCRATCH/pos.csv FE_UFPR_4_0.kicad_pcb
  python3 tools/fab/jlc_bomcpl.py SCRATCH/bom.csv SCRATCH/pos.csv OUTDIR [--rotations tools/fab/jlc_rotations.json] [--origin X,Y] [--hand-solder R2,R3,...]

Writes OUTDIR/FE_UFPR_4_0_BOM.csv (Comment, Designator, Footprint, LCSC Part #) and OUTDIR/FE_UFPR_4_0_CPL.csv
(Designator, Mid X, Mid Y, Layer, Rotation).  Lines whose LCSC is NOFIT / CONSIGNED / empty are dropped from
both files and listed on stdout (consigned parts go on the assembly notes instead).  `--rotations` is a
{footprint-name: degrees-to-add} table filled by the S12 CPL rotation audit (JLC's part orientation differs
from KiCad's for many packages - SOT-23, SOIC, diodes, connectors bite); an empty table means "not audited".
Coordinates come straight from kicad-cli (drill/aux origin); `--origin X,Y` (KiCad page coordinates of the board's
bottom-left corner, e.g. 127.95,219.9) rebases them so that corner is (0,0) with Y up, which is what JLC's preview
expects when the board has no aux origin.  Rotations are normalised to 0..360.  Rotation-table keys are footprint-name
PREFIXES (longest match wins); keys starting with `_` are comments.  Bottom-side rotation is left as KiCad reports it
(plus the table offset) - check D17 (the only polarised bottom part) in the preview.  `--hand-solder` drops the
listed references from both files (Economic single-side PCBA: the 12 B.Cu parts) and prints them for the assembly sheet.
"""
import csv, json, os, sys

BOM, POS, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
ROT = json.load(open(sys.argv[sys.argv.index('--rotations') + 1])) if '--rotations' in sys.argv else {}
ROT = {k: v for k, v in ROT.items() if not k.startswith('_')}
ORG = tuple(float(v) for v in sys.argv[sys.argv.index('--origin') + 1].split(',')) if '--origin' in sys.argv else None
HAND = set(sys.argv[sys.argv.index('--hand-solder') + 1].split(',')) if '--hand-solder' in sys.argv else set()
def rot_offset(fp):
    hits = [k for k in ROT if fp.startswith(k)]
    return ROT[max(hits, key=len)] if hits else None
os.makedirs(OUT, exist_ok=True)
SKIP = ('NOFIT', 'CONSIGNED', '')

import re
def expand(field):
    """kicad-cli writes ranges: 'C16-C18,R2' -> C16 C17 C18 R2"""
    out = []
    for tok in field.split(','):
        tok = tok.strip(); m = re.fullmatch(r'([A-Z]+)(\d+)-([A-Z]+)(\d+)', tok)
        if m and m[1] == m[3]: out += [f'{m[1]}{i}' for i in range(int(m[2]), int(m[4]) + 1)]
        elif tok: out.append(tok)
    return out
def refkey(s): m = re.fullmatch(r'([A-Z]+)(\d+)', s); return (m[1], int(m[2])) if m else (s, 0)

lcsc_of, value_of, fp_of = {}, {}, {}
skipped = []
for r in csv.DictReader(open(BOM)):
    refs = expand(r['Reference'])
    code = r['LCSC'].strip(); fp = r['Footprint'].split(':')[-1]
    for ref in refs:
        if code in SKIP: skipped.append((ref, code or 'EMPTY', r['Value'])); continue
        if ref in HAND: skipped.append((ref, 'HAND_SOLDER', f"{r['Value']} {fp} {code}")); continue
        lcsc_of[ref] = code; value_of[ref] = r['Value']; fp_of[ref] = fp

with open(os.path.join(OUT, 'FE_UFPR_4_0_BOM.csv'), 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['Comment', 'Designator', 'Footprint', 'LCSC Part #'])
    groups = {}
    for ref, code in lcsc_of.items(): groups.setdefault((value_of[ref], fp_of[ref], code), []).append(ref)
    for (val, fp, code), refs in sorted(groups.items(), key=lambda kv: kv[1][0]):
        w.writerow([val, ','.join(sorted(refs, key=refkey)), fp, code])

n_cpl = 0; missing_rot = set()
with open(os.path.join(OUT, 'FE_UFPR_4_0_CPL.csv'), 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['Designator', 'Mid X', 'Mid Y', 'Layer', 'Rotation'])
    for r in csv.DictReader(open(POS)):
        ref = r['Ref']
        if ref not in lcsc_of: continue
        fp = r['Package']; rot = float(r['Rot']); off = rot_offset(fp)
        if off is not None: rot += off
        elif ROT and not re.match(r'[RCL]_\d{4}_\d{4}Metric$', fp): missing_rot.add(fp)
        rot %= 360
        x, y = float(r['PosX']), float(r['PosY'])
        if ORG: x, y = x - ORG[0], y + ORG[1]      # kicad-cli pos Y is already negated (up = +)
        w.writerow([ref, f"{x:.4f}mm", f"{y:.4f}mm", 'Top' if r['Side'] == 'top' else 'Bottom', f'{rot:.1f}'])
        n_cpl += 1

print(f'BOM lines {len(groups)}, CPL parts {n_cpl}, dropped {len(skipped)}: ' + ', '.join(f'{ref}({code})' for ref, code, _ in skipped if code == 'CONSIGNED'))
print('dropped NOFIT/EMPTY:', sum(1 for _, c, _ in skipped if c not in ('CONSIGNED', 'HAND_SOLDER')))
hand = [(ref, v) for ref, c, v in skipped if c == 'HAND_SOLDER']
if hand: print(f'hand-solder ({len(hand)}, off the BOM/CPL): ' + '; '.join(f'{ref} {v}' for ref, v in hand))
if HAND - {ref for ref, _ in hand}: print('WARNING --hand-solder refs not in the BOM:', sorted(HAND - {ref for ref, _ in hand}))
if not ROT: print('NOTE: no --rotations table - rotations are raw KiCad values, CPL audit pending')
if missing_rot: print('footprints not in the rotation table (0 offset applied):', sorted(missing_rot))
