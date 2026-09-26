# fab/ — JLCPCB order package, FE_UFPR 4.0 (`v4.0-release`)


Rebuilt from the committed KiCad files by `sh tools/fab/make_package.sh [boards]` (needs `kicad-cli` 10, `python3`, `curl`, `zip`;
refuses to run while KiCad has the board or a sheet open). Everything here is derived — edit the design, not these files.

| File | Upload as | Notes |
|---|---|---|
| `FE_UFPR_4_0_gerbers.zip` | Gerber | 11 layers (F/In1/In2/B.Cu, F/B.Mask, F/B.SilkS, F/B.Paste, Edge.Cuts) + Excellon PTH/NPTH + drill maps + `.gbrjob`. Git-ignored; `gerbers/` holds the same files unzipped |
| `FE_UFPR_4_0_BOM.csv` | BOM | Comment, Designator, Footprint, LCSC Part # — consigned (J1–J5) and hand-solder lines already removed |
| `FE_UFPR_4_0_CPL.csv` | CPL | Designator, Mid X, Mid Y, Layer, Rotation. Origin = board bottom-left corner, Y up. Rotations = KiCad + `tools/fab/jlc_rotations.json` offsets — **confirm on JLC's placement preview before paying** (`S12_FAB_PACKAGE.md` §3) |
| `jlc_verify.md` / `.json` | — | live stock/price/Basic/value check of every LCSC line on the day the package was built; the header line is the **feeder fee over the Extended codes JLC places** (hand-soldered lines flagged `HAND_SOLDER`, no fee) |
| `kicad_bom.csv` | — | raw `kicad-cli` BOM (includes NOFIT/CONSIGNED placeholders) — the input the two files above were made from |
| **`FE_UFPR_4_0_HANDSOLDER_BOM.csv`** | — | **shopping list for everything the team solders** (bottom-side parts, the lines deselected at JLC, the five connectors): LCSC code where one exists, per-board quantity, quantity for the 2 assembled boards, order quantity for 3 boards (`make_package.sh [assembled]`, +1 spare board) |
| `jlc_order_2026-09-24.xlsx` | — | JLC's BOM-matching export of the 2026-09-24 order (64 lines selected, $92.68 parts) — **predates the 2026-09-26 fee cut; re-upload the BOM/CPL** |

## PCB options (JLC quote page)

| Option | Value | From |
|---|---|---|
| Layers / size / qty | **4** / **178.0 × 130.0 mm** / 5 PCBs | Edge.Cuts |
| Stackup | **JLC04161H-7628**, 1.6 mm, outer 1 oz, inner 0.5 oz | `S9_BOARD_SETUP.md` §3 (board file stackup) |
| Surface finish | **HASL lead-free** (board file); ENIG optional | |
| Min via | 0.6 / 0.3 mm (Default class), smallest drill 0.3 mm | `.kicad_pro` netclasses |
| Min track / clearance | 0.127 mm (designed ≥ 0.25 mm) | `.kicad_dru` |
| Impedance control | no | |
| Castellated holes / edge plating | no | |
| Order-number mark | your choice — no `JLCJLCJLCJLC` placeholder on the silk | |
| Solder mask / silk colour | team's choice (green is the fast lane) | |

## PCBA options

| Option | Value |
|---|---|
| Service | **Economic, single side (top)**; hand-soldered by the team: the 12 bottom parts (D2); deselected for cost on 2026-09-24, J20–J23 / U4 / U12–U17; deselected for the feeder fee on 2026-09-26, C1, F1–F3, L3, U8, R57/R105, R58/R129, Q1, U5–U7 — JLC places **14 Extended codes = $42.98** (edit `HAND=` in `make_package.sh` to change) |
| Qty | **2 assembled** (of 5 PCBs) |
| Tooling holes | let JLC add them (the board has no free edge strip reserved; check they land clear of the J2 overhang and the DT15 flanges in the preview) |
| Confirm parts placement | **yes** — this is the rotation/polarity check |
| Consigned parts | none from JLC's point of view (J1–J5 are on the team) |

## Not in the BOM — team supplies and solders

J1 Molex Mini-Fit Jr 5566-02A · J2 SUB-D 37 socket right-angle (UNC 4-40 jackscrews) · J3 DT15-12PA · J4 DT15-12PB ·
J5 DT15-08PD (vertical DEUTSCH headers + DT06 plugs, W12S/W8S wedgelocks, size-16 contacts — TE samples where available, 12× #4-20 Plastite screws) · 12 bottom-side SMD (R2, R3, D17, C119, C25–C28, R118, R119, C113, C120) · 4× 2×10 headers J20–J23 · U4 URA2415YMD-6WR3 · 6× OPA2376AIDR U12–U17 · **fee cut 2026-09-26:** C1 100 µF (polarised) · F1 · F2 · F3 · L3 CAN choke (pin 1) · U8 (pin 1) · Q1 TO-252 (tab on the +24 V pour — hot air or preheat) · U5–U7 UCC27524 (pin 1) · R57/R105 3.00 k 0.1 % · R58/R129 2.20 k 0.1 % (unmarked — one tape at a time). F1/Q1/C1 are the input power path: nothing powers up until they are fitted.
Codes and quantities: `FE_UFPR_4_0_HANDSOLDER_BOM.csv`. Solder jumper defaults after assembly: JP1 1-2, JP2 open, JP3/4/5 1-2, JP6 bridged
(`S12_FAB_PACKAGE.md` §4).
