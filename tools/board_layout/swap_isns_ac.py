"""Swap ISNS_A_ADC <-> ISNS_C_ADC at J22 (LaunchPad J7) pins 16/12, with their RC buckets.

Applied once on 2026-09-22 (A now on J22.12 = ADCINA5, C on J22.16 = ADCINB4).
NOT idempotent: a second run swaps them back. Usage: python3 swap_isns_ac.py <project dir>
"""
import re, sys
root = sys.argv[1]

# 1. schematic: swap the two hierarchical-label texts on the launchpad sheet
p = f'{root}/launchpad.kicad_sch'; t = open(p).read()
t = t.replace('(hierarchical_label "ISNS_A_ADC"', '(hierarchical_label "@@C"', 1)
t = t.replace('(hierarchical_label "ISNS_C_ADC"', '(hierarchical_label "ISNS_A_ADC"', 1)
t = t.replace('(hierarchical_label "@@C"', '(hierarchical_label "ISNS_C_ADC"', 1)
open(p, 'w').write(t)

# 2. board
p = f'{root}/FE_UFPR_4_0.kicad_pcb'; t = open(p).read()
A, C = '"/ISNS_A_ADC"', '"/ISNS_C_ADC"'

def fp_span(ref):
    m = re.search(r'\(property "Reference" "%s"' % ref, t)
    s = t.rfind('\n\t(footprint ', 0, m.start())
    e = t.find('\n\t(footprint ', m.start())
    e = len(t) if e < 0 else e
    return s, e

def fp_at(ref):
    s, e = fp_span(ref)
    m = re.search(r'\n\t\t\(at ([^)]*)\)', t[s:e])
    return s + m.start(1), s + m.end(1), m.group(1)

edits = []  # (start, end, new)
# swap footprint origins
for a, b in (('R74', 'R98'), ('C68', 'C82')):
    sa, ea, va = fp_at(a); sb, eb, vb = fp_at(b)
    edits += [(sa, ea, vb), (sb, eb, va)]
# J22 pads 12 / 16
s, e = fp_span('J22')
for pad, new in (('12', A), ('16', C)):
    m = re.search(r'\(pad "%s" .*?\(net ("[^"]*")\)' % pad, t[s:e], re.S)
    edits.append((s + m.start(1), s + m.end(1), new))
# pad nets inside the swapped RC parts follow the part (A part keeps A net) -> unchanged
# tracks: every segment/via/arc on A becomes C and vice versa
for m in re.finditer(r'\n\t\((segment|arc|via)\b.*?\n\t\)', t, re.S):
    blk = m.group(0)
    n = re.search(r'\(net ("[^"]*")\)', blk)
    if n and n.group(1) in (A, C):
        edits.append((m.start() + n.start(1), m.start() + n.end(1), C if n.group(1) == A else A))
for s0, e0, new in sorted(edits, reverse=True):
    t = t[:s0] + new + t[e0:]
open(p, 'w').write(t)
print(len(edits), 'board edits')
