#!/usr/bin/env python3
"""S12: turn kicad-cli's BOM + position exports into JLCPCB's BOM and CPL files.

  kicad-cli sch export bom --fields 'Reference,Value,Footprint,LCSC,${QUANTITY}' --labels 'Reference,Value,Footprint,LCSC,Qty' \
      --group-by 'Value,Footprint,LCSC' -o SCRATCH/bom.csv FE_UFPR_4_0.kicad_sch
  kicad-cli pcb export pos --format csv --units mm --side both --use-drill-file-origin -o SCRATCH/pos.csv FE_UFPR_4_0.kicad_pcb
  python3 tools/fab/jlc_bomcpl.py SCRATCH/bom.csv SCRATCH/pos.csv OUTDIR [--rotations tools/fab/jlc_rotations.json]

Writes OUTDIR/FE_UFPR_4_0_BOM.csv (Comment, Designator, Footprint, LCSC Part #) and OUTDIR/FE_UFPR_4_0_CPL.csv
(Designator, Mid X, Mid Y, Layer, Rotation).  Lines whose LCSC is NOFIT / CONSIGNED / empty are dropped from
both files and listed on stdout (consigned parts go on the assembly notes instead).  `--rotations` is a
{footprint-name: degrees-to-add} table filled by the S12 CPL rotation audit (JLC's part orientation differs
from KiCad's for many packages - SOT-23, SOIC, diodes, connectors bite); an empty table means "not audited".
Coordinates come straight from kicad-cli (drill/aux origin), bottom-side rotation is left as KiCad reports it.
"""
import csv, json, os, sys

BOM, POS, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
ROT = json.load(open(sys.argv[sys.argv.index('--rotations') + 1])) if '--rotations' in sys.argv else {}
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
        fp = r['Package']; rot = float(r['Rot'])
        if fp in ROT: rot = (rot + ROT[fp]) % 360
        elif ROT: missing_rot.add(fp)
        w.writerow([ref, f"{float(r['PosX']):.4f}mm", f"{float(r['PosY']):.4f}mm", 'Top' if r['Side'] == 'top' else 'Bottom', f'{rot:.1f}'])
        n_cpl += 1

print(f'BOM lines {len(groups)}, CPL parts {n_cpl}, dropped {len(skipped)}: ' + ', '.join(f'{ref}({code})' for ref, code, _ in skipped if code == 'CONSIGNED'))
print('dropped NOFIT/EMPTY:', sum(1 for _, c, _ in skipped if c != 'CONSIGNED'))
if not ROT: print('NOTE: no --rotations table - rotations are raw KiCad values, CPL audit pending')
if missing_rot: print('footprints not in the rotation table (0 offset applied):', sorted(missing_rot))
