# FE_UFPR v4.0 — LaunchPad ↔ PrimeSTACK interface board (FSAE UFPR)

Interface PCB between a TI **LAUNCHXL-F28379D** (FOC firmware) and an Infineon **PrimeSTACK 6PS04512E43W39693** inverter driving an **Emrax 208** motor, with a **Renishaw RM44AC** analog sin/cos encoder and (new) external **LEM LA 100-P** current sensors.

**This directory is the live redesign.** The predecessor `../FE_UFPR_3_0` (2-layer Eagle import) is **REFERENCE ONLY — never modify its `.kicad_*` files.**

## Roadmap & current phase

**Current phase: S3 COMPLETE. Next: S4 — Gate drive, level shifting, enables.**
*(This line is the ONLY place phase state lives — update it when a session's exit criteria pass.)*

**S3's deliverable is [`S3_POWER_DESIGN.md`](S3_POWER_DESIGN.md)** — every computed value, datasheet
equation and JLC stock check behind the `power` sheet.

**S2's deliverable is [`ARCHITECTURE.md`](ARCHITECTURE.md)** — power tree + budget, LaunchPad
power policy (jumper table), grounding/shield rules, floorplan, mounting status, and the
root-sheet interface net table. S3–S8 implement that contract; changes to it get logged.

Full roadmap: [`REDESIGN_PLAN.md`](REDESIGN_PLAN.md) — 12 sessions, one per Claude Code session. Exit criteria are gates: do not start a session until its prerequisites are met, do not bleed into the next session's scope.

**Session rhythm** (every session): read this file + current phase → fetch prerequisite datasheets / bench results → make the listed decisions and append them to the Decision Log → capture in KiCad (MCP server) → JLCPCB-vet every new part → ERC (schematic) / DRC (layout) → update phase marker → `snapshot_project` + git commit.

## Firmware cross-reference (AUTHORITATIVE)

Never contradict these without logging a decision; the final board must answer `control_v2_pinmap.md` line by line (S12 firmware-handoff doc).

- `/home/jose/foc-f28379d-fsae/foc_f28379d/config/hw/hw_control_v2.h` — pin map + scaling constants
- `/home/jose/foc-f28379d-fsae/foc_f28379d/docs/control_v2_pinmap.md` — fill-in handoff format
- `/home/jose/foc-f28379d-fsae/foc_f28379d/docs/infineon.md` — PrimeSTACK electrical interface (incl. the fault-polarity table that conflicts with firmware)
- `/home/jose/foc-f28379d-fsae/foc_f28379d/docs/production_bringup.md` — bring-up order + hardware caveats
- `/home/jose/foc-f28379d-fsae/CLAUDE.md` — engineering logbook (bench-measured constants, root-cause analyses)

### Pin map (F28379D 337ZWT on LAUNCHXL-F28379D, BoosterPack sites 1+2)

| Function | MCU pin | Notes |
|---|---|---|
| PWM U high / low | GPIO6 / GPIO7 (EPWM4A/B) | **active-HIGH**, 10 kHz center-aligned, 1500 ns deadband; EPWM4 = master (ADC SOC + sync) |
| PWM V high / low | GPIO8 / GPIO9 (EPWM5A/B) | |
| PWM W high / low | GPIO10 / GPIO11 (EPWM6A/B) | |
| Gate-driver master EN | GPIO66 (out) | assumed active-high — bench item |
| Gate-driver aux EN | GPIO131 (out) | assumed active-high; **verify it reaches a header pin** — bench item |
| OC fault A / B / C | GPIO25 / GPIO27 / GPIO26 (in, pull-up) | X-BAR INPUT1/2/3 → hardware trip OSHT1–3; trip action = active short (TZA LOW / TZB HIGH) |
| Over-temperature fault | GPIO64 (in, pull-up) | software read only |
| DC-link OV fault | GPIO52 (in, pull-up) | software read only |
| Encoder SIN / COS | ADCINA2 / ADCINB2 | RM44AC, 1 sin/cos cycle per mech rev; ×10 pole pairs electrical |
| Phase current A / B | ADCINB4 / ADCINC4 | 3rd phase by KCL today; v4 adds channel C (ADC pin chosen in S6/S8) |
| Current offset refs | ADCINA4 / ADCINB5 | wired but never sampled — keep/drop decided in S6 |
| Vbus sense | ADCINC2 | module outputs 6.5 V @ 900 VDC |
| NTC channels | *(none today)* | v4 wires NTC#1 (+#2 if pins allow) to spare ADC pins — chosen in S5, recorded here |
| Status LED | GPIO31 | LaunchPad's own D9 — nothing needed on the board |
| ISR scope probe | GPIO67 | expose a test point (pin unverified on Control_V2) |
| SCI-A debug | GPIO42/43 | LaunchPad USB (XDS100v2) backchannel — **no board connector needed** |

### Analog conditioning targets (from firmware logbook — non-negotiable)

- **ADC VREFHI = 3.0 V.** Every ADC input gets an anti-alias RC at the pin (10 kHz sampling; noise >5 kHz aliases irrecoverably) + charge-bucket cap for the S/H.
- **Encoder:** land **1.5 V bias, ~1.4 V amplitude** at the ADC pins (old board: 2.25 V / 0.725 V = 48% range use + clipping + ~26° elec RMS noise). SIN/COS conditioning must be **matched** (same R/C values, C0G, 1%); firmware auto-calibrates bias/amplitude per ALIGN but rejects sin-vs-cos gain mismatch >30%. Expected result: `RES_SINCOS_BIAS_CODE ≈ 2048`, `RES_SINCOS_AMPL_CODE ≈ 1911`.
- **Current:** both sources (internal + LEM) must produce the **same transfer function**, target ~1.5 V bias, full scale **≥ ±300 A** (SW OC trip is 260 A — must fire before ADC saturates). Zero offsets are captured at runtime → **channel-to-channel gain matching matters more than absolute bias**: 0.1% resistors in gain positions, both channels of a stage in one dual op-amp package.
- **Vbus:** fix all three documented problems — source impedance (buffer or low-Z divider + 1–10 nF C0G reservoir; the old 34.5 kΩ needed a 512-cycle S/H workaround), **Kelvin return** for the sensor ground (−52 mV load-dependent IR-drop offset was measured), recompute `VBUS_DIVIDER_RATIO` for ~1000 V full scale.
- **Gates:** PrimeSTACK inputs LOW = 0–1.5 V, **HIGH = 11–15 V**; channel-to-channel skew ≪ 1500 ns deadband.

## Bench-verified facts vs assumptions

**Verified (bench/scope):** encoder = RM44AC sin/cos, already demodulated, 1 cycle/rev; old front-end 2.25 V / 0.725 V; encoder noise 33.5 mV RMS at ADC pin; Vbus divider = 2×69 k, ratio 297.14 + 11.4 code offset; internal current sensors ≈ 7.5–8 mV/A.

**Verified in S1 from the 3.0 design files (not bench):** BoosterPack header grid ΔX 43.18 mm / ΔY 63.5 mm; DB37 as-built pin→net map (table below); DB37 jackscrew spacing 63.5 mm.

**Verified in S2 from SPRUI77 (LaunchPad User's Guide, `datasheets/`):** GPIO131 reaches header J6-58 (GPIO66 → J6-59, GPIO130 → J6-57) per Table 4; jumper semantics per §5.2: JP1/JP2/JP3 = USB 3.3 V/GND/5 V links (all three removed → debugger galvanically isolated when powered via BoosterPack headers), JP4/JP5 bridge MCU 3.3 V/5 V to site-2 headers, JP6 = USB-derived 5 V (stays out).

**Assumed — MUST bench-verify before the dependent session (see REDESIGN_PLAN.md bench-day checklist):**
- Fault output polarity (firmware says fault=LOW; `infineon.md` says fault=HIGH) → blocks S5
- Enable active levels for GPIO66/GPIO131 → blocks S4
- Internal current-sensor zero-current bias (assumed 2.5 V, never measured) + per-channel sensitivity/polarity → blocks S6
- RM44AC differential vs single-ended, supply V/I, true output levels at the connector → blocks S7
- LaunchPad no-back-feed with the S2 jumper config; GPIO131 header continuity → downgraded to *verification* of documented behavior (S2 finding above), no longer design inputs

## Project structure (S1)

```
FE_UFPR_4_0/
├── FE_UFPR_4_0.kicad_pro     netclasses, track/via presets, netclass patterns
├── FE_UFPR_4_0.kicad_sch     root: A3, 7 hierarchical sheet boxes
├── power / gate_drive / module_status / current_sense /
│   encoder / launchpad / vehicle_io  .kicad_sch   (pages 2–8, A3, titled)
├── FE_UFPR_4_0.kicad_sym     THE project symbol library (28 symbols)
├── FE_UFPR_4_0.pretty/       THE project footprint library (19 footprints)
├── sym-lib-table / fp-lib-table   both ${KIPRJMOD}-relative, project scope only
├── CLAUDE.md / REDESIGN_PLAN.md / ARCHITECTURE.md (S2) / S3_POWER_DESIGN.md (S3)
├── datasheets/               fetched reference PDFs (SPRUI77 LaunchPad UG)
```

**Library rule:** nothing is ever placed from a global/system library. Standard KiCad parts are *re-exported* into `FE_UFPR_4_0.kicad_sym` / `.pretty`. This is the fix for 3.0, whose `sym-lib-table` and `fp-lib-table` point at files that do not exist — it only still opens because of embedded caches.

### Symbol library inventory

| Group | Symbols |
|---|---|
| Passive | `R` `C` `C_Polarized` `L` `FerriteBead` `Polyfuse` `Fuse` `Thermistor_NTC` |
| Semi | `LED` `D` `D_Schottky` `D_TVS` `D_Zener` |
| Power/flags | `GND` `PWR_FLAG` `+3V3` `+5V` `+12V` `+24V` `+15V_ISO` `-15V_ISO` |
| Connector | `DSUB-37_Socket` (generated) `Conn_02x10_Odd_Even` |
| Utility | `TestPoint` `MountingHole` `NetTie_2` `SolderJumper_2_Open` `SolderJumper_3_Open` |

**Appended in S3 (28 → 43 symbols):** `LMR33640ADDA` + `LMR33630ADDA`, `TPS62933` + `TPS62933F`, `AP1117-15` + `AMS1117-3.3`, `Conn_01x02`, `MOSFET_P_GDS`, `D_TVS_Unidirectional`, `Converter_DCDC_URA-YMD_Dual`, `TPS54360DDA` (from the reverted detour, now unused), and power symbols `+24V_IN` `+24V_PROT` `+24V_MOD` `+13V5_GATE`.
- `MOSFET_P_GDS` is KiCad's `IRF9540N` renamed — it is the P-channel symbol with **numeric 1=G / 2=D / 3=S** pins that map to TO-252. `Device:Q_PMOS` uses letter pin *numbers* and cannot map to a footprint.
- `D_TVS_Unidirectional` is `D_Zener` renamed: KiCad ships only **bidirectional** TVS symbols (A1/A2 pins) and the SMCJ26A is unidirectional, so the zener glyph is both electrically correct and unambiguous about K/A polarity.
- `+12V` and `+24V` remain in the library but are now **unused** (superseded by `+13V5_GATE` / `+24V_IN`).

`+15V_ISO` / `-15V_ISO` are KiCad's `+15V` / `-15V` renamed so the power symbol drives the isolated-rail net names used in the net convention below. All BOM-bearing symbols carry an empty hidden **`LCSC`** property so the field is always present in the symbol-fields table.

### Footprint library inventory

`R_0603/0805/1206/2512` · `C_0603/0805/1206/1210` · `L_0805/1206` · `PinHeader_2x10_P2.54mm_Vertical` · `PinSocket_2x10_P2.54mm_Vertical` · `DSUB-37_Socket_Horizontal_P2.77x2.54mm_MountingHoles` · `TestPoint_Pad_D1.5mm` · `TestPoint_THTPad_D1.5mm_Drill0.7mm` · `MountingHole_3.2mm_M3` · `MountingHole_3.2mm_M3_Pad` · `SolderJumper-2_P1.3mm_Open` · `SolderJumper-3_P1.3mm_Open_NumberLabels`

**Appended in S3 (19 → 38 footprints):** `Texas_HSOP-8-1EP_3.9x4.9mm_P1.27mm_ThermalVias` · `D_SMC` · `L_Sunlord_SWPA8040S` · `SOT-583-8` · `SOT-223-3_TabPin2` · `TO-252-2` · `SOT-23` · `D_SMA` · `D_SMB` · `Fuse_1206_3216Metric` · `CP_Elec_8x10.5` · `LED_0603_1608Metric` · `NetTie-2_SMD_Pad0.5mm` · `Molex_Mini-Fit_Jr_5566-02A_2x01_P4.20mm_Vertical` · `L_Changjiang_FNR8040S` · `L_Changjiang_FNR5040S` (exact matches for the chosen inductors) — plus two **derived** because KiCad ships neither:

- **`Fuse_2410_6125Metric`** — Littelfuse 451/453 recommended land: pads 1.96 × 3.15 mm, gap 2.95 mm, centres ±2.455 mm, span 6.86 mm; body 6.10 × 2.69 × 2.69 mm.
- **`Converter_DCDC_Mornsun_URA-YMD-6WR3_THT`** — from the URA_YMD-6WR3 datasheet Top View (PCB Layout): 25.40 × 25.40 mm, Ø1.0 mm pins / Ø1.5 mm holes, 2.54 mm grid, columns 20.32 mm apart, pins 3–5 spanning 20.32 mm, pins 1–2 5.08 mm apart straddling the centre. Pin-out **1=GND(−Vin) 2=Vin 3=+Vo 4=0V 5=−Vo**.

Both libraries were validated by a full KiCad parse — S1: `sym export svg` → 28/28, `fp export svg` → 19/19; **S3: 43/43 symbols and 38/38 footprints**. Note the MCP `import_symbol` writes imported symbols at column 0, so run `kicad-cli sym upgrade` afterwards to restore canonical formatting.

## DB37 — as-built 3.0 pin map (REFERENCE ONLY, not yet the v4.0 pin table)

Extracted from the 3.0 board's `INFINEON_DRV0` pads. Fault pins (2/22/5/6/16), the 24 V pass-through (8/26) and the current-sense pins (30/31/32) are **cross-confirmed by `infineon.md` and this file's pin map**. The rest is 3.0's choice and is *not* authoritative — S4/S5/S6 own the v4.0 pin table.

| Pin | 3.0 net | Pin | 3.0 net | Pin | 3.0 net |
|---|---|---|---|---|---|
| 1 | GND | 14 | — | 27 | GND |
| 2 | FLT_A_IN ✓ | 15 | — | 28 | P_GND |
| 3 | BL15 (gate B low) | 16 | FLT_V_IN ✓ | 29 | TEMP_IN |
| 4 | BH15 (gate B high) | 17 | — | 30 | IA_IN ✓ |
| 5 | FLT_C_IN ✓ | 18 | — | 31 | IB_IN ✓ |
| 6 | OV_TEMP_IN ✓ | 19 | GND | 32 | IC_IN ✓ (left dangling in 3.0) |
| 7 | VDC_IN | 20 | AL15 (gate A low) | 33 | — |
| 8 | +24V ✓ | 21 | AH15 (gate A high) | 34 | — |
| 9 | PTC+ | 22 | FLT_B_IN ✓ | 35 | — |
| 10 | P_GND | 23 | CL15 (gate C low) | 36 | — |
| 11 | A_GND | 24 | CH15 (gate C high) | 37 | GND |
| 12 | A_GND | 25 | GND | G1/G2 | shell, unconnected in 3.0 |
| 13 | A_GND | 26 | +24V ✓ | | |

✓ = independently confirmed by `infineon.md` / firmware pin map.

## JLC-vetted passive kit (S1)

Place from these lines by default. Any new value in a later session gets vetted the same way and appended here. **`LCSC` field is mandatory on every placed symbol.** Stock/price snapshot: 2026-08-18 — S12 re-verifies everything live before ordering.

### Resistors — 0603, ±1%, 100 mW, thick film — **all JLC Basic**

All are the Uniroyal `0603WAF…T5E` series (one manufacturer across the kit ⇒ consistent TCR and one reel family).

| Ω | LCSC | Ω | LCSC | Ω | LCSC |
|---|---|---|---|---|---|
| 0 (jumper) | C21189 | 680 | C23228 | 22 k | C31850 |
| 10 | C22859 | 1 k | C21190 | 33 k | C4216 |
| 22 | C23345 | 1.5 k | C22843 | 47 k | C25819 |
| 33 | C23140 | 2.2 k | C4190 | 68 k | C23231 |
| 47 | C23182 | 3.3 k | C22978 | 100 k | C25803 |
| 100 | C22775 | 4.7 k | C23162 | 220 k | C22961 |
| 150 | C22808 | 6.8 k | C23212 | 470 k | C23178 |
| 220 | C22962 | 10 k | C25804 | 1 M | C22936 |
| 330 | C23138 | 15 k | C22809 | | |
| 470 | C23179 | | | | |

**Appended in S3** (same 0603 ±1 % family; all stock-checked 2026-08-29):

| Ω | LCSC | JLC | Used for |
|---|---|---|---|
| 12 k | C22790 | **Basic** | U1 FB divider bottom |
| 150 k | C22807 | **Basic** | U1 FB divider top (13.500 V) |
| 52.3 k | C23198 | Extended | U2 FB divider top (4.984 V) |

*(5.6 k C23189, 49.9 k C23184, 75 k C23242, 200 k C25811 and 620 k C23219 were vetted for the
reverted TPS54360B design and are no longer used — all Basic/high-stock, kept here as pre-vetted
spares.)*

⚠ **Do not "correct" these to the exact E96 values** — 162 kΩ (C22815) has **1** in stock, 10.2 kΩ (C22772) has **3**, 5.49 kΩ (C23069) has **19**, and 604 kΩ (C23216) only 3 434. See `S3_POWER_DESIGN.md` §8.

Price ≈ $0.85–1.46 / 1000, stock 0.5 M–37 M on every line. **0.1 % gain/divider resistors are deliberately NOT in this kit** — their values are computed in S5/S6/S7 and vetted there.

### Capacitors

| Value | Pkg | Dielectric | V | LCSC | MPN | JLC | Use |
|---|---|---|---|---|---|---|---|
| 100 pF | 0603 | C0G | 50 | C14858 | CL10C101JB8NNNC | **Basic** | filter / compensation |
| 220 pF | 0603 | NP0 | 50 | C106210 | CC0603JRNPO9BN221 | Extended | filter |
| 470 pF | 0603 | NP0 | 50 | C106211 | CC0603JRNPO9BN471 | Extended | filter |
| 1 nF | 0603 | NP0 | 50 | C106246 | CC0603JRNPO9BN102 | Extended | charge bucket / filter |
| 2.2 nF | 0603 | NP0 | 50 | C107043 | CC0603JRNPO9BN222 | Extended | filter |
| 4.7 nF | 0603 | C0G | 50 | C85980 | GRM1885C1H472JA01D | Extended | filter |
| 10 nF | 0603 | NP0 | 50 | C389113 | CC0603JRNPO9BN103 | Extended | filter (C0G ceiling in 0603) |
| 22 nF | 0805 | C0G | 50 | C77069 | GRM21B5C1H223JA01L | Extended | filter (C0G ceiling overall) |
| 10 nF | 0603 | X7R | 50 | C57112 | 0603B103K500NT | **Basic** | *non-critical* bypass only |
| 100 nF | 0603 | X7R | 50 | C14663 | CC0603KRX7R9BB104 | **Basic** | decoupling workhorse |
| 1 µF | 0603 | X5R | 50 | C15849 | CL10A105KB8NNNC | **Basic** | local bypass |
| 1 µF | 0805 | X7R | 50 | C28323 | CL21B105KBFNNNE | **Basic** | bypass where X7R tempco matters |
| 4.7 µF | 0805 | X5R | 25 | C1779 | CL21A475KAQNNNE | **Basic** | rail bulk |
| 10 µF | 0805 | X5R | 25 | C15850 | CL21A106KAYNNNE | **Basic** | rail bulk |
| 10 µF | 1206 | X5R | 50 | C13585 | CL31A106KBHNNNE | **Basic** | 24 V-side bulk |
| 22 µF | 1206 | X5R | 25 | C12891 | CL31A226KAHNNNE | **Basic** | buck output bulk |

**Appended in S3:**

| Value | Pkg | Dielectric | V | LCSC | JLC | Use |
|---|---|---|---|---|---|---|
| 47 nF | 0603 | X7R | 50 | **C1622** | **Basic** | U2 soft-start |
| 100 µF | D8×10.2 elec | — | 50 | C2836439 | Extended | 24 V input bulk / harness LC damping |

### Other parts appended in S3

| Part | LCSC | JLC | Notes |
|---|---|---|---|
| SQD50P06-15L P-FET, −60 V, 15.5 mΩ, TO-252 | C3281500 | Ext | reverse polarity |
| **SMCJ26A** TVS 1500 W, SMC | C310042 | Ext | 26 V standoff; 42.1 V clamp at 35.6 A ⇒ ~30–34 V at realistic surge, under the buck's 38 V abs max |
| BZX84C15 15 V Zener, SOT-23 | C19077472 | **Preferred** | Q1 Vgs clamp |
| SS34 40 V 3 A Schottky, SMA | C8678 | **Basic** | LaunchPad 5 V feed (placed in S8) |
| Fuse 5 A 125 V 2410 | C48467 | Ext | F1 — only in-stock 5 A with adequate V rating |
| Fuse 3 A 63 V 1206 | C182445 | Ext | F2 — module-aux pass-through |
| L 22 µH SWPA8040S220MT 2.1/2.4 A, 69 mΩ | C15857 | Ext | L1 |
| L 3.3 µH FNR5040S3R3NT 3.9/4.45 A | C167960 | Ext | L2 |
| LED red 0603 KT-0603R | C2286 | **Basic** | D4–D8, all five rails |
| LMR33630ADDAR | C841384 | Ext | U1 |
| TPS62933FDRLR | C5219272 | Ext | U2 |
| AMS1117-3.3 | C6186 | **Basic** | U3 |
| URA2415YMD-6WR3 | C5369735 | Ext | U4 — consigned THT, only 362 stock |

### Two hard capacitor constraints found in S1 (they shape S3 and S5–S7)

1. **JLC has no Basic C0G/NP0 part above 100 pF in 0603 — at any voltage.** (220 pF…10 nF: 0 Basic, 0 Preferred, out of 10–46 in-stock C0G options each.) Every anti-alias/filter cap therefore costs a $3 Extended setup fee, so **minimise the number of distinct C0G values board-wide** — reuse one or two filter values everywhere rather than optimising each RC independently.
2. **The practical C0G ceiling at 50 V is ~10 nF (0603) / ~22 nF (0805);** 47 nF and up simply do not exist in stock. A passive anti-alias pole at a *low* source resistance is therefore impossible (a 2 kHz corner at 1 kΩ would need 80 nF of C0G). **Consequence:** put the anti-alias pole in the op-amp feedback network (active filter) and keep only the `100 Ω + 1–10 nF C0G` charge bucket at the ADC pin, exactly as the conditioning targets above describe.
3. Related: **JLC Basic bulk capacitors ≥1 µF are X5R, not X7R** (X7R Basic exists only at 1 µF/0805/50 V). X5R is +85 °C rated, X7R +125 °C. The board sits on top of the inverter — S3 must decide per rail whether X5R's temperature range is acceptable or whether Extended X7R is bought.

## JLCPCB workflow

Board is fabbed + assembled by JLCPCB (4-layer, JLC04161H-7628 stackup).

- **Every part gets an `LCSC` field in its symbol before its session ends.** No unvetted parts survive a session.
- Local DB (`search_jlcpcb_parts` / `get_jlcpcb_part`) finds candidates, **but it cannot answer Basic-vs-Extended, stock, or price** — its Basic count is literally 0 of 7.16 M parts. Use the JLCSearch API for those:
  ```bash
  curl -s "https://jlcsearch.tscircuit.com/resistors/list.json?package=0603&resistance=10000&limit=100"
  curl -s "https://jlcsearch.tscircuit.com/capacitors/list.json?package=0603&capacitance=1e-7&limit=200"
  ```
  Returns `is_basic`, `is_preferred`, `stock`, `price1`, `tolerance_fraction`, `voltage_rating`, `temperature_coefficient`. `curl` works and gives raw JSON — prefer it over WebFetch for this. Endpoint index: `https://jlcsearch.tscircuit.com/`.
- Prefer Basic parts (no per-reel fee). S12 re-verifies every LCSC line against live stock before ordering (stock rots).
- **Consigned / hand-solder list** (not in JLC catalog — expect to solder these): DB37, Deutsch DT/DTM connectors, LEM transducers, possibly the isolated DC/DC module.

## Design rules & conventions

- **Passives:** R = 0603 default (0805 for ≥0.125 W, 1206/2512 for power), E96 1%; C = 0603 X7R 50 V default, 0805/1206 bulk, **C0G/NP0 for every filter/anti-alias/timing cap** (subject to the ceiling above); 0.1% only where the target table demands matching. JLC Basic preferred.
- **Libraries:** ONE project symbol lib + ONE project footprint lib; standard-lib parts are re-exported into the project lib. **No reliance on embedded caches.**
- **Refdes:** strict `R/C/L/D/Q/U/J/TP/H/SW/FB/NT` + number, no punctuation (3.0 had `12REG_IN1`, `UNK3,3V_REG0`).
- **Nets:** `<BLOCK>_<SIGNAL>_<LEVEL>` — e.g. `PWM_UH_3V3` → `PWM_UH_15V`, `ISNS_A_ADC`, `ENC_SIN_ADC`, `FLT_OC_A_3V3`. Rails: `+24V_IN`, `+12V` (or gate rail as decided), `+5V`, `+3V3`, `+15V_ISO`/`-15V_ISO`, `GND`.
- **Grounding:** single unified `GND` net with a solid L2 plane. No separate `A_GND` net — analog integrity is a **layout discipline** (analog partition of the plane; no digital/power return currents crossing it). Power return collapses to one star tie at the 24 V entry. Kelvin pairs for Vbus sense return and current-sense references. (3.0's A_GND closed only through the inverter cable, and GND↔P_GND was tied at two separate net-ties.)
- **Netclasses** — defined in `.kicad_pro` as of S1; **values are baselines, S9 re-derives them against fetched JLCPCB 4-layer capabilities**:

  | Class | Track | Clearance | Via Ø/drill | Priority |
  |---|---|---|---|---|
  | Default | 0.25 mm | 0.20 mm | 0.6 / 0.3 | (lowest) |
  | Analog | 0.30 mm | 0.30 mm | 0.6 / 0.3 | 10 |
  | Gate | 0.40 mm | 0.25 mm | 0.8 / 0.4 | 20 |
  | Power_1A | 0.50 mm | 0.25 mm | 0.8 / 0.4 | 30 |
  | Power_3A | 1.20 mm | 0.30 mm | 1.0 / 0.5 | 40 |

  Track presets 0.25/0.3/0.4/0.5/0.8/1.2/2.0 mm; via presets 0.6/0.3, 0.8/0.4, 1.0/0.5. 14 netclass **patterns** are pre-seeded against the net convention (`+24V_IN`, `GND` → Power_3A; rails → Power_1A; `PWM_*_15V`, `DRV_EN*` → Gate; `ISNS_*`, `ENC_*`, `VBUS_*`, `NTC_*`, `*_ADC` → Analog) so nets self-classify as S3–S8 create them.
  **S3 update:** `+12V` pattern renamed `+13V5_GATE`; added `+24V_PROT`/`+24V_MOD` → Power_3A,
  `ISO_COM` → Power_1A, and `PWR_U*_SW` → Power_1A (buck switch nodes: high di/dt, want wide + short).
  18 patterns total.
- **Mounting:** board mounts on top of the inverter; mounting holes required (3.0 had none — only DB37 jackscrews). Pattern from the PrimeSTACK top-face drawing (S2/S9).

## Decision log (append-only: date — session — decision — rationale)

- 2026-08-18 — S0 — **Fresh project `FE_UFPR_4_0`**, hierarchical sheets, clean libs. 3.0's lib refs are all broken (survives on embedded caches) and every block changes anyway.
- 2026-08-18 — S0 — **4-layer** (Sig/GND/Pwr/Sig, JLC04161H-7628). Unbroken GND reference under all analog is the single biggest noise fix; JLC 4-layer cost delta is small.
- 2026-08-18 — S0 — External current sensor = **LEM LA 100-P** (±15 V supply, 1:2000 current output). ⚠ Its ±150 A range vs the 260 A SW OC trip must be resolved in S6 (accept for testing vs upgrade to LA 200-P/305-S class).
- 2026-08-18 — S0 — Internal/external sensor selection via **solder jumpers** per channel (no active parts in signal path, vibration-immune).
- 2026-08-18 — S0 — **All 3 phase-current channels** conditioned identically (3.0 left phase C, DB37 pin 32, dangling; firmware can adopt Iw later without a board spin).
- 2026-08-18 — S0 — **CAN transceiver added** (TCAN33x/SN65HVD23x class, termination jumper, team-standard connector) — FSAE vehicle integration.
- 2026-08-18 — S0 — **Mechanical:** mounts on top of the inverter; outline free, holes per PrimeSTACK top-face drawing.
- 2026-08-18 — S0 — **Power entry: Mini-Fit + Deutsch DT, barrel jack dropped.** Board passes 24 V aux to the module via DB37 pins 8/26 — entry connectors must be rated for the stack's 40 W aux (~1.7 A @ 24 V) plus board draw.
- 2026-08-18 — S0 — Finding: **A2415SDL-2W (±66 mA) is undersized for two closed-loop LA 100-P** (~50 mA RMS compensation/sensor at 100 Arms + ~10 mA idle each). Resolve in S3: one 2 W module per sensor, one 5 W module, or drop isolation (LEM secondary is already galvanically isolated from the primary).
- 2026-08-18 — S1 — **Project created.** A3 root + 7 A3 sub-sheets (`power`, `gate_drive`, `module_status`, `current_sense`, `encoder`, `launchpad`, `vehicle_io`), all title-blocked. ERC on the empty hierarchy: **0 errors / 0 warnings**.
- 2026-08-18 — S1 — **Single project symbol + footprint lib**, registered project-scope with `${KIPRJMOD}`-relative URIs; standard KiCad parts re-exported, never referenced. Validated by full KiCad parse (28/28 symbols, 19/19 footprints render).
- 2026-08-18 — S1 — **3.0's `F37HP` DB37 footprint REJECTED, not salvaged.** Eagle's mil-grid quantization left the contact pitch alternating 2.7686 / 2.7432 mm instead of a uniform 2.769 mm, so pin1→pin19 spans 49.6824 mm against the correct 49.86 mm — 0.18 mm cumulative, ~0.09 mm of position error at each end of a 1.016 mm drill. Handedness *is* correct (it is genuinely a female DC-37) and the jackscrew spacing *is* the standard 63.5 mm, so only the pitch was wrong. Replaced by `DSUB-37_Socket_Horizontal_P2.77x2.54mm_MountingHoles`, derived from KiCad's dimensionally-exact generated footprint plus two Ø3.2 mm `SH` shell pads at ±31.75 mm.
- 2026-08-18 — S1 — **BoosterPack grid re-verified against the 3.0 board itself:** headers at X 127.064 / 170.244 and Y 51.372 / 114.872 mm, all rotated −90° ⇒ **ΔX 43.18 mm, ΔY 63.5 mm** exactly (= 1.700″ × 2.500″). Carried into S9 verbatim. 3.0's own `2X10` footprint is a clean, defect-free 2.54 mm grid; replaced by KiCad standards anyway for consistency.
- 2026-08-18 — S1 — **Both `PinHeader_2x10` and `PinSocket_2x10` imported.** Pad geometry is identical, so the gender choice is purely mechanical (does the LaunchPad sit above or below?) and is deferred to S2's floorplan without any risk to S1's foundation.
- 2026-08-18 — S1 — **DB37 symbol is numbered 1–37 + G1/G2, not functionally named.** The functional pin table is S4/S5/S6 scope and partly blocked on bench data; 3.0's as-built map is recorded above as reference only so nothing unverified gets baked into a library part.
- 2026-08-18 — S1 — **Capacitor sourcing constraints logged** (no Basic C0G >100 pF; C0G ceiling ~10 nF/0603, ~22 nF/0805; Basic bulk is X5R not X7R). These change how S5–S7 build anti-alias filters and how S3 picks bulk caps — see the numbered list above.
- 2026-08-18 — S1 — **Netclasses + track/via presets + 14 netclass patterns written to `.kicad_pro`** per the conventions above, as S1 baselines for S9 to re-derive.
- 2026-08-25 — S2 — **LaunchPad power policy:** board feeds 5 V into the BoosterPack 5 V pins through a series Schottky (part in S3); silkscreen jumper table **JP1✗ JP2✗ JP3✗ JP4✓ JP5✓ JP6✗** = TI's documented external-power config (SPRUI77 §5.2; removing JP2 opens USB *GND* too → debugger fully isolated). LaunchPad regenerates its own 3.3 V; header 3V3 pins left NC (no paralleled regulators); board carries its own small 3V3 LDO so CAN/fault logic run with the LaunchPad unplugged. Never both sources hard-paralleled — the 3.0 failure mode this replaces.
- 2026-08-25 — S2 — **GPIO131 confirmed on header J6-58** (GPIO66 J6-59, GPIO130 J6-57) from SPRUI77 Table 4 — bench item #11 drops to a continuity sanity check; bench item #10 becomes verification of documented jumper behavior.
- 2026-08-25 — S2 — **Grounding frozen** (ARCHITECTURE.md §4): one GND net + L2 plane; star at 24 V entry; DB37 aux return (pins 10/28) on dedicated copper to the star; Kelvin pairs `VBUS_SNS_RAW`+`VBUS_RTN` and `ISNS_*_RAW`+`ISNS_RTN` exist as sheet-level nets from day one; every deliberate GND junction is a `NetTie_2`. **Shield policy:** every connector shell gets 1 nF C0G ∥ 1 MΩ + solder-jumper direct option; defaults — DB37/CAN soft-tie, encoder + LEM shields direct (receiver-end termination).
- 2026-08-25 — S2 — **Power tree + budget frozen** (ARCHITECTURE.md §1–2): 24→12→5→3.3 cascade (TPS62153's 17 V Vin cap forces the cascade anyway; 12 V rail must exist for gate drivers) + isolated ±15 V branch. Budget ≈ 2.1 A @ 24 V / 2.9 A @ 18 V including the 40 W module aux pass-through → design current 3 A, fuse ~5 A, entry contacts ≥ 8 A. ±15 V load math (3 × LA 100-P ≈ 180 mA ≈ 4 W) confirms the 2 W module is undersized — S3 closes with ≥5 W or per-sensor modules.
- 2026-08-25 — S2 — **Floorplan inherits 3.0's proven arrangement** (extracted from the 3.0 board file: outline 91.9 × 121.7 mm, DB37 centered on a short edge, LaunchPad long axis perpendicular to it): DB37 = module edge; power entry + CAN/switches = service edge; encoder + 3× LEM connectors = analog edge (left flank = analog partition); bucks diagonal-opposite the analog corner. **BoosterPack headers = `PinSocket_2x10`, bottom side; LaunchPad hangs below the board** (stock LaunchPad has male pins on top only), USB/XDS end overhanging the service edge; nylon standoffs at the LaunchPad mounting holes. Closes S1's gender question — `PinHeader_2x10` stays in the library unused.
- 2026-08-25 — S2 — **Mounting pattern PENDING user measurement** (allowed by S2 exit criteria): the 6PS04512E43W39693 mechanical drawing is myInfineon-gated; only the 215 × 280 mm envelope is public (`infineon.md`). Leading plan: board gets its own regular hole pattern (S9), a laser-cut **adapter plate** maps it onto the real module top face — decouples board layout from module geometry.
- 2026-08-25 — S2 — **DB37 lives on the `gate_drive` sheet** (its dominant, layout-critical cargo is the gate bus); module raw signals export via hierarchical pins to `module_status` / `current_sense`. DB37 geometry is de-facto validated (3.0's identical footprint geometry mated the real harness); only the purchasable MPN stays open.
- 2026-08-25 — S2 — **Root interface captured: 40 nets / 80 sheet pins** + stubs + net labels on the root, matching hierarchical labels in all sub-sheets (net table in ARCHITECTURE.md §8). Sheet boxes **re-gridded from integer-mm to 1.27 mm multiples** (S1 had them off the connectivity grid — 80 `endpoint_off_grid` warnings the moment wires appeared; now zero). ERC = exactly 160 `label_dangling` and nothing else — this KiCad flags any label whose net has no component pin yet, so the count is the expected empty-hierarchy noise and burns down as S3–S8 fill sheets.
- 2026-08-29 — S3 — **Gate rail = 13.566 V, not 12.0 V** (user decision; S3/S4 joint). FB divider **75 kΩ / 4.7 kΩ**, both JLC Basic. Centres the rail in the module's 11–15 V HIGH window (12.75–13.29 V at the module across ±2 % rail and a 0.55 V drop), so S4 is free to pick any series damping resistor ≤100 Ω. 12.0 V worked in 3.0 but left only ~0.45 V of margin once tolerance stacked.
- 2026-08-29 — S3 — ⚠ **SUPERSEDED — see the revert entry below.** **12 V buck = TPS54360BDDAR (C524806), replacing the roadmap's LMR33630.** Two reasons: (a) **60 V input rating** — SMBJ33A clamps at 53.3 V, which a 36 V part does not survive; (b) LMR33630 has **no MODE/SYNC pin** (verified against its pin table) so it is auto-mode/PFM-only, and TI's own sizing rule puts its PFM boundary at ≈0.45 A — exactly our 12 V load. That is a part-sizing mismatch, not a tuning problem.
- 2026-08-29 — S3 — **5 V buck = TPS62933FDRLR (C5219272), replacing TPS62153.** TPS6215x has **no MODE pin** either — its power-save mode cannot be defeated (and TPS62153 is the *fixed* 5.0 V member; TPS62150 is the adjustable one). The `F` suffix is **FCCM**: fixed 1.2 MHz at any load including LaunchPad-unplugged, and it is the only family member **without** spread spectrum. This is the rail that feeds every analog front-end, so forced-PWM is a hard requirement here and only here.
- 2026-08-29 — S3 — ⚠ **SUPERSEDED by the revert below (L1 is now 22 µH).** **L1 = 47 µH** so U1 stays in **CCM down to ≈0.13 A**, below the real 0.25–0.5 A load. Do not reduce it in S10 — a smaller inductor raises the DCM/skip threshold back into the working range. 12 V-rail skip noise is otherwise tolerable because that rail feeds only gate drivers and the FCCM 5 V buck.
- 2026-08-29 — S3 — **±15 V = one Mornsun URA2415YMD-6WR3 (C5369735), 6 W, ±200 mA/rail** — closes the S0 flag that the ±66 mA A2415SDL-2W was undersized against ≈180 mA / 4 W for 3× LA 100-P. Datasheet also widens the assumed input range to **9–36 V**. Isolation is kept even though the secondary commons to GND at one point, so the ±15 V return current stays inside the analog partition. ⚠ consigned through-hole part, only 362 in stock.
- 2026-08-29 — S3 — **[ARCH CHANGE] rail `+12V_GATE` renamed `+13V5_GATE`** — the net regulates to 13.57 V and labelling it `+12V` on a schematic is actively misleading. New power symbol derived from KiCad's `+24V`, netclass pattern updated.
- 2026-08-29 — S3 — **[ARCH CHANGE] new global net `+24V_MOD`** — the module-aux pass-through needs its own fused net (F2, 3 A) to cross from `power` to `gate_drive`. S4 lands it on DB37 pins 8/26.
- 2026-08-29 — S3 — **Input fuse F1 = 0451005.MRL, 2410, 5 A / 125 V (C48467)**, user chose SMD/non-replaceable. It is the **only in-stock 5 A SMD fuse with an adequate voltage rating** — the two 1206 alternatives are 32 V and unrated, and a fuse must interrupt the arc at the applied voltage, which the TVS pins at 53.3 V. Cost: one derived footprint (KiCad ships no 2410 fuse land).
- 2026-08-29 — S3 — **Three EN/SS hazards caught during capture, each of which would have destroyed hardware:** U1 EN abs max is **8.4 V** and U2 EN abs max is **6.0 V** — neither may be tied to its input rail, so both get dividers (620 k/49.9 k → UVLO start 15.37 V / stop 13.26 V; 100 k/33 k → 3.37 V); and U2's **SS pin cannot float** (≥6.8 nF required, C13 = 47 nF fitted).
- 2026-08-29 — S3 — **Divider values re-picked against live stock, not just E96 tables.** The natural 13.5 V pair 162 kΩ/10.2 kΩ is unbuyable (**1** and **3** units in stock), as is the exact compensation resistor 5.49 kΩ (**19**). Final picks are Basic/high-stock parts; the unbuyable values are recorded in `S3_POWER_DESIGN.md` §8 so nobody "restores" them later.
- 2026-08-29 — S3 — **All five rail LEDs are the same Basic red part (KT-0603R, C2286)** with silkscreen naming each rail, rather than a green Extended line — and green's ~3.1 V Vf is marginal off the 3.3 V rail anyway. All five series resistors come from the S1 kit.
- 2026-08-29 — S3 — **`power` sheet captured: 79 components, 30 nets, ERC 0 violations on the sheet**, netlist verified node-by-node. Connectivity is by net labels at pins rather than drawn wires — electrically verified but visually dense around U1/U2; a wire-stub tidy-up is logged as a cosmetic follow-up. Both bucks' datasheet layout rules are written onto the sheet as text notes for S10.
- 2026-08-29 — S3 — **REVERTED the gate-rail buck back to LMR33630ADDAR (C841384)** after user challenge. The 60 V TPS54360B swap rested on the S2 assumption `+24V_IN 18–30 V`, which I inherited from ARCHITECTURE.md §1 and never confirmed. **User confirmed the LV rail max is ≤26 V [ARCH CHANGE: input range now 18–26 V]**, which makes a 36 V part correct. Reverting is also a net simplification: synchronous (no catch diode), internally compensated (no R/C/C network), fixed 400 kHz (no R_T) — **5 fewer parts and better efficiency**. FB divider recomputed for **V_ref = 1.000 V** (not 0.8 V): **150 kΩ / 12 kΩ → exactly 13.500 V**, both JLC Basic with >400 k stock. UVLO now via EN divider 100 k/10 k → rising 13.5 V, falling 12.4 V (both already in the S1 kit). L1 **47 µH → 22 µH** (C15857) per TI's ripple rule using the device's 3 A rating = 24.6 %; the rail runs PWM above ~0.35 A and PFM below, which is fine because it feeds only gate drivers and U2's FCCM input.
- 2026-08-29 — S3 — **Lesson logged: two justifications were stacked for one decision.** The LMR33630 was dropped citing *both* PFM behaviour *and* voltage headroom, when only the voltage argument was load-bearing — and that one rested on an unverified inherited assumption. The PFM concern is real only on the **5 V** rail (which feeds the analog front-ends); the gate rail's light-load mode does not matter. **The TPS62153 → TPS62933F swap therefore stands** and is independent of input voltage.
- 2026-08-29 — S3 — **TVS changed SMBJ33A → SMCJ26A (C310042).** The genuinely valid finding from the reverted detour was about the *TVS*, not the buck: SMBJ33A's breakdown is **36.7–40.6 V**, which straddles the LMR33630's **38 V absolute max** — that S2 pair was broken. Both SMBJ26A and SMCJ26A quote a 42.1 V clamp, but the 1500 W SMCJ reaches it at **35.6 A** vs the 600 W SMBJ's **14.3 A**, so at a realistic surge the SMCJ sits around 30–34 V, safely under 38 V. Stand-off 26 V matches the confirmed rail max. Do not substitute an SMBJ.

## Open items (owner session in brackets; struck items resolved with the session noted)

- ~~[S2] BoosterPack header gender~~ — **resolved S2:** `PinSocket_2x10`, bottom side, LaunchPad below.
- **[user, before S9] PrimeSTACK top-face mounting measurement** (or myInfineon drawing export): hole positions/threads, obstructions, DB37 cable arrival point. Board plan decouples via adapter plate (ARCHITECTURE.md §7) so only the plate depends on the result.
- **[user] DB37 purchasable MPN** for the consigned list. Geometry (female, right-angle, 2.77 × 2.54 mm, 63.5 mm jackscrews) is de-facto validated by 3.0 mating the real harness — only the buyable part number is open. If the team ever switches to a *vertical* part, the row pitch becomes 2.84 mm and the footprint must be re-derived.
- ~~[S3] Schottky vs ideal-diode/load-switch for the LaunchPad 5 V feed~~ — **resolved S3:** plain Schottky **SS34, C8678 (JLC Basic)**; V_f ≈ 0.35 V at ~200 mA leaves the LaunchPad ≈4.63 V, ample for its own 3.3 V LDO. **Physically placed in S8** on the `launchpad` sheet at the header.
- ~~[S3] X5R vs X7R for bulk rails~~ — **resolved S3:** X7R wherever a Basic/Preferred X7R exists at the needed value (100 nF, 47 nF, 1 µF); X5R for the bulk ≥4.7 µF where JLC Basic offers nothing else, with ≥2× voltage derating (50 V parts on the 24 V rail, 25 V parts on 5 V/3V3). AMS1117 dissipates 0.25 W → ≈85 °C junction at the 70 °C worst-case local ambient.
- **[S5/S6/S7] Standardise C0G filter values** across sheets to limit Extended part count.
- **[S8] CAN GPIO pair** for `CAN_TX_3V3`/`CAN_RX_3V3` — pick CAN-mux-capable GPIOs that reach the BoosterPack headers (SPRUI77 Tables 1–4 in `datasheets/`); note the LaunchPad's own CAN transceiver hangs on GPIO12/17 via 0 Ω links (J12) — avoid or account for it.
- **[S12] Re-verify `C5369735`** (URA2415YMD-6WR3 isolated module) — only **362 in stock** and it is a consigned through-hole part. Highest supply risk on the board.
- **[S4] `+24V_MOD`** is the fused (F2, 3 A) module-aux pass-through created in S3 — land it on DB37 pins 8/26 on the `gate_drive` sheet.
- **[S4] Series damping resistor ≤100 Ω** on the gate lines keeps the module inside 11–15 V with the 13.566 V rail; log the value actually chosen.
- **[cosmetic, any session] `power` sheet readability** — connectivity is by net labels at pins, not drawn wires. Electrically verified (ERC 0, netlist checked node-by-node) but visually dense around U1/U2 where 8–9 labels converge. A wire-stub pass fanning the IC pins out would make it presentation-quality.
- **[S9] 3D model** for the derived DB37 footprint still points at KiCad's `…_EdgePinOffset9.40mm.step` (correct body, name differs from the footprint) — harmless, revisit if 3D export matters.

## Tooling notes

- KiCad **10.0.5**; MCP server for schematic/PCB editing, ERC/DRC, BOM/gerber export, `snapshot_project`.
- `kicad-cli sym export svg` / `fp export svg` is the fastest way to prove a library actually parses — use it after any hand-edit of `.kicad_sym` / `.kicad_mod`.
- Datasheets via WebFetch/WebSearch (RM44AC, 6PS04512E43W39693, LA 100-P, TC4468, LAUNCHXL-F28379D).
- Temp exports go to the session scratchpad, not the project directory.
