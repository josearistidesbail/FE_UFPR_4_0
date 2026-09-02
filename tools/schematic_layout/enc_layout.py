import sys, os, re, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sheetedit import Sheet, n
from conncheck import analyze, autojunctions

SRC = '/home/jose/Kicad/FE_UFPR_4_0/encoder.kicad_sch'
s = Sheet(SRC)
raw_texts = [b[1] for b in s.blocks if b[0] == 'text']
def rawstr(block):
    m = re.match(r'\(text "((?:[^"\\]|\\.)*)"', block)
    return m.group(1)
TEXTS = [rawstr(b) for b in raw_texts]

s.clear_graphics()
W, J, L, G, H, NC = [], [], [], [], [], []
def wire(*pts): W.append(list(pts))
def lab(t,x,y,r=0,j="left bottom"): L.append((t,x,y,r,j))
def glab(t,x,y,r=0,j="left"): G.append((t,x,y,r,j))
def hlab(t,x,y,r=0,j="left"): H.append((t,x,y,r,j))
def nc(x,y): NC.append((x,y))

VERT = dict(ref_off=(3.302,-1.27), val_off=(3.302,1.905))     # vertical passive: text at right
HORZ = dict(ref_off=(0,-2.921), val_off=(0,3.556))            # horizontal passive: text above/below

# ─────────────────────────────  A. SUPPLY RAIL  ─────────────────────────────
YV = 25.4
s.place('FB1', 35.56, YV, 90, **HORZ)
glab('+5V', 25.4, YV, 0)
wire((25.4,YV),(31.75,YV))
wire((39.37,YV),(120.65,YV))
s.place('TP44', 46.99, YV, 0, ref_off=(1.27,-6.35), val_off=(1.27,-3.81))
s.place('#FLG07', 66.04, YV, 0, ref_off=(1.27,-6.35), val_off=(1.27,-3.81))
lab('ENC_VDD', 99.06, YV, 0)
for x, ref in ((81.28,'C97'), (93.98,'C98')):
    s.place(ref, x, 33.02, 0, **VERT)
    wire((x,YV),(x,29.21)); wire((x,36.83),(x,39.37)); glab('GND', x, 39.37, 90, 'right')

# ─────────────────────────  B. REFERENCE CHAIN  ─────────────────────────────
XC = 120.65
wire((XC,YV),(XC,36.83))
s.place('R105', XC, 40.64, 0, **VERT)
s.place('R106', XC, 55.88, 0, **VERT)
s.place('R107', XC, 71.12, 0, **VERT)
wire((XC,44.45),(XC,52.07))          # ENC_VREF_HI_UB node
wire((XC,59.69),(XC,67.31))          # ENC_VREF3V_UB node
wire((XC,74.93),(XC,77.47)); glab('GND', XC, 77.47, 90, 'right')
# filter caps to the left of the chain
s.place('C101', 107.95, 52.07, 0, ref_off=(-11.43,-1.27), val_off=(-11.43,1.905))
wire((107.95,48.26),(XC,48.26))
wire((107.95,55.88),(107.95,58.42)); glab('GND', 107.95, 58.42, 90, 'right')
lab('ENC_VREF_HI_UB', 110.49, 48.26, 0)
s.place('C102', 107.95, 67.31, 0, ref_off=(-11.43,-1.27), val_off=(-11.43,1.905))
wire((107.95,63.5),(XC,63.5))
wire((107.95,71.12),(107.95,73.66)); glab('GND', 107.95, 73.66, 90, 'right')
# ENC_VREF3V_UB routed into U17 pin 3
wire((XC,63.5),(146.05,63.5)); wire((146.05,63.5),(146.05,68.58)); wire((146.05,68.58),(152.4,68.58))
lab('ENC_VREF3V_UB', 127.0, 63.5, 0)

# ─────────────────────────  C. U17 REFERENCE BUFFERS  ───────────────────────
s.place('U17', 165.1, 76.2, 0, ref_off=(-3.81,-11.43), val_off=(-3.81,11.43))
wire((165.1,60.96),(165.1,55.88)); lab('ENC_VDD', 165.1, 55.88, 0)
wire((165.1,91.44),(165.1,93.98)); glab('GND', 165.1, 93.98, 90, 'right')
# A = ENC_VREF3V follower
wire((152.4,71.12),(146.05,71.12)); lab('ENC_VREF3V', 133.35, 71.12, 0)
wire((146.05,71.12),(133.35,71.12))
wire((177.8,69.85),(190.5,69.85)); lab('ENC_VREF3V', 190.5, 69.85, 0)
s.place('TP42', 184.15, 69.85, 0, ref_off=(-1.27,-3.81), val_off=(-1.27,-6.35))
# B = ENC_VREF_HI follower
wire((152.4,81.28),(139.7,81.28)); lab('ENC_VREF_HI_UB', 139.7, 81.28, 0)
wire((152.4,83.82),(146.05,83.82)); lab('ENC_VREF_HI', 133.35, 83.82, 0)
wire((146.05,83.82),(133.35,83.82))
wire((177.8,82.55),(190.5,82.55)); lab('ENC_VREF_HI', 190.5, 82.55, 0)
s.place('TP43', 184.15, 82.55, 0, ref_off=(-1.27,-3.81), val_off=(-1.27,-6.35))
# U17 decoupling
for x, ref in ((203.2,'C103'), (215.9,'C104')):
    s.place(ref, x, 62.23, 0, **VERT)
    wire((x,58.42),(x,55.88)); wire((x,66.04),(x,68.58)); glab('GND', x, 68.58, 90, 'right')
wire((203.2,55.88),(215.9,55.88)); lab('ENC_VDD', 203.2, 55.88, 0)

# ─────────────────────────────  D. J4 CONNECTOR  ────────────────────────────
s.place('J4', 44.45, 130.81, 0, mirror='y', ref_off=(-8.89,-13.97), val_off=(-8.89,-11.43))
P = s.pins('J4')
nc(*P['5']); nc(*P['6'])
for k in ('7','8','9','11','12'): nc(*P[k])
wire(P['1'],(52.07,125.73)); wire((52.07,125.73),(52.07,116.84)); lab('ENC_VDD', 52.07, 116.84, 0)
wire(P['3'],(57.15,130.81)); glab('GND', 57.15, 130.81, 0)
wire(P['2'],(76.2,128.27)); wire((76.2,128.27),(76.2,104.14))
wire(P['4'],(85.09,133.35)); wire((85.09,133.35),(85.09,160.02))
# shield block
wire(P['10'],(25.4,130.81)); wire((25.4,130.81),(25.4,140.97))
wire((25.4,140.97),(45.72,140.97)); lab('SHIELD_ENC', 27.94, 140.97, 0)
for x, ref in ((25.4,'C113'), (35.56,'R118'), (45.72,'R119')):
    s.place(ref, x, 144.78, 0, **VERT)
wire((25.4,148.59),(45.72,148.59)); glab('GND', 45.72, 148.59, 90, 'right')

# ───────────────────────  E/F. SIN + COS CHANNELS  ──────────────────────────
# sgn = +1 -> channel A (SIN, above U16) ; -1 -> channel B (COS, below U16)
def channel(sgn, RAW, P_, N_, OUT, ADC, Cin, TPin, Rin, Rref, Cref,
            Rn, Rfb, Cfb, Rout, Cadc, Dclamp, TPadc, pP, pN, pO):
    yraw = 104.14 if sgn > 0 else 160.02
    yn   = 118.11 if sgn > 0 else 146.05
    ylnk = 125.73 if sgn > 0 else 138.43
    rot  = 0 if sgn > 0 else 180
    # ---- + branch : RAW -> Cin/TP -> Rin -> P node -> down/up into +IN
    wire((76.2 if sgn>0 else 85.09, yraw),(104.14, yraw))
    lab(RAW, 78.74 if sgn>0 else 92.71, yraw, 0)
    s.place(Cin, 88.9, yraw + 3.81, 0, **VERT)
    wire((88.9, yraw + 7.62),(88.9, yraw + 10.16)); glab('GND', 88.9, yraw + 10.16, 90, 'right')
    s.place(TPin, 97.79, yraw, 0, ref_off=(-1.27,-3.81), val_off=(-1.27,-6.35))
    s.place(Rin, 107.95, yraw, 90, **HORZ)
    wire((111.76, yraw),(143.51, yraw))
    lab(P_, 136.53, yraw, 0)
    for x, ref in ((120.65, Rref), (133.35, Cref)):
        s.place(ref, x, yraw + 3.81, 0, **VERT)
        wire((x, yraw + 7.62),(x, yraw + 10.16)); lab('ENC_VREF3V', x, yraw + 10.16, 0)
    wire((143.51, yraw),(143.51, pP[1])); wire((143.51, pP[1]), pP)
    # ---- - branch : Rn from VREF_HI -> N node -> feedback pair -> up/down into -IN
    jn = "left bottom" if sgn > 0 else "left top"
    jf = "left top" if sgn > 0 else "left bottom"
    wire((100.33, yn),(129.54, yn)); lab(N_, 104.14, yn, 0, jn)
    s.place(Rn, 100.33, yn + sgn*3.81, 180 if sgn > 0 else 0, **VERT)
    wire((100.33, yn + sgn*7.62),(100.33, yn + sgn*10.16))
    lab('ENC_VREF_HI', 100.33, yn + sgn*10.16, 0, jf)
    for x, ref in ((116.84, Rfb), (129.54, Cfb)):
        s.place(ref, x, yn + sgn*3.81, rot, **VERT)
    wire((116.84, ylnk),(129.54, ylnk)); lab(OUT, 121.92, ylnk, 0, jf)
    wire(pN,(146.05, pN[1])); lab(N_, 146.05, pN[1], 0, "right bottom")
    # ---- output stage
    yo = pO[1] - sgn*11.43
    wire(pO,(184.15, pO[1])); wire((184.15, pO[1]),(184.15, yo))
    wire((184.15, yo),(189.23, yo)); lab(OUT, 179.07, pO[1], 0, "left bottom")
    s.place(Rout, 193.04, yo, 90, **HORZ)
    wire((196.85, yo),(241.3, yo))
    yb = yo + 7.62
    s.place(Cadc, 203.2, yo + 3.81, 0, **VERT)
    wire((203.2, yb),(203.2, yb + 2.54)); glab('GND', 203.2, yb + 2.54, 90, 'right')
    s.place(TPadc, 212.09, yo, 0, ref_off=(-1.27,-3.81), val_off=(-1.27,-6.35))
    s.place(Dclamp, 226.06, yb, 180, ref_off=(0,-7.62), val_off=(0,5.08))
    wire((226.06, yo),(226.06, yo + 2.54))
    wire((218.44, yb),(218.44, yb + 2.54)); glab('+3V3', 218.44, yb + 2.54, 90, 'right')
    wire((233.68, yb),(233.68, yb + 2.54)); glab('GND', 233.68, yb + 2.54, 90, 'right')
    hlab(ADC, 241.3, yo, 0)

channel(+1, 'ENC_SIN_RAW','ENC_SIN_P','ENC_SIN_N','ENC_SIN_OUT','ENC_SIN_ADC',
        'C99','TP38','R108','R109','C105','R110','R111','C106','R112','C107','D10','TP40',
        (152.4,124.46),(152.4,127.0),(177.8,125.73))
channel(-1, 'ENC_COS_RAW','ENC_COS_P','ENC_COS_N','ENC_COS_OUT','ENC_COS_ADC',
        'C100','TP39','R113','R114','C108','R115','R116','C109','R117','C110','D11','TP41',
        (152.4,137.16),(152.4,139.7),(177.8,138.43))

# ─────────────────────────────  G. U16  ─────────────────────────────────────
s.place('U16', 165.1, 132.08, 0, ref_off=(-3.81,-11.43), val_off=(-3.81,11.43))
wire((165.1,116.84),(165.1,111.76)); lab('ENC_VDD', 165.1, 111.76, 0)
wire((165.1,147.32),(165.1,152.4)); glab('GND', 165.1, 152.4, 90, 'right')
for x, ref in ((177.8,'C111'), (190.5,'C112')):
    s.place(ref, x, 105.41, 0, **VERT)
wire((177.8,101.6),(190.5,101.6)); lab('ENC_VDD', 177.8, 101.6, 0)
wire((177.8,109.22),(190.5,109.22)); glab('GND', 190.5, 109.22, 90, 'right')

# ─────────────────────────────  H. TEXT NOTES  ──────────────────────────────
NOTE_Y = 178.0
col = [(20.32, [4,0]), (20.32,[0]), (152.4,[2]), (152.4,[3]), (20.32,[1])]
def nlines(t): return t.count('\\n') + 1
def text_by(prefix):
    hits = [t for t in TEXTS if t.startswith(prefix)]
    assert len(hits) == 1, prefix
    return hits[0]
y1 = NOTE_Y
for pre in ['J4 = DEUTSCH DTM13-1', 'RM44AC SOURCE  (RLS/', 'TRANSFER FUNCTION (i']:
    t = text_by(pre); s.add_text(t, 20.32, y1, 1.27); y1 += nlines(t) * 1.9 + 4.0
y2 = NOTE_Y
for pre in ['REFERENCES  R105 3.0', 'ANTI-ALIAS AND PHASE']:
    t = text_by(pre); s.add_text(t, 152.4, y2, 1.27); y2 += nlines(t) * 1.9 + 4.0

# ─────────────────────────────  EMIT  ───────────────────────────────────────
from conncheck import interior
segs = [(a,b) for p in W for a,b in zip(p, p[1:])]
segs = [((round(a[0],4),round(a[1],4)),(round(b[0],4),round(b[1],4))) for a,b in segs]
segs = [(a,b) for a,b in segs if a != b]
allpins = {}
for ref in s.symbols:
    if ref is None: continue
    for k,xy in s.pins(ref).items(): allpins.setdefault(xy,[]).append(f"{ref}.{k}")
# KiCad only bonds a pin to a wire at a wire ENDPOINT -> split every segment at
# each pin lying in its interior.
split = []
for a,b in segs:
    pts = sorted((p for p in allpins if interior(p,a,b)),
                 key=lambda p:(p[0]-a[0])**2+(p[1]-a[1])**2)
    cur = a
    for p in pts: split.append((cur,p)); cur = p
    split.append((cur,b))
split = [(a,b) for a,b in split if a != b]
segs = split
for a,b in segs: s.wire([a,b])
for jx,jy in sorted(autojunctions(segs, allpins)): s.junction(jx,jy)
for t,x,y,r,j in L: s.label(t,x,y,rot=r,just=j)
for t,x,y,r,j in G: s.glabel(t,x,y,rot=r,just=j)
for t,x,y,r,j in H: s.hlabel(t,x,y,rot=r,shape="output",just=j)
for x,y in NC: s.nc(x,y)
OUT = '/home/jose/Kicad/FE_UFPR_4_0/encoder.kicad_sch'
s.save(OUT)
print("written", OUT, " wires:", len(segs), " labels:", len(L)+len(G)+len(H))
