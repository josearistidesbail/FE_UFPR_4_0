import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from layoutlib import *

SRC = '/home/jose/Kicad/FE_UFPR_4_0/current_sense.kicad_sch'
b = Builder(SRC)
XU = 130.81                                    # op-amp column

def half(Yc, up, src, extra, exnet, exglob, rin, rsh, csh, shnet, shglob,
         rret, retnet, retglob, rfb, cfb, outnet, tp, nnet, pnet):
    """One difference-amp half, laid out on the encoder's proven band structure.
    up=True -> the whole network sits ABOVE the op-amp (channel A of the package)."""
    s   = -1 if up else 1
    yP  = Yc + s*27.94                          # + branch run
    yN  = Yc + s*13.97                          # - branch corridor
    yLk = Yc + s*6.35                           # feedback link (= output net)
    yPp = Yc - 7.62 if up else Yc + 5.08        # +IN pin  (pin3 / pin5)
    yNp = Yc - 5.08 if up else Yc + 7.62        # -IN pin  (pin2 / pin6)
    ju  = "left bottom" if up else "left top"
    jd  = "left top"    if up else "left bottom"
    # ---- + branch -------------------------------------------------------
    b.wire((XU-101.6, yP),(XU-55.88, yP))
    (b.hlab if src in b.shapes else b.lab)(
        src, XU-101.6, yP, *(( 180, "right"),) [0] if src in b.shapes else (0, "right bottom"))
    for i, ref in enumerate(extra):
        b.shunt(ref, XU-88.9 + 12.7*i, yP, up=not up, netlab=exnet, glob=exglob)
    b.place(rin, XU-52.07, yP, 90, **(HORZU if up else HORZD))
    b.wire((XU-48.26, yP),(XU-25.4, yP)); b.lab(pnet, XU-47.0, yP, 0, ju)
    b.shunt(rsh, XU-43.18, yP, up=not up, netlab=shnet, glob=shglob)
    b.shunt(csh, XU-30.48, yP, up=not up, netlab=shnet, glob=shglob)
    b.wire((XU-25.4, yP),(XU-25.4, yPp)); b.wire((XU-25.4, yPp),(XU-12.7, yPp))
    # ---- - branch -------------------------------------------------------
    b.wire((XU-96.52, yN),(XU-38.1, yN)); b.lab(nnet, XU-88.9, yN, 0, jd)
    b.shunt(rret, XU-96.52, yN, up=up, netlab=retnet, glob=retglob, pin1_at_node=False)
    for ref, xf in ((rfb, XU-63.5), (cfb, XU-38.1)):
        c = yN - s*3.81
        b.place(ref, xf, c, 0 if up else 180, **VERT)
    b.wire((XU-63.5, yLk),(XU-38.1, yLk)); b.lab(outnet, XU-62.23, yLk, 0, jd)
    b.wire((XU-12.7, yNp),(XU-19.05, yNp))
    b.lab(nnet, XU-19.05, yNp, 0, "right bottom" if up else "right top")
    # ---- output ---------------------------------------------------------
    b.wire((XU+12.7, yLk),(XU+34.29, yLk)); b.lab(outnet, XU+13.97, yLk, 0, ju)
    b.place(tp, XU+22.86, yLk, 0,
            ref_off=(-1.27,-6.35 if up else 8.89), val_off=(-1.27,-3.81 if up else 6.35))
    b.wire((XU+34.29, yLk),(XU+34.29, Yc + s*5.08))
    b.wire((XU+34.29, Yc + s*5.08),(XU+38.1, Yc + s*5.08))

CH = (('A', 45.72, 'U12','JP3','R74','C68',
       ('R67','C64'),  ('R63','R66','C63','R64','R65','C62','TP30'),
       ('R68','R69','C65'), ('R70','R73','C67','R71','R72','C66','TP31')),
      ('B',106.68, 'U13','JP4','R86','C75',
       ('R77','C70'),  ('R75','R79','C71','R78','R76','C69','TP32'),
       ('R80','R81','C72'), ('R82','R85','C74','R83','R84','C73','TP33')),
      ('C',167.64, 'U14','JP5','R98','C82',
       ('R89','C77'),  ('R87','R91','C78','R90','R88','C76','TP34'),
       ('R92','R93','C79'), ('R94','R97','C81','R95','R96','C80','TP35')))
for ph, Yc, U, JP, rout, cadc, IX, I, LX, L in CH:
    b.place(U, XU, Yc, 0, ref_off=(6.35,-17.78), val_off=(-6.35,19.05))
    b.wire((XU, Yc-15.24),(XU, Yc-20.32)); b.glab('+5V', XU, Yc-20.32, 270)
    b.wire((XU, Yc+15.24),(XU, Yc+20.32)); b.gnd(XU, Yc+20.32)
    half(Yc, True,  f'ISNS_{ph}_RAW', IX, None, False, I[0], I[1], I[2], None, False,
         I[3], 'ISNS_RTN', False, I[4], I[5], f'ISNS_{ph}_INT', I[6],
         f'ISNS_{ph}_INT_N', f'ISNS_{ph}_INT_P')
    half(Yc, False, f'LEM_{ph}_M', LX, 'ISO_COM', True, L[0], L[1], L[2], 'ISNS_VREF', False,
         L[3], 'ISO_COM', True, L[4], L[5], f'ISNS_{ph}_LEM', L[6],
         f'ISNS_{ph}_LEM_N', f'ISNS_{ph}_LEM_P')
    b.place(JP, XU+38.1, Yc, 270, mirror='y', ref_off=(-3.302,-6.35), val_off=(-3.302,-3.81))
    b.wire((XU+41.91, Yc),(XU+48.26, Yc)); b.lab(f'ISNS_{ph}_SEL', XU+41.91, Yc, 0, "left bottom")
    b.place(rout, XU+52.07, Yc, 90, **HORZU)
    b.wire((XU+55.88, Yc),(XU+81.28, Yc))
    b.shunt(cadc, XU+66.04, Yc, up=False)
    b.hlab(f'ISNS_{ph}_ADC', XU+81.28, Yc, 0, "left")

# ═════════ REFERENCE BLOCK (U15) ═════════
XR, YR = 279.4, 50.8
b.place('U15', XR, YR, 0, ref_off=(6.35,-17.78), val_off=(-6.35,19.05))
b.wire((XR, YR-15.24),(XR, YR-20.32)); b.glab('+5V', XR, YR-20.32, 270)
b.wire((XR, YR+15.24),(XR, YR+20.32)); b.gnd(XR, YR+20.32)
b.place('R99', 248.92, 35.56, 0, **VERT)
b.wire((248.92,31.75),(248.92,29.21)); b.glab('+5V', 248.92, 29.21, 270)
b.wire((248.92,39.37),(248.92,43.18)); b.wire((248.92,43.18),(266.7,43.18))
b.lab('ISNS_VREF_DIV', 250.19, 43.18, 0, "left top")
b.place('R100', 248.92, 46.99, 0, **VERT)
b.wire((248.92,50.8),(248.92,53.34)); b.gnd(248.92, 53.34)
for ref,x in (('C83',256.54),('C84',262.89)): b.shunt(ref, x, 43.18, up=True)
b.wire((266.7,45.72),(260.35,45.72)); b.lab('ISNS_VREF', 260.35, 45.72, 0, "right bottom")
b.wire((292.1,44.45),(302.26,44.45)); b.lab('ISNS_VREF', 293.37, 44.45, 0, "left bottom")
b.place('TP36', 302.26, 44.45, 0, ref_off=(-1.27,-6.35), val_off=(-1.27,-3.81))
b.wire((266.7,55.88),(260.35,55.88)); b.lab('ISNS_VREF', 260.35, 55.88, 0, "right top")
b.wire((266.7,58.42),(254.0,58.42));  b.lab('ISNS_REF_MON', 254.0, 58.42, 0, "right top")
b.wire((292.1,57.15),(300.99,57.15)); b.lab('ISNS_REF_MON', 293.37, 57.15, 0, "left top")
b.wire((300.99,46.99),(300.99,66.04))
for y, r, c, nm in ((46.99,'R101','C85','ISNS_REF_A_ADC'), (66.04,'R102','C86','ISNS_REF_B_ADC')):
    b.wire((300.99,y),(306.07,y))
    b.place(r, 309.88, y, 90, **HORZU)
    b.wire((313.69,y),(340.36,y))
    b.shunt(c, 325.12, y, up=False)
    b.hlab(nm, 340.36, y, 0, "left")

# ═════════ +5 V DECOUPLING + ISNS_RTN STAR ═════════
b.wire((213.36,90.17),(264.16,90.17)); b.glab('+5V', 213.36, 90.17, 0)
for ref,x in (('C87',213.36),('C88',226.06),('C89',238.76),('C90',251.46),('C91',264.16)):
    b.place(ref, x, 93.98, 0, **VERT)
b.wire((213.36,97.79),(264.16,97.79)); b.gnd(264.16, 97.79)
b.wire((213.36,110.49),(220.98,110.49)); b.hlab('ISNS_RTN', 213.36, 110.49, 180, "right")
b.place('NT4', 223.52, 110.49, 0, ref_off=(0,-3.81), val_off=(0,4.445))
b.wire((226.06,110.49),(233.68,110.49)); b.gnd(233.68, 110.49)

# ═════════ J3 - LEM HARNESS ═════════
XJ, YJ = 224.79, 137.16
b.place('J3', XJ, YJ, 0, mirror='y', ref_off=(0,-13.97), val_off=(0,15.24))
P = b.pins('J3')
for pin, nm, kind in (('1','+15V_ISO','g'), ('2','LEM_A_M','l'), ('3','LEM_B_M','l'),
                      ('4','LEM_C_M','l'), ('5','-15V_ISO','g'), ('6','SHIELD_LEM','l')):
    x,y = P[pin]; d = 6.35 + 8.89*(int(pin) % 2); b.wire((x,y),(x+d,y))
    (b.glab if kind=='g' else b.lab)(nm, x+d, y, 0, "left" if kind=='g' else "left bottom")
b.nc(*P['7'])
for pin in ('8','9','10','11','12'):
    x,y = P[pin]; b.wire((x,y),(210.82,y))
b.wire((210.82,P['12'][1]),(210.82,P['8'][1]))
b.wire((210.82,P['10'][1]),(200.66,P['10'][1])); b.glab('ISO_COM', 200.66, P['10'][1], 180, "right")
b.place('TP37', 205.74, P['10'][1], 0, ref_off=(-1.27,-6.35), val_off=(-1.27,-3.81))
for rail, r1, r2, y, upf in (('+15V_ISO','C92','C93',163.83,False), ('-15V_ISO','C94','C95',186.69,True)):
    b.wire((213.36,y),(238.76,y)); b.glab(rail, 213.36, y, 0)
    for ref,x in ((r1,226.06),(r2,238.76)):
        b.shunt(ref, x, y, up=upf, netlab='ISO_COM', glob=True, pin1_at_node=not upf)
b.wire((280.67,163.83),(306.07,163.83)); b.lab('SHIELD_LEM', 281.94, 163.83, 0)
for ref,x in (('C96',280.67),('R103',293.37),('R104',306.07)):
    b.place(ref, x, 167.64, 0, **VERT)
b.wire((280.67,171.45),(306.07,171.45)); b.gnd(306.07, 171.45)

# ═════════ NOTES ═════════
b.s.add_text(b.texts[6], 289.56, 90.17, 1.27)
b.s.add_text(b.texts[4], 289.56, 120.65, 1.27)
b.notes([1,5], (15.24,), 205.0, 288.0, gap=3.0)
b.notes([0,2], (137.16,), 205.0, 288.0, gap=3.0)
b.notes([3],   (259.08,), 205.0, 244.0, gap=3.0)
print("current_sense:", *b.save(SRC))
