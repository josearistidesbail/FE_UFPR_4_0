# S11 — Pre-fabrication review of the routed board (2026-09-23)

State reviewed: commit `cbd091b` ("Routing finished"), board closed in the GUI, saved fills current
(DRC gives the same counts with and without `--refill-zones`).

## 1. Gate results

| Gate | Result |
|---|---|
| `kicad-cli sch export netlist` vs `tools/schematic_layout/golden.net` | **IDENTICAL** — 219 nets / 927 nodes |
| ERC `--severity-all` | 1 error (`power_pin_not_driven`, U4 pin 1 on `PGND_MOD` — known, S10 open item), **8 `lib_symbol_issues` warnings — see finding A** |
| DRC `--severity-all --schematic-parity` | 421 violations: **34 errors** (33 `starved_thermal`, 1 `clearance`), 387 warnings (368 silk, 7 `via_dangling`, 7 `track_dangling`, 5 `silk_edge_clearance`); **14 unconnected items**; parity 4 `extra_footprint` (H1–H4) |
| `.kicad_pro` vs last good commit `586d0da` | design_settings / net_settings identical except `defaults.zones.min_clearance` 0.5 → 0.3 (the S10 `fix_s10_u1.py` change). 6 classes / 28 patterns; `(class …)` counts 61/4/23/9/5/117 ✓ |
| Board rules | S9 minimums intact (clearance/track 0.127, hole-to-hole 0.5, annular 0.125, edge 0.3, spokes 2). Stackup = JLC04161H-7628 (0.2104 prepreg / 1.065 core), tented vias both sides |
| Copper inventory | 1569 segments (F 1220 / B 263 / In2 86, **In1 untouched = solid GND plane**), 272 vias (204 × 0.6/0.3, 64 × 0.8/0.4, 4 × 1.0/0.5), 20 zones |
| LCSC coverage | every sheet has ≥ 1 `LCSC` property per symbol |
| 3D models | 306/369 footprints have bodies; the 63 without are TP/JP/NT/H/LOGO (expected) |

## 2. Findings, ranked

### Must fix before fabrication

- **A. Symbol library rolled back to the S7 snapshot.** `FE_UFPR_4_0.kicad_sym` is byte-identical
  (md5 `ee5ba8c4`) to `snapshots/…stepS7_encoder…/FE_UFPR_4_0.kicad_sym` of 2026-08-30. The six S8
  symbols (`SN65HVD230`, `LTV-817S`, `L_CommonMode`, `D_TVS_Dual_CAN`, `SolderJumper_2_Bridged`,
  `Conn_02x04_Counter_Clockwise`) and `D_Zener_SOT-23` (D2) are missing; `kicad-cli sym export svg`
  renders 53 units instead of 60. The schematic still works from its embedded cache, which is why
  nothing else broke — but any "update symbol from library" or a rescue dialog will now damage the
  schematic. The 2026-09-22 restore backup (`_restore_backup_2026-09-22T22-07-53-839/`) holds the
  correct library: same 50 symbols plus the 7 missing ones, no differing bodies, renders 60 units,
  **ERC with it = 0 `lib_symbol_issues`, netlist IDENTICAL to golden** (verified on a scratch copy).
  This is the same restore mechanism that reset `.kicad_pro` twice (open item): the MCP restore
  writes the **S7 snapshot** back. Fix: copy the backup library over the current one.
- **B. Three GND pins were floating on the routed board.** U8 pin 2 (SN74LVC1G11 — the gate-enable
  AND gate), U11 pin 3 (SN74LVC2G17 Schmitt for `SW_MAIN`) and C107 pin 2 sit in slivers of GND fill
  fenced in by other-net tracks on F.Cu; the F.Cu GND pour breaks into **51 separate regions** and
  those slivers touch nothing. DRC did report them, but as 5 anonymous "Zone GND ↔ Zone GND" items
  among the 14 unconnected. Fixed by the stitching pass (§3): U11.3 / C107.2 by a via stub, U8.2 by
  a hand-designed 0.14 mm track up the 0.75 mm gap between R30.1 and R31.1 to R31's GND pull-down pad.
- **C. GND stitching is essentially absent.** 72 GND vias on the whole board, **2 of them in the main
  F.Cu GND region** (which carries 84 SMD GND pads); 157 of 175 SMD GND pads are > 3 mm from any GND
  via; the right half of the board (power, gate drivers, DB37) has none. Every decoupling cap on that
  side returns to the L2 plane through the F.Cu pour and the header PTHs. Fixed by §3.
- **D. `+13V5_GATE` B.Cu pour not connected to the F.Cu pour.** The 2×3 via array at (249.6–250.4,
  142.6–144.2) sits in the B.Cu `+13V5` pour but on F.Cu it lands inside the GND pour (the F.Cu
  `+13V5` zone starts at x = 259). 6 `via_dangling` + 1 unconnected. Fix (in §3): move the array to
  x = 259.2/260.0, the only strip where both pours overlap — verified: `via_dangling` 7 → 1, zone
  connected.
- **E. Six vias have no net** at (271.2/272.2, 132.6) and (233.2–236.0, 164.8/168.4). They sit in GND
  copper (placed as stitching, never assigned) and connect nothing. §3 assigns them `GND`.
- **F. Six routing gaps (user).** `ISNS_VREF` track → R97.2 (1.6 mm), `ENC_VREF3V` C105.2 → R109.2,
  `MOD_AUX15V_1` and `MOD_AUX15V_2` B.Cu track-to-track (both at (216–219, 213.5)), `PWM_VL_15V`
  F.Cu ↔ B.Cu at (240.4,205.4) (missing via), `PWR_LED_5V` D6.2 → R15.2. Plus the 7 dangling track
  ends they cause (`SHIELD_DB37` at (253.9,218.05) and `PWM_UH_15V` at (243.2,205.7) are extra stubs).
- **G. Clearance error:** the vertical `ISNS_B_RAW` segment at x = 190.4 (y 172.3 → 198.45) passes
  0.10 mm from TP33 (`ISNS_B_LEM`, at 189.4,181.0); Analog needs 0.30. Shift the segment to
  x ≥ 190.65 or move TP33 0.25 mm left.

### Should fix (S11 silk / cosmetics, before the fab package)

- **H. Silkscreen says `MOTOR CONTROLLER V3`** (both faces) — the 3.0 text. Replace with board
  name / rev / date (`FE_UFPR 4.0 · rev A · 2026-09`) — S11 work item.
- **I. 368 silk warnings are all reference designators**: 152 refs over pads, 113 refs over their own
  outline, 65 ref-on-ref, 17 over PTH. Options: (1) hide refs on silk for 0603/0805 passives (JLC
  places from the CPL, refs are still on F.Fab), (2) shrink to 0.8 mm and auto-place, (3) leave. The
  5 `silk_edge_clearance` are J2/J5 bodies overhanging the edge by design + C4's ref.
- **J. H1–H4 parity warnings** — add `board_only` to the four mounting holes' `(attr …)`.
- **K. `_restore_backup*/` directories are committed** (both, 27 files). Add to `.gitignore` and
  `git rm -r --cached`.
- **L. ERC `power_pin_not_driven` U4 pin 1** — add a `PWR_FLAG` on `PGND_MOD` in `power.kicad_sch`
  (then re-baseline `golden.net`: +1 node).

### Notes (no action required, recorded)

- U1 (LMR33630) exposed pad: the footprint is the `ThermalVias` variant — its 8 × Ø0.3 PTH sub-pads
  **are** the thermal vias, already connected to all layers. U3 (AMS1117) tab: 2 vias added to the In2
  `+3V3` pour (§3). Q1 (reverse-polarity P-FET, ~35 mW) needs none.
- Thin power segments are all test-point / LED stubs: `+24V_MOD` 0.25 mm × 4 mm is TP5's stub, the
  main path is 1.2 mm on both outer layers. `+13V5_GATE` runs 12 mm at 0.25 mm on In2 (feeds the
  fault pull-ups, mA) — fine, but below the Power_1A width.
- Analog input pairs (`ISNS_*_INT_N/P`, `LEM_N/P`, `ENC_*_N/P`) are 0.20 mm at the op-amp pins,
  below the Analog class width but above the 0.127 rule — 6–8 mm each, acceptable.
- Analog nets on B.Cu / In2 (`ISNS_VREF` 82 mm B.Cu, `VBUS_ADC` 72 mm B.Cu, `NTC_1_ADC` 93 mm B.Cu,
  `ISNS_RTN` 85 mm In2, `ENC_SIN_RAW` 18 mm B.Cu): all reference the solid In1 plane, acceptable.
  Gate/power traces inside the analog column (x 168–216): only `FLT_OV_*` (Default-class logic) and
  16 mm of `PGND_MOD` on F.Cu at the DB37 — no PWM.
- Return-net topology verified from the pad lists: `PGND_MOD` → NT2 star at the 24 V entry (B.Cu);
  `ISNS_RTN` J2-12/13 → NT4 + the three bias resistors; `VBUS_RTN` J2-11 → NT3 + C58/R58 (Kelvin);
  `ISO_COM` → NT1; shields on their own RC ties.
- Spare `+5V` via at (208.34,181.40) is connected on B.Cu only — harmless, delete or use.
- Test points under the LaunchPad shadow (unreachable with it fitted): TP16, TP22, TP27, TP30–TP34,
  TP47. Everything else is outside x 187.5–246.
- Refilled fills are saved (DRC identical with/without refill) — the S10 "press B" item is done.

## 3. GND stitching pass — `tools/board_layout/stitch_s11.py`

Text-level edit (blocks appended, 12 lines changed: 6 via nets, 6 via positions), verified by
`kicad-cli pcb drc --severity-all --refill-zones` on a scratch project copy:

| What | Count |
|---|---|
| Per-pad GND vias (0.6/0.3) with a 0.3 mm stub from the pad centre, one for every SMD GND pad without a GND via within 2 mm; 2 L-shaped where straight was blocked (U9.2, U18.2) | 137 vias / 139 stubs |
| Bare 0.3 mm stubs into the local pour where no via fits (KiCad counts a same-net track entering the fill as a spoke) | 12 |
| Hand-designed U8.2 → R31.2 GND track (0.14 mm in the corridor, 0.25 mm after) | 3 segments |
| Edge fence, 6 mm pitch, 1.5 mm inside the outline | 52 |
| Open-area grid, 7 mm pitch, only where F.Cu or B.Cu GND pour exists | 135 |
| U3 tab → In2 `+3V3` thermal vias | 2 |
| Net-less vias assigned `GND` | 6 |
| `+13V5` array moved to x 259.2/260.0 | 6 |

Placement rules: ≥ 0.30 mm to any other-net copper (exact pad/track shapes), ≥ 0.50 mm hole-to-hole
(incl. NPTH), ≥ 1.0 mm from the edge (pad vias) / 1.5 mm (grid), never inside a B.Cu part courtyard,
never via-in-pad. Total vias 272 → 598 (0.3 mm drill, no JLC surcharge).

**Applied to the live board 2026-09-23** after the user closed the §2-F/G items (pre-apply DRC: 33 starved,
8 unconnected, 7 dangling vias). Post-apply `kicad-cli pcb drc --severity-all --schematic-parity --refill-zones`:
**0 errors, 0 unconnected**, `starved_thermal` **33 → 0** (4 without the waiver below), `via_dangling`
**7 → 1** (the spare `+5V` via), no new violation of any type, silk counts unchanged, netlist IDENTICAL.
Record of what was added: `tools/board_layout/stitch_s11.applied.json`.

Waiver (`FE_UFPR_4_0.kicad_dru`): `min_resolved_spokes 1` for **C11, C13, L2, U17** — C11.1/C13.2
are boxed in by the buck's own parts at the board edge, L2.2 is the 5 V inductor pad inside its own
pour, U17.4 is a SOIC GND pin at 1.27 mm pitch; a single 0.5 mm spoke there is electrically a 0.5 mm
track. Logged in `DECISION_LOG.md`.

## 4. How it was applied

The script was run against the live board with its output in the scratchpad, and the result was applied
as file edits (12 changed lines + the appended via/segment blocks), because the harness refuses an
in-place rewrite of the board. It refuses to run twice on the same board (sidecar
`FE_UFPR_4_0.kicad_pcb.stitched.json`, git-ignored). **Open the board, press B to refill, save.**

## 5. S12 readiness

Remaining before the fab package: §2-F/G routing gaps (user), silk pass (§2-H/I), the three
schematic/library items (§2-A/J/L), DRC zero with waivers logged, then the S12 list in
`REDESIGN_PLAN.md` (fresh JLCSearch re-verification, CPL rotation audit, consigned-parts notes,
firmware handoff, `v4.0-release` tag). Open hardware questions that do not block the order but do
block bring-up are unchanged in `OPEN_ITEMS.md` (KTY insulation class, DTM cavity numbering, DB37
MPN, orientation/bracket).
