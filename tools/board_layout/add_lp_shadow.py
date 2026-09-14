#!/usr/bin/env python3
"""S9.6: draw the LaunchPad's 129.9 x 58.4 shadow on Dwgs.User (idempotent - replaces a
previous shadow).  Geometry from S9_BOARD_SETUP.md 1.1 relative to J20 pad 1 = (XG, YG)."""
import re, os, uuid
PROJ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
PCB = os.path.join(PROJ, 'FE_UFPR_4_0.kicad_pcb')
X0, Y0, XG, YG = 50.0, 50.0, 66.0, 14.0
x0, x1 = X0 + XG - 6.43, X0 + XG + 52.0
y0, y1 = Y0 + YG - 31.9, Y0 + YG + 98.0
TAG = 'LAUNCHPAD SHADOW'
s = open(PCB).read()
s = re.sub(r'\n\t\(gr_rect\n(?:\t\t[^\n]*\n)*?\t\t\(layer "Dwgs.User"\)\n\t\t\(uuid "[^"]+"\)\n\t\t\(net 0\)\n\t\)(?=\n)', '', s)  # none expected; harmless
s = re.sub(r'\n\t\(gr_text "' + TAG + r'[^"]*"\n(?:\t\t[^\n]*\n)*?\t\)(?=\n)', '', s)
s = re.sub(r'\n\t\(gr_rect\n\t\t\(start ' + f'{x0:g} {y0:g}' + r'\)\n(?:\t\t[^\n]*\n)*?\t\)(?=\n)', '', s)
rect = (f'\n\t(gr_rect\n\t\t(start {x0:g} {y0:g})\n\t\t(end {x1:g} {y1:g})\n\t\t(stroke\n\t\t\t(width 0.2)\n\t\t\t(type dash)\n\t\t)'
        f'\n\t\t(fill no)\n\t\t(layer "Dwgs.User")\n\t\t(uuid "{uuid.uuid4()}")\n\t)')
txt = (f'\n\t(gr_text "{TAG} 129.9 x 58.4 - LaunchPad sits ABOVE on J20-J23 (male pins up), ~11 mm stack.'
       f' Parts under it <= 8 mm tall; test points under it are unreachable when it is fitted."'
       f'\n\t\t(at {x0 + 1:g} {Y0 + 0.5:g} 90)\n\t\t(layer "Dwgs.User")\n\t\t(uuid "{uuid.uuid4()}")'
       f'\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.2 1.2)\n\t\t\t\t(thickness 0.15)\n\t\t\t)\n\t\t\t(justify left bottom)\n\t\t)\n\t)')
i = s.rindex('\n\t(footprint ')          # insert before the first footprint? no: after the last gr_ item is fine anywhere top-level
j = s.index('\n\t(footprint ')
s = s[:j] + rect + txt + s[j:]
open(PCB, 'w').write(s)
print(f'shadow rect ({x0:g},{y0:g})-({x1:g},{y1:g}) written')
