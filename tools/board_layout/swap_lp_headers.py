#!/usr/bin/env python3
"""S9.6: replace the four B.Cu PinSocket_2x10 footprints (J20..J23) in the board with
PinHeader_2x10_P2.54mm_Vertical on F.Cu at the same (x, y), rotation 0, copying every
property, the schematic path and the pad->net map.  The LaunchPad now sits ABOVE the board
on its own bottom-side receptacles (verified on the 3.0 board by the user), so the board
carries male pins on the top.  Verify afterwards with kicad-cli (DRC + IPC-D-356), never
with this script's own bookkeeping."""
import re, sys, uuid, os
PROJ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
PCB = os.path.join(PROJ, 'FE_UFPR_4_0.kicad_pcb')
LIB = os.path.join(PROJ, 'FE_UFPR_4_0.pretty', 'PinHeader_2x10_P2.54mm_Vertical.kicad_mod')
OLD = 'FE_UFPR_4_0:PinSocket_2x10_P2.54mm_Vertical'
NEW = 'FE_UFPR_4_0:PinHeader_2x10_P2.54mm_Vertical'

s = open(PCB).read()
lib = open(LIB).read().rstrip()
assert lib.startswith('(footprint "PinHeader_2x10_P2.54mm_Vertical"') and lib.endswith(')')
lib_body = lib[len('(footprint "PinHeader_2x10_P2.54mm_Vertical"'):-1]
# drop version/generator and the library's own Reference/Value/KiLib properties
lib_body = re.sub(r'\n\t\((version|generator)[^\n]*', '', lib_body)
lib_body = re.sub(r'\n\t\(property "(Reference|Value|KiLib_Generator)"[^\n]*\n(?:\t\t[^\n]*\n)*?\t\)', '', lib_body)
lib_body = lib_body.replace('\n\t(layer "F.Cu")', '')
i_fp = lib_body.index('\n\t(fp_line')   # graphics + pads start here
lib_graphics = lib_body[i_fp:]

def block_iter(text):
    """yield (start, end) of every top-level footprint block using the OLD lib id."""
    for m in re.finditer(r'\n\t\(footprint "' + re.escape(OLD) + '"', text):
        st = m.start() + 1
        j = text.index('\n\t)\n', st) + 4
        yield st, j

out, pos, done = [], 0, []
for st, en in block_iter(s):
    blk = s[st:en]
    ref = re.search(r'\(property "Reference" "([^"]+)"', blk).group(1)
    fuuid = re.search(r'\n\t\t\(uuid "([^"]+)"\)', blk).group(1)
    x, y = re.search(r'\n\t\t\(at ([-\d.]+) ([-\d.]+)', blk).groups()
    props = re.findall(r'\n\t\t\(property "([^"]+)" "([^"]*)"', blk)
    pm = re.search(r'\n\t\t\(path "[^"]+"\)', blk)      # MCP-placed footprints carry no path
    path = pm.group(0) if pm else ''
    sheet = ''.join(re.findall(r'\n\t\t\(sheet(?:name|file) "[^"]*"\)', blk))
    nets = dict(re.findall(r'\(pad "(\d+)"[^\n]*\n(?:\t\t\t[^\n]*\n)*?\t\t\t\(net "([^"]+)"\)', blk))
    # properties: Reference / Value visible on F layers, everything else hidden on F.Fab
    P = []
    for name, val in props:
        if name == 'Reference':
            P.append(f'\n\t\t(property "Reference" "{val}"\n\t\t\t(at 1.27 -2.38 0)\n\t\t\t(layer "F.SilkS")\n\t\t\t(uuid "{uuid.uuid4()}")\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1 1)\n\t\t\t\t\t(thickness 0.15)\n\t\t\t\t)\n\t\t\t)\n\t\t)')
        elif name == 'Value':
            P.append(f'\n\t\t(property "Value" "{val}"\n\t\t\t(at 1.27 25.24 0)\n\t\t\t(layer "F.Fab")\n\t\t\t(uuid "{uuid.uuid4()}")\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1 1)\n\t\t\t\t\t(thickness 0.15)\n\t\t\t\t)\n\t\t\t)\n\t\t)')
        else:
            if name == 'Footprint':
                val = NEW
            P.append(f'\n\t\t(property "{name}" "{val}"\n\t\t\t(at 0 0 0)\n\t\t\t(layer "F.Fab")\n\t\t\t(hide yes)\n\t\t\t(uuid "{uuid.uuid4()}")\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t)\n\t\t)')
    g = lib_graphics
    # nets + uuids on pads
    def padfix(m):
        n = m.group(1)
        body = m.group(0)
        net = nets.get(n)
        ins = f'\n\t\t(net "{net}")' if net else ''
        return body.replace('\n\t\t(remove_unused_layers no)', f'\n\t\t(remove_unused_layers no){ins}\n\t\t(uuid "{uuid.uuid4()}")', 1)
    g = re.sub(r'\(pad "(\d+)"[^\n]*\n(?:\t\t[^\n]*\n)*?\t\)', padfix, g)
    # uuids on graphics
    g = re.sub(r'(\n\t\(fp_(?:line|rect|circle|poly|text)\b(?:[^\n]*\n)*?)(\t\t\(layer "[^"]+"\)\n)(?!\t\t\(uuid)', lambda m: m.group(1) + m.group(2) + f'\t\t(uuid "{uuid.uuid4()}")\n', g)
    g = g.replace('\n\t', '\n\t\t')          # one level deeper inside the board file
    descr = re.search(r'\n\t\(descr "[^"]*"\)', lib_body).group(0).replace('\n\t', '\n\t\t')
    tags = re.search(r'\n\t\(tags "[^"]*"\)', lib_body).group(0).replace('\n\t', '\n\t\t')
    new = (f'\t(footprint "{NEW}"\n\t\t(layer "F.Cu")\n\t\t(uuid "{fuuid}")\n\t\t(at {x} {y})'
           + descr + tags + ''.join(P) + path + sheet
           + '\n\t\t(attr through_hole)\n\t\t(duplicate_pad_numbers_are_jumpers no)'
           + g + '\n\t\t(embedded_fonts no)\n\t)\n')
    out.append(s[pos:st]); out.append(new); pos = en
    done.append((ref, x, y, len(nets)))
out.append(s[pos:])
open(PCB, 'w').write(''.join(out))
for d in done:
    print('swapped', d)
