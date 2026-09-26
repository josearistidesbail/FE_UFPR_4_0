# S12 — DFM, BOM/CPL, fabrication package, handoff (2026-09-23)

Exit criteria (`REDESIGN_PLAN.md` §S12): order-ready fab package · BOM with zero unvetted lines · handoff doc complete · tag `v4.0-release`.
Companion documents: [`S12_FIRMWARE_HANDOFF.md`](S12_FIRMWARE_HANDOFF.md) (the `control_v2_pinmap.md` answers),
[`fab/README.md`](fab/README.md) (what to upload and which options to tick), `tools/fab/` (the scripts that rebuild `fab/`).

## 0. Gates re-run before anything else

| Gate | Result |
|---|---|
| `kicad-cli pcb drc --severity-all --schematic-parity --refill-zones` | 0 errors, 0 unconnected, 0 parity; 7 warnings (4 `silk_edge_clearance` J2/J5 overhang, 3 `silk_overlap` R24/J2 — by design, S11) |
| `kicad-cli sch erc --severity-all` | 0 |
| `netcmp.py golden.net` | IDENTICAL (219 nets / 927 nodes) |

## 1. BOM audit — one defect found, otherwise clean

**🛑 `C22936` is 1 Ω, not 1 MΩ, and was still on R35, R67, R77, R89, R104, R118.** Logged as a defect on 2026-09-17 with
"the six symbols are not yet changed" — and they never were. The re-verification script passed the line because it only
compared package (0603 = 0603); the fix is `C22935` (`0603WAF1004T5E`, 1 MΩ, Basic, 2.6 M stock). Consequence had it
shipped: `SHIELD_DB37` / `SHIELD_LEM` / `SHIELD_ENC` hard-tied to GND (3.0's harness ground loop back) and the module's
three 5 mA-limited current-sensor outputs shorted to ground. Fixed by `tools/fab/fix_c22936.sh` (six `LCSC` property lines in the sheets **and the same six footprint fields on the board** — DRC
`--schematic-parity` caught the board half; no connectivity change — netlist stays identical). `jlc_verify.py` now compares the BOM value with JLC's description
(`VALUE_MISMATCH`) so the next adjacent-code slip is caught by the script, not by luck.

**Re-verification (live JLCSearch, 2026-09-23, 5 boards) after the fix:** 133 BOM lines → 71 real LCSC lines / 63 codes,
0 NOT_FOUND, 0 OUT_OF_STOCK, 0 LOW_STOCK, 0 VALUE_MISMATCH, 1 PACKAGE_MISMATCH (U1 `LMR33630ADDAR`: JLC "ESOP-8" = KiCad
HSOP-8, naming only). 37 Basic/Preferred lines; **33 Extended lines = 30 codes × $3.07 = $92.10 feeder fees**; parts
**$140.62 / 5 boards**. Placeholders: `NOFIT` × 58 (JP1–JP6, NT1–NT4, 48 TP), `CONSIGNED` × 5 (J1–J5). Table: `fab/jlc_verify.md`
and `JLC_PARTS.md` §S12. Watch: U4 `C5369735` **304** in stock (was 362 on the prep dry-run the same morning), `C77033` 2.2 nF C0G 2 265 for 50.

## 2. Decisions this session (each also in `DECISION_LOG.md`)

| # | Decision | Chosen | Why |
|---|---|---|---|
| D1 | U4 URA2415YMD-6WR3: JLC-place or consign | **JLC-place** (user, 2026-09-23) → **reversed at order time 2026-09-24 (user): deselected at JLC for cost, bought at LCSC (`C5369735`) and hand-soldered.** Same for **J20–J23** (headers) and **U12–U17 OPA2376** | 304 in stock covers 5 boards; consigning saves ≈ $41 but adds a THT hand-solder and a Mouser line for a part JLC already has. If stock is 0 on order day: consign and hand-solder |
| D2 | 12 B.Cu SMD parts (R2/R3, D17/C119, C25–C28, R118/R119/C113/C120) | **Economic single-side PCBA + hand-solder the 12** (user, 2026-09-23; dropped from the BOM/CPL by `make_package.sh` via `--hand-solder`) | Standard two-sided costs +$62.12 flat (2026-09-17 quote) for 12 0603/0805/SMA parts on 5 boards; the team already hand-solders 72 THT joints per board |
| D8 | JLC feeder fee (2026-09-26, user) | **27 → 14 Extended codes ($82.89 → $42.98):** R10/R11 → 68 k/13 k Basic, D1 → SMCJ26CA Preferred, Vbus R57/R58 → 3.00 k/2.20 k (existing 0.1 % lines), and C1, F1–F3, L3, U8, R57/R105, R58/R129, Q1, U5–U7 hand-soldered (`HAND=`) | the fee is $3.07 per Extended code JLC places, once per order; `JLC_PARTS.md` §Feeder-fee reduction has the audit and the options not taken |
| D3 | `HW_NAME` | **`"FE_UFPR_4_0"`** | matches the KiCad project and the tag; firmware side bumps it in the same commit as the §13 defines |
| D4 | Conformal coating | **none before bring-up**; team-applied acrylic after the first article passes, masking DB37, DTM cavities, LaunchPad headers, all TPs and JP1–JP6 | JLC PCBA offers no coating; coating before bring-up hides every test point and jumper the bring-up sheet needs |
| D7 | JLC BOM matching (`fab/jlc_order_2026-09-24.xlsx`) | 70 lines / 289 designators matched 1:1 to our codes, no substitutions; 64 selected, est. parts **$92.68**; six "Unconfirmed" warnings came from D4–D9 being six lines for one part (our BOM grouped by value) → generator now groups by footprint + LCSC (59 lines, 278 CPL parts) | JLC priced each duplicate line at the full 30 pcs; the warnings must otherwise be confirmed by hand |
| D5 | Package format | `kicad-cli` exports + `tools/fab/` scripts, committed in `fab/` (gerbers unzipped + BOM + CPL + verify record); the zip is rebuilt by `make_package.sh` and git-ignored | reproducible from the commit; no plugin dependency |
| D6 | CPL coordinates | rebased to the board's bottom-left corner (`--origin 127.95,219.9`), rotations normalised to 0–360 | the board has no aux origin; page-origin coordinates (x 128–274, y −90…−220) import but make JLC's preview useless for the rotation check |

## 3. CPL rotation / polarity audit

JLC's zero-rotation differs from KiCad's for most non-passive packages. `tools/fab/jlc_rotations.json` carries the offset per
footprint prefix; it was **seeded from the JLCKicadTools community table** (KiCad-standard footprints) and **must be confirmed
on JLC's placement preview** (order page → PCBA → "Component placement") before the order is paid — the preview is the only
authoritative source, and JLC's DFM engineers also send a confirmation email for anything that looks off. Passives (0603–1206 R/C/L) need nothing.

| Footprint | Refs | Seed offset | Source | Preview check |
|---|---|---|---|---|
| `SOT-23` (3-pin) | D2, D10, D11, D13, D18 | −90 | community | pin 1 / cathode (BAT54S common cathode pin 3) |
| `SOT-23-6` | U8, U9, U10, U11, U21 | −90 | community regex `^SOT-23` | **6-pin may differ from 3-pin** — check |
| `SOIC-8_3.9x4.9mm_P1.27mm` | U5–U7, U12–U18 | 270 | community | pin-1 dot |
| `Texas_HSOP-8-1EP_…` (U1, JLC "ESOP-8") | U1 | 270 | assumed = SOIC-8 | check |
| `SOT-223-3_TabPin2` | U3 | 180 | community | tab |
| `SOT-583-8` | U2 | 0 | **unverified** | pin 1 |
| `TO-252-2` | Q1 | 0 | **unverified** | tab (pad 2) |
| `CP_Elec_8x10.5` | C1 | 180 | community | negative stripe |
| `D_SMC` / `D_SMA` / `D_SOD-123` | D1 / D12, D16, **D17 (bottom)** / D14, D15 | 0 | **unverified** | cathode band = KiCad pad 1 (left at 0°) |
| `LED_0603_1608Metric` | D4–D9 | 0 | **unverified** | cathode = pad 1 |
| `Optocoupler_LTV-817S_SMD-4P` | U19, U20 | 0 | community `^SOP-4_` = 0 | pin-1 dot |
| `L_CommonMode_TDK_ACT45B` | L3 | 0 | symmetric pairs | — |
| fuses, inductors, headers | F1–F3, L1, L2, J20–J23 | 0 | non-polar / symmetric | — |
| `Converter_DCDC_Mornsun_URA-YMD-6WR3_THT` | U4 | 0 | **unverified** (only if D1 = JLC-place) | pin 1 |

Bottom side: 12 parts; the only polarised one is **D17** (SMA TVS) — check it separately, JLC's bottom-side rotation convention is not the top-side one mirrored.
After the preview: write the confirmed offsets into `jlc_rotations.json`, re-run `make_package.sh`, re-upload the CPL, mark the table "confirmed <date>".

## 4. Assembly notes (goes with the order; also `fab/README.md`)

- **Consigned / hand-solder (team):** J1 Molex Mini-Fit Jr 5566-02A · J2 SUB-D 37 socket, right-angle, UNC 4-40 jackscrews (MPN still open, `OPEN_ITEMS.md`) · J3 DTM13-12PA-R005 (key A, LEM) · J4 DTM13-12PB-R005 (key B, encoder) · J5 DTM13-08PA-R004 (vehicle) · the 12 B.Cu parts (D2) · **deselected at JLC on 2026-09-24 for cost: J20–J23 headers, U4 URA2415YMD-6WR3, U12–U17 OPA2376 ×6** · **deselected on 2026-09-26 for the feeder fee (D8): C1, F1, F2, F3, L3, U8, R57, R105, R58, R129, Q1, U5–U7** — 42 hand-soldered parts per board. Q1's tab sits on the +24 V pour (hot air or preheat); C1 is polarised; check pin 1 on U5–U8 and L3; the four 0.1 % resistors are unmarked (one tape at a time); F1/Q1/C1 are the input power path, so fit them before the bring-up sheet's first power-on. **Shopping list with LCSC codes: `fab/FE_UFPR_4_0_HANDSOLDER_BOM.csv`** — 2 boards assembled, order quantities for 3 (regenerated by `make_package.sh`; user 2026-09-24). Harness side: DTM06-12SA/-12SB/-08SA plugs, size-20 contacts, W12S/W8S wedgelocks. The three LEM LA 100-P live on the remote sensor board (no burden resistors there — both burdens per channel are on this board).
- **Solder jumpers — factory state (all `NOFIT` = bare pads, set by hand after assembly):**

  | Jumper | Silk | Default | Meaning |
  |---|---|---|---|
  | JP1 | `ILOCK_SEL` (3-pad) | **bridge 1-2** | gate enable requires the cockpit main switch; 2-3 = bench bypass to +3V3. **Never open: U8's C input would float** |
  | JP2 | `SHLD_TIE` | **open** | DB37 shield to GND through 1 nF ‖ 1 MΩ only; bridge = hard tie |
  | JP3 / JP4 / JP5 | `SRC SEL A/B/C` (3-pad) | **bridge 1-2** = internal module sensor | 2-3 = LEM path. **Never open: the ADC input floats.** Firmware constant must follow (`S12_FIRMWARE_HANDOFF.md` §6) |
  | JP6 | `CAN TERM` | **bridged** (footprint is the bridged variant) | 120 Ω on the bus; cut if the bus is terminated elsewhere |

- **Mounting:** H1–H4 Ø4.3 mm for M4 ISO 7380 button heads; **no Ø9 washer at H2** (Q1's tab pad is 0.1 mm from a washer's edge). Orientation (vertical vs horizontal) is a bracket question, not a PCB one.
- **LaunchPad jumpers (`ARCHITECTURE.md`):** JP1/JP2/JP3 **out**, JP4/JP5 **in**, JP6 **out**. Header 3V3 pins are unconnected on the board by design.
- **Silk:** 49 passive references are hidden (36 R, 13 C); F.Fab and the CPL carry them. Test points show their **net name**; TP2 (`+13V5_GATE`), TP28 (`FLT_OV_3V3`) and TP32 (`ISNS_B_INT`) show `TPxx` (label would not fit). Map: §6.
- **Order-number text:** none placed on the board; either accept JLC's mark or tick "Remove Order Number" (paid).

## 5. Bring-up sheet — board side first, then `production_bringup.md` steps 1–10

**A. Rails, nothing plugged but 24 V at J1** (LEDs D4–D8 mirror the rails): TP1 `+24V_PROT` ≈ 24 V → TP5 `+24V_MOD` → TP2 (`+13V5_GATE`) 13.5 V → TP3 `+5V` → TP4 `+3V3` → TP6/TP7 `±15V_ISO` vs TP8 `ISO_COM` → TP45 `+5V_LP` ≈ 4.6 V (Schottky). Current draw with no LaunchPad: record it. Then fit the LaunchPad (jumpers as above), USB only: the board rails must **not** rise.

**B. Enable chain, DB37 unplugged, LaunchPad running:** `BENCH_NO_POWER_STAGE 1`. GPIO66 + GPIO131 HIGH → TP16 `GATE_EN_3V3` HIGH and D9 lit only when JP1 is at 2-3 **or** 12 V is applied to the main-switch input (J5 cavity 3 +, cavity 6 return; start = cavities 4 / 5); TP51 `SW_MAIN_3V3` / TP52 `SW_START_3V3` follow the cockpit inputs. Either enable LOW → TP16 LOW.

**C. Gate signals, DB37 unplugged:** `ol_run` open loop → scope TP10–TP15 (silk `PWM 15V`: UH UL VH VL WH WL): 0 / 13 V levels, complementary pairs, 1500 ns dead-band both edges, 120° phasing. Check channel-to-channel skew ≪ 1500 ns.

**D. Fault receivers:** DB37 unplugged → TP24–TP28 all **HIGH** (pulled up = fault) and firmware shows all five module faults with `MODULE_FAULT_ACTIVE_LOW 0`. Plug the aux-powered module (no DC link) → all LOW. Force one (brown the aux below 18 V → OV/pin 16 flag) → TP28 HIGH, state → FAULT (step 9 of the firmware sequence later checks the HW trip path).

**E. Analog, module aux-powered, no DC link, motor still:** TP36 `ISNS_VREF` = 1.4685 ± 0.005 V; TP30/32/34 `ISNS_x_INT` ≈ 1.50 V (bench item #3: record the exact value — it *is* the module bias × 0.6); TP31/33/35 `ISNS_x_LEM` = TP36 with the LEM board plugged and no current; ADC codes ≈ 2048 / 2005. TP19 `VBUS` vs TP21 `RTN` ≈ 0 with no link, then a bench DC link (24–48 V): note the sensor floor and set `VBUS_OFFSET_CODE`. TP22 `NTC` ≈ module NTC at room temp (10 V = 82 °C — expect well below). TP53 `MOT_TEMP_RAW` ≈ 1.57 V with a KTY81-210 at 25 °C (2000 Ω); ADCINA3 = 1.65 V. TP38/TP39 `ENC_*_RAW` and TP40/TP41 `ENC_*_ADC`: bias 1.49 V, amplitude 1.28 V, SIN/COS within 1 %, while turning the shaft by hand.

**F. Then `production_bringup.md` "Ordered sequence" 1–10 at low DC-link voltage**, `BENCH_NO_POWER_STAGE 0` before step 5, HV only after all pass. The bench items in `S12_FIRMWARE_HANDOFF.md` §14 get answered along the way.

## 6. Test points — silk label ↔ reference ↔ net

| Ref | Net | Silk | Ref | Net | Silk |
|---|---|---|---|---|---|
| TP1 | `+24V_PROT` | +24V_PROT | TP29 | `FLT_OC_A_15V` | FLT_OC_A_15V |
| TP2 | `+13V5_GATE` | **TP2** | TP30 | `ISNS_A_INT` | ISNS_A_INT |
| TP3 | `+5V` | +5V | TP31 | `ISNS_A_LEM` | ISNS_A_LEM |
| TP4 | `+3V3` | +3V3 | TP32 | `ISNS_B_INT` | **TP32** |
| TP5 | `+24V_MOD` | +24V_MOD | TP33 | `ISNS_B_LEM` | ISNS_B_LEM |
| TP6 | `+15V_ISO` | +15V_ISO | TP34 | `ISNS_C_INT` | ISNS_C_INT |
| TP7 | `-15V_ISO` | -15V_ISO | TP35 | `ISNS_C_LEM` | ISNS_C_LEM |
| TP8 | `ISO_COM` | ISO_COM | TP36 | `ISNS_VREF` | ISNS_VREF |
| TP9 | `GND` | GND | TP38 | `ENC_SIN_RAW` | ENC_SIN_RAW |
| TP10–TP15 | `PWM_UH/UL/VH/VL/WH/WL_15V` | UH UL VH VL WH WL under `PWM 15V` | TP39 | `ENC_COS_RAW` | ENC_COS_RAW |
| TP16 | `GATE_EN_3V3` | GATE_EN_3V3 | TP40 | `ENC_SIN_ADC` | ENC_SIN_ADC |
| TP17 | `MOD_AUX15V_1` | MOD_AUX15V_1 | TP41 | `ENC_COS_ADC` | ENC_COS_ADC |
| TP18 | `MOD_AUX15V_2` | MOD_AUX15V_2 | TP44 | `ENC_VDD` | ENC_VDD |
| TP19 | `VBUS_SNS_RAW` | VBUS | TP45 | `+5V_LP` | +5V_LP |
| TP21 | `VBUS_RTN` | RTN | TP46, TP47 | `GND` | GND |
| TP22 | `NTC_1_RAW` | NTC | TP48 | `ISR_PROBE_3V3` | ISR_PROBE_3V3 |
| TP24 | `FLT_OC_A_3V3` | FLT_OC_A_3V3 | TP49 / TP50 | `CAN_H` / `CAN_L` | CAN_H / CAN_L |
| TP25 | `FLT_OC_B_3V3` | FLT_OC_B_3V3 | TP51 | `SW_MAIN_3V3` | SW_MAIN_3V3 |
| TP26 | `FLT_OC_C_3V3` | FLT_OC_C_3V3 | TP52 | `SW_START_3V3` | SW_START_3V3 |
| TP27 | `FLT_OT_3V3` | FLT_OT_3V3 | TP53 | `MOT_TEMP_RAW` | MOT_TEMP_RAW |
| TP28 | `FLT_OV_3V3` | **TP28** | | | |

Under the LaunchPad shadow (unreachable with it fitted): TP16, TP22, TP27, TP30–TP34, TP47 — probe them before fitting the LaunchPad or with it on extension headers.

## 7. Open after S12

Board orientation / bracket (mechanical, not PCB) · DB37 purchasable MPN and jackscrew hardware · H2 screw hardware · DTM cavity numbering against real plugs before crimping · EMRAX KTY insulation class · CPL offsets **confirmed** on the JLC preview (§3) · bench items (`S12_FIRMWARE_HANDOFF.md` §14) · the firmware-side commit that applies §13.
