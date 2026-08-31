# FE_UFPR v4.0 — LaunchPad ↔ PrimeSTACK interface board (FSAE UFPR)

Interface PCB between a TI **LAUNCHXL-F28379D** (FOC firmware) and an Infineon **PrimeSTACK 6PS04512E43W39693** inverter driving an **Emrax 208** motor, with a **Renishaw RM44AC** analog sin/cos encoder and (new) external **LEM LA 100-P** current sensors.

**This directory is the live redesign.** The predecessor `../FE_UFPR_3_0` (2-layer Eagle import) is **REFERENCE ONLY — never modify its `.kicad_*` files.**

## Roadmap & current phase

**Current phase: S7 COMPLETE. Next: S8 — LaunchPad interface, CAN, integration, pin-map freeze.**
*(This line is the ONLY place phase state lives — update it when a session's exit criteria pass.)*

**S7's deliverable is [`S7_ENCODER_DESIGN.md`](S7_ENCODER_DESIGN.md)** — the RM44AC's real output
spec (single-ended, 2.2 Vpp, 3/5·Vdd, 720 Ω), the difference-amp transfer function and every
computed value, why the amplitude target moved from 1.4 V to 1.28 V, the **ratiometric bias
cancellation**, the topology choice that makes an unplugged encoder collapse to the ADC bias
(unconditional loss-of-signal), the phase budget, and the **connector correction that put Deutsch
back on the board** — S6's "the DTM13 drawing is login-gated" premise was false.

**S6's deliverable is [`S6_CURRENT_SENSE_DESIGN.md`](S6_CURRENT_SENSE_DESIGN.md)** — the two
difference-amp stages per channel and every computed value, the **LA 100-P R_M window** (a burden
resistor is not a free knob), why the burden lives on *our* board, the ±15 V budget, the ADC pin
choice, and the correction of a "bench-verified" figure that was never measured.

**S5's deliverable is [`S5_MODULE_STATUS_DESIGN.md`](S5_MODULE_STATUS_DESIGN.md)** — the fault
receiver chain and its noise/timing budget, the decoded **module error table** (overcurrent is NOT
per-phase), the Vbus and NTC front-ends with every computed value, the ADC pin choice, and the
netclass-pattern defect found and fixed there.

**S4's deliverable is [`S4_GATE_DRIVE_DESIGN.md`](S4_GATE_DRIVE_DESIGN.md)** — the gate chain, the
skew/deadband budget, the fail-safe table, and the **authoritative DB37 pin table** taken from the
PrimeSTACK datasheet the user supplied mid-session (`datasheets/Infineon-6PS04512E43W39693-DS-v02_00-en-1840455.pdf`).

**S3's deliverable is [`S3_POWER_DESIGN.md`](S3_POWER_DESIGN.md)** — every computed value, datasheet
equation and JLC stock check behind the `power` sheet.

**S2's deliverable is [`ARCHITECTURE.md`](ARCHITECTURE.md)** — power tree + budget, LaunchPad
power policy (jumper table), grounding/shield rules, floorplan, mounting status, and the
root-sheet interface net table. S3–S8 implement that contract; changes to it get logged.

Full roadmap: [`REDESIGN_PLAN.md`](REDESIGN_PLAN.md) — 12 sessions, one per Claude Code session. Exit criteria are gates: do not start a session until its prerequisites are met, do not bleed into the next session's scope.

**Session rhythm** (every session): read this file + current phase → fetch prerequisite datasheets / bench results → make the listed decisions and append them to the Decision Log → capture in KiCad (MCP server) → JLCPCB-vet every new part → ERC (schematic, **`--severity-all`**) / DRC (layout) → update phase marker → `snapshot_project` + git commit.
**Any change that is meant to be layout-only must prove it:** re-export the netlist and diff it
against `tools/schematic_layout/golden.net` — *identical* is the pass condition, and a
self-written parse is not a substitute for `kicad-cli`'s own output (S7.5).

## Firmware cross-reference (AUTHORITATIVE)

Never contradict these without logging a decision; the final board must answer `control_v2_pinmap.md` line by line (S12 firmware-handoff doc).

- `/home/jose/foc-f28379d-fsae/foc_f28379d/config/hw/hw_control_v2.h` — pin map + scaling constants
- `/home/jose/foc-f28379d-fsae/foc_f28379d/docs/control_v2_pinmap.md` — fill-in handoff format
- `/home/jose/foc-f28379d-fsae/foc_f28379d/docs/infineon.md` — PrimeSTACK electrical interface. ⚠ Its "Digital Outputs: LOW (Fault Active)" line is **wrong** and its own error-table note is right; the real datasheet in `datasheets/` settles it — **fault = HIGH** (S4)
- `/home/jose/foc-f28379d-fsae/foc_f28379d/docs/production_bringup.md` — bring-up order + hardware caveats
- `/home/jose/foc-f28379d-fsae/CLAUDE.md` — engineering logbook (bench-measured constants, root-cause analyses)

### Pin map (F28379D 337ZWT on LAUNCHXL-F28379D, BoosterPack sites 1+2)

| Function | MCU pin | Notes |
|---|---|---|
| PWM U high / low | GPIO6 / GPIO7 (EPWM4A/B) | **active-HIGH**, 10 kHz center-aligned, 1500 ns deadband; EPWM4 = master (ADC SOC + sync) |
| PWM V high / low | GPIO8 / GPIO9 (EPWM5A/B) | |
| PWM W high / low | GPIO10 / GPIO11 (EPWM6A/B) | |
| Gate-driver master EN | GPIO66 (out) | **active-HIGH, confirmed S4** — board-local (U8 input A); the module has no enable pin |
| Gate-driver aux EN | GPIO131 (out) | **active-HIGH, confirmed S4** — board-local (U8 input B). On 3.0 it was the AND gate's *VCC*, not a logic input |
| OC fault A / B / C | GPIO25 / GPIO27 / GPIO26 (in, pull-up) | X-BAR INPUT1/2/3 → hardware trip OSHT1–3; trip action = active short (TZA LOW / TZB HIGH). **S5: `MODULE_FAULT_ACTIVE_LOW` → 0 and X-BAR polarity inverted.** ⚠ OC asserts **all three** pins whatever the leg — these bits do NOT identify the phase |
| Over-temperature fault | GPIO64 (in, pull-up) | software read only |
| DC-link OV fault | GPIO52 (in, pull-up) | software read only |
| Encoder SIN / COS | ADCINA2 / ADCINB2 | RM44AC, 1 sin/cos cycle per mech rev (**datasheet order code `01S`, S7**); ×10 pole pairs electrical. **S7: `RES_SINCOS_BIAS_CODE` 3072 → 2039, `RES_SINCOS_AMPL_CODE` 990 → 1745** |
| Phase current A / B / **C** | ADCINB4 / ADCINC4 / **ADCINA5** | **S6: channel C added on ADCINA5 = J7-66**, suggested ADC-A SOC1. J7-65…69 carry the whole block on five contiguous pins. KCL reconstruction becomes optional |
| Current offset refs | ADCINA4 (J7-69) / ADCINB5 (J7-65) | **S6: KEPT** — both read the buffered `ISNS_VREF` ≈1.4685 V through their own 100 Ω + 22 nF buckets. Same node on two converters ⇒ a free ADC-A vs ADC-B cross-check |
| Vbus sense | ADCINC2 (J3-27) | module outputs 6.5 V @ 900 VDC. **S5: `VBUS_DIVIDER_RATIO` 297.14 → 341.538**, full scale 1024.6 V, 0.250150 V/code |
| NTC channel | **ADCINC3** (ADC-C ch3) | **chosen S5** — BoosterPack site-1 **J3-24**; suggest **ADC-C SOC2** (after the SOC1/Vbus EOC that fires the ISR). ADC-D is NOT on the headers. Divider rated for 10 V |
| Status LED | GPIO31 | LaunchPad's own D9 — nothing needed on the board |
| ISR scope probe | GPIO67 | expose a test point (pin unverified on Control_V2) |
| SCI-A debug | GPIO42/43 | LaunchPad USB (XDS100v2) backchannel — **no board connector needed** |

### Analog conditioning targets (from firmware logbook — non-negotiable)

- **ADC VREFHI = 3.0 V.** Every ADC input gets an anti-alias RC at the pin (10 kHz sampling; noise >5 kHz aliases irrecoverably) + charge-bucket cap for the S/H.
- **Encoder:** land **1.5 V bias, ~1.4 V amplitude** at the ADC pins (old board: 2.25 V / 0.725 V = 48% range use + clipping + ~26° elec RMS noise). SIN/COS conditioning must be **matched** (same R/C values, C0G, 1%); firmware auto-calibrates bias/amplitude per ALIGN but rejects sin-vs-cos gain mismatch >30%. ⚠ **S7 revised the amplitude target down to 1.278 V (`RES_SINCOS_AMPL_CODE ≈ 1745`, bias ≈ 2039), deliberately.** The RM44AC is spec'd at 2.2 **±0.2** Vpp; a 1.4 V nominal design clips at the datasheet's max source (peak code 4124 > 4095). Sizing for the worst case costs 6% of range and makes clipping impossible — 85.2% range use vs 3.0's 48%-with-clipping. **What is NOT negotiable is the SIN/COS RC match**: a matched lag is a pure angle delay the firmware already compensates, a mismatch is correctable by nothing.
- **Current:** both sources (internal + LEM) must produce the **same transfer function**, target ~1.5 V bias, full scale **≥ ±300 A** (SW OC trip is 260 A — must fire before ADC saturates). Zero offsets are captured at runtime → **channel-to-channel gain matching matters more than absolute bias**: 0.1% resistors in gain positions, both channels of a stage in one dual op-amp package.
- **Vbus:** fix all three documented problems — source impedance (buffer or low-Z divider + 1–10 nF C0G reservoir; the old 34.5 kΩ needed a 512-cycle S/H workaround), **Kelvin return** for the sensor ground (−52 mV load-dependent IR-drop offset was measured), recompute `VBUS_DIVIDER_RATIO` for ~1000 V full scale.
- **Gates:** PrimeSTACK inputs LOW = 0–1.5 V, **HIGH = 11–15 V**; channel-to-channel skew ≪ 1500 ns deadband.

## Bench-verified facts vs assumptions

**Verified (bench/scope):** encoder = RM44AC sin/cos, already demodulated, 1 cycle/rev; old front-end 2.25 V / 0.725 V; encoder noise 33.5 mV RMS at ADC pin; Vbus divider = 2×69 k, ratio 297.14 + 11.4 code offset.

**Verified in S1 from the 3.0 design files (not bench):** BoosterPack header grid ΔX 43.18 mm / ΔY 63.5 mm; DB37 as-built pin→net map (table below); DB37 jackscrew spacing 63.5 mm.

**Verified in S2 from SPRUI77 (LaunchPad User's Guide, `datasheets/`):** GPIO131 reaches header J6-58 (GPIO66 → J6-59, GPIO130 → J6-57) per Table 4; jumper semantics per §5.2: JP1/JP2/JP3 = USB 3.3 V/GND/5 V links (all three removed → debugger galvanically isolated when powered via BoosterPack headers), JP4/JP5 bridge MCU 3.3 V/5 V to site-2 headers, JP6 = USB-derived 5 V (stays out).

**Verified in S4 from the PrimeSTACK datasheet (`datasheets/`, pages 2 and 6) — no longer assumptions:**
DB37 pin functions for all 37 pins incl. TOP/BOT within each half-bridge; **fault = HIGH**
("open collector, logic low = no fault", max 15 mA); every analog output rated **load max 5 mA**;
digital input network **10 kΩ to GND + 1 nF to GND**, HIGH = on; **one** temperature pin (29);
pins 9/27 are a **15 V/50 mA supply output**, not sensors; pin 1 is **true earth/shield**;
the module has **no enable input pin**, so both firmware enables are board-local.

**Verified in S5 from the same datasheet (p.6 error table, p.3 optional-components table):**
the **error table decodes which pin asserts for which fault** — and **overcurrent in ANY leg
asserts ALL THREE half-bridge error pins**, so `FLT_OC_A/B/C` cannot identify the faulting phase;
only "error driver core HB x" is unique to one pin. Full decode table in `S5_MODULE_STATUS_DESIGN.md` §1.2.
Datasheet also states **"Over temperature shut down must be realized by customer"** — the module
*reports* OT but does not act on it, which makes the NTC channel a safety function, not a convenience.
The p.3 options table shows **only the "Inverter Section" voltage / current / temperature sensors
fitted** (Unit 1 and Unit 3 columns empty), independently confirming S4's single-temperature-pin finding.

**Assumed — MUST bench-verify before the dependent session (see REDESIGN_PLAN.md bench-day checklist):**
- ~~Fault output polarity~~ — **resolved S4 on paper: fault = HIGH.** Bench now only confirms it.
- ~~Enable active levels for GPIO66/GPIO131~~ — **resolved S4: board-local, we define them ACTIVE-HIGH.**
- ~~NTC output level~~ — **no longer blocks S5**: the divider is rated for the full 0–10 V the datasheet specifies. The bench measurement now only calibrates the curve, needed before the OT trip threshold is set.
- Internal current-sensor **bias AND sensitivity** — ~~blocks S6~~ **no longer blocks: S6 is designed to be
  insensitive to it.** ⚠ The "≈7.5–8 mV/A" this file used to list as *bench-verified* was **not measured** —
  `control_v2_pinmap.md` §6 derives 8.0 mV/A as `2.4 V / 300 A` from an *assumed* 2.5 V bias, and the
  separate bench figure of 78.6 mV/A belongs to the bench clamp+amp board, not the module. The datasheet's
  "4.9 V @ 300 A_RMS" admits two readings (8.00 or 5.66 mV/A); S6 sets the gain for the **higher** one so
  neither reading clips. Bench now only reclaims ADC range (one resistor per channel). Polarity never
  blocked anything — `PHASE_ID_DEFAULT_EN` re-detects each channel's sign at every ALIGN
- ~~RM44AC differential vs single-ended, supply V/I, true output levels at the connector~~ — **resolved S7 from the datasheet** (`datasheets/RLS-RM44_RM58-RM4458D01_01.pdf`): **single-ended** VA/VB, **2.2 ±0.2 Vpp**, offset **3/5·Vdd ±5 mV**, **720 Ω** internal series impedance, 5 V ±5 % / 13 mA, LiYCY 4×0.20 mm² shielded. Bench now only confirms. ⚠ **The installed encoder's actual amplitude is still unknown** and cannot be back-calculated from 3.0's bench figures (2.25 V / 1.45 Vpp) because 3.0's channel A was reworked off-board — the two numbers imply two different gains. S7 is designed to span the whole 2.0–2.4 Vpp datasheet range so it does not matter.
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
│                            / S4_GATE_DRIVE_DESIGN.md (S4)
│                            / S5_MODULE_STATUS_DESIGN.md (S5)
│                            / S6_CURRENT_SENSE_DESIGN.md (S6)
│                            / S7_ENCODER_DESIGN.md (S7)
├── tools/schematic_layout/  sheet generators + connectivity/netlist checkers + golden.net (S7.5)
├── datasheets/               SPRUI77 (LaunchPad UG) + **LEM-LA_100-P-v15** (fetched S6)
│                            + **RLS-RM44_RM58-RM4458D01_01** (fetched S7 — the RM44AC output
│                             spec is on p.10 "AC - Analogue sinusoidal outputs", the part
│                             numbering incl. order code 01S on p.20)
│                            + **TE-DTM13-12PA-R005 / -12PB-R005 / -08PA-R004 customer drawings**
│                             (fetched S7 from TE DocumentDelivery, no login — J3/J4 footprint source)
│                            + **Infineon-6PS04512E43W39693-DS-v02_00**
│                            (user-supplied S4 — the authoritative DB37 pinout is on p.6,
│                             the controller-interface electrical table on p.2,
│                             the mechanical drawing with the mounting pattern on p.5)
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

**Appended in S7 (49 → 51 symbols):** `Conn_02x06_Counter_Clockwise` (KiCad `Connector_Generic` —
its 1..6 / 12..7 numbering is exactly the DTM13 pin order) and `BAT54S` (KiCad `Diode`, 3-pin series
pair: 1=A 2=K 3=COM). Both are standalone definitions — checked for `extends` before copying, per
S6's lesson — and were copied by script rather than by the MCP `import_symbol`. New footprint:
**`DEUTSCH_DTM13-12P-R005_Horizontal`** (41 → 42), hand-derived from TE's customer drawings; full
derivation in `S7_ENCODER_DESIGN.md` §8.3. `BAT54S` reuses S3's `SOT-23`. Library revalidated:
**51/51 symbols (53 SVGs) and 42/42 footprints**.
⚠ **Footprint names in this library carry the metric suffix** — `R_0603_1608Metric`,
`C_0805_2012Metric`, `L_0805_2012Metric`. The inventory table below abbreviates them; assigning the
abbreviated name silently produces `footprint_link_issues` at ERC (S7 hit this on 33 parts).

**Appended in S6 (47 → 49 symbols):** `OPA2376` (dual precision RRIO op-amp) and
`Conn_02x04_Odd_Even` (KiCad `Connector_Generic`). New footprint:
`Molex_Micro-Fit_3.0_43045-0800_2x04_P3.00mm_Horizontal` (40 → 41). Library revalidated:
**49/49 symbols (51 SVGs) and 41/41 footprints**.
⚠ **`OPA2376` is a hand-flattened single-unit symbol**, like `UCC27524D` and `74LVC1G11` already
were — one body, all 8 pins. KiCad's `Amplifier_Operational:OPA2376xxD` is a *derived* symbol
(`extends "LM2904"`), and the MCP `import_symbol` copied it **without its parent**, producing a
library that would not load at all. `kicad-cli sym export svg` caught it in one command. **Always
re-export SVGs after any library edit, and never import a symbol whose definition contains
`extends` without its parent.**

**Appended in S5 (46 → 47 symbols):** `74LVC2G17` (KiCad `74xGxx`, dual non-inverting Schmitt buffer; DBV pinout 1=1A 2=GND 3=2A 4=2Y 5=VCC 6=1Y cross-checked against TI SCES381N). No new footprints — it reuses S4's `SOT-23-6`. Library re-validated: **47/47 symbols (49 SVGs, the 3-unit symbol renders 3) and 40/40 footprints**. S5 also normalised the leading-tab indentation of the four MCP-imported symbols (`UCC27524D`, `74LVC1G11`, `PGND_MOD`, `74LVC2G17`) — cosmetic only; KiCad's parser is whitespace-insensitive.

**Appended in S4 (43 → 46 symbols):** `UCC27524D` (KiCad `Driver_FET`), `74LVC1G11` (KiCad `74xGxx`, pinout cross-checked against TI SCES487I: 1=A 2=GND 3=B 4=Y 5=VCC 6=C), and power symbol `PGND_MOD` (KiCad `GNDPWR` renamed — kept for symmetry with the other rail symbols even though the sheets express power nets as **global labels**, which is the convention S3 established).

**Appended in S3 (28 → 43 symbols):** `LMR33640ADDA` + `LMR33630ADDA`, `TPS62933` + `TPS62933F`, `AP1117-15` + `AMS1117-3.3`, `Conn_01x02`, `MOSFET_P_GDS`, `D_TVS_Unidirectional`, `Converter_DCDC_URA-YMD_Dual`, `TPS54360DDA` (from the reverted detour, now unused), and power symbols `+24V_IN` `+24V_PROT` `+24V_MOD` `+13V5_GATE`.
- `MOSFET_P_GDS` is KiCad's `IRF9540N` renamed — it is the P-channel symbol with **numeric 1=G / 2=D / 3=S** pins that map to TO-252. `Device:Q_PMOS` uses letter pin *numbers* and cannot map to a footprint.
- `D_TVS_Unidirectional` is `D_Zener` renamed: KiCad ships only **bidirectional** TVS symbols (A1/A2 pins) and the SMCJ26A is unidirectional, so the zener glyph is both electrically correct and unambiguous about K/A polarity.
- `+12V` and `+24V` remain in the library but are now **unused** (superseded by `+13V5_GATE` / `+24V_IN`).

`+15V_ISO` / `-15V_ISO` are KiCad's `+15V` / `-15V` renamed so the power symbol drives the isolated-rail net names used in the net convention below. All BOM-bearing symbols carry an empty hidden **`LCSC`** property so the field is always present in the symbol-fields table.

### Footprint library inventory

`R_0603/0805/1206/2512` · `C_0603/0805/1206/1210` · `L_0805/1206` · `PinHeader_2x10_P2.54mm_Vertical` · `PinSocket_2x10_P2.54mm_Vertical` · `DSUB-37_Socket_Horizontal_P2.77x2.54mm_MountingHoles` · `TestPoint_Pad_D1.5mm` · `TestPoint_THTPad_D1.5mm_Drill0.7mm` · `MountingHole_3.2mm_M3` · `MountingHole_3.2mm_M3_Pad` · `SolderJumper-2_P1.3mm_Open` · `SolderJumper-3_P1.3mm_Open_NumberLabels`

**Appended in S4 (38 → 40 footprints):** `SOIC-8_3.9x4.9mm_P1.27mm` · `SOT-23-6` — both straight re-exports of KiCad standards.

**Appended in S3 (19 → 38 footprints):** `Texas_HSOP-8-1EP_3.9x4.9mm_P1.27mm_ThermalVias` · `D_SMC` · `L_Sunlord_SWPA8040S` · `SOT-583-8` · `SOT-223-3_TabPin2` · `TO-252-2` · `SOT-23` · `D_SMA` · `D_SMB` · `Fuse_1206_3216Metric` · `CP_Elec_8x10.5` · `LED_0603_1608Metric` · `NetTie-2_SMD_Pad0.5mm` · `Molex_Mini-Fit_Jr_5566-02A_2x01_P4.20mm_Vertical` · `L_Changjiang_FNR8040S` · `L_Changjiang_FNR5040S` (exact matches for the chosen inductors) — plus two **derived** because KiCad ships neither:

- **`Fuse_2410_6125Metric`** — Littelfuse 451/453 recommended land: pads 1.96 × 3.15 mm, gap 2.95 mm, centres ±2.455 mm, span 6.86 mm; body 6.10 × 2.69 × 2.69 mm.
- **`Converter_DCDC_Mornsun_URA-YMD-6WR3_THT`** — from the URA_YMD-6WR3 datasheet Top View (PCB Layout): 25.40 × 25.40 mm, Ø1.0 mm pins / Ø1.5 mm holes, 2.54 mm grid, columns 20.32 mm apart, pins 3–5 spanning 20.32 mm, pins 1–2 5.08 mm apart straddling the centre. Pin-out **1=GND(−Vin) 2=Vin 3=+Vo 4=0V 5=−Vo**.

Both libraries were validated by a full KiCad parse — S1: `sym export svg` → 28/28, `fp export svg` → 19/19; **S3: 43/43 symbols and 38/38 footprints; S4: 46/46 and 40/40**. Note the MCP `import_symbol` writes imported symbols at column 0, so run `kicad-cli sym upgrade` afterwards to restore canonical formatting.

## DB37 — v4.0 pin table (AUTHORITATIVE, from the datasheet, frozen S4)

Source: `datasheets/Infineon-6PS04512E43W39693-DS-v02_00-en-1840455.pdf` **p.6 circuit diagram**.
Module connector is **SUB-D 37 male, UNC 4-40 female thread**; the board carries the socket.
Full derivation, level maths and timing budget: [`S4_GATE_DRIVE_DESIGN.md`](S4_GATE_DRIVE_DESIGN.md).

| Pin | Module function | v4.0 net | Pin | Module function | v4.0 net |
|---|---|---|---|---|---|
| 1 | True earth / shield | `SHIELD_DB37` | 20 | HB A IGBT **BOT** | `PWM_UL_15V` |
| 2 | HB A error | `FLT_OC_A_15V` | 21 | HB A IGBT **TOP** | `PWM_UH_15V` |
| 3 | HB B IGBT **BOT** | `PWM_VL_15V` | 22 | HB B error | `FLT_OC_B_15V` |
| 4 | HB B IGBT **TOP** | `PWM_VH_15V` | 23 | HB C IGBT **BOT** | `PWM_WL_15V` |
| 5 | HB C error | `FLT_OC_C_15V` | 24 | HB C IGBT **TOP** | `PWM_WH_15V` |
| 6 | Temp. error | `FLT_OT_15V` | 25 | GND digital | `GND` |
| 7 | Voltage DC-link | `VBUS_SNS_RAW` | 26 | 13–30 V supply in | `+24V_MOD` |
| 8 | 13–30 V supply in | `+24V_MOD` | 27 | **15 V/50 mA OUT** | `MOD_AUX15V_2` (TP18) |
| 9 | **15 V/50 mA OUT** ¹ | `MOD_AUX15V_1` (TP17) | 28 | GND (supply return) | `PGND_MOD` |
| 10 | GND (supply return) | `PGND_MOD` | 29 | Temperature (NTC) | `NTC_1_RAW` — **rate 10 V** |
| 11 | GND analog | `VBUS_RTN` (Kelvin) | 30 | HB A current | `ISNS_A_RAW` |
| 12 | GND analog | `ISNS_RTN` | 31 | HB B current | `ISNS_B_RAW` |
| 13 | GND analog | `ISNS_RTN` | 32 | HB C current | `ISNS_C_RAW` |
| 14 | NC | no-connect | 33 | NC | no-connect |
| 15 | NC | no-connect | 34 | NC | no-connect |
| 16 | Voltage error | `FLT_OV_15V` | 35 | NC | no-connect |
| 17 | NC | no-connect | 36 | NC | no-connect |
| 18 | NC | no-connect | 37 | GND digital | `GND` |
| 19 | GND digital | `GND` | G1/G2 | shell | `SHIELD_DB37` |

¹ **Pins 9 and 27 are two pins of the SAME 15 V / 50 mA auxiliary rail, and "PTC" is the FUSE that
protects it — not a temperature sensor.** The p.6 "Out" group draws the IEC **fuse symbol labelled
PTC** in a legend box, in exactly the same style and position as the *two solid fuse symbols* the
"In" group draws for the 13–30 V feed on pins 8/26. A PTC resettable fuse (polyfuse) is what limits
that output to 50 mA. Infineon presumably names it PTC because the rail is *intended* for exciting a
customer-built motor-PTC circuit — which is very likely how "PTC" became a signal name on 3.0's
schematic. **There is no PTC/thermistor interface on this connector**; the module's only temperature
output is pin 29. Duplicated pins are this connector's habit (8/26, 10/28, 19/25/37, 11/12/13).
v4.0 still keeps `MOD_AUX15V_1`/`_2` as **two separate nets**: merging them would be correct and
would share current, but at 50 mA that buys nothing, whereas separate nets stay safe even if this
reading is wrong.

**Controller interface, datasheet p.2 — the numbers every downstream sheet needs:**

| Parameter | Value |
|---|---|
| Aux supply | 18–30 V, 40 W max (connector itself accepts 13–30 V) |
| Digital input | `0–1.5 V` LOW / `11–15 V` HIGH, **logic high = on**, network **10 kΩ to GND + 1 nF to GND** |
| Digital output | open collector, **logic low = no fault** ⇒ **FAULT = HIGH**, sink ≤ **15 mA**, ≤ 15 V |
| Current sensors | 4.7 / 4.9 / 5.0 V at 300 A_RMS, **load max 5 mA** |
| DC-link sensor | 6.4 / 6.5 / 6.6 V at 900 V, **load max 5 mA** |
| NTC (inverter section) | **10 V** at T_NTC = 82 °C, **load max 5 mA** |
| Over-current shutdown | 625 A_peak within 15 µs (module's own) |
| EMC | 1 kV burst on the control interface, 1 kV surge on the 24 V aux |

### 3.0 as-built map (SUPERSEDED — kept only to show what changed)

**34 of 37 pins agree with the datasheet** — the 26 functional pins plus the 8 NC pins 3.0 correctly
left dangling. **Every pin that carries traffic was right in 3.0** (6 gates incl. TOP/BOT within each
leg, 5 faults, 3 phase currents, Vbus, temperature, 24 V in + return, all grounds) and v4.0 keeps
them identical. The interface working on the bench is fully consistent with this.

Only **three** pins change, and none of them are in a signal path:

| Pin | 3.0 did | Reality | What it actually was |
|---|---|---|---|
| **27** | tied to GND | 15 V/50 mA supply **output** | The one genuine electrical mistake — a supply output shorted to ground. **Self-protecting and symptomless**: that output's own PTC resettable fuse (see ¹) trips, goes high-resistance and holds at a small leakage current. Nothing in the signal chain depends on the rail. |
| **9** | divided → header, read as a "PTC" temperature | same 15 V/50 mA output | Dead circuit — reads a constant, not a temperature. Firmware never sampled it (`NTC channels: none today`). Harmless. |
| **1** | tied to GND | "True earth/shield", bonded to module chassis internally | **Not an error.** A hard chassis-to-signal-GND bond is a legitimate choice; it only conflicts with the *soft-tie* policy S2 adopted for v4.0. |

The phantom **NTC#2 channel was an S2 error of ours**, in `ARCHITECTURE.md` §8 — inferred from
`infineon.md`'s spec table listing two NTC part numbers. 3.0 never claimed a second temperature pin.

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

### Parts appended in S4

| Part | LCSC | JLC | Stock | Notes |
|---|---|---|---|---|
| **UCC27524DR** dual 5 A driver, SOIC-8 | C465729 | Ext | 9 550 | U5–U7. VDD 4.5–18 V; TTL input/enable thresholds **independent of VDD**; IN pins pull DOWN 120 kΩ, EN pins pull UP 200 kΩ; outputs LOW during UVLO |
| **SN74LVC1G11DBVR** 3-in AND, SOT-23-6 | C22046 | Ext | 10 443 | U8 enable combiner. Pinout 1=A 2=GND 3=B 4=Y 5=VCC 6=C |

### Parts appended in S7

| Part | LCSC | JLC | Stock | Notes |
|---|---|---|---|---|
| **10.0 kΩ 0603 0.1 %** Yageo RT0603BRD0710KL | C95204 | Ext | 546 640 | R108/110/113/115 — difference-amp input resistors |
| **3.00 kΩ 0603 0.1 %** Yageo RT0603BRD073KL | C136963 | Ext | 116 222 | R105 — reference-chain top |
| **BAT54S** dual series Schottky, SOT-23 | C7420333 | **Preferred** | 314 690 | D10/D11 — ADC clamp to +3V3/GND |
| **Ferrite 600 Ω @100 MHz** GZ2012D601TF, 0805 | C1017 | **Basic** | 369 732 | FB1 — encoder supply. **Must be a ferrite, not a resistor**: the reference chain hangs off the same node, so only a near-zero DCR keeps the bias cancellation exact |
| **DEUTSCH DTM13-12PA-R005** (key A) / **-12PB-R005** (key B) | — | **CONSIGNED** | — | J3 (LEM) / J4 (encoder) |

⚠ **Fourth time: pick the value from live stock, not the E96 table.** 3.01 kΩ 0.1 % (C705772) has
**1 175** in stock and 3.09 kΩ (C861371) **2 980**; the E24 value **3.00 kΩ** has 116 222.

Everything else S7 places comes from the existing kit: 4.99 k 0.1 % `C723532`, 12.0 k 0.1 %
`C326735`, 100 Ω `C22775`, 1 MΩ `C22936`, 0 Ω `C21189`, 1 nF C0G `C106246`, 2.2 nF C0G `C107043`,
22 nF 0805 C0G `C77069`, 100 nF `C14663`, 1 µF/0805 `C28323`, 10 µF/0805 `C15850`, OPA2376 `C46316`.
**S7 introduces no new C0G value** — it reuses 1 nF, 2.2 nF and 22 nF, which **closes the standing
"standardise C0G values" item**: the set is still exactly four (1 nF, 2.2 nF, 4.7 nF, 22 nF).

### Parts appended in S6

| Part | LCSC | JLC | Stock | Notes |
|---|---|---|---|---|
| **OPA2376AIDR** dual precision RRIO op-amp, SOIC-8 | C46316 | Ext | 10 213 | U12–U15. Chosen for output swing (the internal stage must reach **0.060 V**), 25 µV V_os / 0.25 µV/°C (drift *between* calibrations does not cancel), RRI for the 0.04 V common mode. Gain is resistor-set, so precision was not the binding constraint |
| **20.0 kΩ 0603 0.1 %** Yageo RT0603BRD0720KL | C723637 | Ext | 210 576 | internal-stage input resistors |
| **12.0 kΩ 0603 0.1 %** Yageo RT0603BRD0712KL | C326735 | Ext | 38 454 | internal-stage feedback + LEM-stage input + reference divider top |
| **4.99 kΩ 0603 0.1 %** Yageo RT0603BRD074K99L | C723532 | Ext | 92 725 | LEM-stage feedback + reference divider bottom |
| **47.0 Ω 1206 0.1 %** Yageo RT1206BRD0747RL | C870760 | Ext | 5 052 | LEM burden, **two in parallel per channel** = 23.5 Ω |
| **Micro-Fit 3.0 2×4 right-angle** HC-MX3.0-2*4AW | C3294385 | Ext | 14 802 | J3, LEM harness. ⚠ Micro-Fit-compatible clone, not genuine Molex (43045-0812 has **8** in stock) — S12 must check its drawing against the footprint |

⚠ **Do not consolidate the two 12 kΩ lines.** `C22790` (1 %, S3, U1's FB divider) and `C326735`
(0.1 %, S6 gain positions) are different parts for different jobs.

⚠ **Same trap as S3/S5, third time.** The "natural" 0.583 gain pair needs 5.76 kΩ (**3** in stock)
or 5.90 kΩ (1 879). **20.0 k / 12.0 k** was picked from live stock — and happens to give
G = 0.600 exactly, landing the ADC bias on exactly 1.500 V. See `S6_CURRENT_SENSE_DESIGN.md` §6.

Everything else S6 places comes from the S1/S3 kit: 1 MΩ `C22936`, 100 Ω `C22775`, 0 Ω `C21189`,
2.2 nF C0G `C107043`, 4.7 nF C0G `C85980`, 1 nF C0G `C106246`, 22 nF 0805 C0G `C77069`,
100 nF `C14663`, 1 µF/0805 `C28323`, 10 µF/1206 `C13585`.
**S6 introduces no new C0G value** — it reuses four existing lines, closing its half of the
standing "standardise C0G values" item.

### Parts appended in S5

| Part | LCSC | JLC | Stock | Notes |
|---|---|---|---|---|
| **SN74LVC2G17DBVR** dual non-inverting Schmitt buffer, SOT-23-6 | C10429 | Ext | 107 122 | U9–U11 fault receivers. V_CC 1.65–5.5 V; inputs accept 5.5 V; **Ioff** (partial power down) — the property that makes a dead board-3V3 read as FAULT |
| **2.20 kΩ 0603 0.1 %** Yageo RT0603BRD072K2L | C861295 | Ext | 38 458 | R57, Vbus divider top |
| **1.50 kΩ 0603 0.1 %** Yageo RT0603BRD071K5L | C705741 | Ext | 33 446 | R58, Vbus divider bottom — same RT0603B family as R57 so the *ratio* tracks over temperature |

⚠ **There is no hex non-inverting Schmitt at JLC.** `SN74LVC17A` returns **zero** results, which
is why the design is 3 × dual instead of 1 × hex. The hex *inverting* parts do exist
(`SN74LVC14APWR` C7663, 87 k; `74HC14D` C5605 **Basic**, 323 k) and using one would even have
preserved `MODULE_FAULT_ACTIVE_LOW = 1` — rejected because hidden inversion between connector and
GPIO is a bench trap, and because 74HC has no `Ioff`.

⚠ **Do not "improve" the Vbus divider to 2.32 k / 1.65 k.** That pair gives a closer ratio
(999.4 V full scale vs 1024.6 V) but the 1.65 k 0.1 % line has **673** in stock against 33 446 —
the same trap as the S3 divider values. See `S5_MODULE_STATUS_DESIGN.md` §2.2.

Everything else S5 places comes from the S1/S3 kit: 4.7 kΩ `C23162`, 10 kΩ `C25804`,
12 kΩ `C22790`, 3.3 kΩ `C22978`, 1 nF C0G `C106246`, **22 nF 0805 C0G `C77069`**,
100 nF `C14663`, 1 µF/0805 `C28323`. **S5 introduces no new C0G value.**

⚠ **The roadmap's TC4468 is unbuildable at JLC** — 14 in stock (TC4468COE: 4, TC4469COE: 18,
MIC4468ZWM: 25, UCC27523D: 79). The whole TC446x quad family is out. That, not a technical
preference, is why the design is 3× dual instead of 2× quad.

Everything else S4 places comes from the S1/S3 kit: 100 Ω `C22775`, 10 kΩ `C25804`,
**4.7 kΩ `C23162`**, 1 kΩ `C21190`, 680 Ω `C23228`, 1 MΩ `C22936`, 1 µF/0805 `C28323`,
100 nF `C14663`, 10 µF/1206 `C13585`, 1 nF C0G `C106246`, red LED `C2286`.
**S4 introduces no new C0G value** — it reuses the 1 nF line.

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
- **Schematic drawing (S7.5, binding on every sheet from S8 on):** components placed by
  **signal flow, left → right**, functional blocks separated, repeated channels drawn
  **geometrically identical** so a mismatch is visible. **Local nets are carried by wires;
  labels only where a wire would have to cross** something — plus the genuinely sheet-spanning
  nets (rails, `GND`, cross-sheet signals). Every label sits **on a wire endpoint or a pin**,
  never floating. Notes go in non-overlapping columns inside the frame. Tooling + the four
  KiCad traps that make hand-generated sheets fail silently:
  [`tools/schematic_layout/README.md`](tools/schematic_layout/README.md).
  ⚠ **This supersedes the "connectivity is by net labels at pins" pattern** used in S3–S7;
  those Decision Log entries describe how those sheets *were* captured, not how to capture new ones.
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
  **S4 update:** added `PGND_MOD` → Power_3A (module aux return, up to 2.2 A on dedicated copper),
  `PWM_*_DRV` and `GATE_EN*` / `GATE_ILOCK_3V3` → Gate. **22 patterns total.**
  **S5 update — [BUG FIX] every path-sensitive pattern was silently matching nothing.** KiCad
  matches netclass patterns against the **full, path-qualified net name** (`/gate_drive/PWM_UH_15V`),
  not the base name, so any pattern anchored at the start never fired. **24 nets were sitting on
  `Default`, including the entire gate bus and both Kelvin sense pairs.** Only the global power
  nets worked (their names carry no sheet path) and `*_ADC` (already wildcard-led) — which is why
  it went unnoticed for four sessions. The ten path-sensitive patterns are now `*`-prefixed:
  **`*PWM_*_15V` `*DRV_EN*` `*ISNS_*` `*ENC_*` `*VBUS_*` `*NTC_*` `*PWR_U*_SW` `*PWM_*_DRV`
  `*GATE_EN*` `*GATE_ILOCK_3V3`**. Still 22 patterns; no netclass *values* changed (S9 owns those).
  Result: 51 Default / 17 Gate / 11 Analog / 8 Power_1A / 5 Power_3A, netlist byte-identical.
  **Any new pattern must start with `*` unless it names a global power net.**
  **S6 update:** added **`*LEM_*`** → Analog (the LEM secondary nets `LEM_A/B/C_M`). **23 patterns.**
  Verified empirically against the exported netlist, not by eye: all 27 `current_sense` signal nets
  resolve to **Analog**, `SHIELD_LEM` stays Default (matching `SHIELD_DB37`). Project-wide:
  125 nets = 52 Default / **43 Analog** / 17 Gate / 8 Power_1A / 5 Power_3A.
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
- 2026-08-29 — S3 — **`power` sheet captured: 79 components, 30 nets, ERC 0 violations on the sheet**, netlist verified node-by-node. Connectivity is by net labels at pins rather than drawn wires — electrically verified but visually dense around U1/U2; a wire-stub tidy-up is logged as a cosmetic follow-up. **[SUPERSEDED S7.5 — the sheet is now wired; the labels-at-pins pattern is no longer the convention.]** Both bucks' datasheet layout rules are written onto the sheet as text notes for S10.
- 2026-08-29 — S3 — **REVERTED the gate-rail buck back to LMR33630ADDAR (C841384)** after user challenge. The 60 V TPS54360B swap rested on the S2 assumption `+24V_IN 18–30 V`, which I inherited from ARCHITECTURE.md §1 and never confirmed. **User confirmed the LV rail max is ≤26 V [ARCH CHANGE: input range now 18–26 V]**, which makes a 36 V part correct. Reverting is also a net simplification: synchronous (no catch diode), internally compensated (no R/C/C network), fixed 400 kHz (no R_T) — **5 fewer parts and better efficiency**. FB divider recomputed for **V_ref = 1.000 V** (not 0.8 V): **150 kΩ / 12 kΩ → exactly 13.500 V**, both JLC Basic with >400 k stock. UVLO now via EN divider 100 k/10 k → rising 13.5 V, falling 12.4 V (both already in the S1 kit). L1 **47 µH → 22 µH** (C15857) per TI's ripple rule using the device's 3 A rating = 24.6 %; the rail runs PWM above ~0.35 A and PFM below, which is fine because it feeds only gate drivers and U2's FCCM input.
- 2026-08-29 — S3 — **Lesson logged: two justifications were stacked for one decision.** The LMR33630 was dropped citing *both* PFM behaviour *and* voltage headroom, when only the voltage argument was load-bearing — and that one rested on an unverified inherited assumption. The PFM concern is real only on the **5 V** rail (which feeds the analog front-ends); the gate rail's light-load mode does not matter. **The TPS62153 → TPS62933F swap therefore stands** and is independent of input voltage.
- 2026-08-29 — S3 — **TVS changed SMBJ33A → SMCJ26A (C310042).** The genuinely valid finding from the reverted detour was about the *TVS*, not the buck: SMBJ33A's breakdown is **36.7–40.6 V**, which straddles the LMR33630's **38 V absolute max** — that S2 pair was broken. Both SMBJ26A and SMCJ26A quote a 42.1 V clamp, but the 1500 W SMCJ reaches it at **35.6 A** vs the 600 W SMBJ's **14.3 A**, so at a realistic surge the SMCJ sits around 30–34 V, safely under 38 V. Stand-off 26 V matches the confirmed rail max. Do not substitute an SMBJ.
- 2026-08-29 — S4 — **[MAJOR] The PrimeSTACK datasheet arrived and replaced inherited guesswork.** The user supplied `datasheets/Infineon-6PS04512E43W39693-DS-v02_00-en-1840455.pdf` mid-session. Page 6 is the DB37 circuit diagram, page 2 the controller-interface electrical table. The v4.0 pin table above is now **sourced, not inherited** — including TOP/BOT within each half-bridge, which was the one thing I could not have verified from 3.0 alone.
- 2026-08-29 — S4 — **Fault polarity resolved: FAULT = HIGH.** Datasheet p.2: *"Digital output level: open collector, **logic low = no fault**, max 15 mA"*, matching p.6's *"X = high level with required external pull-up"*. `hw_control_v2.h`'s `MODULE_FAULT_ACTIVE_LOW 1` is **inverted** and must become 0 (with the Input X-BAR trip polarity flipped alongside). Bonus: a disconnected DB37 pulls the fault lines HIGH through their pull-ups, so **fail-safe is inherent**. **Bench item #1 no longer blocks S5** — the bench now only confirms.
- 2026-08-29 — S4 — **Module analog outputs are rated `load max 5 mA` each.** S5 may therefore use a plain low-Z resistive divider on Vbus — **no buffer op-amp needed**. Bench item #4 no longer blocks S5.
- 2026-08-29 — S4 — **[ARCH CHANGE] `NTC_2_RAW` and `NTC_2_ADC` retired.** The connector has exactly **one** temperature pin (29) and the options table shows only the inverter-section sensor fitted, so pin 29 is the **10 V** NTC2 channel. Sheet pins and labels deleted from root / `gate_drive` / `module_status` / `launchpad`. S5 must rate that divider for 10 V, not 4.9 V.
- 2026-08-29 — S4 — **DB37 pins 9 and 27 are a 15 V / 50 mA supply OUTPUT (for a PTC), not sensors.** 3.0 tied **pin 27 straight to GND** — a permanently shorted supply output — and divided pin 9 into a header as if it were a temperature reading. v4.0 lands both on test points (`MOD_AUX15V_1/2`, TP17/TP18). Potentially useful later to excite the Emrax PTC.
- 2026-08-29 — S4 — **DB37 pin 1 is "true earth/shield", not GND.** 3.0 hard-tied it to signal ground. v4.0 puts pin 1 on `SHIELD_DB37` together with the shell pins G1/G2, soft-tied via **1 nF C0G ∥ 1 MΩ** with **JP2** to make it a hard tie — exactly the S2 shield policy, which 3.0 predated.
- 2026-08-29 — S4 — **Gate driver = 3 × UCC27524DR (C465729), NOT the roadmap's 2 × TC4468.** Availability was checked first as the roadmap demands, and the entire TC446x/MIC446x quad family is dead at JLC (TC4468: **14** in stock; TC4468COE: 4; MIC4468: 25; UCC27523: 79) against **9 550** for the UCC27524. Functionally identical for us — non-inverting channel with a per-channel enable — at three duals instead of two quads. Its enabling property is that **input and enable thresholds are fixed and independent of VDD** and those pins are rated −5…+20 V regardless of VDD, so one stage spans 3.3 V → 13.5 V.
- 2026-08-29 — S4 — **The module has NO enable input pin**, so both firmware enables are board-local and **we** define their active level: **ACTIVE-HIGH**, as `hw_control_v2.h` assumes. **Bench item #2 no longer blocks S4.** It was only ever open because 3.0 wired GPIO131 to the AND gate's **VCC** rather than to a logic input — the aux "enable" was a supply switch.
- 2026-08-29 — S4 — **Hardware interlock kept, done safely (user decision).** `GATE_EN_3V3 = DRV_EN(GPIO66) ∧ DRV_EN_AUX(GPIO131) ∧ SW_MAIN_3V3`, in one SN74LVC1G11 powered from the board's own +3V3. **JP1 is an exclusive 3-pad solder jumper** (1-2 = interlock active, default; 2-3 = bypass to +3V3 for bench) so the two sources can never fight — 3.0's 2-pad `BYPASS0` shorted across a driven signal. **[ARCH CHANGE] new hierarchical net `SW_MAIN_3V3` into `gate_drive`** (root sheet pin added; the net already existed vehicle_io → launchpad). No RC filter on this path: filtering would delay *de-assertion*, the unsafe direction — conditioning belongs in `vehicle_io` (S8).
- 2026-08-29 — S4 — **Series damping R18–R23 = 100 Ω, and the datasheet's own input network (10 kΩ + 1 nF C0G to GND) is fitted at the DB37.** Worst case the module has it too, giving 5 kΩ ∥ 2 nF. Levels: rail 13.500 V ±2 % ⇒ module sees **12.95…13.62 V**, i.e. **+1.95 V over the 11 V floor and +1.38 V under the 15 V ceiling**. At the 12.0 V rail that was rejected in S3 the same maths gives only 0.52 V of floor margin — **the 13.5 V decision is now quantitatively validated**. Do not lower the 100 Ω in S10: it is what caps the driver's peak current at 127 mA (of 5 A) and damps the harness at the source.
- 2026-08-29 — S4 — **Skew budget closed: 53 ns worst case = 3.5 % of the 1500 ns deadband**, and the *effective* deadtime at the module is **1399 ns** (93 % of nominal) after the asymmetric RC threshold crossings (rise-to-11 V 380 ns vs fall-to-1.5 V 481 ns). Contributions: 27 ns device-to-device, 2 ns in-package (which is the H/L pair of one leg), 24 ns from C0G ±5 %. Matched R (1 %) and C (C0G) on all six channels is what keeps it there — S10 must also match trace length.
- 2026-08-29 — S4 — **[SAFETY] Reset-state pull-downs sized at 4.7 kΩ, not 100 kΩ.** The F28379D powers up with **GPIO pull-ups enabled** (worst case ≈24 kΩ). With 100 kΩ pull-downs the enable inputs would sit at 2.66 V and the PWM inputs at 2.75 V — i.e. **all six gates armed while the MCU is in reset**. 4.7 kΩ puts both at ≈0.53 V, under the worst-case low threshold, at a cost of 0.70 mA per line from a 4 mA-capable GPIO. R30–R32 and R36–R41 exist for this reason and must not be raised. Surfaced by ERC (`pin_not_driven` on pins with no other net member) — a rules check catching a real hazard, not a cosmetic one.
- 2026-08-29 — S4 — **`GATE_EN_3V3` pull-down R33 = 1 kΩ.** Six UCC27524 enable pins present 6 × 200 kΩ = 33.3 kΩ of internal pull-up **to 13.5 V**; a conventional 10 kΩ pull-down would sit at 3.1 V and *enable* the drivers if U8's output ever went high-Z. 1 kΩ gives 0.39 V (0.76 V even if the internal pull-ups were 100 kΩ), under the 0.8 V worst-case threshold.
- 2026-08-29 — S4 — **[ARCH CHANGE] new global net `PGND_MOD`** for DB37 pins 10/28, tied to `GND` at exactly one place: **NT2 on the `power` sheet, at the 24 V entry star**. Keeping it a distinct net until that tie is what makes S2's "dedicated copper, never through the plane under analog" rule enforceable by DRC rather than a layout wish — and it structurally prevents 3.0's defect of bridging GND↔P_GND at two separate net-ties.
- 2026-08-29 — S4 — **`gate_drive` captured: 56 components, 44 nets, ERC 0 violations on the sheet**, netlist verified node-by-node against a hand-written expected-membership table (44/44, zero mismatches). Root-sheet ERC is down to 90 `label_dangling` + 37 `isolated_pin_label` from the S2 baseline of 160 — the documented empty-hierarchy noise, burning down as S5–S8 fill sheets. Skew budget, fail-safe table, polarity chain, DB37 pin table and S10 layout rules are all written onto the sheet as text notes.
- 2026-08-29 — S4 — **Lesson logged: "vet availability first" earned its place in the roadmap.** Had the TC4468 design been drawn before the stock check, the whole enable architecture (quad AND-input driver, 8 channels, enable as the second AND input) would have been built around a part with 14 units in stock, and the rework would have touched every net on the sheet. The check cost one API call.
- 2026-08-29 — S4 — **Windfall for S9: the mechanical drawing is page 5 of the same datasheet** — 215 × 280 mm body, mounting pattern with Ø9.2 and Ø11×10-deep holes, M8×14-deep and M6×11-deep threads, dimensions 195 / 143.2 / 155 / 93 / 31 / 62 / 242.6 / 260, plus the X1 SUB-D position and G1/2" coolant threads. The long-standing "[user, before S9] measure the module top face" item is very likely closed by it; S9 extracts the pattern properly rather than S4 bleeding scope.

- 2026-08-29 — S5 — **[MAJOR FINDING] The datasheet's p.6 error table decoded: overcurrent is NOT per-phase.** An OC in any leg asserts **all three** half-bridge error pins (2/22/5); only "error driver core HB x" is unique to one pin. `FLT_OC_A/B/C` therefore cannot attribute the fault to a phase — firmware must stop implying they can, and use the decode table in `S5_MODULE_STATUS_DESIGN.md` §1.2 instead. Also from p.6/p.2: **"Over temperature shut down must be realized by customer"** — the module reports OT but does not act on it, so the NTC channel is a *safety function*. The p.3 options table (only the Inverter-Section sensors fitted) independently confirms S4's single-temperature-pin reading.
- 2026-08-29 — S5 — **Fault pull-up = 4.7 kΩ to `+13V5_GATE`, then a 10 k/4.7 k divider into a Schmitt.** Levels at the DB37 pin: 0.15 V no-fault (module sinks 2.84 mA of its 15 mA budget) / 10.23 V fault; the receiver trips between 2.60 V and 7.32 V referred to that pin ⇒ **2.45 V / 2.91 V of noise margin**. A 5 V pull-up needing no divider was considered and **rejected**: it leaves only 0.5 V on the low side, and that budget has to absorb *module-GND shift across the harness*, not just board noise. 3.0's 82 kΩ is 17× too weak.
- 2026-08-29 — S5 — **Receiver = 3 × SN74LVC2G17 (C10429), non-inverting.** The hex non-inverting SN74LVC17A **does not exist at JLC** (zero results), so it is 3 duals not 1 hex. Non-inverting is deliberate — a hex *inverting* part is in stock and would even have preserved `MODULE_FAULT_ACTIVE_LOW = 1`, but hidden inversion between connector and GPIO is a bench trap. **`Ioff` is load-bearing:** board +3V3 (AMS1117 off +5V) can die while the LaunchPad lives on its own LDO from the same +5V; with Ioff the outputs go high-Z and the GPIO pull-ups read **FAULT**. Fail-safe also holds for an unplugged DB37 — all five lines float high.
- 2026-08-29 — S5 — **Fault chain response 5.7 µs typ / 8.9 µs worst case** (two 3.56 µs poles from the 2× 1 nF C0G). Accepted deliberately: the module protects itself against OC **within 15 µs** and the PWM period is 100 µs, so this is the *reporting + X-BAR backstop* path and filtering is worth more than microseconds.
- 2026-08-29 — S5 — **Vbus divider = 2.20 kΩ / 1.50 kΩ, 0.1 % Yageo RT0603B (C861295 / C705741).** `VBUS_DIVIDER_RATIO` **297.14 → 341.538**, full scale **1024.6 V**, 0.250150 V/code, module load 1.95 mA of the 5 mA limit. Same resistor *family* on both legs matters more than the tolerance — the divider is ratiometric, so 25 ppm/°C parts track where a thick-film pair could drift 0.6 % differentially (≈6 V of bus). The closer-ratio 2.32 k/1.65 k pair was rejected on **673 units of stock**.
- 2026-08-29 — S5 — **22 nF C0G charge bucket at each ADC pin, fed through 3.3 kΩ** — Vbus corner 1726 Hz, NTC corner 1083 Hz. **This retires the 512-cycle ACQPS workaround:** the S/H sees the bucket (68 ns settling), not the divider. Charge-sharing costs a deterministic 2.8 codes. All three documented 3.0 Vbus defects are now closed — source impedance, Kelvin return (NT3 is the *only* GND tie for `VBUS_RTN`), and scale.
- 2026-08-29 — S5 — **No buffer op-amp on Vbus**, as S4's `load max 5 mA` finding allowed. A plain low-Z divider does the job; the part count and the offset/drift of an op-amp buy nothing here.
- 2026-08-29 — S5 — **NTC divider = 12 kΩ / 4.7 kΩ**, rated for 10 V continuous (DB37 pin 29 is the 10 V NTC2 channel): 10.000 V → 2.814 V = **93.8 % range use**, clips at 10.66 V, load 0.60 mA. Referenced to board **GND, not `VBUS_RTN`** — keeping the Kelvin line single-purpose is worth more than the ~1 % FS error a module-GND shift adds to a thermal channel.
- 2026-08-29 — S5 — **NTC ADC pin = `ADCINC3` (ADC-C ch3), BoosterPack site-1 J3-24; suggested SOC = ADC-C SOC2.** **ADCIND0–D5 are NOT on the BoosterPack headers** (SPRUI77 Fig. 5 — they go to the LaunchPad's own J21 via its differential amps), so ADC-D was not an option. SOC2 converts *after* the SOC1 (Vbus) EOC that fires the 10 kHz ISR, so the slow channel never delays the loop. This leaves **ADC-A SOC1 free for S6's third current channel** (ADCINA3 = J3-26 or ADCINA5 = J7-66).
- 2026-08-29 — S5 — **No fault LEDs.** These five lines drive a hardware trip; nothing optional gets hung on them. Fault indication belongs to the LaunchPad's own D9 and to telemetry.
- 2026-08-29 — S5 — **[BUG FIX] Netclass patterns were silently matching nothing** — see the netclass section above. KiCad matches the **path-qualified** net name, so 24 nets (the whole gate bus, both Kelvin pairs, both buck switch nodes, the enables) sat on `Default`. Ten patterns `*`-prefixed; 28 nets moved to their intended class, none lost one, netlist byte-identical. **Lesson: a convention written into a config file is not a convention until something proves it fires.** The S1/S3/S4 patterns were reviewed by eye four times and the ones that were checked happened to be the ones that worked.
- 2026-08-29 — S5 — **`module_status` captured: 54 components, 22 signal nets, ERC clean of every class except the documented label noise.** Netlist verified node-by-node against a hand-written expected-membership table (**22/22 exact, 0 mismatches**), and every module-side net lands on the DB37 pin the frozen table specifies. Root ERC **89 = 76 `label_dangling` + 13 `isolated_pin_label`**, down from S4's 127. The 15 dangling labels this sheet contributes are its own edge hierarchical labels, which carry no wire because the project captures connectivity as net-labels-at-pins — a cosmetic item, already logged, that should be fixed project-wide in one pass rather than per sheet.

- 2026-08-30 — S6 — **[USER] LEM stays LA 100-P, and the sensors live on a separate board near the motor cables.** Our board provides ±15 V + `ISO_COM` and receives three sensor outputs through **one global connector**. The ±150 A range is knowingly short of the 260 A SW trip — roadmap option (a), taken deliberately.
- 2026-08-30 — S6 — **[USER] The burden resistors are on THIS board**, so the harness carries the LEM secondary **current**, not a voltage. That single choice removes wire resistance, connector contact resistance and board-to-board ground shift from the measurement, makes an unshielded connector acceptable, and puts the gain element on the JLC-assembled board where it can be changed on the bench. **The remote board must not carry burdens.**
- 2026-08-30 — S6 — **Burden = 47 Ω ‖ 47 Ω = 23.5 Ω per channel (C870760, 1206 0.1 %).** The LA 100-P datasheet (fetched this session, `datasheets/LEM-LA_100-P-v15.pdf`) bounds R_M in a **window**, not a maximum: at ±15 V and the full ±150 A range it is **20–25 Ω at 85 °C** (0–33 Ω at 70 °C). The *minimum* exists because the burden must take dissipation out of the transducer at high ambient. Lower current ceiling ⇒ wider window ⇒ more volts/amp. Fitting one resistor instead of two gives 47 Ω, legal to ±100 A — this is the user's "adjust it for different current levels" mechanism, and it is also why it is a parallel pair rather than one hot 0805 (0.132 W → 26 % of rating each).
- 2026-08-30 — S6 — **Topology: two independent difference amps per channel, one 3-pad jumper selecting the OUTPUT.** The two sources are not interchangeable — the module sensor is a 2.5 V-biased signal (and 0.600 × 2.5 = **1.500 V**, so the ADC bias falls out of the attenuation for free), while the LEM burden is bipolar about 0 V and needs the bias injected. Sharing one amp would have meant switching signal, return **and** bias = nine jumper positions across three channels, where a wrong combination still reads plausibly. Cost of the chosen scheme is 3 op-amp halves and 12 resistors; it buys one jumper per channel, no wrong-but-plausible state, and **both stages live at once** on TP30–TP35 so the two sensors can be scoped against each other on the same current.
- 2026-08-30 — S6 — **Both stages reject their own source return.** Internal: V2 = `ISNS_x_RAW`, V1 = `ISNS_RTN` (Kelvin, DB37 12/13), V_bot = GND. LEM: V2 = burden top, V1 = burden bottom (`ISO_COM`, Kelvin), V_bot = `ISNS_VREF`. This closes S2's Kelvin requirement structurally rather than by layout wish, and is what prevents 3.0's measured load-dependent IR-drop offset. **NT4 is `ISNS_RTN`'s only tie to GND.**
- 2026-08-30 — S6 — **Internal gain 20.0 k/12.0 k = 0.600; LEM gain 12.0 k/4.99 k = 0.41583.** ADC: 4.800 mV/A internal (±300 A → ±1.44 V, span 0.06–2.94 V, clips ±312 A) and 4.886 mV/A LEM (+1.8 %). The residual mismatch is deliberate: matching exactly needs a **16 Ω** burden, which is legal at 70 °C but **below the 20 Ω floor at 85 °C**. A closer ratio from another manufacturer family would trade a *constant* 1.8 % (absorbed by one firmware constant) for a *differential tempco* between two thin-film families (up to 0.2 % over 40 °C, absorbed by nothing). **Same family beats closer ratio.**
- 2026-08-30 — S6 — **[FINDING] The module's internal sensor scale is ambiguous in the datasheet, and the design was made not to care.** "4.9 V @ 300 A_RMS" reads either as 8.00 mV/A (clips at 312 A — below the module's own 424 A_pk rated current) or 5.66 mV/A (4.9 V at the peak of a 300 A_RMS sinewave). Gain is set for the **higher** sensitivity: if 8 mV/A is right the target is hit exactly; if 5.66 mV/A is right full scale becomes ±441 A and only range is wasted. **Neither reading clips.** Designing for the lower one would have clipped at 221 A. Also from the same line: the 4.7/5.0 V band is **±3 %**, so the module's own three sensors can differ by several percent — no 0.1 % board resistor fixes that, and firmware calibrates offsets but not gains. That is the reason the LEM path (±0.45 %) exists.
- 2026-08-30 — S6 — **[RECORD CORRECTION] "internal current sensors ≈ 7.5–8 mV/A" was never bench-verified** and has been moved out of this file's verified list. `control_v2_pinmap.md` §6 *derives* it from an assumed 2.5 V bias and marks bias/polarity/limit as "must be verified on bench"; the genuinely bench-measured 78.6 mV/A belongs to the bench clamp+amp board, not the module. **Lesson, and it is S5's lesson again in another costume: a number inherited into a "verified" table is not verified until something points at the measurement.**
- 2026-08-30 — S6 — **[S12 FIRMWARE BUG] `hw_control_v2.h` contradicts itself by 10×.** HEAD has `LEM_V_PER_A 0.0075f` directly beneath a comment block insisting 78.6 mV/A was bench-measured 2026-07-22 and that 8 mV/A was a 9.8× under-estimate. History is `0.008 → 0.0786 → 0.0075`; the commit that made the last change (`e46882a`) documented a phase-ID solver rewrite, not this. One of the two is wrong.
- 2026-08-30 — S6 — **`ISNS_C_ADC` = ADCINA5 (ADC-A ch5) = BoosterPack J7-66**, suggested SOC1, over S5's other candidate ADCINA3 (J3-26). SPRUI77 Table 3 shows the current-sense block then occupies **five contiguous pins on one header** (J7-65…69 = ref B, I_C, I_B, I_A, ref A) across three different converters — adjacent, equal-length traces are exactly what channel-to-channel matching needs, and the per-ADC load stays balanced (A: SIN+I_w, B: I_u+COS, C: I_v+Vbus+NTC).
- 2026-08-30 — S6 — **Offset-reference channels ADCINA4/ADCINB5 KEPT, with an actual job.** Both read the buffered `ISNS_VREF` (≈1.4685 V) through their own 100 Ω + 22 nF buckets, driven by U15B so the ADC's sampling charge never lands on the reference the LEM stages stand on. Same node on two different converters ⇒ firmware gets a live bias reading *and* a free ADC-A vs ADC-B cross-check. This is also why no reference IC is needed: the divider's absolute value does not matter (zero is captured at every CALIBRATE) and its drift is *observable*.
- 2026-08-30 — S6 — **Anti-alias corner deliberately HIGH: 6.03 kHz (internal) / 6.79 kHz (LEM)**, in each difference amp's feedback with a matching cap across R2' so CMRR survives at HF. A single pole is a weak anti-alias filter at any corner (−6 dB at 10 kHz); what actually rejects the switching ripple is **synchronous sampling at the PWM peak**, which the firmware already does. Phase lag in *current* feedback, by contrast, rotates the measured current vector and costs torque accuracy — 9.4° at the 1 kHz max electrical fundamental instead of 19.5° at a 3 kHz corner.
- 2026-08-30 — S6 — **±15 V budget closed: 111 mA/rail worst case vs ±200 mA available** (3 × 12 mA quiescent + 75 mA peak secondary), 1.8× margin — S3's URA2415YMD-6WR3 survives. ⚠ Correcting a number I gave the user earlier in the session: for a balanced 3-phase set the max instantaneous sum of the *positive* secondary currents is **1.0 × peak, not 1.73 ×**.
- 2026-08-30 — S6 — **[SAFETY] With a LEM source selected the software OC trip is INERT.** The LA 100-P saturates at ±150 A against a 260 A `MOTOR_OC_TRIP_A`, and a larger burden lowers that ceiling. Protection there is the module's own 625 A_pk hardware shutdown (<15 µs) plus the `FLT_OC` X-BAR trip from S5. The internal sensors *do* cover ±312 A, so the **default jumper position (internal) is also the one that keeps the SW trip meaningful.** Goes in the S12 handoff, not just on the schematic.
- 2026-08-30 — S6 — **Connector: Deutsch endorsed for the vehicle interface, but the board carries a Micro-Fit 3.0 2×4 right-angle (C3294385).** The usual analog objection to Deutsch is neutralised by the current-mode harness, so the team-standard argument wins — **the DTM 8-way stays at the bulkhead**. It is not on the PCB because TE's product drawing for `DTM13-08PA-R004` is login-gated and the only obtainable dimensions are marketing-level; deriving a through-hole pattern from those would repeat exactly what S1 rejected 3.0's `F37HP` for. One-part swap if the drawing turns up. ⚠ **Key or size the LEM connector differently from S7's encoder connector** — mis-mating ±15 V into an RM44AC destroys it.
- 2026-08-30 — S6 — **[TOOLING] The MCP `import_symbol` produced an unloadable symbol library.** KiCad's `OPA2376xxD` is a *derived* symbol (`extends "LM2904"`) and the tool copied it without its parent; `kicad-cli sym export svg` went from 49 SVGs to 0. Fixed by flattening the parent's body under the child's name, matching how `UCC27524D` and `74LVC1G11` already sit in this library. **The `kicad-cli` re-export after every library edit is not ceremony — it caught a total library failure in one command.**
- 2026-08-30 — S6 — **`current_sense` captured: 94 components, 42 nets, netlist verified node-by-node against a hand-written expected-membership table (42/42 exact, 0 mismatches).** Root ERC **70 = 66 `label_dangling` + 4 `isolated_pin_label`**, down from S5's 89 and containing **no other violation class**. LCSC on 94/94 (82 purchasable + 12 `NOFIT`). Transfer functions, the R_M window, the jumper table, the ±15 V budget, the SW-trip caveat and six S11 layout rules are written onto the sheet as text notes.

- 2026-08-30 — S7 — **[MAJOR CORRECTION] S6's "the DTM13 drawing is login-gated" was false, and it had put the wrong connector on the board.** The user pushed back on being offered Micro-Fit again — *"i specified the deutsch ones"* — and re-testing the premise took one HTTP request: TE's `DocumentDelivery` endpoint (`Action=srchrtrv&DocNm=…&DocType=Customer+Drawing`) serves the full dimensioned customer drawings with **no authentication**. Three are now in `datasheets/`. **Lesson, and it is the fourth costume of the same lesson (S5 patterns, S6 "bench-verified" sensitivity): an inherited blocker is not a blocker until something re-tests it.** S6 reached the right *decision* (Deutsch) and then silently substituted the part on a false premise, which is worse than either choice made openly.
- 2026-08-30 — S7 — **[USER] Both vehicle connectors are now board-mounted Deutsch: J3 (LEM) = `DTM13-12PA-R005` key A, J4 (encoder) = `DTM13-12PB-R005` key B.** Two findings drove the shape. (a) Probing TE's repository across 2/3/4/6/8/12 ways × keys A/B × 11 flange suffixes returns **exactly three documents** — **the DTM13 board-mount family exists only in 8-way and 12-way**, so a 5-wire encoder cannot have a small Deutsch. (b) `-12PA-R005` and `-12PB-R005` are **dimensionally identical**; only the key differs. So one footprint serves both, the compact `-R005` 12-way (38.10 × 41.02 mm) is *smaller* than the 8-way's 4-ear `-R004` flange (68.58 mm), and **mis-mate protection now comes from the connector's own key** instead of from way-count — which survives any future re-pinning. J3's four spare ways go to `ISO_COM` so every rail and every sensor output has its return on the physically adjacent contact (1–12, 2–11, 3–10, 4–9, 5–8); the 2×4 could not do that.
- 2026-08-30 — S7 — **RM44AC resolved on paper: SINGLE-ENDED, 2.2 ±0.2 Vpp, offset 3/5·Vdd ±5 mV, 720 Ω internal series impedance, 5 V/13 mA, LiYCY 4×0.20 mm² shielded, order code `01S` = 1 cycle/mech rev.** Bench items #7–#9 stop blocking. The roadmap's preferred differential/INA receive is **not available**, and a Kelvin ground return is **physically impossible** — the factory cable has 4 cores and no spare conductor. The uncancelled part is 13 mA × 0.26 Ω = **3.4 mV, static**, which the ALIGN bias capture removes. Encoder draw is **13 mA, not the ~60 mA** ARCHITECTURE.md §2 budgeted.
- 2026-08-30 — S7 — **Topology: non-inverting difference amp per channel, `V_bot` = `ENC_VREF3V` (not a fixed 1.5 V).** Same part count as the textbook arrangement, chosen for one property: **with J4 unplugged the input floats to the reference through R1'+R2', so the output lands on the ADC bias exactly and the sin/cos vector collapses to the origin** — `sin²+cos²` ≈ 0 against `SENSOR_RES_MAG_LOW` = 0.25, detected with full margin and **independent of the calibrated amplitude**. The textbook version rails the output instead, which the firmware only catches while amplitude < 1930 codes; a max-amplitude encoder (1904 codes) sits close enough that an unplugged connector could read as a **valid frozen angle** — uncontrolled torque at speed. Cost: the bias now moves with gain, so a bench gain change also re-splits the reference chain (table in `S7_ENCODER_DESIGN.md` §9.1).
- 2026-08-30 — S7 — **Gain 1.16197 V/V (12.0 k/10.0 k with the 720 Ω source correction) ⇒ bias 1.4934 V (2039 codes), amplitude 1.278 V (1745 codes), 85.2 % range use, worst-case swing 0.099–2.888 V.** ⚠ **This deliberately misses CLAUDE.md's "~1.4 V / 1911 codes" target.** At 1.400 V nominal a legal max-amplitude encoder (2.4 Vpp) gives 1.527 V and peak code **4124 > 4095** — it clips, which is one of the three defects the firmware logbook blames for 3.0's 26° electrical noise. Sizing for the worst case costs 6 % of range and makes clipping impossible anywhere in the datasheet's 2.0–2.4 Vpp band. 3.0 achieved 48 % range use *with* clipping.
- 2026-08-30 — S7 — **The bias cancels RATIOMETRICALLY: the reference chain hangs off `ENC_VDD`, the same node that feeds the encoder.** The encoder's offset is 3/5 of *its* Vdd and our subtraction reference is 0.6003 of *the same* node, so the buck's tolerance, its line/load regulation and FB1's 4.9 mV drop all cancel. ⚠ **FB1 must stay a ferrite** — a 10 Ω series resistor at 13 mA would shift the output bias by 94 mV and clip the bottom of the swing.
- 2026-08-30 — S7 — **Reference chain 3.00 k / 4.99 k / 12.0 k, 0.1 % one family (RT0603BRD07, 25 ppm/K) — bought for TCR TRACKING, not accuracy.** A static reference error is removed at every ALIGN; **drift between ALIGNs is not**, and because both channels share these references a shift δ is a *common* shift on sin and cos, i.e. a vector translation giving `δ·√2/A` of angle error. 1 % ratio drift ≈ **6° electrical**; same-family 0.1 % holds it near 0.5°.
- 2026-08-30 — S7 — **Anti-alias pole 6.03 kHz (12.0 k × 2.2 nF), matching S6's corner; total uncompensated lag 10.55° electrical at 6000 rpm, differential SIN↔COS only ≈0.5°.** The governing fact is the firmware's, not the filter's: `sensor_rm44ac.h` already runs a matched 200 Hz IIR **and compensates its lag analytically** (`lag_elec = f_elec/fc`). A matched lag is therefore a correctable delay; a **mismatch is correctable by nothing** — which is why the RCs are identical and C0G, and why matching outranks corner choice. Optional one-constant firmware refinement: `1/fc_eff = 1/200 + 1/6030` → 193.5 Hz. Left optional on purpose so the board does not depend on the live-tunable `res_filt_hz` staying at its default.
- 2026-08-30 — S7 — **[SAFETY] BAT54S clamp (D10/D11) on each ADC line to +3V3/GND.** Unlike S6's stages, whose gain bounds the output below 3.3 V intrinsically, this stage can drive **3.89 V** if a signal line shorts to the encoder's own Vdd — over the F28379D's VDDA+0.3 = 3.6 V absolute max. Also covers a mis-mated ±15 V. Clamp goes to the **board** +3V3 because the LaunchPad's 3V3 header pins are NC by S2 policy.
- 2026-08-30 — S7 — **⚠ The DTM 12-way cavity numbering is EXTRAPOLATED, not verified.** TE's 12-way drawing does not label the cavities; the order used (1–6 / 12–7) follows the 8-way drawing of the same family, which does. Board, symbol and footprint are self-consistent either way, but **the mapping to the molded numbers must be confirmed before a harness is crimped.** Written on both sheets.
- 2026-08-30 — S7 — **`encoder` captured: 46 components, 16 nets, netlist verified node-by-node against a hand-written expected-membership table (16/16 exact, 0 mismatches).** Root ERC **66 = 62 `label_dangling` + 4 `isolated_pin_label`**, *down* from S6's 70 and containing **no other violation class**. Project netlist 125 → 149 nets (131 real + 18 no-connect pseudo-nets), 634 → 745 nodes, classes 61 Default / **58 Analog** / 17 Gate / 8 Power_1A / 5 Power_3A — the pre-existing `*ENC_*` pattern classed all 15 encoder signal nets Analog with no netclass change, and `SHIELD_ENC` stays Default like the other two shields. LCSC on 46/46. Source spec, transfer function, the unplugged-detection argument, the phase budget, the J4 pinout and six S11 layout rules are written onto the sheet as text notes.
- 2026-08-30 — S7 — **[TOOLING] 33 silent `footprint_link_issues` from abbreviated footprint names.** This library's parts are `R_0603_1608Metric`/`C_0805_2012Metric`, but CLAUDE.md's inventory table abbreviates them to `R_0603`/`C_0805`, and assigning the abbreviated name produces a component that places, wires and netlists perfectly while pointing at a footprint that does not exist. Only `--severity-all` ERC surfaced it. **Run `kicad-cli sch erc --severity-all`, not the default severities, before declaring a sheet clean.**

- 2026-08-31 — S7.5 (schematic legibility pass) — **[USER] All five populated sheets re-drawn: components placed by signal flow, local nets carried by wires instead of labels-at-pins.** `power`, `gate_drive`, `module_status`, `current_sense`, `encoder`. Across the five sheets: wires **13 → 699**, labels **748 → 401**, junctions 0 → 17. **Netlist byte-equivalent throughout: 149 nets / 745 nodes, every node set matching.** Project ERC **66 → 40**, and all five sub-sheets are clean of *every* violation class — the 40 remaining are root-sheet labels belonging to the still-empty `launchpad`/`vehicle_io` (S8). Symbol blocks were edited in place, so UUIDs, footprints, `LCSC` fields and instance paths are untouched; only `(at …)`, field positions and the graphical layer changed.
- 2026-08-31 — S7.5 — **Layout convention adopted: wires for local connections, labels only where a wire would have to cross.** This is not a compromise — the difference-amp topology *forces* one label per channel at the −IN entry (the + source arrives from the far left while the feedback ties to the output on the far right, so one branch must cross). Both `encoder` channels and all three `current_sense` channels use the identical band structure, which also satisfies S6's "the three channels must be geometrically IDENTICAL" rule *visually*, not just electrically.
- 2026-08-31 — S7.5 — **[TOOLING] Four KiCad file-format behaviours that silently corrupt a hand-generated schematic.** Each cost a debug cycle and none produce an error message: **(1)** a pin lying *mid-wire* does **not** connect — KiCad bonds a pin only at a wire **endpoint**, so every segment must be split at each pin it crosses; **(2)** symbol field angles are **relative to the symbol body** — a 90°-rotated part needs field angle 270 to render horizontally, but a 180° part needs 0 (an added 180 renders upside-down); **(3)** KiCad applies `(mirror …)` **after** the rotation, not before — only visible on a symbol that is both mirrored *and* rotated (the three `current_sense` source jumpers, whose pin 1/pin 3 silently swapped); **(4)** floating-point drift in generated coordinates produces **zero-length wire fragments** that break connectivity while looking correct in the file — round every coordinate to the same precision as the pin coordinates and drop degenerate segments.
- 2026-08-31 — S7.5 — **[TOOLING] A malformed token aborts KiCad's parse of the whole sheet, silently.** Passing a Python dict where `mirror` was expected emitted `(mirror {'ref_off': …})`; KiCad loaded the first 29 symbols of `current_sense`, discarded the remaining 65 plus every wire and label, and reported **no error at all** — `sch export netlist` exited 0. It surfaced only as "pin not connected" in ERC and as missing nodes in the netlist diff. **Lesson, and it is S5/S6/S7's lesson in a fifth costume: a check that reads your own model instead of the tool's output is not a check.** The geometry engine happily ignored the bad token; only the `kicad-cli` netlist diff caught it. Always gate on the tool's own export, never on your own parse.
- 2026-08-31 — S7.5 — **[VERIFY] The gate that made this safe.** Three independent checks, run after every regeneration: an S-expression→connectivity engine reproducing KiCad's rules (pin/label/wire bonding, no connection at un-junctioned crossings) compared net-by-net against the original; a crossing detector flagging any two wires meeting where they must not; and an order-insensitive netlist fingerprint from `kicad-cli sch export netlist` diffed against a golden baseline. Bugs caught that would otherwise have shipped: a wire shorting across `R108`, `C111`/`C112` shorting `ENC_VDD` to `GND`, a BAT54S pin-direction error dropping the SIN clamp onto the COS line, pull-ups fitted backwards on all five `module_status` fault channels, and `J1`'s ground pin left unwired.

## Open items (owner session in brackets; struck items resolved with the session noted)

- ~~[S2] BoosterPack header gender~~ — **resolved S2:** `PinSocket_2x10`, bottom side, LaunchPad below.
- **[S9] PrimeSTACK mounting pattern — the drawing is now IN HAND** (`datasheets/…-DS-v02_00…pdf` **p.5**): 215 × 280 body, Ø9.2 / Ø11×10-deep holes, M8×14-deep + M6×11-deep threads, 195 / 143.2 / 155 / 93 / 31 / 62 / 242.6 / 260. S9 extracts the exact pattern; the adapter-plate plan (ARCHITECTURE.md §7) stays as the decoupling mechanism but may no longer be necessary.
- **[user] DB37 purchasable MPN** for the consigned list. Geometry (female, right-angle, 2.77 × 2.54 mm, 63.5 mm jackscrews) is de-facto validated by 3.0 mating the real harness **and now by the datasheet's "X1 = 37 contacts, SUB-D, male" with UNC 4-40 female thread** — only the buyable part number is open. If the team ever switches to a *vertical* part, the row pitch becomes 2.84 mm and the footprint must be re-derived.
- ~~[S3] Schottky vs ideal-diode/load-switch for the LaunchPad 5 V feed~~ — **resolved S3:** plain Schottky **SS34, C8678 (JLC Basic)**; V_f ≈ 0.35 V at ~200 mA leaves the LaunchPad ≈4.63 V, ample for its own 3.3 V LDO. **Physically placed in S8** on the `launchpad` sheet at the header.
- ~~[S3] X5R vs X7R for bulk rails~~ — **resolved S3:** X7R wherever a Basic/Preferred X7R exists at the needed value (100 nF, 47 nF, 1 µF); X5R for the bulk ≥4.7 µF where JLC Basic offers nothing else, with ≥2× voltage derating (50 V parts on the 24 V rail, 25 V parts on 5 V/3V3). AMS1117 dissipates 0.25 W → ≈85 °C junction at the 70 °C worst-case local ambient.
- ~~[S7] Standardise C0G filter values~~ — **resolved S7: the set stays at exactly four.** 1 nF `C106246` (EMC at connectors), 2.2 nF `C107043` and 4.7 nF `C85980` (active anti-alias poles), 22 nF 0805 `C77069` (ADC charge buckets). S5, S6 and S7 each added none; S7's matched SIN/COS RCs are 2.2 nF and its buckets 22 nF.
- **[S8] CAN GPIO pair** for `CAN_TX_3V3`/`CAN_RX_3V3` — pick CAN-mux-capable GPIOs that reach the BoosterPack headers (SPRUI77 Tables 1–4 in `datasheets/`); note the LaunchPad's own CAN transceiver hangs on GPIO12/17 via 0 Ω links (J12) — avoid or account for it.
- **[S12] Re-verify `C5369735`** (URA2415YMD-6WR3 isolated module) — only **362 in stock** and it is a consigned through-hole part. Highest supply risk on the board.
- ~~[S4] `+24V_MOD` land it on DB37 pins 8/26~~ — **done S4** (pins 8/26 per the datasheet; return on 10/28 as `PGND_MOD`).
- ~~[S4] Series damping resistor ≤100 Ω~~ — **resolved S4: 100 Ω (R18–R23)**, with the datasheet's 10 kΩ + 1 nF input network fitted at the connector. Module sees 12.95–13.62 V.
- ~~[S4] FSAE shutdown-circuit interlock on the gate enable~~ — **resolved S4 (user):** 3-input AND with `SW_MAIN_3V3`, bypassable by the exclusive jumper JP1.
- **[user, before S12] DB37 hardware:** the module end is SUB-D 37 **male with UNC 4-40 female threads**, so the harness end that mates our socket needs matching jackscrews. Confirm the board-side hardware with the purchasable MPN.
- ~~[S5] Fault pull-up value~~ — **resolved S5: 4.7 kΩ to `+13V5_GATE`** (2.84 mA sink), then 10 k/4.7 k into an SN74LVC2G17 Schmitt. 2.45 V / 2.91 V of noise margin referred to the DB37 pin.
- ~~[S5] `NTC_1_RAW` divider must survive 10 V~~ — **resolved S5: 12 k / 4.7 k**, 10.000 V → 2.814 V (93.8 % range), clips at 10.66 V, 0.60 mA load. ADC pin `ADCINC3` (J3-24).
- **[S8] `vehicle_io` must produce `SW_MAIN_3V3`** as a clean 3.3 V logic level with all contact conditioning on its side — `gate_drive` consumes it as a hardware interlock term with no local filtering by design.
- ~~[cosmetic, any session] `power` and `current_sense` sheet readability~~ — **resolved S7.5.** The S6 objection ("a bulk move risks silently detaching a verified netlist") was answered by building the safety net first, not by avoiding the move: an independent geometry→connectivity engine plus an order-insensitive netlist fingerprint diffed against a golden `kicad-cli` export. Every sheet was re-drawn and re-verified **149 nets / 745 nodes identical**.
- ~~[S6] Third current channel~~ — **resolved S6: `ISNS_C_ADC` = ADCINA5 (J7-66), suggested ADC-A SOC1.** Puts the whole current block on five contiguous J7 pins (65–69) across three converters.
- ~~[S6] LA 100-P ±150 A range vs the 260 A SW trip~~ — **resolved S6 (user): accept.** LEM path is a validation instrument; see the SAFETY decision above.
- ~~[S6] Offset-ref outputs ADCINA4/B5 keep or drop~~ — **resolved S6: KEEP**, both reading the buffered `ISNS_VREF` on two different converters.
- ~~[S6] LEM mounting location + secondary connector~~ — **resolved S6 (user): remote sensor board, one global 8-way connector.**
- ~~[user / S7] Key or size the LEM connector differently from the encoder connector~~ — **resolved S7, and better than by size:** both are DTM13-12P-R005, J3 **key A** and J4 **key B**. A key-A plug physically cannot enter a key-B receptacle, so the ±15 V-into-an-RM44AC hazard is prevented by the connector itself and survives any future re-pinning of either harness.
- ~~[user, if wanted] Board-mounted Deutsch instead of J3's Micro-Fit~~ — **done S7.** The drawing was never gated (see the S7 decision log); J3 is now `DTM13-12PA-R005`, footprint hand-derived from TE's dimensioned drawing, netlist re-verified pin-by-pin.
- ~~[S12] Verify `C3294385`~~ — **moot S7:** J3 no longer uses the Micro-Fit clone. The symbol `Conn_02x04_Odd_Even` and the footprint `Molex_Micro-Fit_3.0_43045-0800_2x04_P3.00mm_Horizontal` remain in the libraries, now **unused**.
- **[user, BEFORE any harness is crimped] Confirm the DTM 12-way cavity numbering** against the molded numbers on a real `DTM06-12SA`/`-12SB`. TE's 12-way drawing does not label them; S7's 1–6 / 12–7 order is extrapolated from the 8-way drawing of the same family. Board, symbol and footprint are self-consistent either way — only the harness mapping is at risk.
- **[user / S9] The DTM13 mounting feature** — the drawing's Ø2.01 mm feature is ambiguous between a plastic locating peg and an M2 screw hole. The footprint uses Ø2.2 mm NPTH, which serves either; confirm against a real part before S9 finalises mechanical.
- **[S9] Board edge budget.** Two DTM13-12P flanges are 2 × 41.02 mm of edge, plus the DB37 and the power entry, against 3.0's inherited 91.9 × 121.7 mm outline. S9 must confirm the analog flank actually holds both or grow the outline.
- **[bench, optional] Measure the installed encoder's amplitude at the connector.** Not blocking — S7 spans the whole 2.0–2.4 Vpp datasheet range — but it says whether the `S7_ENCODER_DESIGN.md` §9.1 gain bump is worth fitting.
- **[S12] DTM contacts and wedgelocks are consigned**: `DTM06-12SA`/`-12SB` plugs, size-20 contacts, `W12S` wedgelocks. Not on the JLC BOM.
- **[user, LEM board] Interface contract:** the remote board needs three LA 100-P, ±15 V / `ISO_COM` decoupling, and wiring — **and must not carry burden resistors.** Both burdens per channel are on this board by design.
- **[S12 firmware] `LEM_V_PER_A` is self-contradictory by 10× in `hw_control_v2.h`** — the define says 7.5 mV/A, the comment directly above says 78.6 mV/A bench-measured. Resolve before the handoff; S6 supplies two new per-source constants anyway.
- **[S10/S11] Reclaim ADC range after bench item #3.** If the module's sensors measure 5.66 mV/A rather than 8.00, the internal stages use only 70 % of the ADC span; one resistor per channel (R65/R76/R88) fixes it. No other change.
- **[S12 firmware] `FAULT_OC_A/B/C` do not identify the faulting phase** — any leg's OC asserts all three. Implement the decode table in `S5_MODULE_STATUS_DESIGN.md` §1.2, and note the module does **not** self-shutdown on over-temperature.
- ~~[cosmetic, project-wide] Hierarchical labels carry no wire stub on any sheet~~ — **resolved S7.5: all five populated sheets re-drawn.** Every label now sits on a wire; project ERC 66 → 40 and **all five sub-sheets are ERC-clean of every class**. The 40 that remain are root-sheet labels for `launchpad` / `vehicle_io`, which S8 fills.
- **[cosmetic, any session] A3 title-block `Title` field overflows its box on all seven sheets** — the S1 sheet titles are longer than the block. Harmless on screen, visible in PDF/print.
- **[S9] 3D model** for the derived DB37 footprint still points at KiCad's `…_EdgePinOffset9.40mm.step` (correct body, name differs from the footprint) — harmless, revisit if 3D export matters.

## Tooling notes

- KiCad **10.0.5**; MCP server for schematic/PCB editing, ERC/DRC, BOM/gerber export, `snapshot_project`.
- `kicad-cli sym export svg` / `fp export svg` is the fastest way to prove a library actually parses — use it after any hand-edit of `.kicad_sym` / `.kicad_mod`.
- Datasheets via WebFetch/WebSearch (RM44AC, 6PS04512E43W39693, LA 100-P, TC4468, LAUNCHXL-F28379D).
- Temp exports go to the session scratchpad, not the project directory.
- **Never trust a hand-generated `.kicad_sch` until `kicad-cli sch export netlist` agrees with a golden baseline.** KiCad fails silently on a malformed token (it drops the rest of the sheet and still exits 0), and its connectivity rules are stricter than they look — see the four S7.5 behaviours in the Decision Log. The generator scripts and the checker live in the session scratchpad; the invariant they enforce is **149 nets / 745 nodes, node sets identical**.
- `kicad-cli sch erc --severity-all` groups some sub-sheet violations under the root's section — read the coordinates, not the section header, to attribute them.
