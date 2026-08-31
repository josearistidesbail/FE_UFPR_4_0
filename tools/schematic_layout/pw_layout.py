import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from layoutlib import *

SRC = '/home/jose/Kicad/FE_UFPR_4_0/power.kicad_sch'
b = Builder(SRC)
b.s.add_text(b.texts[3], 15.24, 16.51, 1.27)

# ═════════ 1. ENTRY: J1 -> F1 -> Q1 (reverse polarity) -> +24V_PROT ═════════
YE = 40.64
b.place('J1', 20.32, YE, 0, mirror='y', ref_off=(-6.35,-6.35), val_off=(-6.35,-3.81))
b.wire((25.4,YE),(45.72,YE)); b.glab('+24V_IN', 30.48, YE, 0)
b.wire((25.4,YE+2.54),(31.75,YE+2.54)); b.wire((31.75,YE+2.54),(31.75,YE+7.62))
b.gnd(31.75, YE+7.62)
b.place('#FLG01', 38.1, YE, 0, ref_off=(0,-6.35), val_off=(0,-3.81))
b.place('F1', 49.53, YE, 90, **HORZU)
b.wire((53.34,YE),(60.96,YE)); b.lab('PWR_24V_FUSED', 53.34, YE, 0, "left top")
b.place('Q1', 66.04, YE+2.54, 90, ref_off=(6.35,-3.81), val_off=(6.35,-6.35))
b.wire((71.12,YE),(114.3,YE)); b.glab('+24V_PROT', 114.3, YE, 0)
b.place('D2', 78.74, YE+3.81, 270, **VERT)                     # Vgs clamp, K on the rail
b.place('D1', 91.44, YE+3.81, 270, **VERT)                     # TVS, K on the rail
b.wire((91.44,YE+7.62),(91.44,YE+10.16)); b.gnd(91.44, YE+10.16)
b.place('TP1', 99.06, YE, 0, ref_off=(-1.27,-6.35), val_off=(-1.27,-3.81))
b.place('#FLG02', 106.68, YE, 0, ref_off=(0,-6.35), val_off=(0,-3.81))
b.wire((66.04,YE+7.62),(66.04,YE+12.7))                        # Q1 gate
b.wire((78.74,YE+7.62),(78.74,YE+12.7)); b.wire((66.04,YE+12.7),(78.74,YE+12.7))
b.lab('PWR_QGATE', 68.58, YE+12.7, 0, "left top")
b.place('R1', 66.04, YE+16.51, 0, **VERT)
b.wire((66.04,YE+20.32),(66.04,YE+22.86)); b.gnd(66.04, YE+22.86)
# +24V_PROT bulk bank
YB = 76.2
b.wire((20.32,YB),(104.14,YB)); b.glab('+24V_PROT', 20.32, YB, 0)
for ref,x in (('C1',27.94),('C2',43.18),('C3',58.42),('C4',73.66),('C23',88.9),('C24',104.14)):
    b.place(ref, x, YB+3.81, 0, **VERT)
b.wire((27.94,YB+7.62),(104.14,YB+7.62)); b.gnd(104.14, YB+7.62)
# module aux pass-through
YM = 93.98
b.wire((20.32,YM),(33.02,YM)); b.glab('+24V_PROT', 20.32, YM, 0)
b.place('F2', 36.83, YM, 90, **HORZU)
b.wire((40.64,YM),(78.74,YM)); b.glab('+24V_MOD', 78.74, YM, 0)
b.place('#FLG03', 46.99, YM, 0, ref_off=(0,-6.35), val_off=(0,-3.81))
b.place('TP5', 55.88, YM, 0, ref_off=(-1.27,-6.35), val_off=(-1.27,-3.81))
b.shunt('C5', 68.58, YM, up=False)
# PGND_MOD star
b.wire((20.32,YM+16.51),(27.94,YM+16.51)); b.glab('PGND_MOD', 20.32, YM+16.51, 0)
b.place('NT2', 30.48, YM+16.51, 0, ref_off=(0,-3.81), val_off=(0,4.445))
b.wire((33.02,YM+16.51),(40.64,YM+16.51)); b.gnd(40.64, YM+16.51)

# ═════════ 2. U1  +24V_PROT -> +13V5_GATE ═════════
XU, YU = 160.02, 60.96
b.place('U1', XU, YU, 0, ref_off=(0,-16.51), val_off=(0,17.78))
b.wire((XU-10.16,YU-5.08),(XU-10.16,41.91)); b.glab('+24V_PROT', XU-10.16, 41.91, 270)
XE1 = 125.73
b.place('R2', XE1, 48.26, 0, **VERT)
b.wire((XE1,44.45),(XE1,41.91)); b.glab('+24V_PROT', XE1, 41.91, 270)
b.wire((XE1,52.07),(XE1,YU)); b.wire((XE1,YU),(XU-10.16,YU))
b.lab('PWR_U1_EN', XE1+1.27, YU, 0, "left bottom")
b.place('R3', XE1, YU+3.81, 0, **VERT)
b.wire((XE1,YU+7.62),(XE1,YU+10.16)); b.gnd(XE1, YU+10.16)
b.wire((XU-10.16,YU+5.08),(146.05,YU+5.08)); b.lab('PWR_U1_VCC', 146.05, YU+5.08, 0, "right bottom")
b.shunt('C6', 146.05, YU+5.08, up=False,
        ref_off=(3.302,5.715), val_off=(3.302,8.636))
b.wire((XU+10.16,YU-5.08),(180.34,YU-5.08)); b.lab('PWR_U1_BOOT', 172.72, YU-5.08, 0)
b.place('C8', 180.34, YU-1.27, 0, ref_off=(3.302,5.715), val_off=(3.302,8.636))
b.wire((XU+10.16,YU-2.54),(190.5,YU-2.54)); b.lab('PWR_U1_SW', 172.72, YU-2.54, 0, "left top")
b.wire((180.34,YU+2.54),(186.69,YU+2.54)); b.wire((186.69,YU+2.54),(186.69,YU-2.54))
b.place('L1', 194.31, YU-2.54, 90, **HORZU)
b.wire((198.12,YU-2.54),(214.63,YU-2.54)); b.glab('+13V5_GATE', 214.63, YU-2.54, 0)
b.nc(XU+10.16, YU+5.08)                                        # PG, intentionally open
b.wire((XU+10.16,YU+2.54),(175.26,YU+2.54)); b.wire((175.26,YU+2.54),(175.26,YU+17.78))
b.wire((175.26,YU+17.78),(196.85,YU+17.78)); b.lab('PWR_U1_FB', 190.5, YU+17.78, 0, "left top")
b.shunt('R5', 196.85, YU+17.78, up=True, netlab='+13V5_GATE', glob=True, pin1_at_node=False)
b.shunt('R6', 184.15, YU+17.78, up=False)
b.wire((XU,YU+10.16),(XU,YU+15.24)); b.gnd(XU, YU+15.24)
YG = 93.98                                                     # +13V5_GATE bank
b.wire((137.16,YG),(187.96,YG)); b.glab('+13V5_GATE', 137.16, YG, 0)
for ref,x in (('C9',137.16),('C10',149.86),('C11',162.56),('C14',175.26),('C15',187.96)):
    b.place(ref, x, YG+3.81, 0, **VERT)
b.wire((137.16,YG+7.62),(187.96,YG+7.62)); b.gnd(187.96, YG+7.62)

# ═════════ 3. U2  +13V5_GATE -> +5V ═════════
XV, YV = 260.35, 60.96
b.place('U2', XV, YV, 0, ref_off=(0,-16.51), val_off=(0,19.05))
b.wire((XV-7.62,YV-7.62),(XV-7.62,41.91)); b.glab('+13V5_GATE', XV-7.62, 41.91, 270)
XE2 = 224.79
b.place('R8', XE2, 48.26, 0, **VERT)
b.wire((XE2,44.45),(XE2,41.91)); b.glab('+13V5_GATE', XE2, 41.91, 270)
b.wire((XE2,52.07),(XE2,YV-5.08)); b.wire((XE2,YV-5.08),(XV-7.62,YV-5.08))
b.lab('PWR_U2_EN', XE2+1.27, YV-5.08, 0, "left bottom")
b.place('R9', XE2, YV-1.27, 0, **VERT)
b.wire((XE2,YV+2.54),(XE2,YV+5.08)); b.gnd(XE2, YV+5.08)
b.wire((XV-7.62,YV+2.54),(241.3,YV+2.54)); b.lab('PWR_U2_SS', 241.3, YV+2.54, 0, "right bottom")
b.shunt('C13', 241.3, YV+2.54, up=False,
        ref_off=(3.302,5.715), val_off=(3.302,8.636))
b.wire((XV-7.62,YV+5.08),(XV-7.62,YV+15.24)); b.wire((XV-7.62,YV+15.24),(XV,YV+15.24))
b.wire((XV,YV+12.7),(XV,YV+15.24)); b.gnd(XV, YV+15.24)
b.wire((XV+7.62,YV-7.62),(276.86,YV-7.62)); b.lab('PWR_U2_BST', 269.24, YV-7.62, 0)
b.place('R12', 280.67, YV-7.62, 90, **HORZU)
b.place('C12', 284.48, YV-3.81, 0, **VERT)
b.lab('PWR_U2_BSTC', 284.48, YV-7.62, 0)
b.wire((XV+7.62,YV),(292.1,YV)); b.lab('PWR_U2_SW', 269.24, YV, 0, "left top")
b.place('L2', 295.91, YV, 90, **HORZU)
b.wire((299.72,YV),(320.04,YV)); b.glab('+5V', 320.04, YV, 0)
b.wire((XV+7.62,YV+7.62),(XV+7.62,YV+17.78)); b.wire((XV+7.62,YV+17.78),(300.99,YV+17.78))
b.lab('PWR_U2_FB', 269.24, YV+17.78, 0, "left top")
b.shunt('R10', 300.99, YV+17.78, up=True, netlab='+5V', glob=True, pin1_at_node=False)
b.shunt('R11', 287.02, YV+17.78, up=False)
YF = 93.98                                                     # +5V bank
b.wire((231.14,YF),(281.94,YF)); b.glab('+5V', 231.14, YF, 0)
for ref,x in (('C16',231.14),('C17',243.84),('C18',256.54),('C19',269.24),('C20',281.94)):
    b.place(ref, x, YF+3.81, 0, **VERT)
b.wire((231.14,YF+7.62),(281.94,YF+7.62)); b.gnd(281.94, YF+7.62)

# ═════════ 4. U3  +5V -> +3V3 ═════════
XL, YL = 149.86, 125.73
b.place('U3', XL, YL, 0, ref_off=(0,-8.89), val_off=(0,-11.43))
b.wire((XL-7.62,YL),(129.54,YL)); b.glab('+5V', 129.54, YL, 180, "right")
b.wire((XL+7.62,YL),(190.5,YL)); b.glab('+3V3', 190.5, YL, 0)
b.wire((XL,YL+7.62),(XL,YL+12.7)); b.gnd(XL, YL+12.7)
b.shunt('C21', 168.91, YL, up=False)
b.shunt('C22', 179.07, YL, up=False)

# ═════════ 5. U4  +24V_PROT -> isolated +/-15 V ═════════
XI, YI = 245.11, 130.81
b.place('U4', XI, YI, 0, ref_off=(0,-13.97), val_off=(0,16.51))
b.wire((XI-12.7,YI-5.08),(219.71,YI-5.08)); b.glab('+24V_PROT', 219.71, YI-5.08, 180, "right")
b.wire((XI-12.7,YI+5.08),(219.71,YI+5.08)); b.glab('GND', 219.71, YI+5.08, 180, "right")
for pin_y, nm, tp in ((YI-5.08,'+15V_ISO','TP6'), (YI,'ISO_COM','TP8'), (YI+5.08,'-15V_ISO','TP7')):
    b.wire((XI+12.7,pin_y),(287.02,pin_y)); b.glab(nm, 287.02, pin_y, 0)
    b.place(tp, 275.59, pin_y, 0, ref_off=(-1.27,-6.35), val_off=(-1.27,-3.81))
YA, YBk, YC = 158.75, 166.37, 173.99                           # isolated decoupling stack
b.wire((269.24,YA),(281.94,YA));  b.glab('+15V_ISO', 269.24, YA, 180, "right")
b.wire((269.24,YBk),(320.04,YBk));b.glab('ISO_COM', 269.24, YBk, 180, "right")
b.wire((294.64,YC),(307.34,YC));  b.glab('-15V_ISO', 307.34, YC, 0)
for ref,x in (('C25',269.24),('C26',281.94)): b.place(ref, x, YA+3.81, 0, **VERT)
for ref,x in (('C27',294.64),('C28',307.34)): b.place(ref, x, YBk+3.81, 0, **VERT)
b.place('NT1', 322.58, YBk, 0, ref_off=(0,-3.81), val_off=(0,4.445))
b.wire((325.12,YBk),(332.74,YBk)); b.gnd(332.74, YBk)

# ═════════ 6. RAIL LEDs + TEST POINTS ═════════
LEDS = (('R13','D4','+24V_PROT','GND','PWR_LED_24V',20.32),
        ('R14','D5','+13V5_GATE','GND','PWR_LED_13V5',44.45),
        ('R15','D6','+5V','GND','PWR_LED_5V',68.58),
        ('R16','D7','+3V3','GND','PWR_LED_3V3',92.71),
        ('R17','D8','+15V_ISO','ISO_COM','PWR_LED_15V',116.84))
for r,d,rail,rtn,lname,x in LEDS:
    b.wire((x,154.94),(x,157.48)); b.glab(rail, x, 154.94, 270)
    b.place(r, x, 161.29, 0, **VERT)
    b.wire((x,165.1),(x,167.64)); b.lab(lname, x, 167.64, 0)
    b.place(d, x, 171.45, 90, **VERT)
    b.wire((x,175.26),(x,177.8)); b.glab(rtn, x, 177.8, 90)
for tp,flg,nm,x in (('TP2','#FLG05','+13V5_GATE',20.32), ('TP3','#FLG06','+5V',60.96),
                    ('TP4',None,'+3V3',101.6), ('TP9','#FLG04','GND',142.24)):
    b.wire((x,187.96),(x + (17.78 if flg else 10.16),187.96)); b.glab(nm, x, 187.96, 0)
    b.place(tp, x+10.16, 187.96, 0, ref_off=(-1.27,-6.35), val_off=(-1.27,-3.81))
    if flg: b.place(flg, x+17.78, 187.96, 0, ref_off=(0,-6.35), val_off=(0,-3.81))

# ═════════ 7. NOTES ═════════
b.notes([2,4,0,5,1], (15.24, 150.0), 198.0, 290.0)
print("power:", *b.save(SRC))
