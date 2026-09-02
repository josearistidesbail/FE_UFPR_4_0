import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from layoutlib import *

SRC = '/home/jose/Kicad/FE_UFPR_4_0/launchpad.kicad_sch'
b = Builder(SRC)

# ── geometry ──────────────────────────────────────────────────────────────────
YC   = 55.88                 # connector centre line (multiple of 1.27)
XS   = (50.8, 129.54, 208.28, 287.02)
STUB = 6.35
def odd_y(pin):  return YC - (10.16 - 2.54*((pin-1)//2))    # pins 1,3,..,19
def even_y(pin): return YC - (10.16 - 2.54*((pin-2)//2))    # pins 2,4,..,20

# symbol-pin -> (kind, name).  kind: H hierarchical, G global, N no-connect
J20 = {1:('N',None), 3:('N',None), 5:('N',None), 7:('N',None), 9:('W','ISR'),
       11:('N',None),13:('N',None),15:('N',None),17:('N',None),19:('N',None),
       2:('G','+5V_LP'), 4:('G','GND'), 6:('N',None), 8:('H','NTC_1_ADC'),
       10:('N',None), 12:('N',None), 14:('H','VBUS_ADC'),
       16:('H','ENC_COS_ADC'), 18:('H','ENC_SIN_ADC'), 20:('N',None)}
J21 = {1:('N',None), 3:('N',None), 5:('N',None), 7:('N',None),
       9:('H','CAN_TX_3V3'), 11:('H','CAN_RX_3V3'),
       13:('N',None),15:('N',None),17:('N',None),19:('N',None),
       2:('G','GND'), 4:('N',None), 6:('N',None), 8:('N',None), 10:('N',None),
       12:('N',None), 14:('H','SW_START_3V3'), 16:('N',None), 18:('N',None),
       20:('H','SW_MAIN_3V3')}
J22 = {1:('N',None), 3:('N',None), 5:('N',None), 7:('N',None), 9:('N',None),
       11:('N',None), 13:('N',None), 15:('H','FLT_OV_3V3'), 17:('N',None), 19:('N',None),
       2:('G','+5V_LP'), 4:('G','GND'), 6:('N',None), 8:('N',None),
       10:('H','ISNS_REF_B_ADC'), 12:('H','ISNS_C_ADC'), 14:('H','ISNS_B_ADC'),
       16:('H','ISNS_A_ADC'), 18:('H','ISNS_REF_A_ADC'), 20:('N',None)}
J23 = {1:('H','PWM_UH_3V3'), 3:('H','PWM_UL_3V3'), 5:('H','PWM_VH_3V3'),
       7:('H','PWM_VL_3V3'), 9:('H','PWM_WH_3V3'), 11:('H','PWM_WL_3V3'),
       13:('N',None), 15:('N',None), 17:('N',None), 19:('N',None),
       2:('G','GND'), 4:('H','DRV_EN_3V3'), 6:('H','DRV_EN_AUX_3V3'),
       8:('N',None), 10:('N',None), 12:('N',None), 14:('H','FLT_OT_3V3'),
       16:('H','FLT_OC_C_3V3'), 18:('H','FLT_OC_B_3V3'), 20:('H','FLT_OC_A_3V3')}

TITLE = ('J20  site 1 front-left   TI J1(odd) + J3(even)',
         'J21  site 1 front-right  TI J4(odd) + J2(even)',
         'J22  site 2 rear-left    TI J5(odd) + J7(even)',
         'J23  site 2 rear-right   TI J8(odd) + J6(even)')

for X, ref, MAP, cap in zip(XS, ('J20','J21','J22','J23'), (J20,J21,J22,J23), TITLE):
    b.place(ref, X, YC, 0, ref_off=(0,-13.97), val_off=(0,16.51))
    for pin,(kind,name) in MAP.items():
        odd = pin % 2 == 1
        px  = X - 5.08 if odd else X + 7.62
        py  = odd_y(pin) if odd else even_y(pin)
        if kind == 'N':
            b.nc(px, py); continue
        ex = px - STUB if odd else px + STUB
        b.wire((px,py),(ex,py))
        rot, just = (180,'right') if odd else (0,'left')
        if   kind == 'H': b.hlab(name, ex, py, rot, just)
        elif kind == 'G': b.glab(name, ex, py, rot, just)
    b.s.add_text(cap, X - 11.43, YC + 21.59, 1.27)

# ── ISR scope probe: J20 pin 9 (GPIO67) -> TP48 ───────────────────────────────
YI = odd_y(9)
b.wire((XS[0]-5.08, YI), (33.02, YI))
b.place('TP48', 39.37, YI, 0, ref_off=(-1.27,-6.35), val_off=(-1.27,-3.81))
b.lab('ISR_PROBE_3V3', 33.02, YI, 180, 'right')

# ── +5V feed to the LaunchPad through the series Schottky (S2 policy) ─────────
YP = 45.72
b.glab('+5V', 330.2, YP, 180, 'right')
b.wire((330.2,YP),(341.63,YP))
b.place('D12', 345.44, YP, 0, **HORZU)
b.wire((349.25,YP),(386.08,YP))
b.shunt('C114', 358.14, YP, up=False)
b.shunt('C115', 368.3, YP, up=False)
b.place('TP45', 377.19, YP, 0, ref_off=(-1.27,-6.35), val_off=(-1.27,-3.81))
b.glab('+5V_LP', 386.08, YP, 0, 'left')

# ── two GND lugs ──────────────────────────────────────────────────────────────
YG = 76.2
b.wire((330.2,YG),(355.6,YG))
b.place('TP46', 330.2, YG, 0, ref_off=(-1.27,-6.35), val_off=(-1.27,-3.81))
b.place('TP47', 342.9, YG, 0, ref_off=(-1.27,-6.35), val_off=(-1.27,-3.81))
b.glab('GND', 355.6, YG, 0, 'left')

# ── notes ─────────────────────────────────────────────────────────────────────
N = [
 "SOCKET NUMBERING - READ THIS FIRST\\n"
 "J20..J23 are OUR refdes. They are NOT TI's J1..J8.\\n"
 "Each socket carries TWO of TI's ten-pin columns: the two J-columns printed\\n"
 "side by side in one SPRUI77 table ARE the two rows of one physical 2x10.\\n"
 "Symbol pin (2k-1) = odd row, pin (2k) = even row, both from table row k.\\n"
 "Verified against the 3.0 board's as-built pad->net map, which mated the\\n"
 "real LaunchPad on the bench. Getting this wrong mates the board to the\\n"
 "wrong pins with no ERC and no DRC complaint.",

 "LAUNCHPAD POWER POLICY (S2) - set these jumpers ON THE LAUNCHPAD\\n"
 "JP1 OUT   JP2 OUT   JP3 OUT   JP4 IN   JP5 IN   JP6 OUT\\n"
 "This is TI's documented external-power configuration (SPRUI77 5.2).\\n"
 "Removing JP2 opens the USB GND link too, so the XDS100v2 debugger is\\n"
 "galvanically isolated whenever the board is powered from the headers.\\n"
 "That matters more than it used to: if the logic 24 V is an external\\n"
 "battery unbonded from the car, this board is a floating island and a\\n"
 "plugged-in laptop would otherwise bond it to mains earth.",

 "5 V FEED AND THE 3V3 PINS\\n"
 "The board feeds +5V into the header 5V pins (TI J3-21 and J7-61) through\\n"
 "D12, a series Schottky. Vf ~0.35 V at ~200 mA leaves ~4.63 V, ample for\\n"
 "the LaunchPad's own 3.3 V LDO.\\n"
 "The header 3V3 pins (TI J1-1, J5-41) are deliberately NO-CONNECT. The\\n"
 "LaunchPad regenerates its own 3.3 V and the board carries its own LDO;\\n"
 "hard-paralleling two regulators is the 3.0 failure mode this replaces.",

 "CAN PIN CHOICE (S8)\\n"
 "CAN-A on GPIO4/GPIO5 = TI J4-36 / J4-35, both on J21.\\n"
 "CAN-B is NOT ROUTABLE on this board: the only free CANTXB on a header is\\n"
 "GPIO16 (J4-33), and every header CANRXB - GPIO7 and GPIO10 - is a PWM\\n"
 "output. Bringing CAN-B out would cost a gate signal.\\n"
 "J21 also carries the two cockpit switch inputs, so every vehicle-facing\\n"
 "digital signal shares one connector and none of them share a body with\\n"
 "ENC_SIN/ENC_COS/VBUS/NTC on J20.\\n"
 "The LaunchPad's own transceiver is CAN-B on GPIO12/GPIO17; neither pin\\n"
 "reaches a header, so the J12 links can never contend.",

 "S9 LAYOUT RULES FOR THIS SHEET\\n"
 "1. Sockets are PinSocket_2x10, BOTTOM side - the LaunchPad hangs below.\\n"
 "2. Grid is exact: dX 43.18 mm, dY 63.5 mm (1.700 in x 2.500 in), taken\\n"
 "   from the 3.0 board and re-verified in S1. Do not re-derive it.\\n"
 "3. Nylon standoffs at the LaunchPad's own mounting holes.\\n"
 "4. Confirm the mated stack height of the chosen socket (C5116528) against\\n"
 "   the standoffs before ordering - the insulator height is not yet checked.\\n"
 "5. Keep the J20 and J22 analog pins away from the J21/J23 digital runs.",
]
POS = [(15.24,100.33), (15.24,163.83), (144.78,100.33), (144.78,151.13), (274.32,100.33)]
for t,(cx,cy) in zip(N, POS):
    b.s.add_text(t, cx, cy, 1.27)

print("launchpad:", *b.save(SRC))
