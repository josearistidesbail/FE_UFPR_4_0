import pcbnew, json, sys
P=sys.argv[1]; J=sys.argv[2]
d=json.load(open(J)); ids=set()
for v in d['violations']:
    if v['type'] in ('track_dangling','via_dangling'):
        for it in v['items']: ids.add(it['uuid'])
b=pcbnew.LoadBoard(P); n=0
for t in list(b.Tracks()) if False else [b.Tracks()[i] for i in range(len(b.Tracks()))]:
    if t.m_Uuid.AsString() in ids: b.Remove(t); n+=1
print("removed",n,"of",len(ids)); pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(P,b)
