#!/usr/bin/env python3
"""Attach the project 3D models (3dmodels/*.step, made by gen_3d_models.py) to the six footprints
KiCad ships no model for, in the library (.kicad_mod) AND in the board's footprint instances, plus the
LaunchPad shadow body on J20 (instance-only: the PinHeader footprint is shared by J20-J23).
Idempotent: a footprint's existing (model ...) blocks that point at one of these paths are replaced.
   python3 attach_3d_models.py            # library + FE_UFPR_4_0.kicad_pcb  (close pcbnew first!)
   python3 attach_3d_models.py --lib-only
   python3 attach_3d_models.py --pcb /path/copy.kicad_pcb"""
import os, re, sys
PROJ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
LIB = os.path.join(PROJ, 'FE_UFPR_4_0.pretty')
PCB = os.path.join(PROJ, 'FE_UFPR_4_0.kicad_pcb')
P = '${KIPRJMOD}/3dmodels/'
MODELS = {  # footprint name -> (model path, opacity)
    'DEUTSCH_DTM13-12P-R005_Horizontal': (P + 'DEUTSCH_DTM13-12P-R005_Horizontal.step', None),
    'DEUTSCH_DTM13-08PA-R004_Horizontal': (P + 'DEUTSCH_DTM13-08PA-R004_Horizontal.step', None),
    'Converter_DCDC_Mornsun_URA-YMD-6WR3_THT': (P + 'Converter_DCDC_Mornsun_URA-YMD-6WR3_THT.step', None),
    'L_CommonMode_TDK_ACT45B': (P + 'L_CommonMode_TDK_ACT45B.step', None),
    'Fuse_2410_6125Metric': (P + 'Fuse_2410_6125Metric.step', None),
    'Optocoupler_LTV-817S_SMD-4P': ('${KICAD10_3DMODEL_DIR}/Package_DIP.3dshapes/SMDIP-4_W9.53mm.step', None),
}
LP_REF, LP_MODEL = 'J20', (P + 'LaunchPad_LAUNCHXL-F28379D_Shadow.step', 0.45)
ALL_PATHS = {v[0] for v in MODELS.values()} | {LP_MODEL[0]}

def block(path, opacity, ind):
    t = ind
    op = f'\n{t}\t(opacity {opacity})' if opacity else ''
    return (f'\n{t}(model "{path}"{op}\n{t}\t(offset\n{t}\t\t(xyz 0 0 0)\n{t}\t)\n{t}\t(scale\n{t}\t\t(xyz 1 1 1)\n{t}\t)'
            f'\n{t}\t(rotate\n{t}\t\t(xyz 0 0 0)\n{t}\t)\n{t})')

def strip_models(body, ind):
    """remove (model ...) blocks at indent `ind` whose path is one of ours"""
    pat = re.compile(r'\n' + ind + r'\(model "([^"]+)"(?:\n' + ind + r'\t[^\n]*)*\n' + ind + r'\)')
    return pat.sub(lambda m: '' if m.group(1) in ALL_PATHS else m.group(0), body)

def do_lib():
    for name, (path, op) in MODELS.items():
        f = os.path.join(LIB, name + '.kicad_mod')
        s = open(f).read().rstrip()
        assert s.endswith(')')
        s = strip_models(s, '\t')
        s = s[:-1].rstrip() + block(path, op, '\t') + '\n)\n'
        open(f, 'w').write(s)
        print('lib :', name, '->', path)

def do_pcb(pcb):
    s = open(pcb).read()
    n = 0
    out, i = [], 0
    for m in re.finditer(r'\n\t\(footprint "FE_UFPR_4_0:([^"]+)"', s):
        end = s.index('\n\t)', m.end())               # pcbnew formatting: block closes at one tab
        fp = s[m.start():end]
        name = m.group(1)
        adds = []
        if name in MODELS: adds.append(MODELS[name])
        if re.search(r'\(property "Reference" "' + LP_REF + '"', fp): adds.append(LP_MODEL)
        if not adds: continue
        fp = strip_models(fp, '\t\t')
        for path, op in adds: fp += block(path, op, '\t\t')
        out.append(s[i:m.start()]); out.append(fp); i = end; n += 1
    out.append(s[i:])
    open(pcb, 'w').write(''.join(out))
    print(f'pcb : {n} footprint instances updated in {pcb}')

if __name__ == '__main__':
    a = sys.argv[1:]
    do_lib() if '--pcb-only' not in a else None
    if '--lib-only' not in a:
        do_pcb(a[a.index('--pcb') + 1] if '--pcb' in a else PCB)
