#!/usr/bin/env python3
"""S10 fix-up (2026-09-23): U1 buck copper, ISNS A/C swap completion, CAN netclass restore.

Text-level edits (no pcbnew import), run ONCE on a project directory:

  python3 tools/board_layout/fix_s10_u1.py <project_dir>

.kicad_pcb
  1. every zone: connect_pads clearance 0.5 -> 0.3 mm (KiCad default was never
     reconciled with the 0.20-0.30 mm netclass clearances; a pour needed 1.25 mm
     of free space to pass and could not reach 1.27 mm-pitch pins)
  2. zone /power/PWR_U1_SW: thermal -> solid (SW node)
  3. footprint-level (zone_connect 2) = solid on U1, L1, C2, C3 (Cin, EP, inductor)
  4. GND stub 0.6 mm F.Cu from U1 pin 1 (PGND) into the exposed pad
  5. FB: U1.5 -> R6.1 -> R5.2, 0.25 mm F.Cu
  6. +24V_PROT to R2.1 (B.Cu): via 1.0/0.5 between C2's pads + F.Cu/B.Cu stubs
  7. J22 pad 12 -> /ISNS_A_ADC, pad 16 -> /ISNS_C_ADC (completes the 2026-09-22 swap)
launchpad.kicad_sch
  8. hierarchical labels ISNS_A_ADC / ISNS_C_ADC exchange positions (same swap)
.kicad_pro
  9. net_settings restored from commit 586d0da (CAN class + 4 patterns lost in b8f2aa2)
"""
import json
import re
import subprocess
import sys
import uuid
from pathlib import Path

proj = Path(sys.argv[1]).resolve()
PCB = proj / "FE_UFPR_4_0.kicad_pcb"
SCH = proj / "launchpad.kicad_sch"
PRO = proj / "FE_UFPR_4_0.kicad_pro"
GOOD_PRO_COMMIT = "586d0da"


def uid():
    return str(uuid.uuid4())


def seg(x1, y1, x2, y2, w, layer, net):
    return (f"\n\t(segment\n\t\t(start {x1} {y1})\n\t\t(end {x2} {y2})\n\t\t(width {w})"
            f"\n\t\t(layer \"{layer}\")\n\t\t(net \"{net}\")\n\t\t(uuid \"{uid()}\")\n\t)")


def via(x, y, size, drill, net):
    return (f"\n\t(via\n\t\t(at {x} {y})\n\t\t(size {size})\n\t\t(drill {drill})"
            f"\n\t\t(layers \"F.Cu\" \"B.Cu\")\n\t\t(net \"{net}\")\n\t\t(uuid \"{uid()}\")\n\t)")


def footprint_block(s, ref):
    i = s.find(f'(property "Reference" "{ref}"')
    assert i > 0, ref
    st = s.rfind("\n\t(footprint", 0, i)
    en = s.find("\n\t(footprint", i)
    if en < 0:
        en = s.find("\n\t(gr_", i)
    return st, en


# ---------------------------------------------------------------- .kicad_pcb
s = PCB.read_text()
log = []

# 1. zone clearances
n = len(re.findall(r"\(connect_pads(?: \w+)?\n\t\t\t\(clearance 0\.5\)", s))
s = re.sub(r"(\(connect_pads(?: \w+)?\n\t\t\t\(clearance )0\.5\)", r"\g<1>0.3)", s)
log.append(f"zones clearance 0.5->0.3: {n}")

# 2. SW zone solid
i = s.find('(net "/power/PWR_U1_SW")\n\t\t(layer "F.Cu")')
assert i > 0
j = s.find("(connect_pads\n", i)
assert 0 < j - i < 400, "SW zone connect_pads not found"
s = s[:j] + "(connect_pads yes\n" + s[j + len("(connect_pads\n"):]
log.append("zone PWR_U1_SW -> solid")

# 3. footprint-level solid zone connection
for ref in ("U1", "L1", "C2", "C3", "C6"):
    st, en = footprint_block(s, ref)
    blk = s[st:en]
    assert "(zone_connect" not in blk, ref
    m = re.search(r"\n\t\t\(attr [^)]*\)", blk)
    assert m, f"{ref}: no (attr) line"
    blk = blk[:m.end()] + "\n\t\t(zone_connect 2)" + blk[m.end():]
    s = s[:st] + blk + s[en:]
    log.append(f"{ref}: zone_connect solid")

# 7. J22 pad nets
st, en = footprint_block(s, "J22")
blk = s[st:en]
before = blk
blk = blk.replace('(pad "12" thru_hole', '(pad "12@" thru_hole').replace('(pad "16" thru_hole', '(pad "16@" thru_hole')
def swap_pad_net(blk, pad, new):
    i = blk.find(f'(pad "{pad}@"')
    j = blk.find("(net \"", i)
    k = blk.find("\")", j)
    old = blk[j + 6:k]
    assert 0 < j - i < 400, pad
    return blk[:j + 6] + new + blk[k:], old
blk, oldA = swap_pad_net(blk, "12", "/ISNS_A_ADC")
blk, oldC = swap_pad_net(blk, "16", "/ISNS_C_ADC")
assert (oldA, oldC) == ("/ISNS_C_ADC", "/ISNS_A_ADC"), (oldA, oldC)
blk = blk.replace('(pad "12@"', '(pad "12"').replace('(pad "16@"', '(pad "16"')
s = s[:st] + blk + s[en:]
log.append("J22.12 -> /ISNS_A_ADC, J22.16 -> /ISNS_C_ADC")

# 4-6. new copper (U1 at 257.445,132.5 rot 180: pin1 260.145,134.405; pin5 254.745,130.595)
new = ""
new += seg(260.145, 134.405, 258.6, 134.405, 0.6, "F.Cu", "GND")                      # pin1 -> EP
new += seg(254.745, 130.595, 254.745, 128.65, 0.25, "F.Cu", "/power/PWR_U1_FB")       # pin5 -> R6.1
new += seg(254.745, 128.65, 253.05, 128.65, 0.25, "F.Cu", "/power/PWR_U1_FB")         # R6.1 -> R5.2
new += seg(262.95, 133.2, 262.95, 134.2, 0.6, "F.Cu", "+24V_PROT")                    # C2.1 -> via
new += via(262.95, 134.2, 1.0, 0.5, "+24V_PROT")
new += seg(262.95, 134.2, 262.95, 132.95, 0.4, "B.Cu", "+24V_PROT")                   # via -> R2.1
i = s.rfind("\n\t(segment")
i = s.find("\n\t)", i) + 3
s = s[:i] + new + s[i:]
log.append("copper: GND stub, FB x2, +24V_PROT via + 2 stubs")
PCB.write_text(s)

# ---------------------------------------------------------------- launchpad.kicad_sch
t = SCH.read_text()
a = '(hierarchical_label "ISNS_A_ADC"\n\t\t(shape'
c = '(hierarchical_label "ISNS_C_ADC"\n\t\t(shape'
assert t.count(a) == 1 and t.count(c) == 1
t = t.replace(a, "@@A@@").replace(c, a).replace("@@A@@", c)
SCH.write_text(t)
log.append("launchpad.kicad_sch: ISNS_A_ADC <-> ISNS_C_ADC label texts exchanged")

# ---------------------------------------------------------------- .kicad_pro
good = json.loads(subprocess.check_output(
    ["git", "-C", str(Path(__file__).resolve().parents[2]), "show", f"{GOOD_PRO_COMMIT}:FE_UFPR_4_0.kicad_pro"]))
cur = json.loads(PRO.read_text())
cur["net_settings"] = good["net_settings"]
# b8f2aa2 also reset board.design_settings.rules to KiCad defaults (same defect as 2026-09-17):
# min clearance/track 0/0.20 instead of 0.127/0.127, hole-to-hole 0.25 vs 0.50, annular 0.10 vs
# 0.125, edge 0.5 vs 0.3, silk 0/0.8 vs 0.15/1.0, solder_mask_min_width gone.  Nothing else in
# the file differs from 586d0da (checked key by key), so both blocks are restored verbatim.
cur["board"]["design_settings"]["rules"] = good["board"]["design_settings"]["rules"]
PRO.write_text(json.dumps(cur, indent=2) + "\n")
log.append(f"net_settings + design_settings.rules restored from {GOOD_PRO_COMMIT}: "
           f"{len(cur['net_settings']['classes'])} classes / {len(cur['net_settings']['netclass_patterns'])} patterns, "
           f"min clearance/track {cur['board']['design_settings']['rules']['min_clearance']}/"
           f"{cur['board']['design_settings']['rules']['min_track_width']}")

print("\n".join(log))
