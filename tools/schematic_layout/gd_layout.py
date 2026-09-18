import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from layoutlib import *

SRC = '/home/jose/Kicad/FE_UFPR_4_0/gate_drive.kicad_sch'
b = Builder(SRC)

# ═════════ 1. GATE-RAIL DECOUPLING BANK (top right of the driver column) ═════════
x0 = 179.07
for i, ref in enumerate(('C36','C29','C30','C31','C32','C33','C34')):
    b.place(ref, x0 + 12.7*i, 34.29, 0, **VERT)
b.wire((x0,30.48),(x0+76.2,30.48)); b.glab('+13V5_GATE', x0, 30.48, 0)
b.wire((x0,38.1),(x0+76.2,38.1));   b.gnd(x0+76.2, 38.1)

# ═════════ 2. ENABLE / INTERLOCK (top left) ═════════
b.place('JP1', 22.86, 55.88, 90, ref_off=(-3.302,-1.27), val_off=(-3.302,1.905))
b.wire((22.86,50.8),(22.86,46.99));  b.glab('+3V3', 22.86, 46.99, 270)
b.wire((22.86,60.96),(22.86,66.04)); b.hlab('SW_MAIN_3V3', 22.86, 66.04, 90)
b.place('U8', 74.93, 60.96, 0, ref_off=(-5.08,-12.7), val_off=(-5.08,13.97))
b.wire((74.93,50.8),(74.93,45.72));  b.glab('+3V3', 74.93, 45.72, 270)
b.wire((74.93,71.12),(74.93,76.2));  b.gnd(74.93, 76.2)
b.place('C35', 93.98, 50.8, 0, **VERT)
b.wire((93.98,46.99),(93.98,44.45)); b.glab('+3V3', 93.98, 44.45, 270)
b.wire((93.98,54.61),(93.98,57.15)); b.gnd(93.98, 57.15)
# staircase: upper rows reach further left so their pulldown drops clear the rows below
for yy, xend, xdrop, ref, name, kind in (
        (55.88, 26.67, 34.29, 'R32', 'GATE_ILOCK_3V3', 'l'),
        (60.96, 41.91, 44.45, 'R30', 'DRV_EN_3V3',     'h'),
        (66.04, 49.53, 54.61, 'R31', 'DRV_EN_AUX_3V3', 'h')):
    b.wire((59.69,yy),(xend,yy))
    b.wire((xdrop,yy),(xdrop,78.74))
    b.place(ref, xdrop, 82.55, 0, **VERT)
    b.wire((xdrop,86.36),(xdrop,88.9)); b.gnd(xdrop, 88.9)
    if kind == 'h': b.hlab(name, xend, yy, 180, "right")
    else:           b.lab(name, 29.21, yy, 0, "left bottom")
# U8 output -> GATE_EN_3V3 -> pulldown, test point, status LED
b.wire((87.63,60.96),(116.84,60.96)); b.lab('GATE_EN_3V3', 88.9, 60.96, 0)
b.shunt('R33', 96.52, 60.96)
b.place('TP16', 106.68, 60.96, 0, ref_off=(-1.27,-6.35), val_off=(-1.27,-3.81))
b.place('R34', 120.65, 60.96, 90, **HORZ)
b.wire((124.46,60.96),(128.27,60.96)); b.lab('LED_GATE_EN', 124.46, 60.96, 0, "left top")
b.place('D9', 132.08, 60.96, 180, **HORZ)
b.wire((135.89,60.96),(139.7,60.96)); b.wire((139.7,60.96),(139.7,66.04)); b.gnd(139.7, 66.04)

# ═════════ 3. THREE GATE DRIVERS ═════════
XD = 111.76
CH = (('U5','U','R36','R37','R18','R19','C37','C38','R24','R25','TP10','TP11'),
      ('U6','V','R38','R39','R20','R21','C39','C40','R26','R27','TP12','TP13'),
      ('U7','W','R40','R41','R22','R23','C41','C42','R28','R29','TP14','TP15'))
for d,(U,ph,rpa,rpb,rsa,rsb,ca,cb,rda,rdb,tpa,tpb) in enumerate(CH):
    Y = 104.14 + 41.91*d
    b.place(U, XD, Y, 0, ref_off=(6.35,-9.525), val_off=(-13.97,15.24))
    b.wire((XD,Y-10.16),(XD,Y-13.97)); b.wire((XD,Y-13.97),(XD-7.62,Y-13.97))
    b.glab('+13V5_GATE', XD-7.62, Y-13.97, 180, "right")
    b.wire((XD,Y+10.16),(XD,Y+13.97)); b.wire((XD,Y+13.97),(XD+7.62,Y+13.97))
    b.glab('GND', XD+7.62, Y+13.97, 0)
    for pin_y, jt in ((Y-5.08,"right bottom"), (Y+5.08,"right top")):     # ENA / ENB
        b.wire((XD-10.16,pin_y),(XD-13.97,pin_y))
        b.lab('GATE_EN_3V3', XD-13.97, pin_y, 0, jt)
    # 2026-09-17: LOW side on channel A (INA/OUTA), HIGH side on channel B, to uncross the J23
    # inputs and the DB37 outputs on the board. The IC-side resistors (rpa/rsa) stay with the
    # channel-A pins; the DB37-side parts (cf/rd/tp) stay with their DB37 pin, i.e. cross rows.
    #        pin_y   up    wire-end     drop-x      shunt dir
    for pin_y, up, rp, rs, cf, rd, tp, xend, xdrop, hl, fk, hk in (
            (Y-2.54, True,  rpa, rsa, cb, rdb, tpb, XD-60.96, XD-45.72, 'L', VERT,  HORZU),
            (Y+2.54, False, rpb, rsb, ca, rda, tpa, XD-48.26, XD-33.02, 'H', VERTL, HORZD)):
        b.wire((XD-10.16,pin_y),(xend,pin_y))
        b.shunt(rp, xdrop, pin_y, up=up, **fk)
        b.hlab(f'PWM_{ph}{hl}_3V3', xend, pin_y, 180, "right")
        b.wire((XD+10.16,pin_y),(XD+26.67,pin_y))
        b.lab(f'PWM_{ph}{hl}_DRV', XD+11.43, pin_y, 0, "left top" if up else "left bottom")
        b.place(rs, XD+30.48, pin_y, 90, **hk)
        b.wire((XD+34.29,pin_y),(XD+85.09,pin_y))
        b.shunt(cf, XD+43.18, pin_y, up=up)
        b.shunt(rd, XD+58.42, pin_y, up=up)
        b.place(tp, XD+71.12, pin_y, 0,
                ref_off=(-1.27,-8.89 if up else 11.43), val_off=(-1.27,-6.35 if up else 8.89))
        b.lab(f'PWM_{ph}{hl}_15V', XD+85.09, pin_y, 0, "right top" if up else "right bottom")

# ═════════ 4. DB37 CONNECTOR ═════════
b.place('J2', 279.4, 130.81, 0, ref_off=(0,-36.83), val_off=(0,38.1))
P = b.pins('J2')
LEFT = {'1':('SHIELD_DB37','l'),'2':('FLT_OC_A_15V','h'),'3':('PWM_VL_15V','l'),
        '4':('PWM_VH_15V','l'),'5':('FLT_OC_C_15V','h'),'6':('FLT_OT_15V','h'),
        '7':('VBUS_SNS_RAW','h'),'8':('+24V_MOD','g'),'9':('MOD_AUX15V_1','l'),
        '10':('PGND_MOD','g'),'11':('VBUS_RTN','h'),'12':('ISNS_RTN','h'),
        '13':('ISNS_RTN','h'),'16':('FLT_OV_15V','h'),'19':('GND','g')}
RIGHT= {'20':('PWM_UL_15V','l'),'21':('PWM_UH_15V','l'),'22':('FLT_OC_B_15V','h'),
        '23':('PWM_WL_15V','l'),'24':('PWM_WH_15V','l'),'25':('GND','g'),
        '26':('+24V_MOD','g'),'27':('MOD_AUX15V_2','l'),'28':('PGND_MOD','g'),
        '29':('NTC_1_RAW','h'),'30':('ISNS_A_RAW','h'),'31':('ISNS_B_RAW','h'),
        '32':('ISNS_C_RAW','h'),'37':('GND','g')}
for pin,(nm,kind) in LEFT.items():
    x,y = P[pin]; d = 6.35 + 8.89*(int(pin) % 2); b.wire((x,y),(x-d,y))
    if   kind=='h': b.hlab(nm, x-d, y, 180, "right")
    elif kind=='g': b.glab(nm, x-d, y, 180, "right")
    else:           b.lab(nm, x-d, y, 0, "right bottom")
for pin,(nm,kind) in RIGHT.items():
    x,y = P[pin]; d = 6.35 + 8.89*(int(pin) % 2); b.wire((x,y),(x+d,y))
    if   kind=='h': b.hlab(nm, x+d, y, 0, "left")
    elif kind=='g': b.glab(nm, x+d, y, 0, "left")
    else:           b.lab(nm, x+d, y, 0, "left bottom")
for pin in ('14','15','17','18','33','34','35','36'): b.nc(*P[pin])
# aux-15V test points live in free space, reached by label (the DB37 flank has no room)
for ref, nm, ty in (('TP17','MOD_AUX15V_1',180.34), ('TP18','MOD_AUX15V_2',193.04)):
    b.wire((340.36,ty),(350.52,ty)); b.lab(nm, 340.36, ty, 0, "left bottom")
    b.place(ref, 350.52, ty, 0, ref_off=(3.81,-1.27), val_off=(3.81,1.905))

# ═════════ 5. SHIELD ═════════
g1, g2 = P['G1'], P['G2']
b.wire(g1,(g1[0]-6.35,g1[1])); b.wire(g2,(g2[0]-6.35,g2[1]))
b.wire((g1[0]-6.35,g1[1]),(g1[0]-6.35,g2[1]))
b.wire((g1[0]-6.35,g1[1]),(233.68,g1[1])); b.wire((233.68,g1[1]),(233.68,166.37))
b.wire((215.9,166.37),(241.3,166.37)); b.lab('SHIELD_DB37', 217.17, 166.37, 0)
for ref,x in (('C43',215.9),('R35',228.6)):
    b.place(ref, x, 170.18, 0, **VERT); b.wire((x,173.99),(x,176.53))
b.place('JP2', 241.3, 171.45, 270, ref_off=(3.302,-1.27), val_off=(3.302,1.905))
b.wire((241.3,176.53),(215.9,176.53)); b.gnd(215.9, 176.53)

# ═════════ 6. NOTES ═════════
b.notes_by(['S4 - GATE DRIVE     ', 'POLARITY CHAIN - ACT', 'DC LEVELS AT THE MOD', 'SKEW vs 1500 ns DEAD', 'JP1 INTERLOCK SELECT', 'FAIL-SAFE TABLE - ev', 'S10 LAYOUT NOTES (ga'], (15.24, 157.48), 212.0, 288.0)
b.s.add_text(b.text_by('DB37 PIN TABLE - fro'), 306.07, 20.32, 1.27)

print("gate_drive:", *b.save(SRC))
