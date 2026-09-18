# S10 — Pre-routing placement review (2026-09-17)

**Status:** the user hand re-placed the whole board on 2026-09-17 (commits d0a6293…c15b0ef) after S9.6.
This review validated it before routing. Section A was **fixed the same day** (see the pre-S10 entries in
`DECISION_LOG.md`); section B is the **user's tightening list before the first track**; section C is what
was verified good. Method: `kicad-cli 10.0.6` (`pcb drc --severity-all --schematic-parity`,
`sch erc --severity-all`, `sch export netlist` + `tools/schematic_layout/netcmp.py`, `pcb export ipcd356`)
plus `pcbnew` pad geometry. Coordinates are absolute KiCad mm; the outline is x 128–274, y 89.95–219.95.


Board file at HEAD c15b0ef ("Finished placing tps"). All checks run on a scratchpad copy with
kicad-cli 10.0.6 (`pcb drc --severity-all --schematic-parity`, `sch erc --severity-all`,
`sch export netlist` + netcmp vs golden.net, pcbnew python for pad geometry). No project file touched.

## A. Blocking — all FIXED 2026-09-17 (kept as the record)

| # | Finding | Evidence | Fix |
|---|---|---|---|
| 1 | **Outline not closed.** Top edge only runs 189.4→274.05; the segment 128→189.4 (61.4 mm, under J5) is missing. Right edge is skewed: top-right corner x=274.052, bottom-right x=274.0. H2 at x=269.07 vs H4 at 269.0. | DRC `invalid_outline` error | add `gr_line (128,89.95)→(189.4,89.95)`; make the right edge x=274.0 top to bottom (or 274.05 both); H2 → x=269.0 |
| 2 | **Netclass regression** (already OPEN_ITEMS #1). 5 classes / 24 patterns; the `CAN` class and the patterns `*PWM_*_3V3`, `*CAN_H*`, `*CAN_L*`, `*MOT_TEMP_*` are gone. | netlist `(class)`: Gate 17, Analog 60, Default 128, CAN 0 | re-add class CAN (0.40/0.30, via 0.8/0.4, dp 0.40/0.30, prio 15) + 4 patterns in `.kicad_pro` |
| 3 | **DB37 shell pads carry no net.** Footprint pads are named `SH`/`SH` (no net); symbol pins are `G1`/`G2` on `SHIELD_DB37`. The JP2/R35/C43 shield tie has nothing to land on. Pre-dates S9.6 (same in 9cf0c5a). | parity `net_conflict` ×2 | rename the two `SH` pads to `G1`, `G2` in `DSUB-37_Socket_Horizontal_P2.77x2.54mm_MountingHoles.kicad_mod`; Update Footprint on J2 |
| 4 | **Six symbols deleted from the project library** in commit d0a6293 (hunk @@ -10632,1919): SN65HVD230 (U18), LTV-817S (U19, U20), SolderJumper_2_Bridged (JP6), D_TVS_Dual_CAN (D13), Conn_02x04_Counter_Clockwise (J5), L_CommonMode (L3). Schematic runs on its embedded cache. | ERC 7 × `lib_symbol_issues` (was 0) | `git checkout 9cf0c5a -- FE_UFPR_4_0.kicad_sym` (that deletion is the only diff in the file); re-run ERC = 0 |
| 5 | **TP37 (ISO_COM) deleted from the board only**; TP20/TP23/TP54 deleted from both. golden.net is stale (3 nets each lost one TP node, nothing else). | parity `missing_footprint`; netcmp | decide TP37 (delete from schematic or re-place), then re-baseline golden.net |
| 6 | **Decision conflicts with OPEN_ITEMS (2026-09-17 team rule):** (a) 12 footprints on B.Cu — the 4 known (R2, R3, D17, C119) plus **8 new**: C25–C28 (U4 ±15 V caps, now under J3), R118/R119/C113 (J4 shield tie) and C120 (KTY 1 nF) under J4. Rule says add nothing to B.Cu; single-side assembly is being priced. (b) H5–H9 deleted (mid-edge holes + 3 LaunchPad standoffs) — rule says they stay until the orientation decision. | footprints.tsv; git diff refs | team/user call; if B.Cu is now allowed, log it in DECISION_LOG and update OPEN_ITEMS |

After the fixes: DRC 0 errors / 389 silk warnings / parity = H1–H4 `extra_footprint` only; ERC 0; netlist classes 61/4/23/9/5/117 = 219; `golden.net` re-baselined; IPC-D-356 lists `J2 -G1/-G2` on `SHIELD_DB37`; 59 symbol units and the DSUB footprint render. Item 6: the user **decided the 12 B.Cu parts stay** (two-sided assembly or hand-solder); H5–H9 remain pending with the orientation. Still open: `_restore_backup_2026-09-17T15-06-19-842/` is committed — `.gitignore` + `git rm -r --cached`.

## B. Placement to tighten (recommended, not blocking)

### B1. Connector-entry 1 nF caps are not at the connectors (systematic)
S4 (§ DB37 network "at the DB37 pins"), S6 §5.5 ("sit at their connector pins") and S7 ("1 nF C0G at the connector") all put the EMC cap at the pin. Only VBUS/NTC (C58/C60, 3–4 mm from J2-7/29) follow it.

| Net | Cap | Connector pin | Distance |
|---|---|---|---|
| PWM_UH/UL/VH/VL/WH/WL_15V | C37/C38/C39/C40/C41/C42 | J2-21/20/4/3/24/23 | 48 / 51 / 39 / 42 / 33 / 36 mm (at U5–U7) |
| FLT_OC_A/B/C, OT, OV | C44/C45/C46/C47/C48 | J2-2/22/5/6/16 | 11 / 17 / 25 / 32 / 11 mm |
| ISNS_A/B/C_RAW | C64/C70/C77 | J2-30/31/32 | 43 / 57 / 75 mm (at U12–U14 column) |
| LEM_A/B/C_M | C65/C72/C79 | J3-2/3/4 | 46 / 23 / 19 mm |
| ENC_SIN/COS_RAW | C99/C100 | J4-2/4 | 58 / 44 mm |

Suggestion: move each 1 nF (and its 10 k / 1 M partner where it is the entry R) next to the pin like C58/C60; TP38/TP39 already sit at J4 and TP10–TP15 at J2, so the slots exist.

### B2. ADC charge-bucket caps not at the header pins (target ≤ 3 mm; VBUS/NTC show it works)

| Net | Header pad | C (22 nF) | R (100 Ω) |
|---|---|---|---|
| ISNS_A_ADC | J22-16 | C68 25.5 mm | R74 23.0 |
| ISNS_C_ADC | J22-12 | C82 19.3 | R98 21.7 |
| ISNS_B_ADC | J22-14 | C75 11.2 | R86 10.6 |
| MOT_TEMP_REF_ADC | J20-12 | C122 24.5 | R131/R132 22–23 |
| MOT_TEMP_ADC | J20-10 | C121 20.8 | R130 19.2 |
| ENC_SIN_ADC | J20-18 | C107 12.7 | R112 12.5 |
| ENC_COS_ADC | J20-16 | C110 5.8 | R117 4.2 |
| ISNS_REF_A/B_ADC | J22-18/10 | C85/C86 6.8 | R101/R102 8.2 |
| VBUS_ADC / NTC_1_ADC | J20-14/8 | C59 2.9 / C61 2.8 | (R upstream, fine) |

ENC_SIN vs ENC_COS chains are also not geometrically matched (SIN's C107 at 12.7 mm, COS's C110 at 5.8 mm; SIN entry at x≈218, COS at x≈202). The R/C values match, which is what the firmware needs, but identical geometry is cheap insurance.

### B3. Decoupling and regulator loops
- **U18 (SN65HVD230)**: its 100 nF + 1 µF (C116/C117, S8 table) sit next to U21 at (244, 131); U18 VCC pin is 18–20 mm away with no cap nearer. Move both to U18 pin 3.
- **U1 (LMR33630)**: VIN pin → nearest ceramic C2 7.7 mm, C3 16.4 mm, no 100 nF at the pin (C4 is at Q1). SW pin → L1 6.7 mm, boot C8 4.0. Datasheet hot loop wants CIN within ~2 mm of VIN/PGND. Output: L1 → C11 4.9 / C9 6.5 mm (acceptable).
- **U2 (TPS62933)**: VIN → C15 3.8 / C14 6.3; SW → L2 4.0; L2 → C16 3.4. Acceptable; tighten C14 if room.
- **U15 (ISNS_VREF buffer)**: output pads to the nearest ISNS_VREF cap 27–31 mm — the channel column (R73/R85/R97, C67/C74/C81) is at x≈175, U15 at x≈204 on the other side of J22. Either move U15 into the column or accept a 30 mm buffered node.
- U17 ENC_VREF3V → C105 6.8–7.9 mm; U19/U20 +3V3 → C118 7–8 mm; U3 → C21 4.9 mm: fine.

### B4. Minor
- LEM channel order is reversed vs J3 (A network at y≈205, pin 2 at y≈164; C at the top) — the three LEM_x_M traces cross. Module channels and J22 pins are ordered A-bottom too, so flipping J3's side only means swapping the three strips.
- D9 (GATE_EN LED) at the bottom-right corner, R34 67 mm away at U8; put R34 beside D9. Bottom-edge LEDs face the module on a vertical board.
- Under the LaunchPad shadow (unreachable when fitted): JP1 ILOCK_SEL solder jumper, TP30–TP35. Nothing taller than 8 mm is under it (C1, L1, J1, U4, J3/J4 all outside).
- U4 (isolated DC/DC) is 120 mm from the 24 V entry; its +24V_PROT feed and its plane return cross the current-sense column. S9.6 floorplan choice, kept — route the feed along the bottom edge, not diagonally.
- Silk: 386 warnings (185 overlap, 199 over copper, 2 edge) — S11.

## C. What checks out
- 146 × 130 mm outline (translated to origin 128, 89.95); J20–J23 grid exactly 43.18 × 63.5 mm at board-local (66, 14); LaunchPad shadow 58.43 × 129.9 with the 17.9 mm overhang above the top edge; J20 pin 1 at the top (USB/service edge). J5 courtyard clears the shadow by 2.1 mm (S9.6 value).
- J2 row 1 at 9.40 mm from the bottom edge (S9 decision); gate pins 20–24/3/4 under the gate-driver block; analog pins 7/11–13/29–32 under NT4/C58/C60.
- All connectors on F.Cu; courtyard overlaps 0, malformed courtyards 0; no pad within 1 mm of the edge.
- Floorplan: encoder top-left (J4 → U16/U17 → J20), current sense bottom-left (J3 → U12–U14 → J22), power tree top-right (J1 → F1 → Q1 → C1/D1 → U1/L1 → U2/L2 → U3), gate drivers bottom-right over the DB37 gate pins, fault receivers bottom-right, ±15 V island bottom-left. NT2 star at the 24 V entry, NT3 at the Vbus divider, NT4 at J2-12/13, NT1 at U4.
- Schematic delta vs golden is exactly the three deleted test points; ERC would be 0 again once the six symbols are restored.
- 370 footprints; unconnected 499 = unrouted, expected.

## D. Applied 2026-09-17 — `tools/board_layout/tighten_s10.py` (user's go: "can you try and move them?")

The script holds every move as an explicit `{ref: (x, y, rot)}`, checks pad orientation (signal pad toward the
connector / header) and courtyard-bbox overlaps, and saves through `pcbnew`. Re-run it on a board at the
2026-09-17 state to reproduce; the user reviews in the GUI and reverts via git if disliked (commit `9802b1b`
is the pre-move state).

| Site | What moved | Result |
|---|---|---|
| DB37 strip | 16 entry caps (C37–C42, C44–C48, C58, C60, C64/C70/C77) in one row at y 207.5, each above its pin at 1.8 mm pitch; their shunt R (R24–R29, R42–R46, R67/R77/R89) in a row at y 204.3; TP10–TP15, TP22, TP47 in a row at y 201.1; F2 vertical beside C5 | cap-to-pin **2.3–6.6 mm** (was 11–75) |
| J3 | C65/C72/C79 at x 169.0 on the pin rows, outside the housing courtyard (like the user's C99/C100 at J4) | 7.6 mm (housing-limited; was 19–46) |
| J22 | cap column x 200.6 / 100 Ω column x 204.0, one cell per pin (C86/R102, C82/R98, C75/R86, C68/R74, C85/R101); U15 + C88 shifted 4.2 mm right | bucket **3.1 mm**, R 6.6 mm on all five (was 6.8–25.5) |
| J20 | same pattern: C61, C121/R130, C122/R131 (+R132), C59 (kept vertical), C110/R117, C107/R112; R113 up 1.8 mm, R115 right 0.1 mm, C104 under U16 | bucket **3.1 mm** on all six; **SIN and COS geometrically identical** |
| U18 | C116 into R121's slot beside pins 2/3, C117 below it, R121 above the IC | 100 nF **2.4 mm**, 1 µF 4.2 mm (was 18–20) |
| U1 | C2 beside VIN/GND (pad-to-pad 2.4 / 2.8 mm), C3 beside it, C11 down 2.3 mm | CIN 2.4 mm (was 7.7) |
| Misc | R34 beside D9 (was 67 mm); JP1 vertical between TP51/TP52, 0.7 mm outside the LaunchPad edge | — |

Gates after the move: `kicad-cli pcb drc --severity-all --schematic-parity` **0 errors**, 403 silk warnings
(199 overlap / 199 over copper / 5 edge — S11), parity = H1–H4 only, 0 courtyard overlaps; netlist identical
to `golden.net`; rendered and inspected at 49 px/mm.

**Residuals (not moved, by choice):** U15's buffered `ISNS_VREF` reaches its channel caps at ≈32 mm (the
channel column is full); U1 SW→L1 stays 6.7 mm (L1 is boxed in by U1 and C8); D9 stays at the bottom edge,
which faces the module on a vertical board; TP30–TP35 stay under the LaunchPad; the raw `ISNS_x_RAW` and
`VBUS/NTC` runs from J2 to their amplifiers are unchanged (the entry RC now sits at the pin, which was the point).
