# Schematic layout tooling (S7.5)

Regenerates a sheet's **graphical layer** — placement, wires, junctions, labels, notes —
while leaving every symbol's identity untouched (UUID, footprint, `LCSC`, instance path).
Only `(at …)`, `(mirror …)` and field positions are rewritten inside a symbol block.

## The invariant

**A layout change must never change the netlist.** Nothing here is trusted until
`kicad-cli` agrees:

```bash
kicad-cli sch export netlist --format kicadsexpr -o /tmp/new.net FE_UFPR_4_0.kicad_sch
python3 tools/schematic_layout/netcmp.py tools/schematic_layout/golden.net /tmp/new.net
# must print: 201 nets, 835 nodes  ...  IDENTICAL
```

`golden.net` was the S7 netlist; **re-baselined in S8** when the `launchpad` sheet
added 52 nets and 90 nodes (149/745 -> 201/835). **If a later session
legitimately changes connectivity, re-baseline `golden.net` in the same commit** and say so
in the Decision Log — otherwise the gate silently stops meaning anything.

## Regenerating a sheet

Each `*_layout.py` rebuilds one sheet from its current file. They are idempotent only
against the *original* sheet, so restore first:

```bash
git checkout encoder.kicad_sch && python3 tools/schematic_layout/enc_layout.py
```

| script | sheet |
|---|---|
| `enc_layout.py` | `encoder` |
| `gd_layout.py` | `gate_drive` |
| `ms_layout.py` | `module_status` |
| `pw_layout.py` | `power` |
| `cs_layout.py` | `current_sense` |
| `lp_layout.py` | `launchpad` |

## Checking before KiCad

`conncheck.analyze(path)` recomputes connectivity from geometry and returns
`(nets, shorts, crossings, pins, segments)`. It reproduces KiCad's rules closely enough to
catch most mistakes in a second rather than a minute — but see the warning below.

```bash
python3 tools/schematic_layout/dump.py current_sense.kicad_sch   # net map + pin geometry
```

## ⚠ The four KiCad behaviours this tooling exists to survive

None of these produce an error message.

1. **A pin lying mid-wire does not connect.** KiCad bonds a pin only at a wire *endpoint*.
   `layoutlib.Builder.save()` therefore splits every segment at each pin it crosses.
2. **Field angles are relative to the symbol body.** A 90°-rotated part needs field angle
   **270** to render horizontally; a 180° part needs **0** (180 renders upside-down).
   `sheetedit.place()` maps this automatically.
3. **`(mirror …)` is applied *after* rotation, not before.** Only visible on a symbol that is
   both mirrored and rotated. Getting it backwards silently swapped pin 1/pin 3 on the three
   `current_sense` source jumpers.
4. **Floating-point drift creates zero-length wire fragments** that break connectivity while
   looking correct in the file. All coordinates are rounded to 4 dp and degenerate segments
   dropped.

## ⚠ And the reason the netlist gate is not optional

A malformed token aborts KiCad's parse of the **whole sheet, silently**. Emitting
`(mirror {…})` (a Python dict passed where `'x'`/`'y'` was expected) made KiCad load the
first 29 symbols of `current_sense`, discard the remaining 65 plus every wire and label, and
**exit 0**. `conncheck` happily ignored the bad token and reported the sheet clean.

**Gate on the tool's own output, never on your own parse.** `sheetedit.place()` now asserts
`mirror in (None,'x','y')`, but the general lesson is the point.
