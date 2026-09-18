# FE_UFPR v4.0 — LaunchPad ↔ PrimeSTACK interface board (FSAE UFPR)

Interface PCB between a TI **LAUNCHXL-F28379D** (FOC firmware) and an Infineon **PrimeSTACK 6PS04512E43W39693** inverter driving an **Emrax 208** motor, with a **Renishaw RM44AC** analog sin/cos encoder and (new) external **LEM LA 100-P** current sensors.

**This directory is the live redesign.** The predecessor `../FE_UFPR_3_0` (2-layer Eagle import) is **REFERENCE ONLY — never modify its `.kicad_*` files.**

## ⚠ How to maintain this file (read before editing it)

This file is loaded into **every** session, so every line costs context. It grew from 22 KB (S1) to
159 KB (S9.6) because each session *appended* its decisions, parts, library additions and notes here.
On 2026-09-17 that history was moved out verbatim. **Rules:**

1. **CLAUDE.md is a snapshot of the current state, not a history.** Edit facts *in place*. Never add
   "S<n> update:" paragraphs, "Appended in S<n>" tables or per-session deliverable summaries.
2. **History goes to the topic files**, never here:
   | What | Where |
   |---|---|
   | Decisions + rationale, lessons | [`DECISION_LOG.md`](DECISION_LOG.md) (append-only) |
   | Open items / resolved items | [`OPEN_ITEMS.md`](OPEN_ITEMS.md) |
   | New LCSC parts, stock findings, JLC workflow | [`JLC_PARTS.md`](JLC_PARTS.md) |
   | Symbols/footprints added to the project libs | [`LIBRARY.md`](LIBRARY.md) |
   | Verified-vs-assumed facts, bench status | [`VERIFIED_FACTS.md`](VERIFIED_FACTS.md) |
   | Tool quirks (KiCad, MCP, kicad-cli, JLCSearch, TE) | [`TOOLING_NOTES.md`](TOOLING_NOTES.md) |
   | Session design detail | that session's `S<n>_*.md` |
3. **Budget: ≤ 300 lines / 40 KB.** Check with `wc -lc CLAUDE.md` before committing. If an edit would
   exceed it, move detail to a topic file and leave a one-line pointer.
4. Something belongs here only if a session **must** know it before doing anything: the current phase,
   authoritative pin maps/targets, conventions, and the hard gates.

## Current phase

**PLACEMENT HAND-REDONE BY THE USER (2026-09-17, commits d0a6293…c15b0ef); PRE-ROUTING VALIDATION PASSED.**
Orientation still open (vertical per S9.6, horizontal on the table) — every connector on the top face,
passives referenced to their own connector/IC pins. 370 footprints (TP20/23/37/54 and holes H5–H9 removed),
DRC 0 errors (`--severity-all`; 389 silk warnings → S11; parity = 4 board-only holes H1–H4), ERC 0,
`golden.net` re-baselined = 219 nets, netclasses 6 classes / 28 patterns verified from the netlist.
**§B tightening applied by `tools/board_layout/tighten_s10.py` (entry caps at pins, ADC buckets 3.1 mm from
header pads, U18/U1 decoupling) — user reviews, then routes S10/S11** (`9802b1b` = pre-move state). Claude does rules, DRC, docs.
⚠ Pending: EMRAX KTY insulation class. Precharge/DC-bus contactor **dropped** (external). Rest: [`OPEN_ITEMS.md`](OPEN_ITEMS.md).
*(Replace this paragraph — don't extend it — when a session's exit criteria pass. Keep it ≤ 8 lines.)*

## Roadmap, documents, session rhythm

Roadmap: [`REDESIGN_PLAN.md`](REDESIGN_PLAN.md) — one session per phase; exit criteria are gates; don't
bleed into the next session's scope. Design docs: [`ARCHITECTURE.md`](ARCHITECTURE.md) (S2 — power tree,
grounding, LaunchPad jumper policy, root net table), [`S3_POWER_DESIGN.md`](S3_POWER_DESIGN.md),
[`S4_GATE_DRIVE_DESIGN.md`](S4_GATE_DRIVE_DESIGN.md), [`S5_MODULE_STATUS_DESIGN.md`](S5_MODULE_STATUS_DESIGN.md),
[`S6_CURRENT_SENSE_DESIGN.md`](S6_CURRENT_SENSE_DESIGN.md), [`S7_ENCODER_DESIGN.md`](S7_ENCODER_DESIGN.md),
[`S8_INTEGRATION_DESIGN.md`](S8_INTEGRATION_DESIGN.md), [`S9_BOARD_SETUP.md`](S9_BOARD_SETUP.md),
[`S9_5_MOTOR_TEMP_DESIGN.md`](S9_5_MOTOR_TEMP_DESIGN.md), [`S9_6_VERTICAL_MOUNT.md`](S9_6_VERTICAL_MOUNT.md).
Full DB37 derivation + 3.0 comparison: [`DB37_PINOUT.md`](DB37_PINOUT.md).

**Layout of the directory:** `FE_UFPR_4_0.kicad_{pro,sch,pcb,dru}` + 7 sub-sheets (`power`, `gate_drive`,
`module_status`, `current_sense`, `encoder`, `launchpad`, `vehicle_io`); project libs
`FE_UFPR_4_0.kicad_sym` / `.pretty`; `tools/schematic_layout/` (sheet generators, `canon.py`,
`golden.net`, README with the KiCad traps); `tools/board_layout/` (`place_s9.py` = the S9.6 generator, superseded by the user's hand placement;
`tighten_s10.py` = the S10 entry-cap/bucket moves; `swap_lp_headers.py`, `add_lp_shadow.py`);
`datasheets/` — PrimeSTACK DS (**p.2** controller interface, **p.5** mechanical, **p.6** DB37 pinout),
SPRUI77 (LaunchPad, header Tables 1–4), RLS RM44 (**p.10** analog outputs, **p.20** order code), LEM LA 100-P,
TE DTM13 customer drawings, LTV-817, ACT45B, SN65HVD230, and `ECU AM06.pdf` / `TCC.pdf` (reference only).

**Session rhythm:** read this file → fetch prerequisite datasheets / bench results → decide, and append
decisions to `DECISION_LOG.md` → capture in KiCad (MCP) → JLC-vet every new part (record in
`JLC_PARTS.md`) → ERC `--severity-all` / DRC → replace the phase paragraph above → update
`OPEN_ITEMS.md` → check the size budget → `snapshot_project` + git commit.

## Hard gates (each one caught a real defect — details in `TOOLING_NOTES.md` / `DECISION_LOG.md`)

- **Layout-only changes must prove it:** re-export with `kicad-cli sch export netlist` and diff against
  `tools/schematic_layout/golden.net` — identical is the pass. A self-written parse is not a check.
- ERC is `kicad-cli sch erc --severity-all`; DRC is `kicad-cli pcb drc --severity-all` (zero
  `malformed_courtyard` before trusting overlap results); pad nets via `kicad-cli pcb export ipcd356`.
- After any library edit: `kicad-cli sym export svg` / `fp export svg` must render every symbol/footprint.
  Never import a symbol that `extends` a parent without the parent.
- **Render and look** after any schematic/board regeneration — the netlist gate is blind to cosmetics.
- After MCP adds parts, run `tools/schematic_layout/canon.py` before any layout script; check every symbol
  has an `LCSC` property. After external `.kicad_pcb` edits, `open_project` before the next MCP write.
- A tool's success message is not its output — check the artifact. An inherited blocker is a claim — re-test it.
- Temp exports go to the session scratchpad, not the project directory.
- A restore / `discard_or_reload` (`_restore_backup_*`) can roll back `.kicad_pro` **and** `.kicad_sym` — afterwards
  diff the whole `board.design_settings` + `net_settings` blocks against the last good commit (6 classes / 28 patterns,
  S9 minimums: clearance/track 0.127, hole-to-hole 0.5, annular 0.125) and check ERC shows no `lib_symbol_issues`.
  DRC runs with `--schematic-parity` (it is the only check comparing footprint pad names to symbol pins).

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
| **Motor temperature** | **ADCINB3** (J3-25) | **chosen S9.5** — EMRAX 208 stator **KTY81-210** on J4 cavities 6/7. PTC: **hotter = HIGHER code**, opposite to the module NTC. Fault window rejects `<1400` / `>3100` → stop the motor (EMRAX requires it) |
| **+3V3 rail monitor** | **ADCINA3** (J3-26) | **chosen S9.5** — 10.0k/10.0k 0.1 % divider; firmware cancels the excitation rail exactly, `R = 2200·V/(V_rail−V)`. Without it the LDO's ±2 % is ±10 K, larger than the sensor's own ±4.7 K |
| NTC channel | **ADCINC3** (ADC-C ch3) | **chosen S5** — BoosterPack site-1 **J3-24**; suggest **ADC-C SOC2** (after the SOC1/Vbus EOC that fires the ISR). ADC-D is NOT on the headers. Divider rated for 10 V |
| Status LED | GPIO31 | LaunchPad's own D9 — nothing needed on the board |
| ISR scope probe | GPIO67 | expose a test point (pin unverified on Control_V2) |
| SCI-A debug | GPIO42/43 | LaunchPad USB (XDS100v2) backchannel — **no board connector needed** |
| **CAN-A TX / RX** | **GPIO4 / GPIO5** | **chosen S8** — BoosterPack **J4-36 / J4-35**, on the `J4+J2` connector, which carries nothing else analog. ⚠ **CAN-B is not routable on this board**: its only free header TX is GPIO16 (J4-33) and *every* header `CANRXB` (GPIO7, GPIO10) is consumed by the PWM bus. The LaunchPad's own transceiver is CAN-**B** (GPIO12/GPIO17) and **neither pin reaches the headers**, so the J12 0 Ω links cannot contend with us |
| **Main switch / start** | **GPIO29 / GPIO59** | **chosen S8** — **J2-11 / J2-14**, the same two pins 3.0 used for `MAIN_SWITCH` / `ENGINE_START`. Keeps every vehicle-facing digital signal on the one connector with CAN. Not defined in `hw_control_v2.h` — S12 hands them over |

### Analog conditioning targets (from firmware logbook — non-negotiable)

- **ADC VREFHI = 3.0 V.** Every ADC input gets an anti-alias RC at the pin (10 kHz sampling; noise >5 kHz aliases irrecoverably) + charge-bucket cap for the S/H.
- **Encoder:** land **1.5 V bias, ~1.4 V amplitude** at the ADC pins (old board: 2.25 V / 0.725 V = 48% range use + clipping + ~26° elec RMS noise). SIN/COS conditioning must be **matched** (same R/C values, C0G, 1%); firmware auto-calibrates bias/amplitude per ALIGN but rejects sin-vs-cos gain mismatch >30%. ⚠ **S7 revised the amplitude target down to 1.278 V (`RES_SINCOS_AMPL_CODE ≈ 1745`, bias ≈ 2039), deliberately.** The RM44AC is spec'd at 2.2 **±0.2** Vpp; a 1.4 V nominal design clips at the datasheet's max source (peak code 4124 > 4095). Sizing for the worst case costs 6% of range and makes clipping impossible — 85.2% range use vs 3.0's 48%-with-clipping. **What is NOT negotiable is the SIN/COS RC match**: a matched lag is a pure angle delay the firmware already compensates, a mismatch is correctable by nothing.
- **Current:** both sources (internal + LEM) must produce the **same transfer function**, target ~1.5 V bias, full scale **≥ ±300 A** (SW OC trip is 260 A — must fire before ADC saturates). Zero offsets are captured at runtime → **channel-to-channel gain matching matters more than absolute bias**: 0.1% resistors in gain positions, both channels of a stage in one dual op-amp package.
- **Vbus:** fix all three documented problems — source impedance (buffer or low-Z divider + 1–10 nF C0G reservoir; the old 34.5 kΩ needed a 512-cycle S/H workaround), **Kelvin return** for the sensor ground (−52 mV load-dependent IR-drop offset was measured), recompute `VBUS_DIVIDER_RATIO` for ~1000 V full scale.
- **Gates:** PrimeSTACK inputs LOW = 0–1.5 V, **HIGH = 11–15 V**; channel-to-channel skew ≪ 1500 ns deadband.

## DB37 — v4.0 pin table (AUTHORITATIVE, frozen S4)

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

¹ Pins 9/27 are the same 15 V / 50 mA aux **output** (its "PTC" is the protecting fuse, not a sensor);
kept as two nets. Only temperature output is pin 29. Details: [`DB37_PINOUT.md`](DB37_PINOUT.md).

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

## Libraries and parts

- **Library rule:** nothing is ever placed from a global/system library. ONE project symbol lib
  (`FE_UFPR_4_0.kicad_sym`) + ONE footprint lib (`FE_UFPR_4_0.pretty`), both `${KIPRJMOD}`-relative;
  standard KiCad parts are re-exported into them. Inventory: [`LIBRARY.md`](LIBRARY.md).
- ⚠ Footprint names carry the metric suffix (`R_0603_1608Metric`) — the abbreviated name silently
  breaks the footprint link.
- **Every placed symbol has an `LCSC` field before its session ends.** Place from the vetted kit in
  [`JLC_PARTS.md`](JLC_PARTS.md); pick values from **live stock**, not the E96 table (four sessions hit this).
  Local JLC DB can't answer Basic/stock/price — use `https://jlcsearch.tscircuit.com/` via `curl`.
- **C0G constraints:** no Basic C0G > 100 pF; ceiling ≈ 10 nF (0603) / 22 nF (0805). The board-wide C0G set
  is exactly four values (1 nF, 2.2 nF `C77033`, 4.7 nF, 22 nF 0805) — don't add a fifth without reason.
- Consigned / hand-solder: DB37, Deutsch DTM connectors (J3/J4/J5), LEM transducers, URA2415YMD-6WR3.

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
- **Netclasses** (`.kicad_pro`; 6 classes, 28 patterns; history in `DECISION_LOG.md` Appendix A):

  | Class | Track | Clearance | Via Ø/drill | Priority |
  |---|---|---|---|---|
  | Default | 0.25 mm | 0.20 mm | 0.6 / 0.3 | (lowest) |
  | Analog | 0.30 mm | 0.30 mm | 0.6 / 0.3 | 10 |
  | Gate | 0.40 mm | 0.25 mm | 0.8 / 0.4 | 20 |
  | Power_1A | 0.50 mm | 0.25 mm | 0.8 / 0.4 | 30 |
  | Power_3A | 1.20 mm | 0.30 mm | 1.0 / 0.5 | 40 |
  | CAN | 0.40 mm | 0.30 mm | 0.8 / 0.4 | 15 (diff-pair 0.40/0.30) |

  **Any new pattern must start with `*`** unless it names a global power net — KiCad matches the
  path-qualified net name. Verify from `kicad-cli`'s `(class …)` netlist output, never by eye.
  **Power_3A is 3.7 A on 1 oz outer but only 1.1 A on 0.5 oz inner** — `+24V_*` / `PGND_MOD` on outer
  layers or ≥ 5 mm L3 pours. Board rules = JLC 4-layer capabilities (`S9_BOARD_SETUP.md` §4).
- **Mounting:** board mounts on top of the inverter; mounting holes required (3.0 had none — only DB37 jackscrews). **S9: six Ø3.2 NPTH board holes (corners + mid-left/right, no pads — the screws must not be a ground path in a floating domain) and three Ø3.2 LaunchPad standoff holes (the user deleted the mid-edge pair and the three standoffs on 2026-09-17; H1–H4 at the corners, 5 mm inset, remain; the rest is decided with the orientation); the PrimeSTACK pattern (M8 on 143.2 × 242.6, Ø9.2 on 195 × 260, datasheet p.5) dwarfs the board, so the adapter plate remains the mechanism.** **S9.6 (PROVISIONAL — the team re-opened this 2026-09-17): the board stands VERTICAL above the module, DB37 edge down, on a DB37 90° adapter mated to X1 (which faces the 3-phase terminal side); the LaunchPad sits ABOVE on male headers and overhangs the top edge 17.9 mm; J5 moved to the top-left; the board needs its own bracket — the connector stack carries no load.** Horizontal is still on the table, so **all connectors stay on the top face**. **B.Cu carries 12 SMD parts by the user's decision (2026-09-17): R2/R3 under U1, D17/C119 under J5, C25–C28 under J3, R118/R119/C113/C120 under J4 — assembled two-sided or hand-soldered; the rest of B.Cu stays continuous copper.**
