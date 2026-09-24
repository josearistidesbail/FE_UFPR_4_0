"""Per-net copper length (tracks only, vias excluded) of two boards, printing nets that changed by > 5 mm.

Usage: python3 7_net_lengths.py OLD.kicad_pcb NEW.kicad_pcb
Used on 2026-09-24 to answer "do the longer traces of the 178 mm board matter?" (DECISION_LOG.md, S12.6).
Loads read-only; never saves (a SaveBoard would rewrite the .kicad_pro next to the board).
"""
import pcbnew, sys

def lengths(path):
    b = pcbnew.LoadBoard(path)
    out = {}
    tr = b.Tracks()
    for i in range(len(tr)):                      # SWIG (py3.14): index, don't iterate
        t = tr[i].Cast()
        if isinstance(t, pcbnew.PCB_VIA):
            continue
        out[t.GetNetname()] = out.get(t.GetNetname(), 0) + t.GetLength() / 1e6
    return out

old, new = lengths(sys.argv[1]), lengths(sys.argv[2])
rows = sorted(((new.get(n, 0) - old.get(n, 0), n) for n in set(old) | set(new)), reverse=True)
print(f"{'net':32s} {'old mm':>8s} {'new mm':>8s} {'delta':>7s}")
for d, n in rows:
    if abs(d) > 5:
        print(f"{n:32s} {old.get(n, 0):8.1f} {new.get(n, 0):8.1f} {d:+7.1f}")
