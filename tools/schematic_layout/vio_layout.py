import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from layoutlib import *

SRC = '/home/jose/Kicad/FE_UFPR_4_0/vehicle_io.kicad_sch'
b = Builder(SRC)
s = b.s

# ── one-time: make sure every instance carries its LCSC field (idempotent) ─────
LCSC={'J5':'CONSIGNED','U18':'C12084','U19':'C109227','U20':'C109227','U21':'C10429','L3':'C88056','D13':'C32677',
      'D14':'C81598','D15':'C81598','D16':'C8678','D17':'C2925443','F3':'C7542932','JP6':'NOFIT',
      'R120':'C25804','R121':'C25804','R122':'C22787','R123':'C4190','R124':'C4190','R125':'C4190',
      'R126':'C4190','R127':'C4190','R128':'C4190','C116':'C14663','C117':'C28323','C118':'C14663',
      'C119':'C14663','TP49':'NOFIT','TP50':'NOFIT','TP51':'NOFIT','TP52':'NOFIT'}
def lcsc_tmpl(x,y,val):
    return (f'\t\t(property "LCSC" "{val}"\n\t\t\t(at {x} {y} 0)\n\t\t\t(show_name no)\n\t\t\t(do_not_autoplace no)\n'
            f'\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t\t(hide yes)\n\t\t\t)\n\t\t)\n')
for blk in s.blocks:
    if blk[0] != 'symbol': continue
    ref = blk[2][0]; val = LCSC[ref]; t = blk[1]
    if '(property "LCSC"' in t:
        blk[1] = re.sub(r'\(property "LCSC" "[^"]*"', f'(property "LCSC" "{val}"', t, count=1)
    else:
        at = re.search(r'\n\t\t\(at ([-\d.]+) ([-\d.]+)', t); k = t.find('\n\t\t(pin ')
        blk[1] = t[:k+1] + lcsc_tmpl(at.group(1), at.group(2), val) + t[k+1:]

# ── helpers ───────────────────────────────────────────────────────────────────
def place_want(ref, x, y, want, rots=(0,90,180,270), mirror=None, **kw):
    """place with the rotation that puts pins where `want` says ({pin:(x,y)})"""
    for r in rots:
        b.place(ref, x, y, r, mirror=mirror, **kw)
        p = b.pins(ref)
        if all(abs(p[k][0]-v[0])<1e-3 and abs(p[k][1]-v[1])<1e-3 for k,v in want.items()):
            return p
    raise SystemExit(f"{ref}: no rotation satisfies {want}; got {p}")
TPU = dict(ref_off=(-1.27,-8.89), val_off=(-1.27,-6.35))   # test point, body up
TPD = dict(ref_off=(-1.27,8.89),  val_off=(-1.27,6.35))    # test point, body down

# ═════════════════ 1. J5 — the vehicle connector ═════════════════════════════
XJ, YJ = 45.72, 73.66
P = place_want('J5', XJ, YJ, {'1':(50.8,71.12),'2':(50.8,73.66),'3':(50.8,76.2),'4':(50.8,78.74),
                              '8':(38.1,71.12),'7':(38.1,73.66),'6':(38.1,76.2),'5':(38.1,78.74)},
               rots=(0,), mirror='y', ref_off=(-8.89,-8.89), val_off=(-8.89,13.97))
# left-side (return) pins -> labels
b.wire(P['8'],(30.48,71.12)); b.lab('CAN_L',        30.48,71.12,0,'right bottom')
b.wire(P['7'],(33.02,73.66)); b.glab('GND',         33.02,73.66,180,'right')
b.wire(P['6'],(30.48,76.2));  b.lab('SW_MAIN_RTN',  30.48,76.2, 0,'right bottom')
b.wire(P['5'],(30.48,78.74)); b.lab('SW_START_RTN', 30.48,78.74,0,'right bottom')

# ═════════════════ 2. CAN block ═══════════════════════════════════════════════
YH, YL = 38.1, 43.18                       # CAN_H / CAN_L lines
# J5.1 -> riser -> CAN_H line
b.wire(P['1'],(58.42,71.12)); b.wire((58.42,71.12),(58.42,YH))
b.wire((58.42,YH),(104.14,YH))             # CAN_H: riser .. L3 pin 1
b.wire((63.5,YL),(104.14,YL))              # CAN_L: label .. L3 pin 2
b.lab('CAN_L', 63.5, YL, 0, 'left bottom')
b.lab('CAN_H', 60.96, YH, 0, 'left bottom')
b.place('TP49', 68.58, YH, 0, **TPU)
b.place('TP50', 73.66, YL, 180, **TPD)
# termination: R122 + JP6 stacked above CAN_H, top end labelled CAN_L
XT = 91.44
b.place('R122', XT, YH-3.81, 0, **VERT)                       # pins YH-7.62 / YH
place_want('JP6', XT, YH-12.7, {'1':(XT,YH-17.78),'2':(XT,YH-7.62)}, rots=(90,270), **VERT)
b.wire((XT,YH-17.78),(XT,YH-20.32)); b.lab('CAN_L', XT, YH-20.32, 0, 'left bottom')
# TVS D13 in its own mini-block (both K pins need a label: a wire would cross)
PD = place_want('D13', 86.36, 55.88, {'1':(83.82,50.8),'2':(88.9,50.8),'3':(86.36,60.96)}, rots=(0,),
                ref_off=(6.35,-1.27), val_off=(6.35,1.905))
b.wire(PD['1'],(83.82,48.26)); b.lab('CAN_H', 83.82, 48.26, 0, 'right bottom')
b.wire(PD['2'],(88.9,48.26));  b.lab('CAN_L', 88.9, 48.26, 0, 'left bottom')
b.wire(PD['3'],(86.36,63.5)); b.gnd(86.36, 63.5)
# common-mode choke L3, windings 1-4 (CAN_H) and 2-3 (CAN_L)
PL = place_want('L3', 109.22, 40.64, {'1':(104.14,YH),'2':(104.14,YL),'4':(114.3,YH),'3':(114.3,YL)}, rots=(0,),
                ref_off=(0,-5.08), val_off=(0,6.35))
# transceiver U18, mirrored so the bus pins face the connector
XU, YU = 134.62, 38.1
PU = place_want('U18', XU, YU, {'7':(XU-10.16,YU),'6':(XU-10.16,YU+2.54),'1':(XU+10.16,YU-2.54),
                                '4':(XU+10.16,YU),'5':(XU+10.16,YU+2.54),'8':(XU+10.16,YU+5.08),
                                '3':(XU,YU-7.62),'2':(XU,YU+10.16)}, rots=(0,), mirror='y',
                ref_off=(2.54,-12.7), val_off=(-12.7,12.7))
b.wire(PL['4'],PU['7'])                                            # CAN_H straight
b.wire(PL['3'],(119.38,YL)); b.wire((119.38,YL),(119.38,YU+2.54)); b.wire((119.38,YU+2.54),PU['6'])
b.lab('CAN_H_XCVR', 114.3, YH, 0, 'left top'); b.lab('CAN_L_XCVR', 114.3, YL, 0, 'left top')
b.wire(PU['3'],(XU,YU-10.16)); b.glab('+3V3', XU, YU-10.16, 270)
b.wire(PU['2'],(XU,YU+12.7));  b.gnd(XU, YU+12.7)
b.nc(*PU['5'])
# logic side
YT, YR, YS = YU-2.54, YU, YU+5.08
b.wire(PU['1'],(190.5,YT)); b.hlab('CAN_TX_3V3', 190.5, YT, 0, 'left')
b.wire(PU['4'],(190.5,YR)); b.hlab('CAN_RX_3V3', 190.5, YR, 0, 'left')
b.shunt('R121', 154.94, YT, up=True, netlab='+3V3', glob=True, pin1_at_node=False)   # TXD pull-up
b.wire(PU['8'],(152.4,YS)); b.shunt('R120', 152.4, YS, up=False)                       # RS slope resistor
b.lab('CAN_RS', 147.32, YS, 0, 'left bottom')
# U18 decoupling
for x, ref in ((167.64,'C116'), (182.88,'C117')):
    b.place(ref, x, 19.05, 0, **VERT)
    b.wire((x,22.86),(x,25.4)); b.gnd(x, 25.4)
b.wire((167.64,15.24),(182.88,15.24)); b.glab('+3V3', 167.64, 15.24, 180, 'right')

# ═════════════════ 3. +5V_VEH feed to the ECU's isolated side ═════════════════
Y5 = 73.66
b.wire(P['2'],(97.79,Y5)); b.lab('+5V_VEH', 53.34, Y5, 0, 'left bottom')
b.shunt('C119', 68.58, Y5, up=False)
PT = place_want('D17', 86.36, Y5+3.81, {'1':(86.36,Y5),'2':(86.36,Y5+7.62)}, rots=(90,270), **VERT)
b.wire(PT['2'],(86.36,Y5+10.16)); b.gnd(86.36, Y5+10.16)
PF = place_want('F3', 101.6, Y5, {'1':(97.79,Y5),'2':(105.41,Y5)}, rots=(90,270), **HORZU)
b.wire(PF['2'],(110.49,Y5))
PS = place_want('D16', 114.3, Y5, {'1':(110.49,Y5),'2':(118.11,Y5)}, rots=(0,), **HORZ)
b.wire(PS['2'],(121.92,Y5)); b.glab('+5V', 121.92, Y5, 0, 'left')

# ═════════════════ 4/5. the two isolated cockpit inputs (identical) ═══════════
def channel(Y, pin, riser_x, Rs1, Rs2, Dap, U, Rpd, unit, TP, RTN, OUT):
    # J5 signal pin -> riser -> series 2 x 2.2k -> opto LED
    b.wire(P[pin],(riser_x,P[pin][1])); b.wire((riser_x,P[pin][1]),(riser_x,Y)); b.wire((riser_x,Y),(81.28,Y))
    b.place(Rs1, 85.09, Y, 90, **HORZ); b.wire((88.9,Y),(91.44,Y))
    b.place(Rs2, 95.25, Y, 90, **HORZ); b.wire((99.06,Y),(107.95,Y))          # passes D's K pin at 102.87
    PO = place_want(U, 115.57, Y+2.54, {'1':(107.95,Y),'2':(107.95,Y+5.08),'3':(123.19,Y+5.08),'4':(123.19,Y)},
                    rots=(0,), ref_off=(0,-6.35), val_off=(0,7.62))
    place_want(Dap, 102.87, Y+3.81, {'1':(102.87,Y),'2':(102.87,Y+7.62)}, rots=(90,270), ref_off=(0,-6.731), val_off=(0,-9.652))
    # LED cathode return, back to the connector through a label (a wire would cross)
    b.wire(PO['2'],(107.95,Y+7.62)); b.wire((107.95,Y+7.62),(74.93,Y+7.62))
    b.lab(RTN, 74.93, Y+7.62, 0, 'right bottom')
    # output side: collector to +3V3, emitter -> pull-down -> Schmitt buffer -> label
    b.wire(PO['4'],(123.19,Y-5.08)); b.glab('+3V3', 123.19, Y-5.08, 270)
    b.wire(PO['3'],(137.16,Y+5.08))
    b.shunt(Rpd, 130.81, Y+5.08, up=False)
    b.place('U21', 152.4, Y+5.08, 0, unit=unit, ref_off=(0,-6.35), val_off=(0,6.35))
    b.wire((165.1,Y+5.08),(190.5,Y+5.08))
    b.place(TP, 172.72, Y+5.08, 0, **TPU)
    b.hlab(OUT, 190.5, Y+5.08, 0, 'left')
channel(101.6,  '3', 63.5,  'R123','R124','D14','U19','R125',1,'TP51','SW_MAIN_RTN', 'SW_MAIN_3V3')
channel(132.08, '4', 55.88, 'R126','R127','D15','U20','R128',2,'TP52','SW_START_RTN','SW_START_3V3')
# U21 power unit + decoupling
b.place('U21', 152.4, 165.1, 0, unit=3, ref_off=(-6.35,0), val_off=(7.62,0))
b.wire((152.4,154.94),(152.4,152.4)); b.glab('+3V3', 152.4, 152.4, 270)
b.wire((152.4,175.26),(152.4,177.8)); b.gnd(152.4, 177.8)
b.place('C118', 185.42, 165.1, 0, **VERT)
b.wire((185.42,161.29),(185.42,158.75)); b.glab('+3V3', 185.42, 158.75, 270)
b.wire((185.42,168.91),(185.42,171.45)); b.gnd(185.42, 171.45)

# ═════════════════ 6. notes ═══════════════════════════════════════════════════
N = [
 "J5 - VEHICLE CONNECTOR: DEUTSCH DTM13-08PA-R004, 8-way, key A (CONSIGNED)\\n"
 "cav 1  CAN_H          cav 8  CAN_L         (twisted pair, adjacent cavities)\\n"
 "cav 2  +5V_VEH out    cav 7  GND           (ECU isolated-side supply, PROVISIONAL)\\n"
 "cav 3  SW_MAIN_IN     cav 6  SW_MAIN_RTN   (FSAE shutdown circuit, car-referenced)\\n"
 "cav 4  SW_START_IN    cav 5  SW_START_RTN  (start button, car-referenced)\\n"
 "Every function sits on a physically adjacent pair (1-8, 2-7, 3-6, 4-5).\\n"
 "WHY 8-WAY: the two DTM13-12P-R005 on this board use keys A and B, and TE's\\n"
 "board-mount DTM13 family exists only in 8- and 12-way. A 12-way plug cannot\\n"
 "enter this 8-way receptacle, so mis-mating the LEM or encoder harness into the\\n"
 "vehicle socket (or vice versa) is impossible by way-count.\\n"
 "!! -R004 is a VERTICAL PANEL FLANGE (68.58 x 33.02 + 4 ears, slots 8.89 x 2.54),\\n"
 "not a flat base like the 12-way -R005: flange + housing hang beyond the board\\n"
 "edge and the flange reaches 4.4 mm below the board. Only the 8 pins hold it.\\n"
 "S9 must (a) put the board edge on the footprint's Dwgs.User line and (b) add a\\n"
 "bracket or panel to the flange slots. Cavity numbers taken from the 8-way\\n"
 "drawing (which labels them): near row 1-4, far row 5-8 - confirm on a real\\n"
 "DTM06-08SA before crimping, like J3/J4.",

 "CAN (S8): CAN-A, GPIO4 TX / GPIO5 RX = LaunchPad J4-36 / J4-35, on J21.\\n"
 "U18 SN65HVD230 (3.3 V, JLC Preferred). This is a dedicated 2-node link to the\\n"
 "ECU; the galvanic barrier is on the ECU side (ISO1042/ISO1050 or ISOW1044),\\n"
 "so OUR node is the non-isolated reference its bus side follows.\\n"
 "Termination: 2 nodes => both ends terminated => R122 120R is FITTED by\\n"
 "default through the bridged jumper JP6 (cut the bridge to remove it).\\n"
 "R120 10k on RS = slope-control mode, ~15 V/us (datasheet fig 33); 0R = full\\n"
 "speed, up to 100k = 2 V/us if emissions demand it. RS > 0.75 Vcc = standby.\\n"
 "R121 10k pull-up on TXD: the transceiver's internal bias is weak (datasheet\\n"
 "10.4), so with the LaunchPad unplugged TXD would float - a floating TXD can\\n"
 "hold the bus dominant. Pull-up = recessive = bus free.\\n"
 "L3 ACT45B 100 uH common-mode choke + D13 PSM712 (+12/-7 V asymmetric CAN\\n"
 "TVS, JLC Basic) at the connector side: the board sits on a 900 V inverter.\\n"
 "No shield pin: the pair is unshielded twisted pair; if a shielded cable is\\n"
 "used, terminate the shield at the ECU end only (our domain floats).",

 "ISOLATED COCKPIT INPUTS (S8): identical channels, drawn identically.\\n"
 "Input accepts 8..30 V DC (nominal 12 V GLV, the AM06 ECU runs on +12V)\\n"
 "referenced to its own RTN pin = car GND. Our logic 24 V is a separate\\n"
 "battery unbonded from the car, so every car-referenced signal crosses an\\n"
 "optocoupler (LTV-817S-C, 5 kV, JLC Basic, CTR 200..400 %).\\n"
 "LED chain 2 x 2.2k = 4.4k: 1.5 mA @ 8 V, 2.5 mA @ 12 V, 5.2 mA @ 24 V\\n"
 "(59 % of 0.1 W per 0603 at 24 V; use 2 x 3.3k if the car ever runs 24 V GLV).\\n"
 "1N4148W anti-parallel: LED V_R max is 6 V, a reversed harness would kill it.\\n"
 "Output = HIGH-SIDE phototransistor with 2.2k pull-down: LED on -> 3.1 V,\\n"
 "LED off / unplugged / broken wire -> 0 V. Fail-safe is inherent: no signal\\n"
 "means SW_MAIN_3V3 LOW means gate enable withheld (gate_drive U8 input C).\\n"
 "Saturation needs 1.4 mA of collector current; 8 V worst case gives >= 2.2 mA.\\n"
 "TIMING (S4 banned filtering here): the only delay is the phototransistor's\\n"
 "own fall time into 2.2k - a few tens of us (3-4 us spec at 100R), i.e. under\\n"
 "one 100 us PWM period. No RC anywhere on this path.\\n"
 "U21 SN74LVC2G17 Schmitt buffer: a 20 us edge into a plain LVC input violates\\n"
 "its 10 ns/V transition-rate limit 1000x over; the Schmitt makes it one clean\\n"
 "edge. Non-inverting on purpose - no hidden inversion between pin and GPIO.\\n"
 "SW_MAIN_IN is the shutdown circuit, hardwired - NOT through the ECU.\\n"
 "Drive SW_START_IN from car GLV through the button, never from +5V_VEH.",

 "+5V_VEH (PROVISIONAL, user confirming with the ECU team): if the ECU's\\n"
 "isolated transceiver powers its bus side from us, this is the pin.\\n"
 "F3 0.2 A polyfuse (trips 0.46 A) + D16 SS34 + D17 SMAJ5.0A + C119.\\n"
 "D16 blocks anything on the harness from back-feeding our +5V rail (the\\n"
 "polyfuse alone would let a mis-wired 12 V reach every 5 V part on the board);\\n"
 "the price is ~0.25 V: expect 4.6..4.75 V at <= 75 mA at the connector.\\n"
 "That is inside ISO1042 / ISOW1044 (4.5..5.5 V) but BELOW ISO1050's 4.75 V\\n"
 "minimum - publish this to the ECU team. Fit 0R for D16 only if they need\\n"
 "a full 5 V and guarantee no back-feed. Load budget 75 mA on +5V (S8).",

 "S9 LAYOUT RULES FOR THIS SHEET\\n"
 "1. J5 on the service edge next to the 24 V entry; board edge on the\\n"
 "   footprint's Dwgs.User line; flange bracket - see the J5 note.\\n"
 "2. CAN pair: keep CAN_H/CAN_L routed as a pair from U18 to J5, D13 and the\\n"
 "   termination right at the connector, L3 between them and U18.\\n"
 "3. The opto LED side (J5 cav 3-6, R123/R124/R126/R127, D14/D15) is CAR-\\n"
 "   referenced: no GND pour under it, >= 1.5 mm creepage to board GND, and\\n"
 "   the RTN nets must not touch anything else.\\n"
 "4. U21 and its 100 nF next to the opto outputs; TP51/TP52 reachable.\\n"
 "5. Remember gate_drive JP2 (DB37 pin 1 soft-tie) stays OPEN: with a floating\\n"
 "   24 V supply it is the only thing between this island and the car chassis.",
]
POS = [(220.98,20.32), (220.98,77.47), (220.98,131.57), (220.98,200.66), (25.4,190.5)]
for t,(cx,cy) in zip(N, POS):
    b.s.add_text(t, cx, cy, 1.27)

print("vehicle_io:", *b.save(SRC))
