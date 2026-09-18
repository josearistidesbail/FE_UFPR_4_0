#!/usr/bin/env python3
"""S10 placement tightening for FE_UFPR_4_0 (2026-09-17).

Moves the connector-entry caps to their connector pins (S4 / S6 §5.5 / S7), the ADC charge
buckets to the BoosterPack header pads, U18's and U1's decoupling to their pins, R34 to D9 and
JP1 out of the LaunchPad shadow.  Absolute board coordinates (mm); rotation = KiCad footprint
orientation (CCW positive; for a 2-pad 0603/0805 at rot 0 pad 1 is at -x, rot +90 puts pad 1 at
+y i.e. BELOW the centre, rot -90 puts pad 1 ABOVE).

usage: tighten_s10.py <board.kicad_pcb> [--apply]   (without --apply: report only)
"""
import sys, math, pcbnew

MOVES = {
    # ---------------- DB37 strip: row A caps (y 207.5, signal pad down), row B shunt R (y 204.3), row C TPs (y 201.1)
    # ISNS raw entries at pins 32/31/30, NTC at 29, VBUS at 7
    'C77': (208.8, 207.5, 90), 'C70': (212.2, 207.5, 90), 'C64': (214.4, 207.5, 90), 'C60': (216.8, 207.5, 90),
    'R89': (208.8, 204.3, 90), 'R77': (212.2, 204.3, 90), 'R67': (214.4, 204.3, 90),
    'F2':  (227.0, 206.2, -90),                         # vertical, pad 2 (+24V_MOD) down toward pins 8/26
    'C58': (229.3, 207.5, 90),
    # PWM + fault entries, west -> east by pin x: 6 OT, 24 WH, 5 OC_C, 23 WL, 4 VH, 22 OC_B, 3 VL, 21 UH, 2 OC_A, 20 UL
    'C47': (231.0, 207.5, 90), 'C41': (232.8, 207.5, 90), 'C46': (234.6, 207.5, 90), 'C42': (236.4, 207.5, 90),
    'C39': (238.2, 207.5, 90), 'C45': (240.0, 207.5, 90), 'C40': (241.8, 207.5, 90), 'C37': (243.6, 207.5, 90),
    'C44': (245.4, 207.5, 90), 'C38': (247.2, 207.5, 90),
    'R45': (231.0, 204.3, -90), 'R28': (232.8, 204.3, 90), 'R44': (234.6, 204.3, -90), 'R29': (236.4, 204.3, 90),
    'R26': (238.2, 204.3, 90),  'R43': (240.0, 204.3, -90), 'R27': (241.8, 204.3, 90), 'R24': (243.6, 204.3, 90),
    'R42': (245.4, 204.3, -90), 'R25': (247.2, 204.3, 90),
    'TP47': (212.4, 201.1, 0), 'TP22': (216.8, 201.1, 0),
    'TP15': (230.4, 201.1, 0), 'TP14': (233.1, 201.1, 0), 'TP13': (235.8, 201.1, 0),
    'TP12': (238.5, 201.1, 0), 'TP11': (241.2, 201.1, 0), 'TP10': (243.9, 201.1, 0),
    # FLT_OV at pin 16 (x 202.45)
    'C48': (202.5, 207.5, 90), 'R46': (202.5, 204.3, -90),
    # ---------------- J3 LEM entries on the pin rows, outside the housing courtyard (like C99/C100 at J4)
    'C65': (169.0, 163.6, 0), 'C72': (169.0, 167.8, 0), 'C79': (169.0, 172.0, 0),
    # ---------------- J22 ADC buckets: caps x 200.6, 100 R x 204.0 (ADC pad = pad 2 -> rot 180), one cell per pin
    'C86': (200.6, 177.61, 0), 'R102': (204.0, 177.61, 180),
    'C82': (200.6, 180.15, 0), 'R98':  (204.0, 180.15, 180),
    'C75': (200.6, 182.69, 0), 'R86':  (204.0, 182.69, 180),
    'C68': (200.6, 185.23, 0), 'R74':  (204.0, 185.23, 180),
    'C85': (200.6, 187.77, 0), 'R101': (204.0, 187.77, 180),
    'U15': (208.6, 176.3, -90), 'C88': (212.3, 180.2, -90),
    # ---------------- J20 ADC buckets
    'C61':  (200.6, 111.57, 0),
    'C121': (200.6, 114.11, 0), 'R130': (204.0, 114.11, 180),
    'C122': (200.6, 116.2, 0),  'R131': (204.0, 116.2, 180), 'R132': (204.0, 112.4, 0), 'R113': (204.5, 110.4, 0),
    'C59':  (199.4, 119.1, 90),  'R115': (201.3, 119.0, 90),
    'C110': (200.6, 122.0, 0),  'R117': (204.0, 122.0, 180),
    'C107': (200.6, 124.54, 0), 'R112': (204.0, 124.54, 180),
    'C104': (207.6, 123.6, 180),
    # ---------------- U18 decoupling, U1 input caps, R34 -> D9, JP1 out of the shadow
    'C116': (234.2, 115.5, -90), 'C117': (234.2, 119.3, -90), 'R121': (233.0, 111.5, 0),
    'C2': (262.6, 134.4, -90), 'C3': (265.3, 132.0, -90), 'C11': (262.6, 139.0, 90),
    'R34': (251.4, 217.3, 90),
    'JP1': (248.0, 123.0, 90),   # vertical, in the TP51/TP52 column, 0.7 mm outside the LaunchPad edge
}
# expected side of the "signal" pad after the move: (pad number, 'down'|'up'|'left'|'right')
EXPECT = {**{c:('1','down') for c in ('C77','C70','C64','C60','C58','C47','C41','C46','C42','C39','C45','C40','C37','C44','C38','C48')},
          **{r:('1','down') for r in ('R89','R77','R67','R28','R29','R26','R27','R24','R25')},
          **{r:('2','down') for r in ('R45','R44','R43','R42','R46')},
          'F2':('2','down'),
          **{c:('1','left') for c in ('C65','C72','C79','C86','C82','C75','C68','C85','C61','C121','C122','C110','C107')},
          **{r:('2','left') for r in ('R102','R98','R86','R74','R101','R130','R131','R117','R112')},
          'R132':('1','left'), 'C116':('1','up'), 'C117':('1','up'), 'C2':('1','up'), 'C3':('1','up')}

def mm(v): return v/1e6
def main():
    path=sys.argv[1]; apply='--apply' in sys.argv
    b=pcbnew.LoadBoard(path)
    fps={f.GetReference():f for f in b.GetFootprints()}
    missing=[r for r in MOVES if r not in fps]; assert not missing, missing
    for r,(x,y,rot) in MOVES.items():
        f=fps[r]; f.SetPosition(pcbnew.VECTOR2I(int(round(x*1e6)),int(round(y*1e6)))); f.SetOrientationDegrees(rot)
    # pad-side checks
    bad=[]
    for r,(num,side) in EXPECT.items():
        f=fps[r]; c=f.GetPosition(); p=[p for p in f.Pads() if p.GetNumber()==num][0].GetPosition()
        dx,dy=mm(p.x-c.x),mm(p.y-c.y)
        ok={'down':dy>0.3,'up':dy<-0.3,'left':dx<-0.3,'right':dx>0.3}[side]
        if not ok: bad.append((r,num,side,round(dx,2),round(dy,2)))
    print('pad-side violations:', bad or 'none')
    # courtyard bbox overlaps between moved parts and everything on the same layer
    def bb(f):
        lay=pcbnew.F_Cu if f.GetLayerName()=='F.Cu' else pcbnew.B_Cu
        r=f.GetCourtyard(lay).BBox(); return (mm(r.GetLeft()),mm(r.GetTop()),mm(r.GetRight()),mm(r.GetBottom()),f.GetLayerName())
    boxes={r:bb(f) for r,f in fps.items()}
    ov=[]
    for r in MOVES:
        a=boxes[r]
        if a[2]-a[0]<0.01: continue
        for s,c in boxes.items():
            if s==r or c[4]!=a[4] or c[2]-c[0]<0.01: continue
            if s in ('J2','J3','J4','J5') : continue   # polygon courtyards: DRC checks them
            if a[0]<c[2]-0.005 and c[0]<a[2]-0.005 and a[1]<c[3]-0.005 and c[1]<a[3]-0.005:
                if (s,r) not in ov: ov.append((r,s))
    print('bbox overlaps:', ov or 'none')
    # outline + shadow sanity
    for r in MOVES:
        a=boxes[r]
        if a[0]<128.3 or a[2]>273.7 or a[1]<90.25 or a[3]>219.65: print('NEAR EDGE', r, a)
    if apply:
        pcbnew.SaveBoard(path,b); print('saved', path)
main()
