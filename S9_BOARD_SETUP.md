# S9 — Board setup, stackup, rules, placement

**Status: S9 exit criteria met on 2026-09-02.** 369 footprints placed (360 from the schematic + 9
mounting holes), KiCad DRC **0 errors** at `--severity-all` (386 silkscreen warnings, all from
reference-designator text that S11's silkscreen pass owns; 499 unconnected items = the unrouted
netlist), schematic parity 0, no courtyard overlaps. This document is the deliverable: every
number on the board came from somewhere, and this is where.

The board file grew from an empty 2-layer A4 stub to a 4-layer, 146 × 130 mm board with a JLC
stackup, JLC-derived design rules, six netclasses and a complete starting placement. Nothing in
the schematic changed: the `kicad-cli` netlist still diffs **IDENTICAL** against `golden.net`
(220 nets / 914 nodes), so the S8 freeze stands.

---

## 1. Inputs that were verified this session (not inherited)

| Fact | Source | How it was checked |
|---|---|---|
| PrimeSTACK top-face mounting pattern | datasheet p.5 rendered at 400 dpi and cropped | four **Ø9.2** through-holes (Ø17 × 11 deep counterbores) on a **195 × 260** grid, four **M8 × 14 deep** threads on **143.2 × 242.6**, both centred on the 215 × 280 body; pixel-measured centres agree with the printed dimensions to <2 mm |
| LaunchPad physical arrangement | SPRUI77 Fig. 12 (top silk) | with the USB at the top and the component side up, **J1 is the outer-left column with pin 1 at the USB end**, J3 inner-left, J4 inner-right (pin 40 at top), J2 outer-right (pin 20 at top); site 2 (J5/J7/J8/J6) below in the same order — the arrangement 3.0's as-built grid already implied |
| LaunchPad outline and mounting holes | SPRUI77 Fig. 12/14 rendered at 300 dpi, blob analysis in numpy | scale from the 2.54 mm header pitch (7.81 px/mm; block-to-block 63.7 vs 63.5 mm and row-to-row 43.37 vs 43.18 mm confirm it); board **129.9 × 58.4 mm**; positions below, **±0.3 mm** |
| Socket handedness on the board | `get_component_pads J20` after the flip to B.Cu | pad 1 at (116, 64), pad 2 at (118.54, 64), pad 3 at (116, 66.54): odd column left, even column right, pins running toward the DB37 |
| JLCPCB 4-layer capabilities | jlcpcb.com/capabilities, fetched 2026-09-02 | table in §4 |
| JLC04161H-7628 stackup | jlcpcb.com/impedance | §3 |
| Netclass assignment | `kicad-cli sch export netlist` `(class …)` output | 55 Default / 58 Analog / 23 Gate / 9 Power_1A / 5 Power_3A / **4 CAN** |

### 1.1 LaunchPad geometry relative to J1 pin 1 (board orientation, USB up)

| Feature | x (mm) | y (mm) |
|---|---|---|
| board left / right edge | −6.43 | +52.0 |
| board USB end / far end | (y) −31.9 | +98.0 |
| corner holes | −3.87 and +49.5 | −29.3 and +95.3 |
| mid holes | +22.77 / +6.82 / +25.26 | −2.75 / +20.17 / +64.6 |
| J3 / J4 / J2 columns | +2.54 / +43.18 / +45.72 | — |

The far corner holes and the mid holes are what the board's standoffs use (§6). The USB end
overhangs the service edge by **17.9 mm**, which is what keeps the XDS100 connector reachable.

⚠ These come from a figure in a user's guide, not from a drawing. Before the order, put a
caliper on the real LaunchPad: hole-to-hole 124.6 × 53.4 mm on the corners, and J1-pin-1 to the
USB-end edge 31.9 mm. A 0.5 mm error still fits a Ø3.2 hole with a Ø5 standoff.

---

## 2. Outline and floorplan

**146 × 130 mm**, rectangular, origin at KiCad (50, 50). Board-local coordinates below are
measured from the top-left corner, x right, y down. 3.0 was 91.9 × 121.7; the growth is entirely
the two board-mounted DTM13 12-way receptacles (41.5 mm along the edge × 38.6 mm deep each),
which S2's floorplan predates.

```
   x=0        41   64 66  71   78          106 109  115              146
 y=0 ┌─H1──────────────[J5 8-way, flange off-board]────────[J1]──H2─┐
     │ J4 (enc) │ enc  │J20│bkt│  vehicle_io  │J21│  24 V entry     │
  12 │ 12-way   │front │   │   │  CAN, optos  │   │  F1 Q1 D1 C1    │
  46 │ key B    │-end  │   │ lp│              │   │  U1 13.5 V buck │
  54 H5─────────┼──────┼───┼───┴──────────────┼───┤  U2 5 V buck   H6
     │ J3 (LEM) │ cur- │   │      (spare)     │   │  U3 3V3         │
  78 │ 12-way   │rent  │J22│cs_ref│gate_logic │J23│  U5 U6 U7       │
     │ key A    │sense │   │      │  pull-downs│   │  gate drivers   │
 100 ├──────────┴──────┴───┴──────┴───────────┴───┴─────────────────┤
     │ U4 ±15 V │ iso │H9│ms_ov│ms_div│ fault receivers │ (spare)   │
 111 │ 25×25    │caps │  │ DB37 EMC / aux TPs │ 10k+1nF networks │JP2│
 119 ├──────────┴─────┴──┴────────────────────┴──────────────────┴───┤
 130 └─H3─────────────[ J2 DB37, pin 1 right, gate pins right ]────H4─┘
```

Why each thing is where it is:

- **Sockets J20–J23** on the bottom, unrotated, J1-pin-1 at **(66, 14)**, grid 43.18 × 63.5.
  The LaunchPad envelope (x 59.6…118, y −17.9…112) is then clear of every other through-hole
  part: the U4 pins at x ≤ 41, the DB37 rows at y ≥ 120.6, J3/J4 at x ≤ 39.
- **J4 (encoder) top-left, J3 (LEM) bottom-left**, mating faces 1.0 mm inside the left edge,
  cables exit left. Order chosen by the ADC pins: `ENC_SIN/COS_ADC` are J20 pads 16/18 (y 32–34),
  the five current-sense pins are J22 pads 10–18 (y 89–98). Each front-end sits beside its own
  connector *and* its own socket. The DTM housings cover 41 × 38 mm each; nothing goes under them
  on the top side.
- **J5 (vehicle 8-way)** on the top edge with its `Dwgs.User` edge line on y = 0: pin field
  x 65.7…78.3, CAN pins 1/8 at the right end next to `vehicle_io`, the 68.6 mm flange hangs
  off-board from x 21 to 90. It hangs 2.8 mm below the board's bottom face; the LaunchPad's top
  surface is 11 mm below (2.5 mm header base + 8.5 mm socket), so nothing on the LaunchPad reaches
  it — and JP1–JP3 shunts, the tallest candidates, are removed by S2's jumper policy anyway.
- **J2 (DB37)** on the bottom edge, rotation 0, pin 1 at x = 116: this puts the six gate pins
  (3/4/20/21/23/24, px 0…−12.5) and four of the five fault pins under the bottom-right corner,
  beside J23 (which carries `PWM_*_3V3` on its odd pads) and the gate drivers, and the analog
  pins (7, 11–13, 29–32) at x 77…90, above the isolated island and the current-sense strip.
  Pin-row-1-to-edge is KiCad's 9.40 mm; 3.0's as-built part sat 12.07 mm from the edge (§9).
- **Power column** x 115…145: entry (Mini-Fit J1 at the top-right corner, F1, Q1, D1/D2, C1),
  then U1, U2, U3 top-down, then U5–U7 at y 85…102 — right of J23 and 10–20 mm from the DB37
  gate pins. The datasheet 10 k + 1 nF networks and the 100 Ω series resistors sit in a band
  directly above the gate pins (`db_in`, x 100…126, y 111…119).
- **U4 (±15 V)** bottom-left, rotation 180 so the 24 V input pins face the board interior and the
  ±15 V/ISO_COM pins face J3's pin field 20 mm above it. Its input/output caps and `NT1` are in
  the 15 mm strip beside it.
- **Module status** splits by pin: `U11` (FLT_OV from pin 16, x 70.5) and the Vbus/NTC dividers
  (pins 7/11/29, x 84–95) at the left of the bottom band; `U9`/`U10` and their dividers at the
  fault pins (x 98–109), outputs 10–15 mm from J23's even pads 14–20. The Vbus/NTC charge buckets
  are at J20 pads 8/14, on the right side of J20 where the even pads are.
- **Current sense** in the left strip x 41…64, y 47…102: LEM burdens and stages nearest J3, the
  three OPA2376 in a column, the source jumpers and ADC buckets at the bottom next to J22. The
  internal-sensor inputs (`ISNS_x_RAW` + `ISNS_RTN`) come 60–80 mm from the DB37 along the
  bottom band — S11 routes them as pairs. `U15` (reference buffer) and the two reference buckets
  are on the right of J22 because pads 10/18 are even (right-side) pads.
- **Encoder** in the left strip y 12…46, ferrite and supply caps at the top nearest J4, the
  clamps and buckets at the bottom nearest J20's pads 16/18.
- **`vehicle_io`** x 78…106, y 15…44 under J5, between the two upper sockets; its four GPIO
  nets land on J21 (pads 9/11/14/20) immediately to its right.
- **The 2×10 socket strips are barriers.** A signal cannot cross a socket column between pads
  (0.84 mm gap at the Analog clearance); it goes round the socket end. Every block was placed so
  that its traffic reaches its socket pads *without* crossing a column: analog on the left of
  J20/J22, buckets for even pads on the right, gate/CAN/switch logic left of J21/J23.
- The centre (x 71…103, y 50…83) is deliberately empty except the LaunchPad 5 V feed `D12`.
  It is where the `VBUS_DIV`/`NTC_DIV` traces run from the DB37 to J20 and where S10 puts the
  plane stitching.

---

## 3. Stackup — JLC04161H-7628, encoded in the board file

| Layer | Material | Thickness | εr |
|---|---|---|---|
| F.Cu | 1 oz copper | 0.035 |  |
| prepreg | 7628 × 1 | 0.2104 | 4.4 |
| In1.Cu (**GND plane**, L2) | 0.5 oz | 0.0152 |  |
| core | FR-4 | 1.065 | 4.6 |
| In2.Cu (**power**, L3) | 0.5 oz | 0.0152 |  |
| prepreg | 7628 × 1 | 0.2104 | 4.4 |
| B.Cu | 1 oz copper | 0.035 |  |

Total 1.586 → nominal 1.6 mm, HASL lead-free. Layer roles follow S0: signal / GND / power /
signal. The 0.21 mm to the ground plane is what makes L1 traces referenced tightly; the 1.07 mm
core between the two inner layers means L3 pours are **not** a good return path for L4 — S10/S11
keep the analog signals on L1 over the L2 plane.

---

## 4. Design rules from JLCPCB's 4-layer capability page

| JLC capability (4-layer) | JLC value | Board rule | Margin |
|---|---|---|---|
| trace / space, 1 oz outer & 0.5 oz inner | 0.09 / 0.09 mm | `min_track_width` 0.127, `min_clearance` 0.127 | 1.4× |
| via hole (no extra charge) / via diameter | 0.20 / 0.30 mm | `min_through_hole_diameter` 0.20, `min_via_diameter` 0.50, annular 0.125 | 0.30/0.60 via is the default |
| hole to copper (different net) | 0.20 mm | `min_hole_clearance` 0.20 | — |
| hole to hole | 0.45–0.50 mm | `min_hole_to_hole` 0.50 | — |
| copper to routed edge | 0.20 mm | `min_copper_edge_clearance` 0.30 | 1.5× |
| solder-mask bridge | 0.10 mm | `solder_mask_min_width` 0.10 | — |
| silk line / text height | 0.15 mm / 1.0 mm | `min_silk_clearance` 0.15, `min_text_height` 1.0, thickness 0.15 | — |
| PTH annular ring | 0.15 min, 0.20 recommended | pads ≥ 1.6 on 1.0 drills everywhere | — |

The netclass *values* were kept (they are routing discipline, comfortably above every floor),
but their current rating was re-derived with IPC-2221 at ΔT = 20 °C so S10 knows what they buy:

| Class | Track | Outer 1 oz | Inner 0.5 oz | Verdict |
|---|---|---|---|---|
| Default | 0.25 | 1.2 A | 0.6 A | signals |
| Analog | 0.30 | 1.4 A | 0.7 A | signals |
| Gate | 0.40 | 1.7 A | 0.8 A | 5 A peaks for tens of ns, fine |
| Power_1A | 0.50 | 2.0 A | **0.6 A** | rails carry ≤0.5 A each; on L3 use pours ≥ 1 mm |
| Power_3A | 1.20 | 3.7 A | **1.1 A** | `+24V_IN/PROT/MOD`, `PGND_MOD`, `GND`: **outer layers or ≥ 5 mm pours on L3**, never a 1.2 mm inner trace |
| CAN (new) | 0.40 / gap 0.30 | — | — | routed as a pair U18 → L3 → J5 |

Two netclass changes, both verified in the `kicad-cli` netlist (not by reading the pattern list):

- **`*PWM_*_3V3` → Gate.** S8 found the MCU-side half of the gate bus on Default. It now shares
  the class of its `_DRV` and `_15V` halves so S10 applies one rule to the whole bus (Gate 17 → 23 nets).
- **New class `CAN`** (0.40 track, 0.30 clearance, 0.8/0.4 via, diff-pair 0.40/0.30, priority 15)
  on `*CAN_H*` / `*CAN_L*` — 4 nets. Closes the S8 open item.

One project DRC rule, `FE_UFPR_4_0.kicad_dru`: pad-to-pad *inside* `U2` (TPS62933F, SOT-583,
0.5 mm pitch = 0.20 mm gap) relaxes to 0.15 mm. Without it the Power_1A/Power_3A clearances flag
the package's own pads. 0.15 mm is still 1.6× JLC's floor; the rule is scoped to that one
footprint so it cannot leak into routing.

---

## 5. Placement tooling

`tools/board_layout/place_s9.py` regenerates the placement from the floorplan: it reads the
golden netlist, derives block membership from **net families** (`ISNS_A_*`, `FLT_OV_*`,
`PWR_U1_*`, …) rather than from reference numbers — the first pass that guessed by refdes put
seven parts nowhere and overflowed five blocks — packs each block with a shelf packer over the
library courtyards, and emits `moves.json` for the MCP's `batch_move_components`. Dense blocks
pack tallest-first (`sort=True`), which trades functional adjacency for fit; the anchor parts
(sockets, connectors, U4) are fixed by hand. Leftovers fall back to the block holding most of
their net-neighbours, then to a rail → block map.

It is a **starting placement**. S10/S11 will move parts within their blocks freely; the value of
the script is that the block *structure* — which edge, which side of which socket, what is next
to what — is written down and reproducible.

---

## 6. Mounting

**Board holes (M3, Ø3.2 NPTH, no pad):** `H1`–`H4` at the corners (5, 5) / (141, 5) / (5, 125)
/ (141, 125), `H5` mid-left (5, 54) in the 7 mm gap between J4 and J3, `H6` mid-right (141, 62.5)
between the two bucks. No pad and no plane connection: with the floating 24 V supply (S8) the
board must not be bonded to the chassis through its screws any more than through `JP2`.

**LaunchPad standoffs (Ø3.2 NPTH):** `H7` (88.77, 11.25), `H8` (91.26, 78.6), `H9` (62.13, 109.3)
= the LaunchPad's near-centre, mid and far-left-corner holes (§1.1). The far-right corner hole
lands on the fault-receiver/gate-driver corner and was dropped: three standoffs plus 80 socket
pins is ample. Standoff length = 11 mm (2.5 mm header base + 8.5 mm socket insulator) — **the
socket height is still unverified for `C5116528`** (S8 open item; it sets this number).

**PrimeSTACK:** the top face offers four M8 threads on 143.2 × 242.6 and four Ø9.2 through-holes
on 195 × 260. Both grids dwarf the board, so ARCHITECTURE.md §7's **adapter plate stays the
plan**: a laser-cut plate picks up two or four M8 points and carries the board's own M3 pattern.
⚠ The same top face carries the phase and DC busbar terminals (M6/M8, the 155/93/31 and 62/62
patterns on the drawing). The plate must hold the board above them with HV-grade clearance, and
the DB37 harness arrives at the module's side face (X1 in the side view) — both are the user's
mechanical call, not the board's.

---

## 7. Checks

| Check | Result |
|---|---|
| `kicad-cli pcb drc --severity-all` | **0 errors**; 386 warnings, all silkscreen (199 `silk_overlap`, 183 `silk_over_copper`, 4 `silk_edge_clearance`); 499 unconnected items (nothing routed); parity 0 |
| courtyard overlaps (KiCad) | none. The MCP's own checker reported three, all artefacts of using a bounding box for J5's L-shaped courtyard |
| netlist vs `golden.net` | IDENTICAL, 220 nets / 914 nodes |
| airwire sanity (18 key nets) | `PWM_*_15V` 27–28 mm, `VBUS_SNS_RAW` 31, `NTC_1_RAW` 22, `+24V_MOD` 19, `ISNS_A_RAW` 83 and `ISNS_RTN` 75 (the DB37-to-strip run, routed as a pair in S11), `PGND_MOD` 99 (DB37 → entry star, by design), `+15V_ISO` 106 |

Found and fixed on the way: **J5's courtyard was two overlapping rectangles**, which KiCad
reports as *malformed (self-intersecting)* — and a malformed courtyard is silently excluded from
the overlap test, so the S8 footprint would never have flagged a collision. It is now one
eight-vertex polygon in the library and in the board's embedded copy.

---

## 8. What S10 inherits

- L2 = solid GND; L3 = power islands: `+24V_PROT` down the right column, `+13V5_GATE` to the
  driver corner, `+5V` to the analog strip and the two `+5V_LP` pins, `+3V3` local, ±15 V only
  inside the island and along J3. `PGND_MOD` on its own copper from the DB37 to `NT2` (S4).
- Buck hot loops per the S3 sheet notes: `U1`–`L1`–`C9/C10` and `U2`–`L2`–`C14` are already
  adjacent; rotate/nudge inside the block, do not move them out of it.
- Gate bus: six matched-length runs U5–U7 → `R18–R23` → `R24–R29`/`C37–C42` → DB37, all within
  25 mm. Keep them on L1 over the plane.
- Nothing crosses a socket column. If a route must, it goes around the socket end.

## 9. Open items created or touched by S9

- **[user] LaunchPad hole positions** — confirm §1.1 on the real board before ordering.
- **[user] DB37 MPN** decides the edge offset: KiCad's footprint puts the edge 9.40 mm from
  pin row 1; 3.0's as-built part sat at 12.07 mm. A part with the longer offset simply protrudes
  2.7 mm; a part with the shorter one on a 12.07 board would be recessed and its plug hood would
  hit the edge — which is why 9.40 was chosen.
- **[user] J5 flange bracket** — still nothing retains it but its eight pins; the four slots are
  off-board at x 25.5 and 49.7 (flange centre 16.6 mm right of the pin field), z ±15.4.
- **[user / S12] socket insulator height** for `C5116528` sets the 11 mm standoff length.
- **[S11] silkscreen**: 386 warnings from auto-placed reference text; the pass that fixes them
  also adds the jumper tables, connector pinouts and the JP2 warning.
- **[S10] `Power_3A` on inner layers** is 1.1 A at 1.2 mm — pours only.
