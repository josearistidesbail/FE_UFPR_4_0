import pcbnew
S='/tmp/claude-1000/-home-jose-Kicad-FE-UFPR-4-0/4ee08434-1f53-4717-a0dd-e5ea610de7ee/scratchpad/place/'
P=S+'FE_UFPR_4_0.kicad_pcb'; b=pcbnew.LoadBoard(P); FM=pcbnew.FromMM; mm=pcbnew.ToMM
LIB='/home/jose/Kicad/FE_UFPR_4_0/FE_UFPR_4_0.pretty'
def V(x,y): return pcbnew.VECTOR2I(FM(x),FM(y))
def ftext(f,match):
    for i in range(len(f.GraphicalItems())):
        g=f.GraphicalItems()[i].Cast()
        if g.GetClass() in ('PCB_TEXT','FP_TEXT') and match in g.GetText(): return g
TXT={'J3':((124.5,158.4),(124.5,156.8)),'J5':((114.2,157.1),(114.2,158.7)),'J4':((151.1,160.5),(151.1,162.1))}
for ref,fpn in (('J3','DEUTSCH_DT15-12P_Vertical'),('J4','DEUTSCH_DT15-12P_Vertical'),('J5','DEUTSCH_DT15-08P_Vertical')):
    old=b.FindFootprintByReference(ref); new=pcbnew.FootprintLoad(LIB,fpn); new.SetFPID(pcbnew.LIB_ID('FE_UFPR_4_0',fpn))
    new.SetPosition(old.GetPosition()); new.SetOrientation(old.GetOrientation()); new.SetReference(ref); new.SetValue(old.GetValue()); new.SetPath(old.GetPath())
    for k,v in old.GetFieldsText().items():
        if k in ('Reference','Value','Footprint','Datasheet'): continue
        new.SetField(k,v)
    new.SetAttributes(old.GetAttributes())
    b.Remove(old); b.Add(new)
    for p in new.Pads():
        n=p.GetNumber()
        if n: op=old.FindPadByNumber(n); p.SetNetCode(op.GetNetCode() if op else 0)
    (rx,ry),(kx,ky)=TXT[ref]; new.Reference().SetPosition(V(rx,ry)); new.Reference().SetVisible(True)
    t=ftext(new,'KEY'); t.SetPosition(V(kx,ky))
    print(ref,'exchanged; nets',sum(1 for p in new.Pads() if p.GetNumber() and p.GetNetCode()>0))
tp=b.FindFootprintByReference('TP36'); ftext(tp,'ISNS').SetPosition(V(173.5,147.4))
pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(P,b); print('saved')
