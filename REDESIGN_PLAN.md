# FE_UFPR_4_0 Redesign Roadmap

**Scope:** full redesign of the LaunchPad ↔ PrimeSTACK interface board as a fresh 4-layer KiCad project, one focused session per phase. Confirmed baseline decisions live in `CLAUDE.md` → Decision log. Firmware cross-reference paths and conditioning targets live in `CLAUDE.md` — this file assumes you've read it.

## How to use this roadmap

- **One session = one numbered phase.** Don't start a session until its prerequisites are checked; don't bleed into the next phase's scope.
- Every session follows the rhythm in `CLAUDE.md` (read → fetch → decide+log → capture → JLC-vet → ERC/DRC → update phase → commit).
- **JLC vetting per part:** local DB (`search_jlcpcb_parts`) for candidates → WebFetch `https://jlcsearch.tscircuit.com` for Basic/Extended + stock + price → record LCSC number in the symbol before the session ends.
- **Exit criteria are gates.** A session isn't done until all pass (or a failure is explicitly waived in the Decision Log with a reason).

## Phase map

```
S1 Foundation ─► S2 Architecture ─► S3 Power ─► S4 Gate drive ─► S5 Module status
   ✅              ✅                 ✅            ✅                ◄── next
                       │                                               │
  BENCH DAY (before S5/S6/S7) ────────────► S6 Current sense ─► S7 Encoder
                       │                                               │
                       └────────► S8 Integration & pin-map freeze ◄────┘
                                            │
                          S9 Stackup & placement ─► S10 Routing: power/gate
                                            │               │
                                            └─► S11 Routing: analog + DRC zero
                                                            │
                                               S12 DFM / BOM / fab package
```

---

## S1 — Project foundation, libraries, standards  ✅ **DONE (2026-08-18)**

**Objective:** Create `FE_UFPR_4_0` and the curated, JLC-vetted library foundation so no later session ever places an unvetted symbol/footprint.

**Prerequisites:** none (first session).

**Work items:**
- `create_project` at `/home/jose/Kicad/FE_UFPR_4_0`; git init; root sheet + empty hierarchical sheets: `power`, `gate_drive`, `module_status`, `current_sense`, `encoder`, `launchpad`, `vehicle_io` (CAN + cockpit switches).
- Create + register ONE project symbol lib and ONE footprint lib (no embedded-cache reliance).
- Salvage from 3.0 (copy into project lib, then verify): DB37/F37HP symbol + footprint (check pad geometry vs the physical part), 2×10 BoosterPack headers (grid ΔX 43.18 mm / ΔY 63.5 mm is known-good — copy exactly).
- Build the **vetted passive kit**: ~20 Basic resistor values (E96 1%, 0603) + ~10 Basic cap values (0603 X7R, C0G for filters, bulk 0805/1206), LCSC numbers recorded in a table in CLAUDE.md.
- Netclasses + track-width presets in `.kicad_pro` (per CLAUDE.md conventions).
- **Move `CLAUDE.md` + `REDESIGN_PLAN.md` into the new dir** (adapt paths); leave a pointer CLAUDE.md in `FE_UFPR_3_0` ("redesign lives in ../FE_UFPR_4_0; this project is reference-only"). ✅ done — this file and `CLAUDE.md` are now canonical here; `../FE_UFPR_3_0/CLAUDE.md` is a stub pointer.

**Exit criteria:** project opens with zero broken lib references ✅ (both tables `${KIPRJMOD}`-relative, 28/28 symbols + 19/19 footprints validated by `kicad-cli`); passive-kit table with LCSC numbers exists ✅ (27 R + 16 C in `CLAUDE.md`); ERC runs on the empty hierarchy ✅ (0/0/0); first commit made ✅.

**Deviations from plan, logged in `CLAUDE.md`:** the 3.0 `F37HP` footprint was **rejected rather than salvaged** (Eagle mil-grid pitch corruption, 0.18 mm cumulative span error) and rebuilt from KiCad's exact generator output; the 3.0 `2X10` footprint was clean but replaced by KiCad standards for consistency — its *placement grid* (ΔX 43.18 / ΔY 63.5 mm) is what was actually salvaged, re-measured from the 3.0 board.

---

## S2 — System architecture: power tree, grounding, floorplan, mechanical  ✅ **DONE (2026-08-25)**

**Objective:** Freeze board-level architecture on paper before any circuit capture. Deliverable = architecture section in project docs + root sheet with labeled sheet pins.

**Outcome:** all four decisions made and logged (CLAUDE.md Decision log 2026-08-25); deliverable = `ARCHITECTURE.md` + root sheet with 40 nets / 80 sheet pins, stubs and labels, matching hierarchical labels pre-declared in every sub-sheet. ERC = exactly the empty-sub-sheet noise (160 `label_dangling`, 0 warnings — sheet boxes were re-gridded to 1.27 mm to kill 80 off-grid warnings). **Deviations:** PrimeSTACK drawing is myInfineon-gated → mounting pattern logged as *pending user measurement* with an adapter-plate decoupling plan (exit criteria allow this). Windfall: SPRUI77 fetched (now in `datasheets/`) — GPIO131 confirmed on header J6-58, bench items #10/#11 downgraded to verifications.

**Prerequisites:** S1 ✅. Fetch: **PrimeSTACK 6PS04512E43W39693 mechanical drawing** (top-face dimensions + usable mounting points — the board mounts on top of the inverter). LaunchPad bench item #10/#11 helpful but not blocking.

**Decisions:**
1. **LaunchPad power-domain policy** (3.0 hard-parallels LaunchPad 3V3/5V with board regulators). Leading: board powers LaunchPad at 5 V through a series Schottky/load switch; USB isolated via LaunchPad jumpers JP1/JP2/JP4/JP5; the required jumper config goes on silkscreen. Never both sources hard-paralleled.
2. **Grounding** (implements CLAUDE.md §Design rules): single GND plane L2; analog partition by placement; single star tie for the 24 V power return; Kelvin pairs for Vbus + sensor returns; chassis/shield tie policy at each connector shell (direct vs 1 nF ∥ 1 MΩ — decide).
3. **Power tree:** 24 V → 12 V (or ~13.5 V, see S4) → 5 V → 3.3 V cascade confirmation; isolated ±15 V branch for LEMs; clean filtered 5 V for the encoder. Power budget table with per-rail estimates (include PrimeSTACK 40 W aux pass-through via DB37).
4. **Floorplan + connector plan:** DB37 edge (⚠ S1 hand-off: confirm the DB37 physical part — the footprint currently assumes *female, right-angle, 2.77 × 2.54 mm rows, 63.5 mm jackscrews*; a vertical part changes the row pitch to 2.84 mm — and pick the BoosterPack header gender, `PinHeader` vs `PinSocket`); LaunchPad orientation; Mini-Fit + Deutsch DT power entry; encoder connector; LEM secondary connectors; CAN connector; mounting-hole pattern from the PrimeSTACK drawing (confirm with user).

**Exit criteria:** architecture doc section written (power budget, grounding description, floorplan sketch); root sheet with sheet pins ERC-clean except unimplemented sub-sheets; mounting pattern confirmed or logged as pending user measurement.

---

## S3 — Power supplies sheet  ✅ **DONE (2026-08-29)**

**Outcome:** `power` sheet captured — **75 components, 29 nets, ERC 0 violations on the sheet**,
netlist verified node-by-node, all 60 BOM parts carry an `LCSC` field, every value computed from
datasheet equations. Deliverable = [`S3_POWER_DESIGN.md`](S3_POWER_DESIGN.md).

**Deviations from plan, logged in `CLAUDE.md`:** the **5 V** converter changed
**TPS62153 → TPS62933F**. TPS62153 has no MODE pin, so its power-save mode cannot be defeated — and
on a board that samples at 10 kHz a load-dependent PFM burst rate is exactly the wrong failure mode
for the rail that feeds every analog front-end. The `F` suffix is FCCM (fixed 1.2 MHz at any load)
and is the only family member without spread spectrum.

The **gate-rail** buck stays the roadmap's **LMR33630A**. An interim swap to a 60 V TPS54360B was
made on transient-headroom grounds and then **reverted** after user challenge: it rested on the S2
assumption `18–30 V`, and the real LV rail max is **≤26 V** (now an **[ARCH CHANGE]**: input range
18–26 V). Reverting also removed 5 parts — synchronous, internally compensated, fixed 400 kHz.
Gate rail set to **13.500 V** exactly (150 k/12 k, V_ref = 1.000 V), user's call over 12.0 V.
What *did* change is the **TVS**: SMBJ33A breaks down at 36.7–40.6 V, straddling the LMR33630's
38 V absolute max, so it becomes the 1500 W **SMCJ26A**. Two further **[ARCH CHANGE]** items: rail
renamed `+12V_GATE` → `+13V5_GATE`, and new global net `+24V_MOD` for the fused pass-through.

**Traps caught during capture:** TPS62933F's EN pin is rated **6.0 V** max — tying it to the 13.5 V
rail would destroy it — and its **SS pin cannot float** (≥6.8 nF required). Also: the "obvious" E96
divider values were **unbuyable** (162 kΩ → 1 in stock, 10.2 kΩ → 3, 5.49 kΩ → 19), so every value
was re-picked from Basic, high-stock parts against live stock.

**Objective:** Complete `power`: input protection, all rails, isolated ±15 V, indicators, entry connectors.

**Prerequisites:** S2. Datasheets: LMR33630, TPS62153 (or replacements), A2415SDL-2W + 5 W alternatives (Mornsun URB2415 family etc.).

**Decisions:**
- **Input protection:** P-FET reverse polarity, SMBJ33A-class TVS, fuse/polyfuse, bulk caps. Entry = Mini-Fit (power distribution) + Deutsch DT (vehicle), no barrel. Connector current rating ≥ stack aux (~1.7 A @ 24 V) + board draw.
- **12 V buck:** keep LMR33630 if JLC-available; **compute the FB divider from scratch** (3.0's values were literally "R"). Setpoint 12.0 vs ~13.5 V decided jointly with S4 (module HIGH ≥ 11 V after drops; max 15 V; TPS62153 Vin max 17 V tolerates 13.5 V).
- **5 V / 3.3 V:** keep TPS62153 (+ LM1117-3.3 only if the board itself needs 3.3 V — with the S2 power policy the LaunchPad may make its own 3.3 V; prefer running ADC-driving op-amps from clean 5 V).
- **±15 V for LEMs — close the undersizing flag** (CLAUDE.md Decision log): one A2415SDL-2W per sensor vs one 5 W module vs no isolation (LEM secondary already galvanically isolated; keep isolation if sensors mount remotely near HV cabling — likely yes).
- Per-rail LED indicators; no sequencing needed.

**Exit criteria:** ERC-clean; zero placeholder values (every divider computed and annotated); datasheet layout notes for both bucks copied into sheet notes (for S10); power budget updated with real numbers; LCSC fields set.

---

## S4 — Gate-drive path, level shifting, enables  ✅ **DONE (2026-08-29)**

**Outcome:** `gate_drive` captured — **56 components, 44 nets, ERC 0 violations on the sheet**,
netlist verified node-by-node (44/44, zero mismatches). Deliverable =
[`S4_GATE_DRIVE_DESIGN.md`](S4_GATE_DRIVE_DESIGN.md).

**The session's defining event was an input, not a decision:** the user placed the real PrimeSTACK
datasheet in `datasheets/`. Page 6 is the **authoritative DB37 pinout**, page 2 the controller
electrical table, page 5 the **mechanical drawing S9 has been waiting for**. Five inherited beliefs
were wrong and are now corrected in `CLAUDE.md`: fault is **HIGH** not LOW (firmware's
`MODULE_FAULT_ACTIVE_LOW` is inverted); analog outputs drive **5 mA** so S5 needs no Vbus buffer;
there is **one** NTC pin (29) and it is the **10 V** channel; pins 9/27 are a **15 V/50 mA supply
output** that 3.0 shorted to ground; pin 1 is **true earth/shield**, not GND.

**Deviations from plan, logged in `CLAUDE.md`:** the topology is **3 × UCC27524** (dual 5 A, per-channel
enable), **not** the roadmap's 2 × TC4468 — the availability-first rule caught that the whole
TC446x/MIC446x quad family is dead at JLC (14 / 4 / 25 in stock) against 9 550 for the UCC27524. The
enables are **board-local** because the module has no enable pin, so bench item #2 stopped being a
blocker: we define them ACTIVE-HIGH, as firmware assumes. The hardware interlock survives as a
3-input AND (`SN74LVC1G11`, properly powered — 3.0 fed its AND gate's VCC from GPIO131) with an
**exclusive 3-pad bypass jumper**.

**Trap caught during capture:** the F28379D powers up with **GPIO pull-ups enabled**. With the
first-pass 100 kΩ pull-downs, the enable and PWM inputs would have sat at ≈2.7 V — arming all six
gates while the MCU is in reset. Pull-downs are **4.7 kΩ** for that reason. Separately, the six
UCC27524 enable pins present 33 kΩ of internal pull-up **to 13.5 V**, so the enable-net pull-down is
**1 kΩ**; a conventional 10 kΩ would have sat at 3.1 V and enabled the drivers.

**Numbers that closed the exit criteria:** module input **12.95–13.62 V** against an 11–15 V window
(validating S3's 13.5 V rail — a 12.0 V rail leaves only 0.52 V); worst-case channel-to-channel skew
**53 ns = 3.5 %** of the 1500 ns deadband; **effective deadtime 1399 ns**; gate-path draw **≈10 mA**.

**Objective:** Replace the 3-stage chain (6× '1G126 → CD4504B → GPIO-powered AND gate) with a **single-stage 3.3 V → gate-rail** solution with hardware enable gating. All 6 PWM + 2 enables to the DB37.

**Prerequisites:** S3 rail decision. Bench item #2 (enable active levels). Datasheets: TC4468/TC4469, MIC4468/9, UCC27523/24; PrimeSTACK input current spec.

**Decisions:**
- **Topology — vet availability FIRST, design second.** Leading: **2× TC4468** (quad 1.2 A MOSFET driver, VDD 4.5–18 V, each channel a 2-input AND, TTL thresholds ≈ 3.3 V-compatible; skew tens of ns ≪ 1500 ns deadband). 8 channels = 6 PWM + 2 enables; the second AND input becomes hardware `DRV_EN` — deletes all three old stages in one move. Alternatives: MIC4468/MIC4469, 3× UCC2752x (dual w/ EN), discrete totem last resort.
- **Gate rail:** 12 V vs 13.5 V (margin above the 11 V minimum after series-R + cable drop; 15 V absolute max at module).
- **Fail-safe:** 100 k pulldowns per line at the DB37 side (unpowered LaunchPad ⇒ gates LOW = off) + ~100 Ω series damping near the driver.
- **MAIN_SWITCH / FSAE shutdown-circuit interlock:** decide whether the hardware enable is gated by the car's shutdown circuit and how (ask team about rules mapping of the old /MAIN_SWITCH concept; `vehicle_io` sheet carries the switch inputs).

**Exit criteria:** ERC-clean ✅ (0 on the sheet); skew-vs-deadband note written ✅ (on the sheet + §6 of the
deliverable); DB37 pin table ✅ — **complete for all 37 pins, not just gates/enables, because the
datasheet made it possible**; end-to-end active-HIGH polarity chain documented ✅ and consistent with
`hw_control_v2.h` (with the one firmware correction, `MODULE_FAULT_ACTIVE_LOW`, logged for S12).

---

## S5 — Module status: fault receivers, Vbus sense, NTC

**Objective:** Receive side for the PrimeSTACK's 5 open-collector fault lines, the Vbus analog output, and the NTC channel(s).

**Prerequisites:** ~~BENCH DAY #1 / #4~~ — **both answered by the datasheet in S4** (fault = HIGH; analog outputs drive 5 mA). Remaining: **BENCH DAY item #5 (NTC output at room temperature, one channel)**. Historical text: ~~items #1 (fault polarity — the doc conflict is unresolvable on paper), #4 (Vbus drive capability), #5 (NTC outputs)~~.**

**Decisions:**
- **Fault receivers:** pull-up rail (gate rail vs dedicated — outputs rated to 15 V) and value (recompute for a few mA of noise immunity; 3.0's 82 k is weak for a cable run), then divider/RC/Schmitt (SN74LVC2G17) or comparator to 3.3 V. **Fail-safe requirement: a disconnected DB37 must read as FAULT asserted** in whatever polarity the bench establishes. Record the final `MODULE_FAULT_ACTIVE_LOW` value for firmware (affects X-BAR inversion too).
- **Vbus front-end — fix all three documented problems:** (1) impedance: low-Z divider if the bench says the sensor can drive it, else buffer op-amp; 1–10 nF C0G reservoir at the ADC pin regardless; (2) **Kelvin return**: dedicate a DB37 sensor-return pin, routed as a pair to the analog region; (3) scaling: 6.5 V @ 900 V → ~1000 V full scale into 3.0 V; recompute `VBUS_DIVIDER_RATIO`; 0.1% divider resistors.
- **NTC:** wire NTC#1 (4.9 V @ 125 °C-equiv) and, if pins allow, NTC#2 (⚠ 10 V @ 82 °C-equiv — divider must tolerate 10 V) to spare ADC channels; **choose and record the ADC pins now** so firmware can adopt them later.
- Anti-alias RC on every input this sheet touches (slow channels can take ~1 kHz corners).

**Exit criteria:** ERC-clean; firmware-handoff note updated (fault polarity + `MODULE_FAULT_ACTIVE_LOW`, new `VBUS_DIVIDER_RATIO`, NTC pin assignments); every ADC input has its RC.

---

## S6 — Current sensing: 3 channels, dual-source (internal / LEM)  ✅ **DONE (2026-08-30)**

**Outcome:** `current_sense` captured — **94 components, 42 nets, netlist verified node-by-node
(42/42 exact, 0 mismatches)**, root ERC down to 70 and containing no violation class beyond the two
documented cosmetic ones. Deliverable = [`S6_CURRENT_SENSE_DESIGN.md`](S6_CURRENT_SENSE_DESIGN.md).

**The session's shaping input was the user's, not a datasheet:** the LEMs go on a **separate board
near the motor cables**, reached through **one global connector** — and the **burden resistors stay
on our board**, so the harness carries the LEM secondary *current* rather than a voltage. That one
choice deletes wire resistance, contact resistance and board-to-board ground shift from the
measurement and is what makes an unshielded automotive connector acceptable here.

**Deviations from plan, logged in `CLAUDE.md`:** the roadmap's "same transfer function for both
sources" is **not achievable** and was consciously dropped. Matching the slopes exactly needs a
16 Ω burden, which the fetched LA 100-P datasheet puts **below the 20 Ω floor** of its R_M window at
85 °C. Instead each channel carries **two independent difference amps** (internal + LEM) that both
run permanently, with a single 3-pad jumper selecting which *output* reaches the ADC — three extra
op-amp halves buying one jumper per channel instead of nine positions, no wrong-but-plausible state,
and both sensors scopeable against each other on the same current.

**Traps caught during capture:** (a) the module's internal sensor scale is **ambiguous in the
datasheet** — "4.9 V @ 300 A_RMS" reads as either 8.00 or 5.66 mV/A — so the gain is set for the
*higher* one, which cannot clip under either reading; (b) `CLAUDE.md` listed that sensitivity as
**bench-verified when it never was**, and the genuinely measured 78.6 mV/A belongs to a different
device; (c) the MCP `import_symbol` produced an **unloadable symbol library** by copying a derived
symbol without its parent, caught by the mandated `kicad-cli` re-export.

**Numbers that closed the exit criteria:** internal 20.0 k/12.0 k → G = 0.600 → ADC bias **exactly
1.500 V**, ±300 A → ±1.44 V, clipping at ±312 A; LEM 12.0 k/4.99 k with a 47 ‖ 47 Ω = 23.5 Ω burden
→ 4.886 mV/A, +1.8 % of the internal slope; **±15 V load 111 mA/rail against ±200 mA (1.8×)**;
`ISNS_C_ADC` on **ADCINA5 = J7-66**.

**Objective:** Three identical conditioning channels, each fed from either the PrimeSTACK internal sensor (DB37 pins 30/31/32) or an external LA 100-P, selected by **solder jumpers**, both sources landing the **same transfer function** on the ADC.

**Prerequisites:** **BENCH DAY item #3 (internal sensor bias + mV/A + polarity — bias was NEVER verified) and #12 (LEM data if in hand).** S3's ±15 V decision closed. Datasheets: LA 100-P, op-amp candidates. User input: where the LEMs mount (on-board apertures are impossible at this current — they clamp motor cables remotely → connector needed).

**Decisions:**
- **Resolve the LA 100-P range tension with the user before freezing:** ±150 A measuring range vs the 260 A SW OC trip and 300 Arms module rating. Options: (a) accept — LEM path is a *validation/bench* instrument, module internal sensors + module hardware OC (625 Apk) remain the protection, and consciously note the SW trip is LEM-inert; (b) upgrade to LA 200-P / LA 305-S / LF 305-S class (±300–500 A) for full coverage. Log the choice.
- **Transfer function (both sources):** target ~1.5 V bias, ±300 A ↔ ±1.4 V (≈ 4.6 mV/A at the pin). Internal path: ~8 mV/A biased ~2.5 V → attenuate + re-bias. LEM path: burden resistor (precision, power-rated) + gain to the SAME slope. Firmware sees one calibration (`LEM_V_PER_A` replacement recorded).
- **Matching over accuracy:** 0.1% in gain positions, dual op-amps pairing channels, shared **buffered 1.5 V reference** (divider or reference IC) for all bias injection.
- **Solder-jumper detail:** 3-pad jumpers selecting source per channel, placed at high-impedance nodes so contact R is irrelevant; silkscreen table.
- **Op-amps:** OPA2376 (incumbent) vs OPA2365/OPA2320 vs TLV9062 (budget) — run from clean 5 V; 100 Ω + ≥1 nF C0G charge bucket at every ADC pin; anti-alias corner ~2–5 kHz (electrical fundamental ≤ ~1 kHz).
- Keep/drop the ADCINA4/ADCINB5 offset-reference outputs (cheap buffer taps — recommend keep).
- **LEM secondary connectors:** 3 pins per sensor (+15 / −15 / M out), Deutsch DT/DTM per team standard — decided jointly with S7's connector direction.

**Exit criteria:** ERC-clean ✅ (no real violation class); transfer-function table in the sheet +
handoff note ✅ — **but the two sources are NOT identical**, by the R_M-floor argument above, so the
handoff carries two constants instead of one; ±15 V load calculation closed ✅ (111 mA vs 200 mA);
SW-OC-trip coverage explicitly stated ✅ — **waived on the LEM path with rationale** (LA 100-P
saturates at ±150 A vs a 260 A trip; protection there is the module's 625 A_pk hardware shutdown,
and the *default* jumper position is the internal sensor, which does cover ±312 A).

---

## S7 — Encoder front-end (RM44AC) + connector

**Objective:** Rebuild the encoder subsystem from zero (3.0: channel B deleted, channel A half-reworked outside the board outline): hit **1.5 V bias / ~1.4 V amplitude** on SIN→ADCINA2, COS→ADCINB2, with matched anti-alias RCs, and select the vibration/noise-optimized connector.

**Prerequisites:** **RM44AC datasheet (WebFetch — mandatory): differential vs single-ended, supply V/I, output impedance/swing. BENCH DAY items #7–9 (scope the real output at the connector — the gain math uses THESE numbers, not nominals).** Cable length/type on the car.

**Decisions:**
- **Topology:** differential outputs → INA/precision diff-amp receive (big common-mode rejection over the harness — strongly preferred if available); single-ended → non-inverting scale/shift. Gain + offset computed from bench-measured levels to land exactly 1.5 V ± 1.4 V with clamp margin below 3.0 V.
- **Noise budget:** ≤ ~10 mV RMS at the pin (≈3× better). Encoder fundamental ≤ ~100 Hz (1 cycle/rev, ≤ 6000 rpm) → aggressive ~1 kHz corner is safe. **SIN and COS RCs identical** (C0G, 1%) — mismatched lag = angle error.
- **Protection:** BAT54S-class clamps (as 3.0 started), low-C ESD/TVS on lines leaving the board.
- **Connector:** (a) Deutsch DTM board header (DTM13 family — team standard, rugged, hand-solder part); (b) panel-mount DT/DTM + short internal harness to a locking on-board header (Micro-Fit+/JST — keeps team-standard external interface, assembly-friendly PCB); (c) shielded M12 circular (best EMC, non-standard). Criteria: vibration retention, shield termination path, team standard, JLC assembly impact. Encoder 5 V feed: filtered/dedicated per S3.
- **Shield strategy** per S2 policy; signal return Kelvin to the analog region.

**Exit criteria:** ERC-clean; transfer function + expected `RES_SINCOS_BIAS_CODE ≈ 2048` / `RES_SINCOS_AMPL_CODE ≈ 1911` in the handoff note; SIN/COS RC values identical and documented; connector decision logged.

---

## S8 — LaunchPad interface, CAN, integration, pin-map freeze

**Objective:** Capture the 4× 2×10 header interface + `vehicle_io` (CAN, cockpit switches), connect every sheet, and run the **full cross-check against the firmware pin map**. This is the schematic-freeze gate.

**Prerequisites:** S3–S7 done. Fetch: **LAUNCHXL-F28379D schematic/pinout** — verify every GPIO/ADCIN actually reaches a header pin (**especially GPIO131**; the 337ZWT muxes some GPIOs to multiple pins — confirm the routed one). Bench item #11 if not yet done.

**Work items:**
- `launchpad` sheet: 4 header symbols, per-pin nets, explicit no-connects on unused pins; the S2 power-domain implementation + silkscreen jumper-table note.
- `vehicle_io`: CAN transceiver (TCAN33x/SN65HVD23x class, 3.3 V, on free CAN-A/B pins — verify header availability), 120 Ω termination via solder jumper, team-standard connector; MAIN_SWITCH/ENGINE_START inputs with proper conditioning (pulldowns, RC, protection — NOT powered from a GPIO like 3.0's AND gate).
- **Pin-map cross-check table** (goes into CLAUDE.md): every row of `hw_control_v2.h` vs the netlist — GPIO6–11, GPIO66/131, GPIO25/27/26/64/52, ADCINB4/C4 (+ new C channel), ADCINA4/B5, ADCINC2, ADCINA2/B2, NTC pins from S5, CAN pins.
- Test points: every ADC input, every rail, gate rail, fault lines, 2× GND lugs.
- Zero-ERC; annotate; `generate_netlist`; first full BOM export → **JLC audit pass** (every refdes has LCSC; Basic/Extended counts; consigned list: DB37, Deutsch, LEMs, DC/DC).

**Exit criteria:** ERC zero; pin-map table 100% matched (or mismatches resolved + logged); BOM audit table exists; commit tagged `v4.0-schematic-freeze`. **Any schematic change after this reopens S8's checklist.**

---

## S9 — Board setup, stackup, placement

**Objective:** Outline, stackup, rules, full placement (no routing).

**Prerequisites:** S8 freeze. PrimeSTACK top-face mounting pattern confirmed (from S2; measure the real unit if the drawing is ambiguous).

**Work items:**
- `create_board_from_schematic` / sync; outline sized to the inverter top-face; **mounting holes** (M3+ per pattern, plus LaunchPad standoff holes); stackup JLC04161H-7628; fetch JLCPCB 4-layer capabilities and encode as design rules; netclass→rule mapping.
- Placement by region: power entry + regulators together; DB37 + gate drivers adjacent; **analog partition** (current sense, encoder, Vbus) far from bucks and gate bus; LaunchPad headers at the exact 3.0 geometry; ±15 V isolated island with spacing; connectors on edges per harness plan.
- `check_courtyard_overlaps`; height check under the LaunchPad envelope; `estimate_airwire_lengths` sanity.

**Exit criteria:** all footprints placed; zero courtyard overlaps; ratsnest reviewed; placement screenshot reviewed with user; placement-stage DRC clean.

---

## S10 — Routing I: power, gate path, planes

**Objective:** Power distribution, DB37/gate region, plane pours.

**Work items:** L2 solid GND first; L3 power islands; buck layouts per the datasheet notes captured in S3 (tight hot loops, thermal vias); gate lines as a grouped bus to DB37, series-R near driver; 24 V entry path + star return tie; `add_gnd_stitching_vias` around bucks and board edge.

**Exit criteria:** all power + gate nets routed; zone fills healthy (no starved islands); DRC clean on routed nets; verified that no gate/power trace crosses the analog partition on L1/L4.

---

## S11 — Routing II: analog + full DRC zero

**Objective:** Analog routing and everything remaining; reach zero DRC.

**Work items:** analog traces short/direct over unbroken L2; SIN/COS as a matched pair; Vbus + Kelvin return as a pair from DB37 to divider/buffer; anti-alias RCs physically at the ADC-pin end (header side, not source side); remaining signals; silkscreen pass (readable refdes, jumper tables, connector pinouts, LaunchPad JP config, board name/rev/date); `refill_zones`; DRC to zero (waivers logged).

**Exit criteria:** DRC zero; per-layer PDF/SVG exports reviewed; GND star/Kelvin topology spot-verified with `get_net_connections`.

---

## S12 — DFM, BOM/CPL, fabrication package

**Objective:** JLCPCB order package + final documentation.

**Work items:**
- Final BOM + CPL (fabrication-toolkit); **fresh JLCSearch re-verification of every LCSC line** (stock/pricing rot — this is not a repeat of session records); CPL rotation/polarity audit (SOT-23, diodes, connectors bite);
- Gerbers + drill + position files; assembly notes for consigned/hand-solder parts (DB37, Deutsch, LEMs, DC/DC module if applicable);
- **Firmware-handoff document** answering `control_v2_pinmap.md` line by line: `LEM_V_PER_A`, `VBUS_DIVIDER_RATIO`, `RES_SINCOS_BIAS_CODE`/`AMPL_CODE`, `MODULE_FAULT_ACTIVE_LOW`, NTC channels, new Isense-C channel, CAN pins, `HW_NAME` bump coordination;
- Physical bring-up checklist (rails first → gate signals scoped at DB37 → per `production_bringup.md` order).

**Exit criteria:** order-ready fab package; BOM with zero unvetted lines; handoff doc complete; tag `v4.0-release`.

---

# Appendix A — Bench-day checklist (ONE bench session, before S5/S6/S7)

Everything below is marked "assumed" in the firmware docs but is load-bearing for hardware design.

**Setup A — PrimeSTACK aux-powered only (24 V aux, NO DC link, no motor):**
1. ~~**Fault polarity**~~ *(**RESOLVED S4 from the datasheet: fault = HIGH.** Now only a confirmation, not a gate)*: 10 k pull-ups to 12 V on DB37-side fault pins (module pins 2/22/5/6/16); record healthy-state levels; force a cheap fault (brown-out aux below 18 V → watch the voltage flag, pin 16). Conclusion per pin: fault pulls LOW or releases HIGH?
2. ~~**Enable active levels**~~ *(**RESOLVED S4: the module has no enable pin.** The enables are board-local and defined ACTIVE-HIGH. Nothing to measure)*: toggle master/aux enable between 0 V and 12 V with gates off; watch whether drivers arm (fault flags / gate response). Confirm active-high for GPIO66/GPIO131 functions.
3. **Internal current sensors** *(**no longer blocks S6** — the design is deliberately insensitive to the answer: gain is set for the highest plausible sensitivity, so neither reading of the datasheet clips. The bench now only lets S10/S11 reclaim ADC range by changing one resistor per channel)*: zero-current bias of all three outputs (assumed 2.5 V — never verified); then a known DC current (bench supply + clamp-meter reference, 10–50 A loop) through one phase → mV/A + polarity per channel; channel-to-channel spread.
4. **Vbus sensor** *(**no longer blocks S5** — the datasheet rates every analog output at "load max 5 mA", so a resistive divider is allowed. Still worth measuring the low-voltage floor)*: output at 0 V and 24–48 V DC link; quantify the "unusable < ~40 V" floor; load with 10 k then 3.3 k → droop ⇒ divider allowed or buffer mandatory.
5. **NTC output** at room temperature — **one channel only** (DB37 pin 29, the 10 V inverter-section NTC). There is no second temperature pin.
6. **DB37 cable**: length, shield termination end, gauge.

**Setup B — RM44AC encoder:**
7. Differential or single-ended (datasheet first, then scope both legs).
8. Supply voltage rating + measured current.
9. Output bias/amplitude at the connector, unloaded AND loaded — S7's gain math uses these numbers.

**Setup C — LaunchPad** *(downgraded to verifications by S2 — SPRUI77 documents both; see `datasheets/`)*:
10. Verify no back-feed with the S2 jumper config (JP1/JP2/JP3 out, JP4/JP5 in, JP6 out): USB-only plug-in must not raise the header 3V3/5V pins.
11. Continuity sanity check: GPIO131 → header J6 pin 58 (SPRUI77 Table 4 says it's routed; confirm on the physical board).

**Setup D — LEM sensors (if in hand):**
12. Model label photo; supply current at zero primary; zero-current output; aperture fit on the actual motor cables.

---

# Appendix B — Candidate part directions (seeds, not selections)

- **Single-stage 3.3 V→gate rail (S4):** ✅ **SELECTED: 3× UCC27524DR (C465729).** The TC446x/MIC446x quad family was rejected on **stock**, not merit — TC4468 had 14 units at JLC. Do not "restore" it in a later session.
- **LEM (S6):** LA 100-P (confirmed baseline; ±150 A range — see S6 tension); LA 200-P / LA 305-S / LF 305-S (≥±300 A); HO 150-S/250-S open-loop 5 V (kills the ±15 V problem, lower accuracy — likely rejected for FOC).
- **±15 V isolated (S3):** A2415SDL-2W ×1 per sensor; Mornsun URB2415 5 W class; Mean Well DKA15.
- **Op-amps (S5/S6/S7):** OPA2376 (incumbent), OPA2365, OPA2320, TLV9062 (budget); INA826/INA333-class or matched diff-amp for differential encoder receive.
- **Fault receive (S5):** divider + SN74LVC2G17 Schmitt; LM2903 comparator; BJT inverter.
- **CAN (S8):** TCAN332/TCAN337, SN65HVD230/232 (3.3 V).
- **Protection:** SMBJ33A input TVS; P-FET reverse polarity; low-C ESD arrays on off-board lines; BAT54S ADC clamps.
- **Connectors:** Deutsch DTM13 board headers (encoder/LEM), Deutsch DT (power), Molex Micro-Fit+ / locking JST (internal harness option), Mini-Fit Jr (power distribution, carried over).

---

# Appendix C — Open items (decide in the noted session)

| Item | Session | Notes |
|---|---|---|
| ~~Offset-ref outputs (ADCINA4/B5) keep/drop~~ | S6 ✅ | **KEPT** — both read the buffered `ISNS_VREF` on two different converters (bias monitor + ADC-A/B cross-check) |
| NTC: one or both channels + ADC pin choice | S5 | NTC#2 outputs up to 10 V — divider rating |
| Fault pull-up rail: gate rail vs dedicated | S5 | outputs rated to 15 V |
| FSAE shutdown-circuit interlock on gate enable | S4 | ask team — maps the old /MAIN_SWITCH concept to rules |
| ~~LA 100-P ±150 A range vs 260 A SW trip~~ | S6 ✅ | **accepted (user)** — LEM is a validation instrument; SW trip inert on that path, module HW OC covers it |
| ~~LEM mounting location + secondary connector~~ | S6 ✅ | **remote sensor board, ONE 8-way connector**; Deutsch DTM at the bulkhead, Micro-Fit 3.0 2×4 on the PCB |
| Gate rail setpoint 12 vs 13.5 V | S3+S4 | margin above 11 V minimum at module |
| Encoder connector: DTM header vs panel DT vs M12 | S7 | vibration + shield + team standard |
| Conformal coating / cleaning spec | S12 | affects open connectors |
| `HW_NAME` / firmware version bump | S12 | firmware says "Control_Board_v2" today |
