import pcbnew, json, sys
P=sys.argv[1]; J=sys.argv[2]
b=pcbnew.LoadBoard(P); mm=pcbnew.ToMM
d=json.load(open(J)); kill=set()
for v in d['violations']:
    if v['type']=='items_not_allowed':
        for it in v['items']:
            if it['description'].startswith('Via'): kill.add(it['uuid'])
    if v['type']=='shorting_items':
        for it in v['items']:
            if it['description'].startswith('Track'): kill.add(it['uuid'])
T=[b.Tracks()[i] for i in range(len(b.Tracks()))]; n=0
for t in T:
    u=t.m_Uuid.AsString(); net=t.GetNetname()
    if u in kill or net.startswith('unconnected-'):
        b.Remove(t); n+=1
print('removed',n)
pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(P,b); print('filled+saved')
