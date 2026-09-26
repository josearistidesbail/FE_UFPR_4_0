# S5 — Module status: fault receivers, Vbus sense, NTC

Deliverable for session 5. Everything the `module_status` sheet does, with the numbers behind it.
Source of truth for the module side is `datasheets/Infineon-6PS04512E43W39693-DS-v02_00-en-1840455.pdf`
(controller-interface table **p.2**, DB37 circuit diagram + error table **p.6**, optional-components
table **p.3**). The DB37 pin map itself is frozen in [`CLAUDE.md`](CLAUDE.md) and was derived in
[`S4_GATE_DRIVE_DESIGN.md`](S4_GATE_DRIVE_DESIGN.md).

---

## 0. Summary of decisions

| # | Decision | Why |
|---|---|---|
| 1 | **Fault pull-ups go to `+13V5_GATE`, 4.7 kΩ**, then a 10 k/4.7 k divider into a Schmitt | Noise margin at the *DB37 pin* is 2.45 V / 2.91 V. A 5 V pull-up would have left 0.5 V against module-GND shift across the harness. See §1.3. |
| 2 | **Receiver = 3 × SN74LVC2G17 (dual non-inverting Schmitt)** | The hex non-inverting part (SN74LVC17A) **does not exist at JLC**. Non-inverting keeps GPIO polarity identical to the DB37 pin; `Ioff` makes a dead board-3V3 read as FAULT. See §1.4. |
| 3 | **Vbus divider 2.20 k / 1.50 k, 0.1 % thin film** → full scale **1024.6 V** — **re-picked 2026-09-26: 3.00 k / 2.20 k → 981.8 V** | `VBUS_DIVIDER_RATIO` 297.14 → **341.538** → now **327.273**. Fixes all three documented 3.0 defects. See §2. |
| 4 | **22 nF C0G charge bucket at each ADC pin**, fed through 3.3 kΩ | Kills the 512-cycle ACQPS workaround: the S/H now sees the bucket (68 ns settling) instead of a 34.5 kΩ divider. See §2.3. |
| 5 | **NTC divider 12 k / 4.7 k**, rated for 10 V continuous | DB37 pin 29 is the **10 V** NTC2 channel, and it is the module's *only* temperature output. 93.8 % range use. See §3. |
| 6 | **NTC ADC pin = ADCINC3** (BoosterPack site-1 **J3-24**), suggested **ADC-C SOC2** | Same header as Vbus (ADCINC2 = J3-27); converting after the SOC1 EOC that fires the ISR means the slow channel never delays the loop. See §3.2. |
| 7 | **No fault LEDs** | These five lines drive a hardware trip. Nothing optional gets hung on them. |

**New JLC part lines: three.** `C10429` (SN74LVC2G17DBVR), `C861295` (2.20 k 0.1 %),
`C705741` (1.50 k 0.1 %). Everything else comes from the S1/S3 kit, and **S5 introduces no new
C0G value** — it reuses the 1 nF and 22 nF lines already vetted in S1.

---

## 1. Fault receivers — 5 identical channels

### 1.1 What the module actually does

Datasheet p.2: *"Digital output level: open collector, **logic low = no fault**, max. 15 mA"*,
`Vout low 0…1.5 V`, `Vout high 15 V`. p.6 adds *"X = high level with required external pull up
resistor"*. So **FAULT = HIGH**, and the pull-up is ours to provide — it defines the high level.

This was already resolved on paper in S4. S5 only builds to it. The firmware constant
`MODULE_FAULT_ACTIVE_LOW` must go **1 → 0**, and the Input X-BAR trip polarity must be inverted
with it (OSHT1–3 on GPIO25/27/26).

### 1.2 The error table — the significant S5 finding

Page 6 carries an **Error Table** that S4 did not decode. Reading it off the column positions:

| Condition | Pin 2 (HB A) | Pin 22 (HB B) | Pin 5 (HB C) | Pin 6 (Temp) | Pin 16 (Volt) |
|---|:--:|:--:|:--:|:--:|:--:|
| Error driver core HB A | X | | | | |
| Error driver core HB B | | X | | | |
| Error driver core HB C | | | X | | |
| Overcurrent HB A | X | X | X | | |
| Overcurrent HB B | X | X | X | | |
| Overcurrent HB C | X | X | X | | |
| Overtemperature output stage | X | X | X | X | |
| Overtemperature PCB | | | | X | |
| Overvoltage DC-link (option) | X | X | X | | X |
| Undervoltage power supply | | | | | X |

The mapping is self-checking: each *"error driver core HB x"* row lights exactly one column, and
*"Overtemperature PCB"* / *"Undervoltage power supply"* light exactly the Temp / Volt column.

**Consequences:**

1. **Overcurrent is not per-phase.** An OC in *any* leg asserts all three HB error pins. The
   firmware bits `FAULT_OC_A/B/C` therefore **cannot identify which phase faulted** — a claim
   the current firmware comments imply. Phase attribution has to come from the current channels.
2. The only condition unique to one pin is *"error driver core HB x"*. So a decode is possible:

   | Observed | Meaning |
   |---|---|
   | exactly one of A/B/C | driver-core fault in that half-bridge |
   | A+B+C only | overcurrent, leg unknown |
   | A+B+C + Temp | overtemperature output stage |
   | A+B+C + Volt | DC-link overvoltage |
   | Temp only | overtemperature PCB |
   | Volt only | supply undervoltage |

3. This is why **all five lines get identical receivers**, not just the three that feed the X-BAR:
   the decode needs Temp and Volt sampled with the same fidelity and timing as A/B/C.
4. Datasheet note: *"Over temperature shut down must be realized by customer."* The module
   **reports** over-temperature but does not shut itself down for it. The OT trip is our
   responsibility, built from `FLT_OT` (pin 6) plus the NTC channel of §3. That promotes the NTC
   channel from a convenience to a **safety function**.

The p.3 optional-components table also confirms the module's fitted options: **voltage sensor,
current sensor and temperature sensor, all in the "Inverter Section" column only.** Unit 1 and
Unit 3 are empty — which independently confirms S4's conclusion that there is exactly one
temperature output and it is the 10 V inverter-section one.

### 1.3 Level design and why the pull-up is 13.5 V

Per channel: `DB37 — R_pu 4.7 k to +13V5_GATE — C 1 nF to GND — R_a 10 k — node _DIV —
R_b 4.7 k ∥ C 1 nF to GND — Schmitt`.

| Quantity | Value |
|---|---|
| DB37 pin, no fault (module sinks) | **0.15 V**, sink current **2.84 mA** (limit 15 mA) |
| DB37 pin, fault | **10.23 V** |
| Schmitt input when faulted | **3.271 V** nominal, **3.157 V** worst case (rail −2 %, R ±1 %) |
| SN74LVC2G17 thresholds at V_CC 3.3 V ±5 % | V_T+ ≤ **2.34 V**, V_T− ≥ **0.83 V** (interpolated from the 3.0 V / 4.5 V rows) |
| Margin at the Schmitt | **0.82 V** over V_T+ worst case |
| Trip window *referred to the DB37 pin* | **2.60 V … 7.32 V** |
| Noise margin from the LOW state | **2.45 V** |
| Noise margin from the HIGH state | **2.91 V** |
| Load on `+13V5_GATE` | 5 × 2.84 mA = **14.2 mA**; P(R_pu) = 38 mW, 0603 at 38 % |

**Why not a 5 V pull-up.** A 5 V pull-up would need no divider at all (LVC inputs are rated to
5.5 V), which is tempting — five fewer resistors and a lower-impedance node. It was rejected on
one number: the low-side margin would be only **0.5 V** (V_T+ max 2.34 V against a 0.15 V low).
That budget has to absorb *module-GND shift across the harness*, not just board noise — the
module's open-collector emitter sits on its own digital ground, several metres of harness away,
next to 2.2 A of aux return and an inverter's common-mode currents. Spending 13.5 V of swing to
buy 2.45 V of margin is the right trade here, and the extra divider is two resistor values that
were already in the kit.

The direction that matters is asymmetric and both are covered: a false *fault* is a nuisance
shutdown, while a *missed* fault would need 7.6 V of noise to pull the line down through a 4.7 kΩ
pull-up — which cannot happen.

### 1.4 Receiver part

| | |
|---|---|
| Part | **SN74LVC2G17DBVR**, LCSC **C10429**, SOT-23-6, Extended, 107 122 in stock |
| Pinout | 1 = 1A, 2 = GND, 3 = 2A, 4 = 2Y, 5 = V_CC, 6 = 1Y — verified against TI SCES381N, matches KiCad's `74xGxx:74LVC2G17` exactly |
| Allocation | U9 = OC_A / OC_B, U10 = OC_C / OT, U11 = OV / spare (input tied to GND, output no-connect) |

**Why not a hex.** The obvious choice was one hex non-inverting Schmitt (SN74LVC17A) for six
channels in one package. **JLC does not carry it at all** — zero results. The hex *inverting*
part (SN74LVC14A / 74HC14D, the latter Basic with 323 k stock) is available, and using it would
even preserve `MODULE_FAULT_ACTIVE_LOW = 1`. It was rejected because hidden inversion between the
connector and the GPIO is exactly the sort of thing that costs a day on the bench, and because
74HC has no `Ioff`:

**`Ioff` is load-bearing.** The board's +3V3 comes from the AMS1117 off +5V, while the LaunchPad
regenerates its *own* 3.3 V from the same +5V feed. So "board 3V3 dead, MCU alive" is a reachable
state. With `Ioff`, the LVC outputs go high-Z, the F28379D's reset-default GPIO pull-ups take over,
and every fault line reads **HIGH = FAULT**. A part without `Ioff` could sit low and report
*no fault* while its own supply is dead. (Note the cascade 24 → 13.5 → 5 → 3.3 also means
`+3V3` can never be up without `+13V5_GATE`, so the pull-ups can't be missing while the
receivers are alive.)

### 1.5 Timing

Both 1 nF caps see a Thevenin of 3.56 kΩ, so the chain is two ≈3.56 µs poles. Numerically
integrating the actual network from the no-fault state:

| | to V_T+ typ (1.6 V) | to V_T+ max (2.34 V) |
|---|---|---|
| Fault assertion → Schmitt input crosses | **5.7 µs** | **8.9 µs** |

That is fine, and deliberately so: the module protects itself against overcurrent **within 15 µs**
(625 A_peak) and the PWM period is 100 µs. This path is *reporting plus X-BAR backstop*, not
primary protection, so filtering is worth more than microseconds. The falling edge (fault clears)
is driven by the module's saturated transistor and is much faster.

### 1.6 Fail-safe

An unplugged or broken DB37 lets every fault line float to `+13V5_GATE` through its pull-up ⇒
**all five read FAULT**. No firmware action required, and it holds for a cut wire, a bad crimp,
or a disconnected harness. This satisfies the roadmap's explicit fail-safe requirement.

---

## 2. Vbus front-end

### 2.1 The three defects being fixed

From the firmware logbook, the 3.0 Vbus channel had three separate problems. All three are
addressed here, and none of them needed an op-amp — the datasheet's `load max 5 mA` rating (S4)
is what makes a plain resistive divider legitimate.

| # | 3.0 defect | v4.0 fix |
|---|---|---|
| 1 | 34.5 kΩ source impedance forced a 512-cycle S/H | 1269 Ω Thevenin (892 Ω before 2026-09-26) **plus a 22 nF bucket at the ADC pin** — the S/H sees the bucket, 68 ns settling |
| 2 | sensor return shared the power path; **−52 mV load-dependent offset** measured | dedicated Kelvin return on **DB37 pin 11**, joined to GND at **NT3 and nowhere else** |
| 3 | scale wrong / not recomputed | `VBUS_DIVIDER_RATIO` 297.14 → **327.273**, full scale 981.8 V (341.538 / 1024.6 V before 2026-09-26) |

### 2.2 Divider

Module sensor: **6.4 / 6.5 / 6.6 V at 900 V**, load max 5 mA ⇒ 7.222 mV/V typical.

> **Re-picked 2026-09-26 (JLC feeder-fee cut, `DECISION_LOG.md`): R57 = 3.00 k (`C136963`, the R105 line),
> R58 = 2.20 k (`C861295`, the R129 line).** Both values were already on the BOM, same RT0603B family, so the
> ratio-tracking argument below still holds and the 1.50 k line (`C705741`) is gone. Full scale drops to
> 981.8 V (967 V at the 6.6 V/900 V sensor extreme) — ample for the ≤ 600 V FSAE bus. The tables below are
> the current values; the 2.20 k / 1.50 k figures are kept in brackets.

| | |
|---|---|
| R57 | **3.00 kΩ 0.1 %**, Yageo RT0603BRD073KL, LCSC **C136963** [was 2.20 k `C861295`] |
| R58 | **2.20 kΩ 0.1 %**, Yageo RT0603BRD072K2L, LCSC **C861295** [was 1.50 k `C705741`] |
| Gain | 2200 / 5200 = **0.423077** [0.405405] |
| Thevenin | **1269 Ω** [892 Ω] |
| Module load at 1000 V | **1.39 mA** = 28 % of the 5 mA limit [1.95 mA] |
| Full scale (3.000 V at the ADC) | **981.8 V** [1024.6 V] |

Both resistors are the **same Yageo RT0603B family** (thin film, 25 ppm/°C). That matters more
than the absolute tolerance: the divider is ratiometric, so same-family parts track each other
over temperature, whereas a 100 ppm/°C thick-film pair could drift ~0.6 % differentially over a
60 °C swing — 6 V of bus error, which would matter to a UV/OV trip.

> The first pair considered was 2.32 k / 1.65 k (a closer ratio, full scale 999.4 V), but the
> 1.65 k 0.1 % line had only **673** in stock. The chosen pair has **50× the stock** for a
> full-scale difference nobody can measure, following the S3 lesson about picking values against
> live stock rather than E96 tables.

Transfer:

| Bus | Sensor | ADC | Code |
|---|---|---|---|
| 100 V | 0.722 V | 0.306 V | 417 |
| 400 V | 2.889 V | 1.222 V | 1669 |
| 600 V | 4.333 V | 1.833 V | 2503 |
| 800 V | 5.778 V | 2.444 V | 3337 |
| 900 V | 6.500 V | 2.750 V | 3755 |
| 981.8 V | 7.091 V | 3.000 V | 4096 (saturates above) |

### 2.3 Anti-alias and the charge bucket

`VBUS_DIV — R59 3.3 kΩ — VBUS_ADC — C59 22 nF C0G to GND`, with C59 sitting **at the BoosterPack
ADC pin**.

| | |
|---|---|
| Corner | **1583 Hz** (R_th + R_s = 4569 Ω) [1726 Hz, 4192 Ω] |
| τ | 100.5 µs ≈ 1 τ per 100 µs sample period [92.2 µs] |
| S/H charge sharing | C_h/(C_h+C_b) = 0.068 % = **2.8 codes** worst case, deterministic |
| DC error from average S/H current | 2.1 mV = **2.8 codes** [1.9 mV, 2.6 codes] |
| Settling seen by the S/H | (R_on 500 Ω)(C_h 15 pF)·ln(2·4096) = **68 ns** |

**The 512-cycle ACQPS workaround can be retired.** ~320 ns of acquisition is already generous.

If the module's sensor output ever rails to 15 V, the divider node reaches 6.35 V open-circuit and the ADC
clamp takes **0.64 mA** through R59 — inside the F28379D's ±2 mA per-pin clamp limit. R57
dissipates ≈30 mW in that condition (0603, 30 %). [2.20 k/1.50 k: 6.08 V, 0.63 mA, 36 mW]

### 2.4 Kelvin return

`VBUS_RTN` (DB37 pin 11) is a distinct net that meets `GND` at exactly one place: **NT3**, a
`NetTie_2` next to R58. R58's bottom and the connector-side EMC cap C58 both return to
`VBUS_RTN`; the ADC bucket C59 returns to `GND` at the ADC pin, where the S/H current belongs.

Keeping `VBUS_RTN` a separate net until NT3 is what makes S2's "dedicated copper, never shared
with power return" rule enforceable by DRC instead of being a layout wish — the same mechanism
S4 used for `PGND_MOD`.

---

## 3. NTC / temperature

### 3.1 Divider

DB37 pin 29 is the module's **only** temperature output, and it is the inverter-section NTC2
channel: **10 V at T_NTC = 82 °C**, load max 5 mA. The divider must therefore hold off 10 V
continuously — which is exactly the trap 3.0 fell into by reading pin 9 instead (a 15 V supply
output, not a sensor).

| | |
|---|---|
| R60 / R61 | **12 kΩ / 4.7 kΩ**, both JLC Basic, both already in the S1 kit |
| Gain | **0.281437** |
| 10.000 V in | **2.814 V** = 93.8 % of the 3.0 V range |
| Clips at | **10.66 V** of module output |
| Module load | **0.60 mA** |
| R62 / C61 | 3.3 kΩ + 22 nF C0G ⇒ corner **1083 Hz** — the roadmap's "slow channels can take ~1 kHz" target |
| ADC clamp if the output rails to 15 V | 0.10 mA |

`NTC_VOLTS_PER_CODE = 3.0 / 0.281437 / 4096 = 0.002602 V(module)/code`.

The 93.8 % figure is deliberate: it leaves a little headroom above the 82 °C point rather than
clipping exactly at it, since the module reports OT but does not act on it (§1.2).

**Reference.** The NTC divider returns to board `GND`, not to `VBUS_RTN`. The module's analog
grounds (pins 11/12/13) are already committed as Kelvin returns for Vbus and the current sensors,
and adding a third consumer to the Vbus Kelvin line would put 0.6 mA of NTC current into it. The
cost of referencing to board GND is that a module-GND shift of V_m appears as 0.281·V_m at the
ADC — about 1 % of full scale for 100 mV of shift, i.e. a fraction of a degree. That is the right
trade for a channel whose job is a thermal trip, not precision thermometry.

### 3.2 ADC channel choice

`ADCIND0–D5` are **not** on the BoosterPack headers on the LAUNCHXL-F28379D — they go to the
board's own J21 header via the on-board differential amplifiers (SPRUI77 Figure 5). So the NTC
must land on ADC-A/B/C. From SPRUI77 Tables 1–4 the BoosterPack analog pins are:

| Site 1 (J3) | 23 | 24 | 25 | 26 | 27 | 28 | 29 | 30 |
|---|---|---|---|---|---|---|---|---|
| | ADCIN14 | **ADCINC3** | ADCINB3 | ADCINA3 | ADCINC2 *(Vbus)* | ADCINB2 *(COS)* | ADCINA2 *(SIN)* | ADCINA0 |

| Site 2 (J7) | 63 | 64 | 65 | 66 | 67 | 68 | 69 | 70 |
|---|---|---|---|---|---|---|---|---|
| | ADCIN15 | ADCINC5 | ADCINB5 *(ref)* | ADCINA5 | ADCINC4 *(Iv)* | ADCINB4 *(Iu)* | ADCINA4 *(ref)* | ADCINA1 |

**Chosen: `ADCINC3` — site 1, J3-24.**

- It is on **ADC-C**, the same converter as Vbus, and physically in the same header three pins
  away — both `module_status` signals land in one place, which is what the analog partition wants.
- Suggested SOC allocation is **ADC-C SOC2**. The 10 kHz ISR is fired by the **ADC-C SOC1 (Vbus)**
  end-of-conversion, so a SOC2 added after it converts *outside* the critical path: the NTC result
  is simply read one cycle late, which is meaningless for a thermal signal.
- It leaves ADC-A completely free apart from SIN, so **S6 can put the third current channel on
  ADC-A SOC1** and keep the three converters balanced (A: SIN+Iw, B: Iu+COS, C: Iv+Vbus+NTC).
  ADCINA3 (J3-26) and ADCINA5 (J7-66) are both still free for it.

---

## 4. What was captured

`module_status.kicad_sch` — **54 components, 22 signal nets, 3 rails.**

| Group | Refs |
|---|---|
| Fault pull-ups 4.7 k | R42–R46 |
| Fault series 10 k | R47–R51 |
| Fault bottom 4.7 k | R52–R56 |
| Fault caps 1 nF C0G (connector side / Schmitt side) | C44–C48 / C49–C53 |
| Schmitt receivers | U9, U10, U11 |
| Decoupling 100 nF / bulk 1 µF | C54–C56 / C57 |
| Vbus | R57 3.00 k 0.1 %, R58 2.20 k 0.1 % (2026-09-26), R59 3.3 k, C58 1 nF, C59 22 nF, **NT3** |
| NTC | R60 12 k, R61 4.7 k, R62 3.3 k, C60 1 nF, C61 22 nF |
| Test points | TP19–TP29 |

**Verification.** The root netlist was checked against a hand-written expected-membership table:
**22/22 nets match exactly, 0 mismatches**, and every `*_15V` / `VBUS_*` / `NTC_*` net lands on
the DB37 pin the frozen table says it should (J2.2, J2.22, J2.5, J2.6, J2.16, J2.7, J2.11, J2.29).
All three rails resolve to a single net each. Every component carries an `LCSC` field.

**ERC (root):** 89 violations = 76 `label_dangling` + 13 `isolated_pin_label`, down from S4's
90 + 37 = **127**. Zero errors of any other class. `module_status` contributes 15 of the dangling
labels — its own edge hierarchical labels, which have no wire attached because the project's
capture convention is net-labels-at-pins. That is the same cosmetic item already logged for
`power` and `gate_drive`, not an electrical defect; the netlist proves the nets are connected.

---

## 5. Netclass patterns were silently broken (found in S5, fixed)

Checking what class the new nets landed in exposed a **latent project-wide defect**: KiCad matches
netclass patterns against the **full, path-qualified net name** (`/gate_drive/PWM_UH_15V`), not the
base name. Every pattern that was anchored at the start therefore never matched anything.

**24 nets were silently sitting on `Default`**, including:

- the **entire gate bus** — all six `PWM_*_15V` and all six `PWM_*_DRV`, which S4 explicitly
  designed for the `Gate` class (0.40 mm track, 0.8/0.4 mm vias)
- **both Kelvin sense pairs** — `VBUS_SNS_RAW`, `VBUS_RTN`, `ISNS_*_RAW`, `ISNS_RTN`
- `NTC_1_RAW`, `DRV_EN*`, `GATE_EN_3V3`, `GATE_ILOCK_3V3`, both buck switch nodes

Only the **global power nets** (`GND`, `+3V3`, `+13V5_GATE`, `+24V_*`, `PGND_MOD`, `ISO_COM`, the
isolated rails) worked, because their net names carry no sheet path — and `*_ADC`, because it
already began with a wildcard. That is why the breakage went unnoticed for four sessions: the
patterns that were *checked* by eye were the ones that happened to work.

**Fix:** the ten path-sensitive patterns were prefixed with `*` (`PWM_*_15V` → `*PWM_*_15V`, etc.).
No netclass *values* were touched — S9 still owns those. Result: 28 nets moved to their intended
class, **none lost a class, and the netlist is byte-identical**. Distribution is now
51 Default / 17 Gate / 11 Analog / 8 Power_1A / 5 Power_3A.

One side effect worth knowing: `LED_GATE_EN` (the gate-enable indicator LED net on `gate_drive`)
matches `*GATE_EN*` and is now `Gate` class. Harmless — it just gets wider copper than it needs.

---

## 6. Firmware handoff (for S12 / `hw_control_v2.h`)

| Constant | Now | Change to | Note |
|---|---|---|---|
| `MODULE_FAULT_ACTIVE_LOW` | `1` | **`0`** | fault = HIGH; the receiver chain is non-inverting |
| Input X-BAR trip polarity | active-low | **invert** | OSHT1–3 on GPIO25/27/26 must follow the flag |
| `VBUS_DIVIDER_RATIO` | `297.14f` | **`327.273f`** (341.538 before 2026-09-26) | V(bus) per V(ADC) |
| `VBUS_VOLTS_PER_CODE` | derived | **0.239702 V/code** | full scale 981.8 V |
| `VBUS_OFFSET_CODE` | `11.4f` | **re-measure** | the old value was an artefact of the old divider |
| NTC channel | none | **ADCINC3**, ADC-C ch3, J3-24 | suggest ADC-C **SOC2** |
| `NTC_VOLTS_PER_CODE` | — | **0.002602 V(module)/code** | 10 V = 82 °C; clips at 10.66 V |
| Vbus `ACQPS` | 512 cycles | **~320 ns is ample** | bucket at the pin; 68 ns settling |

Also for the firmware, from §1.2: **`FAULT_OC_A/B/C` do not identify the faulting phase.** Any
leg's overcurrent asserts all three. The decode table in §1.2 is what the fault-status reporting
should implement.

**Bench trim.** The module's own sensor tolerance is 6.4 / 6.5 / 6.6 V at 900 V = **±1.5 %**,
which dominates the 0.1 % divider. `VBUS_DIVIDER_RATIO` should be trimmed against a meter during
bring-up; the divider's job is to be *stable*, not to be absolutely right on its own.

---

## 7. S10 layout requirements

1. **R42–R46 and C44–C48 sit at the DB37**, not at the Schmitts — they terminate the harness where
   it enters. R_a/R_b/C_a and U9–U11 group together at the far end.
2. **C58** at DB37 pins 7/11 and **C60** at pin 29, each returned to its own reference.
3. `VBUS_SNS_RAW` + `VBUS_RTN` route as a **pair** into the analog partition. **NT3 is the only
   GND tie** for `VBUS_RTN` — within a few mm of R58, with no other current sharing that copper.
   This is the fix for the measured −52 mV offset; getting it wrong reintroduces the bug.
4. **C59 / C61 hard against the BoosterPack ADC pins J3-27 / J3-24**, ground vias straight into the
   analog partition. They are the S/H charge source; distance here undoes §2.3.
5. C54–C56 within 2 mm of each 74LVC2G17 V_CC/GND pair; C57 is the local 3V3 bulk.
6. The five `FLT_*_15V` traces carry 13.5 V edges — keep them off the analog partition.

---

## 8. Open items leaving S5

- **[bench]** Item #5, the NTC output at room temperature, is still unmeasured. It no longer
  *blocks* anything: the divider is rated for the full 0–10 V range the datasheet specifies, so
  the measurement only calibrates the curve. Needed before the OT trip threshold can be set.
- **[bench]** Confirm fault polarity and the receiver thresholds on the real harness. Resolved on
  paper (§1.1); the bench now only confirms.
- **[S6]** Third current channel: **ADC-A SOC1** is free and keeps the converters balanced;
  ADCINA3 (J3-26) and ADCINA5 (J7-66) are the candidate pins.
- **[S9]** Netclass *values* still to be re-derived against JLCPCB 4-layer capability. The
  *patterns* are now correct (§5).
- **[cosmetic, project-wide]** Hierarchical labels on every sheet have no wire stub, which is what
  produces the 76 `label_dangling` ERC entries. A single consistent wire-stub pass across
  `power` / `gate_drive` / `module_status` would clear them; doing it per-sheet would leave the
  project inconsistent.
- **[cosmetic]** The A3 title-block **Title** field overflows its box on every sheet — the S1
  sheet titles are longer than the block. Pre-existing, affects all seven sheets.
