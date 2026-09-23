# S12 prep — DFM, BOM/CPL, fab package, firmware handoff (prepared 2026-09-23, session not started)

Everything below was set up and dry-run **after** the S11 pass was committed (`2688252`, "Finishing tp naming":
DRC 0 / 0 unconnected / parity clean / 7 by-design silk warnings, ERC 0, netlist = `golden.net`). Nothing in
the design changed for this prep. Scope and exit criteria: [`REDESIGN_PLAN.md`](REDESIGN_PLAN.md) §S12 —
order-ready fab package, BOM with zero unvetted lines, handoff doc complete, tag `v4.0-release`.

## 0. How to run the session

1. Re-run the gates once (DRC with `--schematic-parity --refill-zones`, ERC, netlist diff) — nothing else touches the design first.
2. §1 exports → §2 re-verification (fresh, on the day of the order — the baseline below is a *starting point*, not the record) → §3 CPL audit → §4 handoff → §5 assembly notes → §6 bring-up sheet.
3. Decisions the session must make explicitly (they change the order): **U4 consign or JLC-place** (§2), **the 12 B.Cu parts: hand-solder, or Standard two-sided PCBA** (§3), `HW_NAME` string (§4), conformal coating (Appendix C of the plan).
4. Record: LCSC lines re-verified in `JLC_PARTS.md` (`### S12 re-verification` table = the `jlc_verify.py --md` output), decisions in `DECISION_LOG.md`, the package in `fab/` (new, committed), tag.

## 1. Tooling — all dry-run into the scratchpad on 2026-09-23

No plugin is installed (`~/.local/share/kicad/10.0/3rdparty/plugins` does not exist), so the package comes from `kicad-cli` +
two scripts in `tools/fab/`. Every command below ran clean; outputs went to the session scratchpad, not the project.

```bash
SCR=<scratchpad>/s12
# BOM (kicad-cli groups references into ranges "C16-C18" — jlc_bomcpl.py expands them).  ⚠ zsh: keep ${QUANTITY} in SINGLE quotes.
kicad-cli sch export bom --fields 'Reference,Value,Footprint,LCSC,${QUANTITY}' --labels 'Reference,Value,Footprint,LCSC,Qty' \
    --group-by 'Value,Footprint,LCSC' -o $SCR/bom.csv FE_UFPR_4_0.kicad_sch
# positions (page origin — the board has no aux origin; KiCad's Y is negative-down and JLC's importer accepts KiCad pos files as-is)
kicad-cli pcb export pos --format csv --units mm --side both --use-drill-file-origin --exclude-dnp -o $SCR/pos.csv FE_UFPR_4_0.kicad_pcb
# gerbers (11 layers, mask-subtracted, drill origin) + Excellon PTH/NPTH + maps
kicad-cli pcb export gerbers --board-plot-params --layers F.Cu,In1.Cu,In2.Cu,B.Cu,F.Mask,B.Mask,F.SilkS,B.SilkS,F.Paste,B.Paste,Edge.Cuts \
    --subtract-soldermask --use-drill-file-origin -o $SCR/gerb/ FE_UFPR_4_0.kicad_pcb
kicad-cli pcb export drill --format excellon --excellon-units mm --excellon-separate-th --generate-map --map-format gerberx2 -o $SCR/gerb/ FE_UFPR_4_0.kicad_pcb
# live JLC check of every LCSC line (curl; ~1 min) and the JLC-format BOM + CPL
python3 tools/fab/jlc_verify.py $SCR/bom.csv --boards 5 --out $SCR/jlc_verify.json --md $SCR/jlc_verify.md
python3 tools/fab/jlc_bomcpl.py $SCR/bom.csv $SCR/pos.csv $SCR/jlc [--rotations tools/fab/jlc_rotations.json]
```

- `jlc_verify.py` flags `NOT_FOUND / OUT_OF_STOCK / LOW_STOCK (< 3× the run) / EXTENDED / PACKAGE_MISMATCH`, prices the run, and writes the
  markdown table for `JLC_PARTS.md`. It uses `curl` because JLCSearch answers Python's `urllib` User-Agent with **HTTP 403**, and falls back to
  the `resistors/list.json?lcsc=` endpoint because `/api/search` does not index every part (`C25804`, the 10 k 0603 used 16×, is missing there).
- `jlc_bomcpl.py` drops `NOFIT` / `CONSIGNED` lines from both files and prints them; `--rotations` is the per-footprint offset table the §3
  audit produces (`{"SOT-23": 180, ...}`) — without it the CPL carries raw KiCad rotations and says so.
- Gerber sanity on the dry run: F.Cu 1.6 MB, In1 498 KB (solid GND), In2 69 KB, B.Cu 722 KB, Edge 739 B (one closed outline), PTH drill 12.3 KB,
  NPTH 515 B (H1–H4 Ø4.3 + the DB37 shell holes). Board 146.0 × 130.0 mm.

## 2. JLC re-verification — baseline of 2026-09-23 (`tools/fab/jlc_verify_2026-09-23.md`)

| | |
|---|---|
| BOM | 364 symbols → 133 lines; **71 real LCSC lines / 63 unique codes**; 0 lines without an `LCSC` field; 0 DNP |
| Placeholders | `NOFIT` × 58 (JP1–JP6, NT1–NT4, 48 TP), `CONSIGNED` × 5 (J1 Mini-Fit, J2 DB37, J3/J4/J5 Deutsch DTM) |
| Basic / Preferred | 37 lines; **33 plain-Extended lines = 30 codes × $3.07 = $92.10** feeder fees (same as the 2026-09-17 audit: nothing cuttable) |
| Parts cost | **$140.63 for 5 boards** at today's JLCSearch prices (excl. consigned parts, fees, PCB) |
| Not found / OOS | none (C25804 only via the resistors endpoint — Basic, 37 M stock) |
| Package check | U1 `LMR33630ADDAR` = JLC "ESOP-8" vs KiCad `HSOP-8-1EP` — same package, naming only |
| Low stock | **U4 `C5369735` URA2415YMD-6WR3: 362** (need 5 — and the consign question is still open, `JLC_PARTS.md` watch list) · U2 `C5219272` 2 255 · **`C77033` 2.2 nF C0G: 2 265 for 50 needed** |

On the day: re-run, paste the table into `JLC_PARTS.md`, and treat any `LOW_STOCK` on the 2.2 nF C0G as a real risk (10 per board, the only
C0G value of that size in the kit — the alternates are in `JLC_PARTS.md` §capacitors).

## 3. CPL — rotation / polarity audit (not done yet)

JLC's part orientation differs from KiCad's for most non-passive packages; a wrong offset means every SOT-23 or SOIC on the run is rotated.
Audit each footprint family once against JLC's part image (order page → "Component placement" preview) and write the offset into
`tools/fab/jlc_rotations.json`. Passives (R/C 0603–1206, non-polar) need no audit. Bottom side: 12 SMD parts (R2/R3, D17/C119, C25–C28,
R118/R119/C113/C120 — user's decision 2026-09-17) are in the CPL as `Bottom`; **Economic PCBA is single-side**, so either hand-solder them
(drop from BOM/CPL, add to §5) or order Standard two-sided — decide before upload.

| Ref | Footprint | KiCad rot | Side | JLC offset (fill) |
|---|---|---|---|---|
| D17 | D_SMA | -90 | bottom | |
| C1 | CP_Elec_8x10.5 | 90 | top | |
| D1 | D_SMC | 0 | top | |
| D2 | SOT-23 | 0 | top | |
| D4 | LED_0603_1608Metric | 0 | top | |
| D5 | LED_0603_1608Metric | -90 | top | |
| D6 | LED_0603_1608Metric | -90 | top | |
| D7 | LED_0603_1608Metric | 180 | top | |
| D8 | LED_0603_1608Metric | 90 | top | |
| D9 | LED_0603_1608Metric | 90 | top | |
| D10 | SOT-23 | 180 | top | |
| D11 | SOT-23 | 180 | top | |
| D12 | D_SMA | 90 | top | |
| D13 | SOT-23 | 0 | top | |
| D14 | D_SOD-123 | -90 | top | |
| D15 | D_SOD-123 | -90 | top | |
| D16 | D_SMA | 0 | top | |
| D18 | SOT-23 | 90 | top | |
| F1 | Fuse_2410_6125Metric | 0 | top | |
| L1 | L_Sunlord_SWPA8040S | 0 | top | |
| L2 | L_Changjiang_FNR5040S | 180 | top | |
| L3 | L_CommonMode_TDK_ACT45B | 0 | top | |
| Q1 | TO-252-2 | 90 | top | |
| U1 | Texas_HSOP-8-1EP_3.9x4.9mm_P1.27mm_Therm | 180 | top | |
| U2 | SOT-583-8 | -90 | top | |
| U3 | SOT-223-3_TabPin2 | 180 | top | |
| U4 | Converter_DCDC_Mornsun_URA-YMD-6WR3_THT | 180 | top | |
| U5 | SOIC-8_3.9x4.9mm_P1.27mm | 180 | top | |
| U6 | SOIC-8_3.9x4.9mm_P1.27mm | 180 | top | |
| U7 | SOIC-8_3.9x4.9mm_P1.27mm | 180 | top | |
| U8 | SOT-23-6 | -90 | top | |
| U9 | SOT-23-6 | 90 | top | |
| U10 | SOT-23-6 | 90 | top | |
| U11 | SOT-23-6 | 90 | top | |
| U12 | SOIC-8_3.9x4.9mm_P1.27mm | -90 | top | |
| U13 | SOIC-8_3.9x4.9mm_P1.27mm | -90 | top | |
| U14 | SOIC-8_3.9x4.9mm_P1.27mm | -90 | top | |
| U15 | SOIC-8_3.9x4.9mm_P1.27mm | -90 | top | |
| U16 | SOIC-8_3.9x4.9mm_P1.27mm | 180 | top | |
| U17 | SOIC-8_3.9x4.9mm_P1.27mm | 180 | top | |
| U18 | SOIC-8_3.9x4.9mm_P1.27mm | 90 | top | |
| U19 | Optocoupler_LTV-817S_SMD-4P | 0 | top | |
| U20 | Optocoupler_LTV-817S_SMD-4P | 0 | top | |
| U21 | SOT-23-6 | 0 | top | |

Pin-1 / polarity references: LEDs D4–D9 (cathode mark), D1 SMC / D12/D16/D17 SMA / D14/D15 SOD-123 (cathode band), C1 electrolytic
(negative stripe), U4 module (pin 1), Q1 TO-252 (tab), optocouplers U19/U20 (pin-1 dot), J1 Mini-Fit (key).

## 4. Firmware handoff — pre-filled answers for `control_v2_pinmap.md` (verify each against the schematic before sending)

Target file: `/home/jose/foc-f28379d-fsae/foc_f28379d/docs/control_v2_pinmap.md` (fill-in) → `config/hw/hw_control_v2.h`. Values below come
from the design docs named in the last column; the S12 job is to re-read them off the **schematic** line by line, then write the handoff.

| Item (pinmap §) | Firmware today (`hw_control_v2.h`) | FE_UFPR 4.0 answer | Source |
|---|---|---|---|
| §1 PWM U/V/W | EPWM4/5/6 A/B = GPIO6–11, 10 kHz, 1500 ns, high-side ON = HIGH | **unchanged**; DB37 20/21, 3/4, 23/24 via UCC27524 ×3 (U5–U7), 11–15 V at the module | `S4` |
| §2 master EN / aux EN | GPIO66 / GPIO131, level "HIGH/LOW" unfilled | **both active-HIGH**, board-local (U8 inputs A/B; U8 input C = `SW_MAIN_3V3` interlock via JP1) | `S4`, `S8` |
| §3 fault flags | GPIO25/27/26 OC A/B/C, GPIO64 OT, GPIO52 DCOV, `MODULE_FAULT_ACTIVE_LOW 1` | **`MODULE_FAULT_ACTIVE_LOW 0`** (module: open collector, LOW = no fault ⇒ fault = HIGH; X-BAR polarity inverts). All five wired; OC A/B/C → HW trip (OSHT1–3), OT/OV software. ⚠ the module asserts **all three OC pins** on any leg. Levels shifted 15 V → 3.3 V on-board (U9–U11); no MCU pull-up needed (`S5` receiver) | `S4` §7, `S5` |
| §4 status LED | GPIO31 | unchanged (LaunchPad D9) | — |
| §5 ADC map | Iu = B4, Iv = C4, Iw none, Vbus = C2, SIN = A2, COS = B2 | **Iu = ADCINA5 (J7-66), Iv = ADCINC4, Iw = ADCINB4 (J7-68)** — A↔C swapped 2026-09-22 for routing; `ISENSE_NUM_CHANNELS 3`, KCL optional. Vbus **ADCINC2** ✓, SIN **ADCINA2** ✓, COS **ADCINB2** ✓. Offset refs `ISNS_VREF` ≈ 1.4685 V on **ADCINA4 + ADCINB5** (kept). New: **NTC ADCINC3** (J3-24, suggest ADC-C SOC2), **motor KTY ADCINB3** (J3-25), **+3V3 monitor ADCINA3** (J3-26) | `CLAUDE.md` pin map, `S6`, `S5`, `S9.5` |
| §6 current scaling | `LEM_V_PER_A 0.0075` (contradictory comments), bias 2048 placeholder | at the ADC pin: **internal path 4.800 mV/A** (module 8 mV/A assumed, ×0.6), **LEM path 4.886 mV/A** (23.5 Ω burden) → `LEM_V_PER_A` per source (JP3–JP5 select), bias ≈ 1.4685 V (code ≈ 2005), full scale ≥ ±300 A (±441 A if the module is 5.66 mV/A); signs: bench | `S6` §3–§5 |
| §7 Vbus | ratio 297.14, offset 11.4 | **`VBUS_DIVIDER_RATIO 341.538`** (2.20 k / 1.50 k 0.1 % on the module's 6.5 V @ 900 V), **0.250150 V/code**, full scale 1024.6 V; `VBUS_OFFSET_CODE` re-measure; Kelvin return `VBUS_RTN` (NT3) | `S5` §2 |
| §8 encoder | bias 3072 / ampl 990 codes | **`RES_SINCOS_BIAS_CODE 2039`, `RES_SINCOS_AMPL_CODE 1745`** (1.493 V / 1.278 V, 85 % range, no clip at 2.4 Vpp), 1 cycle/mech rev (RM44AC `01S`), matched RC per channel — pinmap's "0–3.3 V clips" caveat is **fixed by this board** | `S7` §4 |
| new: NTC (module) | none | ADCINC3, divider **12 k / 4.7 k** (÷3.553: 10 V → 2.814 V, 93.8 % range), returns to `GND` | `S5` §3 |
| new: motor temp | none | KTY81-210 (PTC: hotter = **higher** code) on ADCINB3, `MOT_TEMP_R_TOP 2200` from `+3V3`; rail on ADCINA3 through 10.0 k/10.0 k → `R = 2200·V/(V_rail−V)`, `V_rail = 2 × ADCINA3`; **fault window: code < 1400 or > 3100 → stop** (EMRAX) | `S9.5` |
| new: CAN-A | none | **GPIO4 TX / GPIO5 RX** (J4-36 / J4-35), SN65HVD230, JP6 = 120 Ω termination (bridged by default); CAN-B not routable | `S8` |
| new: switches | none | **GPIO29 `SW_MAIN_3V3`**, **GPIO59 `SW_START_3V3`** (J2-11 / J2-14), opto-isolated, 0 V = LOW = withheld | `S8` §5 |
| §9 SCI / §10 clock | USB backchannel, `_LAUNCHXL_F28379D` | unchanged; ISR probe GPIO67 → **TP48** `ISR_PROBE_3V3` | — |
| `HW_NAME` | `"Control_Board_v2"` | propose **`"FE_UFPR_4_0"`** — coordinate the bump with the firmware side (Appendix C) | — |
| `BENCH_NO_POWER_STAGE` | 0 | leave; the bring-up sheet (§6) says when to set 1 | — |

## 5. Assembly notes — seeds

- **Consigned / hand-solder:** J1 Mini-Fit Jr 5566-02A, J2 DB37 socket (UNC 4-40 jackscrews), J3/J4 DTM13-12P (keys A/B), J5 DTM13-08PA;
  the LEM LA 100-P sensors live on the remote board (not this BOM). **U4 URA2415YMD-6WR3 has a real LCSC line** — decide (§0).
- **Solder jumpers (all `NOFIT`, default state from the schematic values):** JP1 `ILOCK_SEL`, JP3/JP4/JP5 `SRC SEL A/B/C` (internal vs LEM per
  phase), JP2 `SHLD_TIE` (open), JP6 CAN termination (**bridged** footprint = 120 Ω in). Put the default table on the assembly sheet.
- Mounting: H1–H4 Ø4.3 M4 — **button/cheese heads at H2, no Ø9 washer** (`OPEN_ITEMS.md`).
- Silk carries **net names** on the test points; the table below maps them back to `TPxx` (only F.Fab and the CPL show numbers).

## 6. Bring-up sheet — seeds (order per `production_bringup.md`, board-side checks first)

1. **Rails, nothing plugged:** TP1 `+24V_PROT` → TP5 `+24V_MOD` → TP2 `+13V5_GATE` → TP3 `+5V` → TP4 `+3V3` → TP6/TP7/TP8 `±15V_ISO`/`ISO_COM`
   → TP45 `+5V_LP` (LaunchPad power policy: `ARCHITECTURE.md` jumper table). LEDs D4–D9 mirror the rails + `GATE_EN`.
2. **Gate chain, DB37 unplugged:** firmware `ol_run` open-loop → scope `PWM 15V` row (WH WL VH VL UH UL) for 11–15 V levels, complementary
   pairs, 1500 ns deadband, 120° phasing; enables at TP16 `GATE_EN_3V3` with JP1 interlock in both positions.
3. **Fault receivers:** TP24–TP28 (`FLT_*_3V3`) read LOW with the module healthy / DB37 unplugged = HIGH (pulled up = fault) — matches
   `MODULE_FAULT_ACTIVE_LOW 0`.
4. **Analog:** `ISNS_VREF` (TP36) ≈ 1.4685 V; `ISNS_*_INT/LEM` (TP30–TP35) at zero current ≈ VREF; `VBUS` (TP19 vs `RTN` TP21) at a bench DC link;
   `NTC` TP22; encoder TP38–TP41 bias 1.49 V / 1.28 V amplitude; TP53 `MOT_TEMP_RAW` with the KTY table.
5. Then `production_bringup.md` steps 1–10 at low voltage; HV only after all pass.

### Test points — silk label ↔ reference ↔ net

| Ref | Net | Silk shows |
|---|---|---|
| TP1 | `+24V_PROT` | +24V_PROT |
| TP2 | `+13V5_GATE` | TP2 |
| TP3 | `+5V` | +5V |
| TP4 | `+3V3` | +3V3 |
| TP5 | `+24V_MOD` | +24V_MOD |
| TP6 | `+15V_ISO` | +15V_ISO |
| TP7 | `-15V_ISO` | -15V_ISO |
| TP8 | `ISO_COM` | ISO_COM |
| TP9 | `GND` | GND |
| TP10 | `PWM_UH_15V` | UH *(under `PWM 15V`)* |
| TP11 | `PWM_UL_15V` | UL *(under `PWM 15V`)* |
| TP12 | `PWM_VH_15V` | VH *(under `PWM 15V`)* |
| TP13 | `PWM_VL_15V` | VL *(under `PWM 15V`)* |
| TP14 | `PWM_WH_15V` | WH *(under `PWM 15V`)* |
| TP15 | `PWM_WL_15V` | WL *(under `PWM 15V`)* |
| TP16 | `GATE_EN_3V3` | GATE_EN_3V3 |
| TP17 | `MOD_AUX15V_1` | MOD_AUX15V_1 |
| TP18 | `MOD_AUX15V_2` | MOD_AUX15V_2 |
| TP19 | `VBUS_SNS_RAW` | VBUS |
| TP21 | `VBUS_RTN` | RTN |
| TP22 | `NTC_1_RAW` | NTC |
| TP24 | `FLT_OC_A_3V3` | FLT_OC_A_3V3 |
| TP25 | `FLT_OC_B_3V3` | FLT_OC_B_3V3 |
| TP26 | `FLT_OC_C_3V3` | FLT_OC_C_3V3 |
| TP27 | `FLT_OT_3V3` | FLT_OT_3V3 |
| TP28 | `FLT_OV_3V3` | TP28 |
| TP29 | `FLT_OC_A_15V` | FLT_OC_A_15V |
| TP30 | `ISNS_A_INT` | ISNS_A_INT |
| TP31 | `ISNS_A_LEM` | ISNS_A_LEM |
| TP32 | `ISNS_B_INT` | TP32 |
| TP33 | `ISNS_B_LEM` | ISNS_B_LEM |
| TP34 | `ISNS_C_INT` | ISNS_C_INT |
| TP35 | `ISNS_C_LEM` | ISNS_C_LEM |
| TP36 | `ISNS_VREF` | ISNS_VREF |
| TP38 | `ENC_SIN_RAW` | ENC_SIN_RAW |
| TP39 | `ENC_COS_RAW` | ENC_COS_RAW |
| TP40 | `ENC_SIN_ADC` | ENC_SIN_ADC |
| TP41 | `ENC_COS_ADC` | ENC_COS_ADC |
| TP44 | `ENC_VDD` | ENC_VDD |
| TP45 | `+5V_LP` | +5V_LP |
| TP46 | `GND` | GND |
| TP47 | `GND` | GND |
| TP48 | `ISR_PROBE_3V3` | ISR_PROBE_3V3 |
| TP49 | `CAN_H` | CAN_H |
| TP50 | `CAN_L` | CAN_L |
| TP51 | `SW_MAIN_3V3` | SW_MAIN_3V3 |
| TP52 | `SW_START_3V3` | SW_START_3V3 |
| TP53 | `MOT_TEMP_RAW` | MOT_TEMP_RAW |

## 7. Still open going into S12 (not blockers for the package)

Board orientation (vertical provisional — affects the bracket, not the PCB), EMRAX KTY insulation class, H2 screw hardware, TPs under the
LaunchPad shadow (TP16, TP22, TP27, TP30–TP34, TP47). Full list: [`OPEN_ITEMS.md`](OPEN_ITEMS.md).
