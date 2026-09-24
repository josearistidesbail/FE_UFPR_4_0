import pcbnew, sys, math
P=sys.argv[1]; b=pcbnew.LoadBoard(P); FM=pcbnew.FromMM; mm=pcbnew.ToMM
def V(x,y): return pcbnew.VECTOR2I(FM(x),FM(y))
LEFT=96.0
# --- outline
n=0
for i in range(len(b.Drawings())):
    d=b.Drawings()[i].Cast()
    if d.GetLayerName()!='Edge.Cuts': continue
    s,e=d.GetStart(),d.GetEnd()
    if abs(mm(s.x)-127.95)<0.01: d.SetStart(V(LEFT,mm(s.y))); n+=1
    if abs(mm(e.x)-127.95)<0.01: d.SetEnd(V(LEFT,mm(e.y))); n+=1
print('edge points moved',n)
# --- zones
for z in b.Zones():
    o=z.Outline()
    if z.GetNetname()=='GND' and z.GetAssignedPriority()==0:
        for k in range(o.VertexCount(0)):
            v=o.CVertex(k)
            if abs(mm(v.x)-128.0)<0.01: o.SetVertex(k,V(LEFT+0.05,mm(v.y)))
        print('GND plane extended')
    if z.GetZoneName()=='ISO_COM_PLANE':
        pts=[(166.95,149.45),(166.95,217.7),(LEFT+0.25,217.7),(LEFT+0.25,159.6),(132.6,159.6),(132.6,149.45)]
        o.RemoveAllContours()
        o.NewOutline()
        for x,y in pts: o.Append(FM(x),FM(y))
        z.SetOutline(o) if hasattr(z,'SetOutline') else None
        print('ISO_COM zone reshaped')
# --- moves
MOVES={ # ref: (x,y,rot)
 'J5':(114.2,128.0,180),'J4':(151.1,129.2,180),'J3':(113.9,189.5,180),
 'H3':(136.4,214.9,0),
 'TP44':(171.9,113.7,0),'TP38':(171.9,117.7,0),'C99':(171.9,119.7,0),'C100':(172.0,123.5,0),'TP39':(171.9,126.0,0),'TP53':(171.8,138.8,0),
 'C92':(135.0,197.5,-90),'C93':(137.3,197.5,-90),'C94':(135.0,204.5,-90),'C95':(137.3,204.5,-90),'D8':(139.3,197.5,90),'R17':(139.0,194.2,180),
 'TP6':(134.5,165.0,0),'TP8':(137.5,165.0,0),'TP7':(140.5,165.0,0),
 'C25':(113.9,178.4,180),'C26':(113.9,181.0,180),'C27':(113.9,196.2,0),'C28':(113.9,193.6,0),
 'R119':(151.1,124.5,0),'R118':(151.1,127.0,0),'C113':(151.1,129.5,0),'C120':(151.1,137.0,180),
 'C119':(114.2,125.3,180),'D17':(114.2,141.5,180),
}
for ref,(x,y,rot) in MOVES.items():
    f=b.FindFootprintByReference(ref); assert f, ref
    f.SetPosition(V(x,y)); f.SetOrientationDegrees(rot)
# logo on B.Cu
for f in b.GetFootprints():
    if f.GetReference().startswith('LOGO') and f.GetLayerName()=='B.Cu':
        f.SetPosition(V(139.5,174.5)); print('logo moved')
print('moved',len(MOVES))
# --- B.Cu keepouts under the screw heads
def octagon(cx,cy,r):
    return [(cx+r*math.cos(math.radians(a)),cy+r*math.sin(math.radians(a))) for a in range(22,383,45)]
screws=[]
for cx,cy,dx,dy in ((114.2,128.0,10.67,13.6),(151.1,129.2,10.67,17.54),(113.9,189.5,10.67,17.54)):
    for sx in (-dx,dx):
        for sy in (-dy,dy): screws.append((cx+sx,cy+sy))
for cx,cy in screws:
    z=pcbnew.ZONE(b); z.SetIsRuleArea(True); z.SetDoNotAllowZoneFills(True); z.SetDoNotAllowTracks(True); z.SetDoNotAllowVias(True)
    z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False)
    z.SetLayer(pcbnew.B_Cu); z.SetZoneName('DT15_screw_head')
    o=z.Outline(); o.NewOutline()
    for x,y in octagon(cx,cy,3.9): o.Append(FM(x),FM(y))
    b.Add(z)
print('keepouts',len(screws))
pcbnew.SaveBoard(P,b); print('saved')
