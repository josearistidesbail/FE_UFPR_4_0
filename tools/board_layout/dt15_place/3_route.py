import pcbnew, sys
S='/tmp/claude-1000/-home-jose-Kicad-FE-UFPR-4-0/4ee08434-1f53-4717-a0dd-e5ea610de7ee/scratchpad/place/'
P=S+'FE_UFPR_4_0.kicad_pcb'; b=pcbnew.LoadBoard(P); FM=pcbnew.FromMM; mm=pcbnew.ToMM
old=pcbnew.LoadBoard(S+'old.kicad_pcb')
def V(x,y): return pcbnew.VECTOR2I(FM(x),FM(y))
L={n:b.GetLayerID(n) for n in ('F.Cu','B.Cu','In1.Cu','In2.Cu')}
def net(n):
    ni=b.GetNetInfo().GetNetItem(n); assert ni, n; return ni
NC={'Default':(0.25,0.6,0.3),'Analog':(0.30,0.6,0.3),'Gate':(0.40,0.8,0.4),'Power_1A':(0.50,0.8,0.4),'Power_3A':(1.20,1.0,0.5),'CAN':(0.40,0.8,0.4)}
def ncl(n): return NC.get(net(n).GetNetClassName(),NC['Default'])
def width(n): return FM(ncl(n)[0])
def pad(ref,num):
    f=b.FindFootprintByReference(ref); p=f.FindPadByNumber(str(num)); return (mm(p.GetPosition().x),mm(p.GetPosition().y))
def seg(n,layer,pts,w=None):
    ni=net(n); w=w or width(n)
    for (x0,y0),(x1,y1) in zip(pts,pts[1:]):
        t=pcbnew.PCB_TRACK(b); t.SetStart(V(x0,y0)); t.SetEnd(V(x1,y1)); t.SetWidth(w); t.SetLayer(L[layer]); t.SetNet(ni); b.Add(t)
def via(n,x,y):
    ni=net(n); v=pcbnew.PCB_VIA(b); v.SetPosition(V(x,y)); c=ncl(n)
    v.SetWidth(FM(c[1])); v.SetDrill(FM(c[2])); v.SetLayerPair(L['F.Cu'],L['B.Cu']); v.SetNet(ni); b.Add(v)
def move(ref,x,y,rot=None):
    f=b.FindFootprintByReference(ref); f.SetPosition(V(x,y))
    if rot is not None: f.SetOrientationDegrees(rot)
# ---- fine placement
move('H1',101.0,95.0); move('TP6',136.6,193.0); move('TP7',139.5,209.0)
move('J3',114.5,189.5); move('H3',136.6,214.9)
move('C92',135.0,196.9); move('C93',137.3,196.9); move('C94',135.8,205.5); move('C95',138.1,205.5)
# shift J3's four screw keepouts by +0.6 in x
for z in b.Zones():
    if z.GetIsRuleArea() and z.GetZoneName()=='DT15_screw_head':
        bb=z.GetBoundingBox(); cx,cy=mm(bb.GetCenter().x),mm(bb.GetCenter().y)
        if 160<cy<215 and cx<130:
            o=z.Outline()
            for k in range(o.VertexCount(0)):
                v=o.CVertex(k); o.SetVertex(k,V(mm(v.x)+0.6,mm(v.y)))
print('J3 keepouts shifted')
move('C119',121.6,125.3,0); move('D17',122.8,131.0,90)
# C119 pad1 must be the left (west) pad; D17 pad1 the top pad; R17 pad1 the top pad
def orient(ref,cond,rots):
    for r in rots:
        b.FindFootprintByReference(ref).SetOrientationDegrees(r)
        if cond(pad(ref,1),pad(ref,2)): return r
    raise SystemExit('orient fail '+ref)
print('C119 rot',orient('C119',lambda a,c:a[0]<c[0],(0,180)))
print('D17 rot',orient('D17',lambda a,c:a[1]<c[1],(90,-90)))
move('R17',139.3,192.5); print('R17 rot',orient('R17',lambda a,c:a[1]<c[1],(90,-90)))
# ---- restore eastern parts of the old routes
RESTORE={'/encoder/ENC_COS_RAW':182.2,'/encoder/MOT_TEMP_RAW':168.85,'/vehicle_io/CAN_H':173.74,'/vehicle_io/CAN_L':173.74,
         '/vehicle_io/SW_MAIN_RTN':171.9,'/vehicle_io/SW_START_RTN':171.0,'Net-(J5-Pin_3)':171.45,'Net-(J5-Pin_4)':170.55}
T0=[b.Tracks()[i].Cast() for i in range(len(b.Tracks()))]
existing={(round(mm(t.GetPosition().x),2),round(mm(t.GetPosition().y),2)) for t in T0 if t.GetClass()=='PCB_VIA'}
for t in T0:
    if t.GetClass()=='PCB_VIA' and t.GetNetname()=='GND' and (round(mm(t.GetPosition().x),2),round(mm(t.GetPosition().y),2)) in ((116.05,97.65),(129.4,97.35)): b.Remove(t); print('GND via removed')
OT=[old.Tracks()[i].Cast() for i in range(len(old.Tracks()))]; n=0
for t in OT:
    nm=t.GetNetname()
    if nm not in RESTORE: continue
    if t.GetClass()=='PCB_VIA':
        x=mm(t.GetPosition().x)
        if x>=RESTORE[nm] and (round(x,2),round(mm(t.GetPosition().y),2)) not in existing: v=pcbnew.PCB_VIA(b); v.SetPosition(t.GetPosition()); v.SetWidth(t.GetWidth()); v.SetDrill(t.GetDrillValue()); v.SetLayerPair(t.TopLayer(),t.BottomLayer()); v.SetNet(net(nm)); b.Add(v); n+=1
    else:
        x0,x1=mm(t.GetStart().x),mm(t.GetEnd().x)
        if min(x0,x1)>=RESTORE[nm]-0.01: s=pcbnew.PCB_TRACK(b); s.SetStart(t.GetStart()); s.SetEnd(t.GetEnd()); s.SetWidth(t.GetWidth()); s.SetLayer(t.GetLayer()); s.SetNet(net(nm)); b.Add(s); n+=1
print('restored',n)
# ---- J3 group
J31,J32,J33,J34,J35,J36=[pad('J3',i) for i in (1,2,3,4,5,6)]
c251,c261,c272,c282=pad('C25',1),pad('C26',1),pad('C27',2),pad('C28',2)
seg('+15V_ISO','B.Cu',[c261,(c251[0],c261[1]-0.2),c251,J31,(142.4,J31[1]),(142.4,193.0)])
via('+15V_ISO',142.4,193.0)
u43=pad('U4',3); r171=pad('R17',1); r172=pad('R17',2); c921=pad('C92',1); c931=pad('C93',1)
seg('+15V_ISO','F.Cu',[(142.4,193.0),u43])
seg('+15V_ISO','F.Cu',[(142.4,193.0),(142.4,r171[1]),r171,(135.0,r171[1]),c921,(136.6,c921[1]),(c931[0],c931[1]-0.0) if False else c931])
seg('+15V_ISO','F.Cu',[(136.6,r171[1]),pad('TP6',1)],w=FM(0.5))
print('classes', net('+15V_ISO').GetNetClassName(), net('-15V_ISO').GetNetClassName(), net('/vehicle_io/+5V_VEH').GetNetClassName())
seg('ISO_COM','F.Cu',[pad('C92',2),pad('C93',2),(pad('D8',1)[0],pad('C93',2)[1]),pad('D8',1)])
seg('/power/PWR_LED_15V','F.Cu',[r172,pad('D8',2)])
seg('-15V_ISO','B.Cu',[c282,(c272[0],c282[1]+0.2),c272,J35])
c942=pad('C94',2); c952=pad('C95',2); u45=pad('U4',5)
seg('-15V_ISO','F.Cu',[J35,(121.3,J35[1]),(121.3,209.5),(134.9,209.5),(c942[0],c942[1]+1.6),c942,(137.4,c952[1]),c952,(139.5,c952[1]+1.4),pad('TP7',1),(140.6,210.1),(140.6,212.7),u45])
# LEM signals: horizontals at pad y, verticals at 158/160/162, then to the C65/C72/C79 pads
c651,c721,c791=pad('C65',1),pad('C72',1),pad('C79',1)
seg('/current_sense/LEM_A_M','F.Cu',[J32,(158.0,J32[1]),(158.0,c651[1]+0.0),c651])
seg('/current_sense/LEM_B_M','F.Cu',[J33,(160.0,J33[1]),(160.0,c721[1]),c721])
seg('/current_sense/LEM_C_M','F.Cu',[J34,(122.1,J34[1]),(124.1,189.7),(162.0,189.7),(162.0,c791[1]),c791])
r1031=pad('R103',1)
r1041=pad('R104',1)
seg('/current_sense/SHIELD_LEM','B.Cu',[J36,(122.6,J36[1]),(123.6,199.6),(164.0,199.6),(164.9,198.7),(164.9,187.5)]); via('/current_sense/SHIELD_LEM',164.9,187.5)
seg('/current_sense/SHIELD_LEM','F.Cu',[(164.9,187.5),(166.75,r1041[1]),r1041])
# ---- J4 group (rot 180: right column x 155.66 = pins 1..6 top->bottom; left column pins 7..12 bottom->top)
J41,J42,J44,J46,J410=[pad('J4',i) for i in (1,2,4,6,10)]
tp44=pad('TP44',1); c971=pad('C97',1)
seg('/encoder/ENC_VDD','F.Cu',[J41,(160.5,J41[1]),(164.9,tp44[1]),tp44,(c971[0],tp44[1]-1.4),c971])
c991=pad('C99',1); tp38=pad('TP38',1)
seg('/encoder/ENC_SIN_RAW','F.Cu',[J42,(166.8,J42[1]),(169.6,c991[1]),c991,(172.1,118.72),(172.1,118.7)])
tp39=pad('TP39',1); c1001=pad('C100',1)
seg('/encoder/ENC_COS_RAW','F.Cu',[J44,(164.5,J44[1]),(169.9,tp39[1]),tp39,(174.0,tp39[1]),(182.2,tp39[1]-8.2),(182.2,109.45)])
seg('/encoder/ENC_COS_RAW','F.Cu',[tp39,(c1001[0],tp39[1]-0.68),c1001])
tp53=pad('TP53',1)
seg('/encoder/MOT_TEMP_RAW','F.Cu',[J46,(167.4,J46[1]),(168.85,138.85)])
c1201=pad('C120',1)
seg('/encoder/MOT_TEMP_RAW','B.Cu',[c1201,(154.0,c1201[1]),(J46[0],c1201[1]+1.66),J46])
r1181,r1191,c1131=pad('R118',1),pad('R119',1),pad('C113',1)
seg('/encoder/SHIELD_ENC','B.Cu',[J410,r1181,r1191]); seg('/encoder/SHIELD_ENC','B.Cu',[r1181,c1131])
# ---- J5 group (rot 180: right column x 118.76 = pins 1..4 top->bottom; left column pins 5..8 bottom->top)
J51,J52,J53,J54,J55,J56,J58=[pad('J5',i) for i in (1,2,3,4,5,6,8)]
# CAN pair on F.Cu: CAN_L (left pad) upper lane 94.0, CAN_H (right pad) lower lane 94.7
seg('/vehicle_io/CAN_H','F.Cu',[J51,(J51[0],94.7),(181.0,94.7),(182.0,95.72),pad('R122',2)])
seg('/vehicle_io/CAN_L','F.Cu',[J58,(J58[0],94.0),(178.8,94.0),(179.5,93.3)]); via('/vehicle_io/CAN_L',179.5,93.3)
seg('/vehicle_io/CAN_L','B.Cu',[(179.5,93.3),(179.5,100.5),(182.3,100.5)]); via('/vehicle_io/CAN_L',182.3,100.5)
seg('/vehicle_io/CAN_L','F.Cu',[(182.3,100.5),(183.6,101.15),pad('JP6',1)])
# switch nets + +5V on B.Cu lanes: verticals MAIN 111.8 / Pin3 112.35 / START 115.5 / Pin4 116.05 / +5V 116.9 ; lanes 96.0 / 96.55 / 97.1 / 97.65 / 98.2
seg('/vehicle_io/SW_MAIN_RTN','B.Cu',[J56,(111.8,J56[1]),(111.8,96.0),(171.9,96.0),(171.9,103.79)])
seg('Net-(J5-Pin_3)','F.Cu',[J53,(112.6,J53[1])]); via('Net-(J5-Pin_3)',112.6,J53[1])
seg('Net-(J5-Pin_3)','B.Cu',[(112.6,J53[1]),(112.6,96.55),(171.45,96.55),(171.45,104.35)])
seg('/vehicle_io/SW_START_RTN','B.Cu',[J55,(115.8,J55[1]),(115.8,97.1),(171.0,97.1),(171.0,104.54)])
seg('Net-(J5-Pin_4)','B.Cu',[J54,(116.35,J54[1]),(116.35,97.65),(170.55,97.65),(170.55,104.72)])
seg('/vehicle_io/+5V_VEH','B.Cu',[J52,(116.9,J52[1]),(116.9,98.2),(168.3,98.2),(168.3,101.5)]); via('/vehicle_io/+5V_VEH',168.3,101.5)
f31=pad('F3',1); seg('/vehicle_io/+5V_VEH','F.Cu',[(168.3,101.5),(168.3,f31[1]),f31])
c1191=pad('C119',1); d171=pad('D17',1)
seg('/vehicle_io/+5V_VEH','B.Cu',[J52,c1191]); seg('/vehicle_io/+5V_VEH','B.Cu',[J52,(J52[0]+1.2,J52[1]+1.2),(d171[0],d171[1]-1.0),d171])
# ---- silk housekeeping
def ftext(ref,match):
    f=b.FindFootprintByReference(ref)
    for i in range(len(f.GraphicalItems())):
        g=f.GraphicalItems()[i].Cast()
        if g.GetClass() in ('PCB_TEXT','FP_TEXT','PCB_FIELD') and match in g.GetText(): return g
    return None
for r in ('C25','C26','C27','C28','R118','R119','C113','C120','C119','D17','H3'):
    b.FindFootprintByReference(r).Reference().SetVisible(False)
def refpos(r,x,y): b.FindFootprintByReference(r).Reference().SetPosition(V(x,y))
refpos('C92',135.0,200.4); refpos('C93',137.3,200.4); refpos('D8',139.3,200.4); refpos('R17',139.3,190.2)
refpos('C94',135.8,202.9); refpos('C95',138.1,202.9); refpos('F3',171.9,102.2)
refpos('J3',124.5,158.4); refpos('J5',114.2,157.1); refpos('J4',151.1,160.5)
for r,x,y in (('J3',124.5,156.8),('J5',114.2,158.7),('J4',151.1,162.1)):
    t=ftext(r,'KEY')
    if t: t.SetPosition(V(x,y))
for r,x,y in (('TP7',139.5,211.3),('TP6',136.6,190.6),('TP44',174.6,115.6)):
    t=ftext(r,'V') or ftext(r,'ENC')
    if t: t.SetPosition(V(x,y))
    else: print('no text for',r)
pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(P,b); print('routed+saved')
