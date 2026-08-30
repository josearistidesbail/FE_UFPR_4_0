# S6 — Current sensing: 3 channels, dual-source (internal / LEM)

**Session deliverable.** Every value on the `current_sense` sheet, where it came from, and what is
still assumed. Companion to [`S3_POWER_DESIGN.md`](S3_POWER_DESIGN.md),
[`S4_GATE_DRIVE_DESIGN.md`](S4_GATE_DRIVE_DESIGN.md) and
[`S5_MODULE_STATUS_DESIGN.md`](S5_MODULE_STATUS_DESIGN.md).

**Datasheet fetched this session:** `datasheets/LEM-LA_100-P-v15.pdf` (LEM International, v15,
6 July 2023). It is the source for every LEM number below.

---

## 0. The two user decisions that shaped the session

1. **LA 100-P accepted, no upgrade.** The ±150 A measuring range is knowingly short of the 260 A
   software OC trip. Consequence formalised in §9.
2. **The sensors live on an external board near the motor cables.** Our board provides the
   symmetrical supply and a local return, and receives three sensor outputs through **one global
   connector** — not one per sensor. The user asked for Deutsch and asked to be argued with; §10
   is that argument and what was actually built.

A third decision followed from the second and was made by the user during the session:
**the burden resistors are on *our* board**, so the harness carries current, not voltage.

---

## 1. What the LA 100-P datasheet actually constrains

| Parameter | Symbol | Value |
|---|---|---|
| Primary nominal RMS current | I_PN | 100 A |
| Primary measuring range | I_PM | 0 … **±150 A** |
| Turns ratio | N_P/N_S | **1 : 2000** |
| Secondary nominal RMS current | I_SN | 50 mA |
| Supply voltage (±5 %) | U_C | ±12 … 15 V |
| Current consumption @ ±15 V | I_C | 8+I_S / 10+I_S / **12+I_S** mA (min/typ/max) |
| Accuracy @ I_PN, 25 °C, ±15 V | ε | ±0.45 % |
| Linearity | ε_L | < 0.15 % |
| Electrical offset @ I_P = 0 | I_OE | ±0.10 mA (= ±0.2 A primary) |
| Magnetic offset after 3× I_PN overload | I_OM | ±0.15 mA (= ±0.3 A primary) |
| Offset drift −25…+85 °C | I_OT | ±0.30 mA max (= ±0.6 A primary) |
| Delay to 90 % for an I_PN step | t_D90 | < 1 µs (at di/dt = 100 A/µs) |
| Secondary winding resistance | R_S | 120 Ω @ 70 °C, **128 Ω @ 85 °C** |

### 1.1 The measuring-resistance window — and why it has a *minimum*

| Supply | Max current | R_M @ 70 °C | R_M @ 85 °C |
|---|---|---|---|
| ±12 V | ±100 A | 0 … 50 Ω | 0 … 42 Ω |
| ±12 V | ±120 A | 0 … 22 Ω | 0 … 14 Ω |
| **±15 V** | **±100 A** | 0 … 110 Ω | **20 … 102 Ω** |
| **±15 V** | **±150 A** | 0 … 33 Ω | **20 … 25 Ω** |

The **maximum** is a compliance limit: the output stage must drive I_S·(R_S + R_M) inside the
supply rails. The **minimum at 85 °C** is a thermal limit in the opposite direction — the burden
has to take dissipation *out of* the transducer at high ambient. So R_M is not a free knob:

> **Lower current ceiling → wider window → more volts per amp.** At the full ±150 A range and a hot
> ambient there are only 5 Ω of legal width (20–25 Ω).

Note ±12 V only reaches ±120 A; the ±15 V rail S3 already provides is what buys the full range.

### 1.2 Burden choice: 47 Ω ‖ 47 Ω = 23.5 Ω

Fitted as **two 1206 parts in parallel per channel** (R68/R69, R80/R81, R92/R93).

| Check | Value |
|---|---|
| Position in the 85 °C window | 23.5 Ω of 20–25 Ω — 3.5 Ω above the floor, 1.5 Ω below the ceiling |
| Compliance | I_S(R_S+R_M) = 0.075 × (128+23.5) = **11.4 V** of ±15 V |
| Burden voltage at ±150 A | 0.075 A × 23.5 Ω = **±1.7625 V** |
| Dissipation at ±150 A | 0.132 W total, **66 mW per 1206 = 26 %** of rating |
| Harness contribution | a few hundred mΩ of cable adds to R_M and eats ceiling margin, not floor margin |

The parallel pair is not only a power decision. It is the **range-adjust mechanism the user asked
for**: fit one resistor instead of two for 47 Ω (legal up to ±100 A, where the 85 °C window opens to
20–102 Ω), or change the pair. Two 1206 pads rework far more easily than one hot 0805.

Tolerance: 0.1 %, Yageo RT1206BRD07 thin film — the burden is the LEM path's **gain-setting
element** and gain is *not* captured at runtime (only offset is), so its tolerance is a direct
current-reading error. A parallel pair also averages: two 0.1 % parts give ≈0.07 %.

---

## 2. Why the burden is on this board

The LA 100-P secondary is a **current source**. Where the burden sits decides what the harness
carries.

| Burden on the **sensor** board | Burden on **this** board (chosen) |
|---|---|
| Harness carries a voltage | Harness carries a **current** |
| Wire resistance, connector contact resistance and board-to-board ground shift all appear in the reading | None of them appear — the burden voltage is developed on our board, referenced to our own analog return |
| Gain element is on a hand-built board bolted near the motor cables | Gain element is a 0.1 % part on the JLC-assembled board, three channels from one reel |
| Re-burdening means opening the remote enclosure | Re-burdening happens on the bench, next to the ADC |

The compliance cost of moving it is nil: a few hundred mΩ of cable against a 23.5 Ω burden and a
25 Ω ceiling. This is also what makes an **unshielded** connector acceptable (§10).

One consequence to respect in layout: the M current returns through the **burden**, so the burden's
low side is the node the difference amp must Kelvin-sense — S11 rule 2.

---

## 3. The module's internal sensor — what the datasheet does *not* say

PrimeSTACK datasheet p.2 gives exactly one line for the internal current sensors:

> Analog current sensor output, inverter section — **load max 5 mA, @ 300 A_RMS: 4.7 / 4.9 / 5.0 V**
> (min / typ / max, for V_IU ana2 / V_IV ana2 / V_IW ana2)

It gives **no zero-current bias and no polarity**. Everything downstream of those two facts is
still bench item #3.

### 3.1 A correction to the project's own record

`CLAUDE.md` listed "internal current sensors ≈ 7.5–8 mV/A" under **bench-verified**. It is not.
`control_v2_pinmap.md` §6 *derives* 8.0 mV/A as `2.4 V / 300 A` from an **assumed** 2.5 V bias, and
marks bias, polarity and sensor limit as *"assumed, must be verified on bench"*. The separate
bench-measured figure of 78.6 mV/A in `hw_control_v2.h` belongs to a **different device** — the
bench clamp-and-amp board, not the module. The CLAUDE.md line has been moved to the assumed list.

*(Unrelated but adjacent: `hw_control_v2.h` HEAD carries `LEM_V_PER_A 0.0075f` directly under a
comment block insisting 78.6 mV/A was bench-measured and that 8 mV/A was a 9.8× under-estimate.
History is `0.008 → 0.0786 → 0.0075`, and the commit that made the last change documented a
phase-ID solver rewrite, not this. One of the two is wrong by 10×. Logged for S12.)*

### 3.2 The ambiguity that actually matters, and why it does not block

"4.9 V @ 300 A_RMS" has two defensible readings:

| Reading | Implied sensitivity | Consequence |
|---|---|---|
| 4.9 V at 300 A **instantaneous** | 8.00 mV/A | sensor clips at 312 A, i.e. *below* the module's own 300 A_RMS = 424 A_pk rating |
| 4.9 V at the **peak** of a 300 A_RMS sinewave (424 A_pk) | 5.66 mV/A | sensor linear to ~441 A_pk |

The second is the more plausible design intent — a sensor that saturates below its own module's
rated current would be useless — but the first cannot be excluded, and neither matches a sensor
feeding the 625 A_pk over-current shutdown (which is almost certainly desaturation detection in the
gate drivers, not this analog output).

**The design does not have to pick.** The gain is set for the **higher** sensitivity (8 mV/A):

- if 8.00 mV/A is right → ±300 A lands on ±1.44 V, exactly the conditioning target;
- if 5.66 mV/A is right → ±300 A lands on ±1.02 V and full scale becomes ±441 A.

Either way **there is no clipping and the ≥±300 A requirement is met**; the pessimistic case only
wastes ADC range. Designing for the *lower* sensitivity would have inverted that: it would clip at
221 A if the higher one turned out to be true. One resistor per channel reclaims the range after
the bench measures it.

Polarity is a non-issue: `PHASE_ID_DEFAULT_EN = 1` re-detects each channel's sign at every ALIGN.

### 3.3 A finding nobody should design around

The 4.7 / 5.0 V min–max band is **±3 %**, and the three channels are specified as one line. No
amount of 0.1 % board resistors fixes a several-percent spread between the module's own three
sensors, and firmware calibrates **offsets** at runtime but **not gains**. The internal path is
therefore the *convenient* source, not the accurate one — which is precisely why the LEM path
(±0.45 %) exists.

---

## 4. Topology: two independent difference amps per channel

Each stage is a four-resistor difference amp:

```
V_out = (R2/R1)·(V2 − V1) + V_bot      with R1'=R1 and R2'=R2
        V2 → non-inverting series R,   V1 → inverting series R,
        V_bot → bottom of the non-inverting divider
```

| | V2 (signal) | V1 (return it rejects) | V_bot |
|---|---|---|---|
| **Internal** | `ISNS_x_RAW` (DB37 30/31/32) | `ISNS_RTN` (DB37 12/13, Kelvin) | **GND** |
| **LEM** | `LEM_x_M` (top of burden) | `ISO_COM` (bottom of burden, Kelvin) | **ISNS_VREF** |

Both sources are "a voltage across a two-terminal source", so both get the same circuit — and the
rejection of the *source's own return* is built in, which is what closes S2's Kelvin requirement
and prevents the load-dependent IR-drop error measured on 3.0's Vbus channel.

### 4.1 Why V_bot differs, and why that forced two stages instead of one

The two sources are **not** electrically interchangeable:

- the internal sensor is a **2.5 V-biased** signal, and 0.600 × 2.5 V = **1.500 V** — the target ADC
  bias falls out of the attenuation for free, so V_bot = GND;
- the LEM burden is a **true bipolar** signal about 0 V, so the 1.5 V bias must be *injected*.

A single shared amp with a jumper would therefore have to switch **three** things — signal, return
and V_bot — i.e. nine jumper positions across three channels, where a wrong combination still
produces a plausible-looking reading. That is the class of bench trap S5 rejected when it refused a
hidden inversion in the fault chain.

**Chosen instead: both stages are built and both run permanently; one 3-pad jumper per channel
selects which output reaches the ADC.** Cost is three extra op-amp halves and twelve resistors.
What it buys:

- one jumper per channel, and no combination of positions can produce a wrong-but-plausible reading;
- each path is scaled optimally for its own sensor;
- **both outputs are live simultaneously** on TP30–TP35 — the two sensors can be scoped against each
  other on the same current, which is the entire point of having a reference-grade LEM.

The jumper sits at an op-amp output feeding 100 Ω into a 22 nF bucket: no DC flows, so contact
resistance is irrelevant, satisfying the roadmap's "place jumpers where contact R doesn't matter".

---

## 5. Component values

### 5.1 Internal stage — R1 = 20.0 kΩ, R2 = 12.0 kΩ (0.1 %)

| Quantity | Value |
|---|---|
| Gain | 12.0/20.0 = **0.600 exactly** |
| ADC bias at 0 A | 0.600 × 2.5 V = **1.500 V** — the conditioning target, hit exactly |
| ADC sensitivity (at 8 mV/A) | **4.800 mV/A** |
| ±300 A | ±1.440 V → span **0.060 … 2.940 V** |
| Clipping | ±312.5 A (≥ the required ±300 A) |
| Module loading | 0.625 × V_RAW / 20 kΩ ≤ **0.153 mA** at 4.9 V, plus 4.9 µA of bleed — of a 5 mA budget |
| Op-amp input common mode | 0.375 × V_RAW = 0.04 … 1.84 V |
| CMRR (resistor-limited, 0.1 %) | ≈52 dB → ≤**0.13 %** gain error; it is a gain term, not a nonlinearity |

`R67/R77/R89 = 1 MΩ` bleed each `ISNS_x_RAW` to GND: with the DB37 unplugged the input would
otherwise float and the stage output would be undefined. At 1 MΩ the loading error is ≤0.01 % and a
disconnected module reads as a hard 0 V — unmistakably "not connected" rather than "zero current".

### 5.2 LEM stage — R1 = 12.0 kΩ, R2 = 4.99 kΩ (0.1 %), R_M = 23.5 Ω

| Quantity | Value |
|---|---|
| Gain | 4.99/12.0 = **0.41583** |
| ADC sensitivity | 0.41583 × 23.5/2000 = **4.886 mV/A** (**+1.8 %** vs the internal path) |
| ±150 A | ±0.733 V about 1.4685 V → span **0.736 … 2.201 V** |
| Burden loading by the amp | 17.2 kΩ across 23.5 Ω = −0.13 % gain, identical on all three channels |
| ADC resolution | 0.150 A/code (internal: 0.153 A/code) |

The +1.8 % mismatch is deliberate. Making the slopes identical needs a 16 Ω burden — **legal at
70 °C but below the 20 Ω floor at 85 °C**. The alternative, a closer resistor ratio from a different
manufacturer family, would trade a *constant* 1.8 % (absorbed by one firmware constant) for a
*differential temperature coefficient* between two thin-film families (up to 0.2 % over 40 °C, and
not absorbed by anything). **Same family beats closer ratio.** All four 0.1 % lines are Yageo
RT thin film.

### 5.3 Bias reference — 1.4685 V, buffered

`R99` 12.0 kΩ / `R100` 4.99 kΩ from +5 V → **1.4685 V**, filtered by `C83` 1 µF ‖ `C84` 100 nF
(R_th = 3.52 kΩ → **45 Hz** corner, which kills 5 V-rail noise), buffered by **U15A**.

The buffer is not optional: the reference feeds the *bottom of each non-inverting divider*, so any
source impedance adds directly to R2' and unbalances the difference amp. A 700 Ω divider impedance
against R2' = 4.99 kΩ would be a 12 % gain error on that leg.

No reference IC. Justification: (a) the firmware captures each source's zero at every CALIBRATE, so
absolute accuracy buys nothing; (b) **the node is measured live** on two ADC channels (§8), so
drift is observable rather than silent. The divider reuses the two 0.1 % values the LEM stages
already need — **zero additional BOM lines**.

### 5.4 Anti-alias and charge bucket

The pole is in each difference amp's feedback, with a matching capacitor across R2' so common-mode
rejection does not collapse at HF (S1's sourcing constraint #2 rules out a passive pole at low
source impedance — no C0G above ~22 nF exists in stock).

| Stage | R2 | C | Corner | Phase lag at 1 kHz |
|---|---|---|---|---|
| Internal | 12.0 kΩ | 2.2 nF C0G | **6.03 kHz** | 9.4° |
| LEM | 4.99 kΩ | 4.7 nF C0G | **6.79 kHz** | 8.4° |

Corner chosen high on purpose. A single pole is a weak anti-alias filter at any corner (−6 dB at
10 kHz here), while phase lag in *current* feedback rotates the measured current vector and costs
torque accuracy at speed. What actually rejects the 10 kHz switching ripple is **synchronous
sampling at the PWM peak**, which the firmware already does. The 12 % corner mismatch is between
*sources*, never between channels — all three channels use identical values.

`100 Ω + 22 nF C0G` at each ADC pin is the charge bucket for the S/H, as in S5.

**No new C0G value is introduced.** 2.2 nF (`C107043`), 4.7 nF (`C85980`), 1 nF (`C106246`) and
22 nF/0805 (`C77069`) are all existing S1-kit lines — this closes the S6 half of the standing
"standardise C0G values" item.

### 5.5 EMC caps at the connectors

`C64/C70/C77` (1 nF C0G, module side) and `C65/C72/C79` (1 nF C0G, LEM side) sit at their connector
pins. They form **no** anti-alias pole with our 20 k/12 k input resistors because they are upstream
of them, working against the source's own low output impedance — deliberate, so the EMC cap and the
filter corner stay independent.

---

## 6. Values picked against live stock, not against E96

Third session running, same trap. A sweep of 0.1 % 0603 stock at JLC:

| Value | Best 0.1 % line | Stock |
|---|---|---|
| **20.0 kΩ** | RT0603BRD0720KL `C723637` | **210 576** |
| **12.0 kΩ** | RT0603BRD0712KL `C326735` | **38 454** |
| **4.99 kΩ** | RT0603BRD074K99L `C723532` | **92 725** |
| 5.76 kΩ | RT0603BRD075K76L `C861489` | **3** ⚠ |
| 5.90 kΩ | RT0603BRE075K9L `C862231` | 1 879 ⚠ |
| 4.32 kΩ | AT0603BRD074K32L `C855881` | 2 260 |
| 4.42 kΩ | RT0603BRD074K42L `C861442` | 157 ⚠ |

The "natural" pair for a 0.583 gain is 12.0 k / 7.0 k, and the natural E96 neighbours (5.76 k,
5.90 k) are effectively unbuyable. **20.0 k / 12.0 k is both the best-stocked pair on the board and
the one that lands the bias on exactly 1.500 V** — the constraint and the ideal coincided for once.

⚠ **Do not "consolidate" the two 12 kΩ lines.** `C22790` (1 %, S3, U1's FB divider) and `C326735`
(0.1 %, this sheet) are different parts for different jobs.

---

## 7. ±15 V budget — closes S6's exit criterion

| Term | Per rail |
|---|---|
| 3 × quiescent, worst case (12 mA each) | 36 mA |
| Peak instantaneous secondary current | 75 mA |
| **Total worst case** | **111 mA** |
| URA2415YMD-6WR3 capability (S3) | ±200 mA, 6 W |
| **Margin** | **1.8×** |

For a balanced three-phase set the maximum instantaneous sum of the *positive* secondary currents
is **1.0 × peak** (at the angle where one phase peaks and the other two sit at −½), not 1.73 ×.
The three secondaries also sum to zero, so the two rails share the load rather than both carrying
worst case. S3's supply choice survives unchanged.

---

## 8. ADC pin allocation

**`ISNS_C_ADC` → ADCINA5 → BoosterPack site-2 `J7-66`** (SPRUI77 Table 3, GPIO94).

S5 had left ADC-A SOC1 free and nominated ADCINA3 (J3-26) or ADCINA5 (J7-66). ADCINA5 wins on a
layout argument that only shows up when you read the header table: the current-sense signals occupy
**five contiguous pins on one header**.

| J7 pin | Signal | ADC |
|---|---|---|
| 65 | `ISNS_REF_B_ADC` | ADCINB5 |
| **66** | **`ISNS_C_ADC`** | **ADCINA5** |
| 67 | `ISNS_B_ADC` | ADCINC4 |
| 68 | `ISNS_A_ADC` | ADCINB4 |
| 69 | `ISNS_REF_A_ADC` | ADCINA4 |

Three channels on three *different* converters (B, C, A) keeps the per-ADC load balanced —
A: SIN + I_w, B: I_u + COS, C: I_v + Vbus + NTC — while the traces stay adjacent and equal-length,
which is what channel-to-channel matching actually needs. Suggested SOC: **ADC-A SOC1**.

### 8.1 The offset-reference channels: KEEP, with a job

`ADCINA4` / `ADCINB5` were wired on 3.0 and never sampled. They are kept, driven by **U15B**
(a second buffer following `ISNS_VREF`, so the ADC's sampling charge kick never lands on the
reference the LEM stages use), each through its own 100 Ω + 22 nF bucket.

Both read the **same** node, on **two different converters**. That makes them useful rather than
decorative: firmware gets a live reading of the bias the LEM path is standing on, *and* an ADC-A
vs ADC-B comparison on a known common node — an inter-converter offset/gain check for free.

---

## 9. Safety: the software OC trip is inert on the LEM path

The LA 100-P saturates at ±150 A. `MOTOR_OC_TRIP_A` is 260 A. **With a LEM selected, the software
over-current check can never fire before the ADC clips**, and choosing a larger burden for a
lower-current bench range lowers that ceiling further.

This is roadmap option (a), taken knowingly:

- protection on the LEM path is the module's **own 625 A_pk hardware shutdown within 15 µs**, plus
  the `FLT_OC` lines received on `module_status` and routed to the X-BAR hardware trip (S5);
- the **internal** sensors do cover ±312 A, so the **default jumper position (internal) is also the
  one that keeps the software trip meaningful**. The LEM path is a validation instrument.

This must appear in the S12 firmware handoff, not only on the schematic.

---

## 10. The connector — argued, and what was actually built

**The Deutsch choice is right for the vehicle interface, and I am not arguing against it.** The
usual objection to Deutsch for analog — no shield termination, no controlled impedance — is
neutralised here by the current-mode harness (§2): contact resistance in the mΩ and the absence of
a 360° shield simply do not enter the measurement. Against that, DT/DTM give IP67 sealing, a
secondary lock wedge, keying, and the team already stocks them.

Four caveats were raised: prefer **DTM** over DT on size, go **8-way** rather than 6 to get a shield
pin plus a spare, accept that a shield can only pigtail into a pin, and **key or size the LEM
connector differently from the encoder connector (S7)** — mis-mating ±15 V into an RM44AC destroys
it. That last one is the only one that worries me.

**What was built, and why it is not a board-mounted Deutsch.** The candidate part is
`DTM13-08PA-R004` (8-way, 4.19 mm pitch, PCB header, right-angle). TE's product drawing is behind a
login, and the only dimensions obtainable from distributors are marketing-level. Deriving a
through-hole pattern from those would repeat exactly the mistake S1 rejected 3.0's `F37HP` for.

So the board carries **J3 = Molex Micro-Fit 3.0, 2×4, right-angle** (`C3294385`, 14 802 in stock,
footprint `Molex_Micro-Fit_3.0_43045-0800_2x04_P3.00mm_Horizontal`, dimensionally exact from the
KiCad standard library), and the **Deutsch DTM 8-way stays as the bulkhead / harness connector**,
where its sealing and locking actually earn their keep. Micro-Fit is 3 mm pitch, latching, 5 A per
contact, and in the JLC catalogue — so it is assembled rather than consigned.

**This is a one-part swap if the user wants the Deutsch on the PCB itself.** The nets, the stage
design and the pin functions do not change; it needs the TE product drawing and a derived footprint.
Logged as an open item.

### 10.1 J3 pinout

| Pin | Net | Pin | Net |
|---|---|---|---|
| 1 | `+15V_ISO` | 2 | `-15V_ISO` |
| 3 | `ISO_COM` | 4 | `ISO_COM` |
| 5 | `LEM_A_M` | 6 | `LEM_B_M` |
| 7 | `LEM_C_M` | 8 | `SHIELD_LEM` |

The LA 100-P has only three pins (+C, −C, M) and **no ground pin**: I(+15) − I(−15) = I_M. The
M current returns through our burden to `ISO_COM` on this board, so the harness `ISO_COM` wire
carries only the remote board's decoupling current and stays a quiet reference. Local decoupling at
J3: `C92/C94` 10 µF + `C93/C95` 100 nF per rail.

`SHIELD_LEM` follows S2's policy for LEM shields — **direct tie**, implemented as `R103` 0 Ω fitted,
with `C96` 1 nF ‖ `R104` 1 MΩ in parallel so removing one resistor falls back to a soft tie without
a board spin.

---

## 11. Op-amp: OPA2376AIDR

`C46316`, SOIC-8 (footprint already in the library from S4), 10 213 in stock. Four packages:
U12/U13/U14 = one per channel (internal + LEM half in the same package), U15 = reference buffer +
monitor buffer.

Gain is set entirely by resistor ratios, so op-amp precision is *not* the binding constraint —
TLV9002 or MCP6002 would work electrically. OPA2376 was chosen for three specific properties:

1. **Rail-to-rail output that actually reaches the rail.** The internal stage must swing to
   **0.060 V** at −300 A; OPA2376 swings within ~10 mV of the rail at these loads.
2. **25 µV V_os and 0.25 µV/°C.** Offsets are captured at CALIBRATE, but *drift between*
   calibrations is not — this makes that term vanish.
3. Rail-to-rail **input**, so the internal stage's 0.04 V common mode at low current is in range.

Supply is the clean FCCM +5 V from S3 (OPA2376 max 5.5 V). Verified swing envelopes: internal
0.060–2.940 V, LEM 0.736–2.201 V, LEM common mode 0.520–1.555 V — all inside the rails.

---

## 12. Failure modes

| Condition | Result | Comment |
|---|---|---|
| DB37 unplugged | internal stages read 0 V (rail) | 1 MΩ bleeds pull `ISNS_x_RAW` down; distinguishable from "zero current" |
| LEM connector unplugged | LEM stages read the bias (1.4685 V) | burden pulls `LEM_x_M` to `ISO_COM`; no rail-stuck output |
| Board +5 V dead, module alive | ≤0.25 mA into the op-amp input clamp via 20 kΩ | far under the input current limit |
| Single M contact backs out, supply still connected | that sensor's secondary is open with primary current flowing | the only genuine hazard; mitigation is the connector's own lock. Unplugging the *whole* connector is safe — it removes ±15 V at the same time |
| `LEM_x_M` at −1.76 V | normal operation | **no unipolar ESD clamp to GND may be fitted on those nets** (S11 rule 5) |
| Jumper moved without CALIBRATE | zero offset wrong by ~31 mV ≈ 6 A | the two sources have different bias points by design; documented on the sheet |

---

## 13. Firmware handoff (for S12)

- **Two current constants, one per source**, selected by JP3/JP4/JP5 — not one shared calibration.
  Internal: 4.800 mV/A at the ADC (subject to bench item #3). LEM at the default 23.5 Ω burden:
  4.886 mV/A. `LEM_V_PER_A` becomes a per-source value.
- **A third channel exists**: `ISNS_C_ADC` on **ADCINA5 (ADC-A ch5), suggested SOC1**.
  `ISENSE_NUM_CHANNELS` can go 2 → 3 and the KCL reconstruction becomes optional.
- **Offset references are now real signals**: ADCINA4 and ADCINB5 both read the buffered
  `ISNS_VREF` (≈1.4685 V) through their own buckets.
- **The software OC trip is inert whenever a LEM source is selected** (§9).
- Re-run CALIBRATE after moving any source jumper.
- Resolve the `LEM_V_PER_A` 0.0075 vs 78.6 mV/A contradiction in `hw_control_v2.h` (§3.1).

---

## 14. Capture results

| Check | Result |
|---|---|
| Components placed | **94** (R63–R104, C62–C96, U12–U15, J3, JP3–JP5, TP30–TP37, NT4) |
| Nets on the sheet | **42** |
| Netlist verification | **42/42 exact against a hand-written expected-membership table, 0 mismatches** |
| Sheet ERC | 0 violations of any real class |
| Root ERC | **70** = 66 `label_dangling` + 4 `isolated_pin_label` — down from S5's 89, and *only* the two documented cosmetic classes |
| LCSC coverage | 94/94 (82 purchasable + 12 `NOFIT` copper-only) |
| Netclass verification | all 27 signal nets → **Analog** (`SHIELD_LEM` → Default, matching `SHIELD_DB37`). Project: 125 nets, Analog 11 → **43** |
| Libraries | 49 symbols / 41 footprints, revalidated by full `kicad-cli` parse (51 SVGs — `74LVC2G17` renders 3) |

### 14.1 Library work

- **`OPA2376`** — added as a **flattened single-unit** symbol (one body, all 8 pins), matching how
  the project already carries `UCC27524D` and `74LVC1G11`.
  ⚠ **Tooling note:** the MCP `import_symbol` of KiCad's `OPA2376xxD` produced an **unloadable
  library**. That symbol is *derived* (`extends "LM2904"`) and the tool imported it without its
  parent. `kicad-cli sym export svg` caught it immediately — which is exactly why CLAUDE.md
  mandates that check after any library edit. The fix was to flatten the parent's body under the
  child's name and metadata.
- **`Conn_02x04_Odd_Even`** — appended by hand after the same tool refused it.
- **`Molex_Micro-Fit_3.0_43045-0800_2x04_P3.00mm_Horizontal`** — straight re-export of the KiCad
  standard footprint.

---

## 15. Still open

- **Bench item #3** is narrowed, not closed: the module's zero-current bias and per-channel
  sensitivity/polarity remain unmeasured. The design is deliberately insensitive to it (§3.2);
  the measurement only lets S10/S11 reclaim ADC range by changing one resistor per channel.
- **Board-mounted Deutsch** — needs the TE product drawing for `DTM13-08PA-R004` before a footprint
  can be derived honestly (§10).
- **Micro-Fit clone pad pattern** — `C3294385` is a HanChuan Micro-Fit 3.0-compatible part, not
  genuine Molex (8 units of `43045-0812` in stock). S12 must check its drawing against the
  footprint before ordering.
- **LEM board interface contract** — the remote board needs only: three LA 100-P, ±15 V/ISO_COM
  decoupling, and wiring. **It must not carry burden resistors.**
