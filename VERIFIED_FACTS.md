# FE_UFPR v4.0 — Verified facts vs assumptions

What has been verified, from what source, and what is still assumed. Update entries **in place**
(strike and annotate) rather than appending new paragraphs. (Moved out of `CLAUDE.md` on 2026-09-17, verbatim.)

## Bench-verified facts vs assumptions

**Verified (bench/scope):** encoder = RM44AC sin/cos, already demodulated, 1 cycle/rev; old front-end 2.25 V / 0.725 V; encoder noise 33.5 mV RMS at ADC pin; Vbus divider = 2×69 k, ratio 297.14 + 11.4 code offset.

**Verified in S1 from the 3.0 design files (not bench):** BoosterPack header grid ΔX 43.18 mm / ΔY 63.5 mm; DB37 as-built pin→net map (table below); DB37 jackscrew spacing 63.5 mm.

**Verified in S2 from SPRUI77 (LaunchPad User's Guide, `datasheets/`):** GPIO131 reaches header J6-58 (GPIO66 → J6-59, GPIO130 → J6-57) per Table 4; jumper semantics per §5.2: JP1/JP2/JP3 = USB 3.3 V/GND/5 V links (all three removed → debugger galvanically isolated when powered via BoosterPack headers), JP4/JP5 bridge MCU 3.3 V/5 V to site-2 headers, JP6 = USB-derived 5 V (stays out).

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
