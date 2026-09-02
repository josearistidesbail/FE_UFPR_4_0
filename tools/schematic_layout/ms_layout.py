import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from layoutlib import *

SRC = '/home/jose/Kicad/FE_UFPR_4_0/module_status.kicad_sch'
b = Builder(SRC)

# ═════════ 1. FIVE FAULT RECEIVER CHANNELS ═════════
CH = (('FLT_OC_A','R42','C44','R47','R52','C49','U9', 1,'TP24','TP29'),
      ('FLT_OC_B','R43','C45','R48','R53','C50','U9', 2,'TP25', None),
      ('FLT_OC_C','R44','C46','R49','R54','C51','U10',1,'TP26', None),
      ('FLT_OT',  'R45','C47','R50','R55','C52','U10',2,'TP27', None),
      ('FLT_OV',  'R46','C48','R51','R56','C53','U11',1,'TP28', None))
for i,(nm,rpu,cin,rs,rdv,cdv,bu,bunit,tpo,tpi) in enumerate(CH):
    Y = 38.1 + 30.48*i
    b.hlab(f'{nm}_15V', 17.78, Y, 180, "right")
    b.wire((17.78,Y),(76.2,Y))
    b.shunt(rpu, 33.02, Y, up=True, netlab='+13V5_GATE', glob=True, pin1_at_node=False)
    b.shunt(cin, 45.72, Y, up=False)
    if tpi: b.place(tpi, 58.42, Y, 0, ref_off=(-1.27,-6.35), val_off=(-1.27,-3.81))
    b.place(rs, 80.01, Y, 90, **HORZU)
    b.wire((83.82,Y),(110.49,Y)); b.lab(f'{nm}_DIV', 85.09, Y, 0)
    b.shunt(rdv, 91.44, Y, up=False)
    b.shunt(cdv, 102.87, Y, up=False)
    b.place(bu, 125.73, Y, 0, unit=bunit, ref_off=(0,-8.89), val_off=(0,11.43))
    b.wire((138.43,Y),(166.37,Y))
    b.place(tpo, 152.4, Y, 0, ref_off=(-1.27,-6.35), val_off=(-1.27,-3.81))
    b.hlab(f'{nm}_3V3', 166.37, Y, 0, "left")
# spare half of U11 - input parked at GND, output unconnected
YS = 182.88
b.place('U11', 125.73, YS, 0, unit=2, ref_off=(0,-8.89), val_off=(0,11.43))
b.wire((110.49,YS),(100.33,YS)); b.gnd(100.33, YS, up=False)
b.nc(138.43, YS)
b.s.add_text(b.text_by('FAULT RECEIVERS  (5 '), 15.24, 26.67, 1.27)

# ═════════ 2. +3V3 SUPPLY / DECOUPLING (power units of U9-U11) ═════════
for ref,x in (('U9',177.8),('U10',203.2),('U11',228.6)):
    b.place(ref, x, 40.64, 0, unit=3, ref_off=(-6.35,0), val_off=(0,13.97))
b.wire((177.8,30.48),(254.0,30.48)); b.glab('+3V3', 177.8, 30.48, 180, "right")
b.wire((177.8,50.8),(254.0,50.8));   b.glab('GND',  177.8, 50.8, 180, "right")
b.wire((254.0,30.48),(254.0,36.83)); b.wire((254.0,50.8),(254.0,44.45))
for ref,x in (('C54',254.0),('C55',266.7),('C56',279.4),('C57',292.1)):
    b.place(ref, x, 40.64, 0, **VERT)
b.wire((254.0,36.83),(292.1,36.83)); b.wire((254.0,44.45),(292.1,44.45))
b.s.add_text(b.text_by('+3V3 SUPPLY / DECOUP'), 190.5, 22.86, 1.27)

# ═════════ 3. VBUS SENSE (Kelvin) ═════════
YV = 76.2
b.hlab('VBUS_SNS_RAW', 190.5, YV, 180, "right")
b.wire((190.5,YV),(215.9,YV))
b.place('TP19', 200.66, YV, 0, ref_off=(-1.27,-6.35), val_off=(-1.27,-3.81))
b.place('C58', 209.55, YV+3.81, 0, **VERT)                     # to VBUS_RTN, not GND
b.place('R57', 219.71, YV, 90, **HORZU)
b.wire((223.52,YV),(245.11,YV)); b.lab('VBUS_DIV', 231.14, YV, 0)
b.place('R58', 228.6, YV+3.81, 0, **VERT)
b.place('R59', 248.92, YV, 90, **HORZU)
b.wire((252.73,YV),(281.94,YV))
b.shunt('C59', 261.62, YV, up=False)
b.place('TP20', 271.78, YV, 0, ref_off=(-1.27,-6.35), val_off=(-1.27,-3.81))
b.hlab('VBUS_ADC', 281.94, YV, 0, "left")
YR = YV + 7.62                                                  # Kelvin return rail
b.wire((209.55,YR),(238.76,YR))
b.place('TP21', 219.71, YR, 0, ref_off=(-1.27,8.89), val_off=(-1.27,6.35))
b.place('NT3', 241.3, YR, 0, ref_off=(0,-3.81), val_off=(0,4.445))
b.wire((243.84,YR),(251.46,YR)); b.gnd(251.46, YR)
b.hlab('VBUS_RTN', 209.55, YR, 180, "right")
b.s.add_text(b.text_by('VBUS SENSE  (Kelvin)'), 190.5, 66.04, 1.27)

# ═════════ 4. NTC / TEMPERATURE ═════════
YN = 114.3
b.hlab('NTC_1_RAW', 190.5, YN, 180, "right")
b.wire((190.5,YN),(215.9,YN))
b.place('TP22', 200.66, YN, 0, ref_off=(-1.27,-6.35), val_off=(-1.27,-3.81))
b.shunt('C60', 209.55, YN, up=False)
b.place('R60', 219.71, YN, 90, **HORZU)
b.wire((223.52,YN),(245.11,YN)); b.lab('NTC_1_DIV', 231.14, YN, 0)
b.shunt('R61', 233.68, YN, up=False)
b.place('R62', 248.92, YN, 90, **HORZU)
b.wire((252.73,YN),(281.94,YN))
b.shunt('C61', 261.62, YN, up=False)
b.place('TP23', 271.78, YN, 0, ref_off=(-1.27,-6.35), val_off=(-1.27,-3.81))
b.hlab('NTC_1_ADC', 281.94, YN, 0, "left")
b.s.add_text(b.text_by('NTC / TEMPERATURE  ('), 190.5, 104.14, 1.27)

# ═════════ 5. NOTES ═════════
b.notes_by(['VBUS FRONT-END   DB3', 'NTC / TEMPERATURE   ', 'FIRMWARE HANDOFF (hw'], (311.15,), 26.67, 200.0)
b.notes_by(['MODULE ERROR TABLE -', 'S10 LAYOUT NOTES (mo', 'FAULT RECEIVERS - 5 '], (15.24, 116.84), 196.0, 288.0)

print("module_status:", *b.save(SRC))
