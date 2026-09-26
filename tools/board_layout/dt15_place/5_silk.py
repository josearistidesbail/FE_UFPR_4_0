import pcbnew, math
S='/tmp/claude-1000/-home-jose-Kicad-FE-UFPR-4-0/4ee08434-1f53-4717-a0dd-e5ea610de7ee/scratchpad/place/'
P=S+'FE_UFPR_4_0.kicad_pcb'; b=pcbnew.LoadBoard(P); FM=pcbnew.FromMM; mm=pcbnew.ToMM
def V(x,y): return pcbnew.VECTOR2I(FM(x),FM(y))
def rrpoly(x0,y0,x1,y1,r,n=6):
    pts=[]
    for cx,cy,a0 in ((x1-r,y0+r,-90),(x1-r,y1-r,0),(x0+r,y1-r,90),(x0+r,y0+r,180)):
        for k in range(n+1):
            a=math.radians(a0+90*k/n); pts.append((cx+r*math.cos(a),cy+r*math.sin(a)))
    return pts
for ref,L in (('J3',59.21),('J4',59.21),('J5',55.12)):
    f=b.FindFootprintByReference(ref); cx,cy=mm(f.GetPosition().x),mm(f.GetPosition().y)
    kill=[]
    for i in range(len(f.GraphicalItems())):
        g=f.GraphicalItems()[i].Cast()
        if g.GetLayerName()=='F.SilkS' and g.GetClass()=='PCB_SHAPE' and g.GetShapeStr() in ('Line','Arc'): kill.append(g)
    for g in kill: f.Remove(g)
    W=35.26; pts=rrpoly(cx-W/2-0.12,cy-L/2-0.12,cx+W/2+0.12,cy+L/2+0.12,6.47)
    sh=pcbnew.PCB_SHAPE(f); sh.SetShape(pcbnew.SHAPE_T_POLY); sh.SetLayer(b.GetLayerID('F.SilkS')); sh.SetWidth(FM(0.12)); sh.SetFilled(False)
    sh.SetPolyPoints([V(x,y) for x,y in pts]); f.Add(sh)
    print(ref,'silk items removed',len(kill),'polygon added')
for r in ('C92','C93','C94','C95','D8','R17'): b.FindFootprintByReference(r).Reference().SetVisible(False)
def ftext(ref,match):
    f=b.FindFootprintByReference(ref)
    for i in range(len(f.GraphicalItems())):
        g=f.GraphicalItems()[i].Cast()
        if g.GetClass() in ('PCB_TEXT','FP_TEXT') and match in g.GetText(): return g
for r,m,x,y in (('TP44','ENC_VDD',176.8,112.4),('TP7','15V',136.9,211.3),('TP36','ISNS',178.2,147.6)):
    t=ftext(r,m); t.SetPosition(V(x,y)) if t else print('no text',r)
pcbnew.SaveBoard(P,b); print('saved')
