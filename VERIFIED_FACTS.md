# FE_UFPR v4.0 — Verified facts vs assumptions

What has been verified, from what source, and what is still assumed. Update entries **in place**
(strike and annotate) rather than appending new paragraphs. (Moved out of `CLAUDE.md` on 2026-09-17, verbatim.)

## Bench-verified facts vs assumptions

**Verified (bench/scope):** encoder = RM44AC sin/cos, already demodulated, 1 cycle/rev; old front-end 2.25 V / 0.725 V; encoder noise 33.5 mV RMS at ADC pin; Vbus divider = 2×69 k, ratio 297.14 + 11.4 code offset.

**Verified in S1 from the 3.0 design files (not bench):** BoosterPack header grid ΔX 43.18 mm / ΔY 63.5 mm; DB37 as-built pin→net map (table below); DB37 jackscrew spacing 63.5 mm.

**Verified in S2 from SPRUI77 (LaunchPad User's Guide, `datasheets/`):** GPIO131 reaches header J6-58 (GPIO66 → J6-59, GPIO130 → J6-57) per Table 4; jumper semantics per §5.2: JP1/JP2/JP3 = USB 3.3 V/GND/5 V links (all three removed → debugger galvanically isolated when powered via BoosterPack headers), JP4/JP5 bridge MCU 3.3 V/5 V to site-2 headers, JP6 = output of the target-side 3.3 → 5 V boost (LaunchPad U12, LMR62421X) to the target 5 V (stays out). ~~JP6 = USB-derived 5 V~~ — **corrected 2026-11-05** from SPRUI77 Table 2 ("Enables 5 V supply from isolated 3.3 V") and Figure 4: the boost runs whenever the target 3.3 V is up (R14 pulls its SD pin high); JP6 only connects its output. Bench, board 1: JP6 out.

**Verified in S8 from SPRUI77 Tables 1–4 (the authoritative header pin-out):** the **entire firmware
pin map lands on BoosterPack pins** — 23 of 26 signals resolve to a header pin, and the three that do
not (`GPIO31` status LED, `GPIO42`/`GPIO43` SCI-A) are exactly the three this file already documents as
deliberately off-header. Checked by parsing the tables out of the PDF and diffing against the pin map,
not by eye. Confirms independently: **GPIO131 → J6-58** (S2), **ADCINC3 → J3-24** (S5), the
**five contiguous current pins J7-65…69** (S6), and **GPIO67 → J1-5**, which retires this file's
"pin unverified on Control_V2" caveat on the ISR probe. **Closed netlist-side on 2026-09-01:** every
socket pin in the exported netlist was mapped through the socket rule and SPRUI77 to its MCU function
and compared with the pin map — **29/29 signals on the expected pin, 0 mismatches, 47 no-connects**
(`S8_INTEGRATION_DESIGN.md` §7).

**Verified in S8 from TE's `DTM13-08PA-R004` drawing (rev D):** the 8-way is a **right-angle part with
a VERTICAL panel flange** (68.58 × 33.02 + four slotted ears), pins exit the flange rear and bend down;
**PCB rows are 6.35 ± 0.25 mm apart** (section B-B), columns 4.191; the flange hangs 4.4 mm below the
board top and only the 8 pins retain the part. S7's comparison table had assumed a 4.19 mm grid for
it — corrected. TE's repository holds **no** `DTM13-12PC/12PD`, `DTM13-08PB` or `DT13-08/12PA` drawing
under any flange suffix tried (probed slowly after a 222-request burst earned a temporary 403).

**Verified 2026-09-23 on te.com (logged-in browser) and from TE drawings C-DT15-12PX rev D2 / C-DT15-08PX-XXXX rev A (`datasheets/`):** TE **does** list vertical DTM headers — `DTM15-12PA/PB/PC/PD` (drawing C-DTM15-12PX rev B2: 60.96 × 33.02 panel flange, PCB screwed to the rear face, 4.19 mm pin pitch, cavities 1–6 / 12–7 printed) — the S7 "no vertical DTM13" result was a name miss; there is **no vertical 8-way DTM**. TE sample program ("Amostras disponíveis"): DTM headers → only the four 101 mm EEC-325X4 telematics parts; DT → DT15-12PA, DTF15-12PA, DT15-08PD, DT13-08PA, DT06-12SA, DT06-08SA, W12S, W8S, 0462-201-16141, 1062-16-0122 **yes**; DT06-12SB, DT06-08SD, DTM15-*, DTM13-12PA/PB-R005, DTM13-08PA-R004 **no**. DT 12-way cavity numbers are printed on the drawing (mating face: pin 1 bottom-left, 1–6 up the left column, 7–12 down the right); the 8-way has TE's own "Recommended PCB layout" on sheet 2 (pin holes Ø1.88 +0.13, screw holes Ø3.43 +0.13, rows ±2.73 / ±7.175, columns ±4.56, screws 21.34 × 27.2). Body = flange outline on the board, flange face 15.52 mm up, 30.1 mm overall, pins 3.1 mm below.

**Verified in S4 from the PrimeSTACK datasheet (`datasheets/`, pages 2 and 6) — no longer assumptions:**
DB37 pin functions for all 37 pins incl. TOP/BOT within each half-bridge; **fault = HIGH**
("open collector, logic low = no fault", max 15 mA); every analog output rated **load max 5 mA**;
digital input network **10 kΩ to GND + 1 nF to GND**, HIGH = on; **one** temperature pin (29);
pins 9/27 are a **15 V/50 mA supply output**, not sensors (bench 2026-11-03: 0 V with the module powered; unused on the board); pin 1 is **true earth/shield**;
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
- ~~Fault output polarity~~ — **resolved S4 on paper: fault = HIGH.** **Bench-confirmed 2026-11-03** (bring-up B/D, board 1).
- ~~Enable active levels for GPIO66/GPIO131~~ — **resolved S4: board-local, we define them ACTIVE-HIGH.**
- ~~NTC output level~~ — **no longer blocks S5**: the divider is rated for the full 0–10 V the datasheet specifies. The bench measurement now only calibrates the curve, needed before the OT trip threshold is set.
- Internal current-sensor **bias AND sensitivity** — ~~blocks S6~~ **no longer blocks: S6 is designed to be
  insensitive to it.** ⚠ The "≈7.5–8 mV/A" this file used to list as *bench-verified* was **not measured** —
  `control_v2_pinmap.md` §6 derives 8.0 mV/A as `2.4 V / 300 A` from an *assumed* 2.5 V bias, and the
  separate bench figure of 78.6 mV/A belongs to the bench clamp+amp board, not the module. The datasheet's
  "4.9 V @ 300 A_RMS" admits two readings (8.00 or 5.66 mV/A); S6 sets the gain for the **higher** one so
  neither reading clips. Bench now only reclaims ADC range (one resistor per channel). Polarity never
  blocked anything — `PHASE_ID_DEFAULT_EN` re-detects each channel's sign at every ALIGN.
  ⚠ **Bench 2026-11-03: the outputs read 0 V at zero current with the module powered** — the 2.5 V bias
  assumption is wrong and the internal path clips negative currents (§ Bench, board 1; rework in `OPEN_ITEMS.md`)
- ~~RM44AC differential vs single-ended, supply V/I, true output levels at the connector~~ — **resolved S7 from the datasheet** (`datasheets/RLS-RM44_RM58-RM4458D01_01.pdf`): **single-ended** VA/VB, **2.2 ±0.2 Vpp**, offset **3/5·Vdd ±5 mV**, **720 Ω** internal series impedance, 5 V ±5 % / 13 mA, LiYCY 4×0.20 mm² shielded. Bench now only confirms. ~~The installed encoder's actual amplitude is still unknown~~ (3.0's bench figures couldn't settle it: its channel A was reworked off-board) — **bench 2026-11-05: ≈ 2.0 Vpp**, the low end of the datasheet (amplitude ≈ 1583 codes at the ADC against 1745 for a 2.2 Vpp source; § Bench, board 1). S7 spans the whole 2.0–2.4 Vpp range, so nothing clips.
- ~~LaunchPad no-back-feed with the S2 jumper config; GPIO131 header continuity~~ — **bench 2026-11-03:** GPIO66/GPIO131 verified by bring-up B; the back-feed test found D12 drawn backwards and that the LaunchPad has no 5 V → 3.3 V regulator (both in `OPEN_ITEMS.md`, reworked on board 1)

## Bench, board 1 (2026-11-03 to 05, bring-up per `S12_FAB_PACKAGE.md` §5)

- **A (power) — pass** after rework: all rails OK, 0.096 A idle at 24 V. D12 rotated; LaunchPad 3.3 V fed by the U3 → J20.1 wire, LaunchPad JP1–JP3 out (USB isolated).
- **B (gate enable) — pass:** boots to IDLE; `module_fault` 0x1F with the DB37 unplugged (fail-safe HIGH); GATE_EN only with GPIO66 AND GPIO131 AND the main switch, and pulling the switch drops it in hardware. Fault found: U6 pin 3 (GND) open.
- **C (PWM) — pass:** all six module inputs LOW at every enable (firmware all-LOW off state); open loop at 0.3 / 10 Hz: levels, complementary pairs, 1500 ns dead band and 120° phasing correct. Enable-edge scope capture skipped.
- **D (trip path) — pass for OC A/B:** shorting plug; OC A → OSHT1 only, OC B → OSHT2 only, MCU pins in the active-short pattern while GATE_EN stays LOW; OT/DCOV open → software fault. Two firmware bugs fixed (firmware `308a542`). Protection-armed boot with the real module: `module_fault` 0x00, `tz_trip` 0. SysConfig arms OSHT before the pad inversion, so every boot latches a spurious OST; the firmware clears it, and it cannot reach the module (GATE_EN LOW until RUN).
- **E (analog) — partial:** encoder receiver 1.41 V on both channels, encoder unplugged (design 1.50 V; ⚠ that was a marginal U17 pin 6 joint, 1.498 / 1.499 V after the reflow, see the encoder entry below); LEM paths = `ISNS_VREF` ≈ 1.47 V; Vbus floor 0.12 V at DB37 pin 7 (≈ 66 codes, no link); module NTC 0.62 V at room temperature; module aux ≈ 0.47 A at 24 V (0.57 A total). **Module current outputs 0 V at zero current** (internal-sensor entry above). Module 15 V outputs (pins 9/27) 0 V. Faults found: U16 GND joint, U16/U17 bridges and flux, a U13 joint.
- **LEM swap (2026-11-04) — pass.** JP3–JP5 moved to 2-3, J3 harness plugged.
  - **Zero, no primary current:** every LEM stage output reads the same as TP36 on the meter (0 mV difference). ADC means of 1000 samples: A5 / C4 / B4 within ±1.3 codes of A4 / B5.
  - **`ISNS_VREF`:** 1.462 V, 1996 codes (design 1.4685 V, 2005). The R99/R100 divider runs off `+5V`, so `+5V` is about 0.4 % low. Harmless: CALIBRATE captures the real zero.
  - **Meter loop test:** 10 turns at about 0.11 A (1.1 A-turns, 250 Ω from 30 V) through each sensor in turn, along the arrow. Each gave +6 mV on its own stage output only (expected +5.4 to +5.9 mV), for A, B and C. So each sensor is powered, and its scale, sign and harness pinning are right.
  - **ADC loop test, sensor A only:** a 7.5-code step (about 1.12 A-turns) on ADCINA5 only; B4 and C4 unchanged. The header and firmware channel mapping are right: no A/C swap. The loop ran against the arrow that time, so the step was negative. B/C mapping at the ADC was not tested separately; ALIGN in F checks it.
  - **Internal-sensor outputs:** re-checked with the module powered, all 0 V. The earlier 3.5 V on `ISNS_B` came from the U13 joint.
- **Encoder (2026-11-05) — pass after rework.**
  - **Fault:** U17 pin 6 (−INB of the `ENC_VREF_HI` follower) was an open joint. Pin 5 read 4.22 V, pin 6 0.12 V, pin 7 5.0 V, so `ENC_VREF_HI` sat at the rail: TP40/TP41 read 0.60 V with the encoder unplugged and swung 0 → 1.76 V, clipped, with it plugged. The 1.41 V of 2026-11-03 was the same joint, marginal. Reflowed.
  - **After the fix:** bias 2045 / 2047 codes (1.498 / 1.499 V; design 2039). Turned by hand: SIN 468–3629, COS 465–3639 codes, amplitude ≈ 1580–1585 codes, so the installed encoder gives ≈ 2.0 Vpp. Firmware calibration: `res_mag` 0.98. Angle noise at standstill 2.6° electrical rms before the filter (3.0 board ≈ 26°).
- **F (first motion, DC link 31 V) — started; closed-loop current passes.** Firmware `b3c431e` (branch `sensorless-observer`).
  - **Phase ID:** map A → U, B → V, C → W, no inversion. This closes the B/C ADC mapping gap left by the A-only loop test.
  - **Resolver:** direction correct; electrical offset 106.6°, repeatable over three ALIGNs (106.8–107.3° once ALIGN became closed-loop, firmware `b655878`).
  - **Closed loop:** 0 → 2 → 5 A q-steps in 1–2 ms with Id ≈ 0; phase peaks 4–7 A; no faults. Later the same day: speed mode, current-PI and dead-time retunes, Id up to 20 A at standstill without a trip (firmware `CLAUDE.md`, bring-ups G–K).
  - The firmware had assumed a 24 V link. `BENCH_DC_LINK_V` is now 31: keep it equal to the supply.
- **ADC interference (2026-11-05) — characterised and worked around in firmware; source not removed.**
  - **Level:** about 5 codes rms (3.7 mV, ≈ 0.8 A on a current channel) on every channel of all three ADCs, with the power stage not switching: A4 6.7, B5 4.4, C2 5.7, A5 4.9, B4 5.8, C4 5.9, A2/B2 5.5. It doesn't depend on the signal level, and the passive nodes (Vbus, the `ISNS_VREF` refs) are as noisy as the op-amp stages.
  - **One shared interference:** channels converted at the same instant correlate 0.8–0.99; one conversion slot (290 ns) later the correlation is −0.9. Flat to Nyquist at 10 kHz (aliased), kurtosis ≈ 1.9 (mostly periodic, with jitter); single-tone fits give 1.55–1.69 MHz. What is left per channel is 0.54–0.61 codes (0.08 A): the board's analog chains sit at the ADC's own floor.
  - **Not VREFHI:** the LaunchPad drives VREFHI from one REF5030 through two OPA350s (ADC A+C, B+D), which doesn't match the correlation pattern, and the error doesn't scale with code.
  - **Lead suspect: the LaunchPad's U12** (LMR62421X, 1.6 MHz boost; not the board's U12, which is the phase-A OPA2376). Its VIN is the target 3.3 V and R14 pulls its SD pin up, so it runs whenever target 3.3 V is present, whatever JP6 says. The U3 → J20.1 rework is what wakes it (JP6 is out). Other candidates: board U2 TPS62933F (1.2 MHz), U1's third harmonic (1.2 MHz), the LaunchPad's TPS62080 core buck, the PrimeSTACK's internal supplies through the DB37 grounds.
  - **Kill test, not run** (the user won't modify the LaunchPad for now): board off, tie LaunchPad U12 pin 4 (SD), or R14's non-3V3 pad, to LaunchPad GND, then re-capture with the encoder plugged and unplugged.
  - **Firmware workaround:** Iu, Iv and Iw convert in the same slot (`5432839`), so the three-sensor Clarke cancels the shared error: at IDLE Iα 0.98 → 0.15 A rms, Iβ 0.08 A; closed loop at zero reference Id / Iq 0.06 / 0.16 A rms. Dead-time compensation subtracts the zero sequence before its sign ramp (`3c4c562`). Every SOC now uses the same 15-cycle window, so the three ADCs convert in lockstep (`f8e06ef`).
  - **Not cured:** SIN/COS still carry the shared shift (atan2 doesn't cancel it), ≈ 2.6° electrical, which matches the measured standstill noise. Only removing the source fixes that.
- **Vbus reads about 4× low (2026-11-05).** 77 codes at 31 V against 46–48 codes with the link off: Δ ≈ 22 mV at ADCINC2, i.e. ≈ 52 mV at DB37 pin 7 through the divider, where 31 × 6.5 / 900 = 224 mV is expected.
  - Most likely the module sensor's low-end non-linearity: the old Control_V2 board showed the same signature with the same sensor (an affine fit over 20–150 V put code 0 near 16 V; compressed below 40 V, linear from 40 to 150 V). "Link off" isn't 0 V either (the old bench floored at ≈ 6 V from gate-drive back-feed).
  - To localise: meter TP19–TP21 with the link on and off. ≈ 52 mV there means the module sensor; ≈ 224 mV means the R57/R58 path.
  - Calibrate only from metered points ≥ 40 V, or at the operating bus (firmware `vbuscal`). Settle it before HV; until then the firmware uses `vbus_ovr` = 31.
- **XDS100 drops.** Twice on 2026-11-03 while LaunchPad JP1/JP2 were in (USB ground tied to the board); isolated since. Three more on 2026-11-05, each on an encoder hot-plug with JP1–JP3 out: most likely a common-mode step through the cable shield and the debugger's isolator. **Rule: plug the encoder in only with the board unpowered.**
