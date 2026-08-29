# S4 — Gate drive, level shifting, enables (deliverable)

Frozen 2026-08-29 (S4). Scope: the `gate_drive` sheet — 3.3 V → gate-rail single-stage drive for
six PWM lines, hardware enable gating, the DB37 to the PrimeSTACK, and the shield/return policy at
that connector.

> **The session's single most important input arrived mid-session:** the user placed
> `datasheets/Infineon-6PS04512E43W39693-DS-v02_00-en-1840455.pdf` in the project. Page 6 carries
> the **authoritative DB37 pinout and circuit diagram**; page 2 carries the **controller-interface
> electrical table**. Everything below is derived from that document rather than from the 3.0
> as-built board, and it overturned five inherited assumptions — see §3.

Companion docs: [`CLAUDE.md`](CLAUDE.md) (decision log), [`ARCHITECTURE.md`](ARCHITECTURE.md) (S2
contract, amended by this session), [`S3_POWER_DESIGN.md`](S3_POWER_DESIGN.md) (the 13.500 V rail
this sheet consumes).

---

## 1. What replaces what

3.0 drove the module through **three** stages: 6 × SN74LVC1G126 tri-state buffers (5 V) → a CD4504B
level shifter (5 V → 12 V) → a SOT-23-5 AND gate whose **VCC came from GPIO131**. The AND gate ANDed
`DRV_EN` (GPIO66) with a cockpit `MAIN_SWITCH` and drove the six buffers' `OE` pins.

Three things were wrong with that:

1. **A GPIO was used as a power rail.** GPIO131 sourced the whole AND gate's supply current. The
   "aux enable" in `hw_control_v2.h` is therefore not a logic enable at all on Control_V2 — it is a
   supply switch. That is why bench item #2 ("enable active levels") was ever open.
2. **Three stages of propagation delay and three sets of tolerances** sat inside a 1500 ns deadband.
3. **CD4504B is slow and weak** (tens of mA, hundreds of ns at 12 V) driving a harness.

v4.0 is **one stage**: `3 × UCC27524` (dual 5 A low-side driver). Its inputs are TTL-threshold and
— the property that makes the single stage possible — **the input and enable thresholds are fixed
and independent of VDD**, and those pins are rated −5 V … +20 V *regardless of VDD* (datasheet
SLUSFA9 §6.1 note 3). So a 3.3 V CMOS signal switches an output stage running from 13.5 V, directly.

Both enables become real logic inputs on a properly-powered 3-input AND gate.

---

## 2. Topology selection — availability first

`REDESIGN_PLAN.md` §S4 says *"vet availability FIRST, design second"*, with 2 × TC4468 as the
leading candidate. That check failed:

| Candidate | LCSC | JLC stock (2026-08-29) | Verdict |
|---|---|---|---|
| TC4468COE713 (quad AND-input driver) | C632547 | **14** | ✗ unbuildable |
| TC4468COE | C642031 | **4** | ✗ |
| TC4469COE | C642033 | 18 | ✗ |
| MIC4468ZWM | C641628 | **25** | ✗ |
| UCC27523D (dual, enable) | C206023 | 79 | ✗ |
| **UCC27524DR (dual, enable)** | **C465729** | **9 550** | ✓ **chosen** |
| UCC27524DSDR (WSON) | C2676911 | 17 104 | ✓ alternate package |

The roadmap's whole TC446x family is effectively out of stock at JLC. UCC27524 gives the same
functional block — non-inverting channel with a **per-channel enable** — in a dual instead of a
quad, so three packages instead of two. That is the only cost.

**Why UCC27524 and not a level-shifter + buffer:**

- VDD 4.5–18 V (abs max 20 V) covers the 13.500 V rail with margin, and the rail's own TVS/clamp
  chain (S3) never presents more than that to this pin.
- Input thresholds 1.8 V min high / 1.2 V max low, **independent of VDD**, with 1 V hysteresis.
- **Inputs have internal 120 kΩ pull-downs** — "outputs held low when inputs floating".
- **Enable pins have internal 200 kΩ pull-ups** to VDD and are active-high.
- Outputs **held LOW during VDD UVLO** (rising 4.1 V, falling 3.8 V typ).
- 17 ns typ / 27 ns max propagation delay; **1 ns typ / 2 ns max delay matching between the two
  channels of one package** — and the two channels of one package are the high and low side of the
  *same* half-bridge, which is exactly where matching matters.

The 5 A output capability is far more than a logic input needs; it is not the reason for the
choice, and §5 shows the series resistor keeps peak current to 127 mA.

**Enable combiner: SN74LVC1G11** (single 3-input AND, SOT-23-6), C22046, 10 443 in stock.
Pinout verified against TI SCES487I: **1 = A, 2 = GND, 3 = B, 4 = Y, 5 = VCC, 6 = C** — KiCad's
symbol matches. tpd 4.1 ns max at 3.3 V, ±24 mA drive, and `Ioff` partial-power-down so its output
does not back-feed when +3V3 is down.

---

## 3. What the datasheet overturned

| # | Inherited belief | Source of the belief | Datasheet says | Consequence |
|---|---|---|---|---|
| 1 | Fault asserted = **LOW** | `hw_control_v2.h`: `MODULE_FAULT_ACTIVE_LOW 1`; `infineon.md` "LOW (Fault Active)" | p.2: *"Digital output level: open collector, **logic low = no fault**, max 15 mA"*; p.6 error table: *"X = high level with required external pull-up"* | **Fault = HIGH.** Firmware is inverted. Blocks S5 no longer — bench item #1 is answered on paper. |
| 2 | Module analog outputs may not be able to drive a divider | never measured; S5 planned a buffer op-amp | p.2: every analog output rated **"load max 5 mA"** | S5 may use a plain resistive divider on Vbus. Bench item #4 answered on paper. |
| 3 | Two NTC channels exist, pin 29 and pin 9 | `ARCHITECTURE.md` §8, from 3.0's net names | p.6: **one** "Temperature" pin (29). p.2 lists NTC1 4.9 V and NTC2 10 V but only the inverter-section sensor is fitted | `NTC_2_RAW`/`NTC_2_ADC` retired. Pin 29's divider must be rated for **10 V**. |
| 4 | Pin 9 = "PTC+" sensor input; pin 27 = GND | 3.0 as-built | p.6: pins 9 and 27 are **15 V / 50 mA supply OUTPUTS** (labelled PTC) | **3.0 shorted a 15 V supply output (pin 27) to ground.** v4.0 brings both to test points. |
| 5 | Pin 1 = GND | 3.0 as-built | p.6: pin 1 = **"True earth / shield"** | Pin 1 joins the shell net `SHIELD_DB37` under the S2 soft-tie policy, not GND. |

Two further confirmations that were *assumptions* until now:

- **Gate pin assignment including TOP/BOT within a leg** — p.6 names them explicitly
  ("20 HB A IGBT BOT", "21 HB A IGBT TOP", …). 3.0's mapping was right; it is now sourced.
- **The module has no enable input pin.** The digital-input group on p.6 is exactly the six gate
  lines plus NC. So the two firmware enables are necessarily *board-local*, we define their active
  level, and **bench item #2 no longer blocks S4** — it was only ever open because 3.0 wired
  GPIO131 to a supply pin.

Cross-validation: the datasheet's NC set (14, 15, 17, 18, 33, 34, 35, 36) is **exactly** the set of
pins 3.0 left dangling. Independent agreement on 8 pins.

### 3.1 How much of this was actually broken in 3.0? — not much, and nothing that ran

Rows 1–3 above are corrections to *documents* (the firmware header, `infineon.md`, and our own
`ARCHITECTURE.md`), not to 3.0's board. Only rows 4 and 5 touch 3.0's wiring, and **34 of the 37
pins were right**: all six gates including TOP/BOT within each leg, all five fault lines, the three
phase currents, Vbus, temperature, the 24 V feed and return, every ground, and the eight NC pins.
v4.0 carries all of those over unchanged. **The interface working on the bench is exactly what this
table predicts.**

| Pin | 3.0 | Reality | Real-world consequence |
|---|---|---|---|
| 27 | GND | 15 V/50 mA supply output | The only true mistake. A supply output shorted to ground — but nothing in the signal chain depends on that rail, so it is **symptomless**; ≤0.75 W dissipated inside the module. |
| 9 | divider → header as "PTC" | same output | A dead circuit reading a constant. Firmware never sampled it (`NTC channels: none today`). Harmless. |
| 1 | GND | true earth/shield (bonded to module chassis) | **Not an error** — a hard chassis-to-signal-ground bond is a defensible choice. It conflicts only with the *soft-tie* policy S2 adopted for v4.0, which is a new rule, not a 3.0 defect. |

The phantom NTC#2 (row 3) was **our** error, introduced in S2's `ARCHITECTURE.md` §8 by inferring a
second channel from `infineon.md`'s spec table. It never existed in 3.0's netlist either.

---

## 4. DB37 pin table — v4.0, authoritative

Module-side connector is **SUB-D 37 male with UNC 4-40 female threads**; the board carries the
socket (`DSUB-37_Socket_Horizontal_P2.77x2.54mm_MountingHoles`, geometry validated in S1).

| Pin | Datasheet function | v4.0 net | Group |
|---|---|---|---|
| 1 | True earth / shield | `SHIELD_DB37` | shield |
| 2 | HB A error | `FLT_OC_A_15V` | → `module_status` |
| 3 | HB B IGBT BOT | `PWM_VL_15V` | ← driver |
| 4 | HB B IGBT TOP | `PWM_VH_15V` | ← driver |
| 5 | HB C error | `FLT_OC_C_15V` | → `module_status` |
| 6 | Temp. error | `FLT_OT_15V` | → `module_status` |
| 7 | Voltage DC-link | `VBUS_SNS_RAW` | → `module_status` |
| 8 | 13–30 V supply in | `+24V_MOD` | ← `power` (F2, 3 A) |
| 9 | 15 V / 50 mA out (PTC) | `MOD_AUX15V_1` | TP17 |
| 10 | GND (supply return) | `PGND_MOD` | → star, `power`/NT2 |
| 11 | GND analog | `VBUS_RTN` | Kelvin → `module_status` |
| 12 | GND analog | `ISNS_RTN` | → `current_sense` |
| 13 | GND analog | `ISNS_RTN` | → `current_sense` |
| 14 | NC | no-connect | |
| 15 | NC | no-connect | |
| 16 | Voltage error | `FLT_OV_15V` | → `module_status` |
| 17 | NC | no-connect | |
| 18 | NC | no-connect | |
| 19 | GND digital | `GND` | |
| 20 | HB A IGBT BOT | `PWM_UL_15V` | ← driver |
| 21 | HB A IGBT TOP | `PWM_UH_15V` | ← driver |
| 22 | HB B error | `FLT_OC_B_15V` | → `module_status` |
| 23 | HB C IGBT BOT | `PWM_WL_15V` | ← driver |
| 24 | HB C IGBT TOP | `PWM_WH_15V` | ← driver |
| 25 | GND digital | `GND` | |
| 26 | 13–30 V supply in | `+24V_MOD` | ← `power` |
| 27 | 15 V / 50 mA out (PTC) | `MOD_AUX15V_2` | TP18 |
| 28 | GND (supply return) | `PGND_MOD` | → star |
| 29 | Temperature (NTC) | `NTC_1_RAW` | → `module_status`, **rate for 10 V** |
| 30 | HB A current | `ISNS_A_RAW` | → `current_sense` |
| 31 | HB B current | `ISNS_B_RAW` | → `current_sense` |
| 32 | HB C current | `ISNS_C_RAW` | → `current_sense` |
| 33–36 | NC | no-connect | |
| 37 | GND digital | `GND` | |
| G1, G2 | shell | `SHIELD_DB37` | shield |

**Half-bridge ↔ phase mapping:** module HB-A/B/C ← firmware U/V/W. Which motor phase that actually
is depends on the motor cable, and the firmware's ALIGN phase-ID stage re-derives `isense_map`
anyway, so only self-consistency matters here — and the table is self-consistent.

**Three return groups, deliberately kept separate to the board:**

- `GND` (pins 19/25/37) — logic reference for the gate and fault lines, joins the plane at the
  driver/fault region.
- `PGND_MOD` (pins 10/28) — the module aux return, up to 2.2 A. A **distinct net** all the way to
  `NT2` on the `power` sheet, which is the single 24 V-entry star tie. This is what makes the
  "dedicated copper, never through the plane under analog" rule of `ARCHITECTURE.md` §4.2
  enforceable by DRC instead of being a layout wish. 3.0's failure mode was `GND`↔`P_GND` tied at
  *two* separate net-ties; there is now exactly one.
- `VBUS_RTN` (pin 11) and `ISNS_RTN` (pins 12/13) — Kelvin returns, exported to their front-end
  sheets and joined to GND only there (S5/S6). Pin 11 alone for Vbus so the −52 mV load-dependent
  IR-drop offset measured on 3.0 cannot re-form; 12 and 13 paralleled for the three current
  channels.

**Shield:** pin 1 + G1 + G2 on `SHIELD_DB37`, tied to GND through **C43 1 nF C0G ∥ R35 1 MΩ**, with
**JP2** (2-pad solder jumper) to make it a hard tie. Default = soft, per `ARCHITECTURE.md` §5.

---

## 5. DC levels at the module input

Datasheet p.2, "Digital input level", test conditions: **"resistor to GND 10 kΩ, capacitor to GND
1 nF, logic high = on"**, giving `Vin low 0–1.5 V` and `Vin high 11–15 V`.

That network is fitted on our side of the connector — **R24–R29 = 10 kΩ, C37–C42 = 1 nF C0G**, at
the DB37 pins. If the module also contains it internally the two parallel, which is the worst case
and is what the numbers below assume (R = 5 kΩ, C = 2 nF).

Series damping **R18–R23 = 100 Ω**, at the driver outputs.

```
  UCC27524 OUT ──[ R 100Ω ]──┬── DB37 pin ── harness ── module input
     ROH 5Ω / ROL 0.6Ω       ├── R 10 kΩ ── GND
                             └── C 1 nF C0G ── GND
```

| Quantity | Value | Source |
|---|---|---|
| Rail `+13V5_GATE` | 13.500 V nominal, ±2 % → **13.23 … 13.77 V** | S3 (150 k/12 k, V_ref = 1.000 V) |
| Driver pull-up resistance ROH | 5 Ω typ, **8.5 Ω max** | SLUSFA9 §6.5 |
| Driver pull-down resistance ROL | 0.6 Ω typ, 1.1 Ω max | SLUSFA9 §6.5 |
| Total series | 100 Ω + 8.5 Ω = 108.5 Ω worst case | |
| Load to GND | 5 kΩ (both networks) … 10 kΩ (module's only) | |
| **V(module) HIGH, worst-case min** | 13.23 × 5000/5108.5 = **12.95 V** | vs 11 V required → **+1.95 V margin** |
| **V(module) HIGH, worst-case max** | 13.77 × 10000/10108.5 = **13.62 V** | vs 15 V limit → **+1.38 V margin** |
| **V(module) LOW** | ≈ 0 V (ROL 1.1 Ω against 5 kΩ) | vs 1.5 V limit → passes trivially |
| Current per line at HIGH | 13.0 / 5 kΩ = **2.6 mA** | |

This validates the S3 decision to set the gate rail at **13.500 V rather than 12.0 V**: at 12.0 V
±2 % the worst-case module level would be 11.52 V, only 0.52 V above the 11 V floor before any
harness drop. At 13.5 V there is 1.95 V.

**Current drawn from `+13V5_GATE` by this sheet**

| Item | Current |
|---|---|
| 6 gate lines × 2.6 mA × 50 % duty | 7.8 mA |
| 3 × UCC27524 static (0.7 mA typ, 1.0 mA max) | 2.1 mA (3.0 mA max) |
| Switching: C·V²·f = 2.1 nF × 13.4² × 10 kHz = 3.8 mW | 0.3 mA |
| **Total** | **≈ 10 mA (12 mA max)** |

Well under the `ARCHITECTURE.md` §2 allowance. Resistor dissipation: charging 2.1 nF twice per
10 kHz cycle is 3.8 mW shared across ROH/ROL and the 100 Ω, i.e. ≈3.5 mW in each 0603 — 3.5 % of
its 100 mW rating.

---

## 6. Timing: skew against the 1500 ns deadband

`PWM_DEADBAND_NS = 1500` (`hw_control_v2.h`), 10 kHz centre-aligned.

**Device contributions (SLUSFA9 §6.6, D package):**

| Parameter | Typ | Max |
|---|---|---|
| tD1 turn-on propagation delay | 17 ns | 27 ns |
| tD2 turn-off propagation delay | 17 ns | 27 ns |
| tD3/tD4 enable → output | 17 ns | 27 ns |
| tM delay matching between the two channels of one package | 1 ns | 2 ns |
| Rise / fall (1.8 nF) | 6 / 10 ns | 10 / 14 ns |

**Network contribution.** τ = (100 Ω + 5 Ω) × (1 nF ours + 1 nF module + ≈0.1 nF harness) = **220 ns**,
with a final value of 13.37 V:

- rise to the module's 11 V threshold: −τ·ln(1 − 11/13.37) = **380 ns**
- fall to the module's 1.5 V threshold: τ·ln(13.37/1.5) = **481 ns**

Both are identical on all six channels because R is 1 % and C is C0G ±5 %, so only the ±5 % spread
differs channel to channel: **±19 ns / ±24 ns**.

**Worst-case channel-to-channel skew**

```
  27 ns  device-to-device propagation spread (max, no min specified → full range assumed)
 +  2 ns  in-package channel matching (max) — this is the high/low pair of one leg
 + 24 ns  RC tolerance spread
 = 53 ns  =  3.5 % of the 1500 ns deadband
```

**Effective deadtime at the module.** The MCU turns the top off at T and the bottom on at T + 1500 ns:

```
  top actually off  : T + 481 (fall to 1.5 V) + 27 (driver)  = T +  508 ns
  bottom actually on: T + 1500 + 380 (rise to 11 V) + 27     = T + 1907 ns
  effective dead interval                                    =      1399 ns   (93 % of nominal)
```

Positive with 1.4 µs to spare, and the module's own EiceDRIVER cores add their interlock on top. If
the module has no internal network and only ours is fitted, τ = 116 ns and the effective deadtime
rises to 1447 ns.

**Do not "optimise" R18–R23 downward in S10.** 100 Ω is what limits the driver's peak current into
the 2.1 nF network to 13.4 / 105 = **127 mA** (against a 5 A capability) and damps the harness at
the source. Dropping to 47 Ω buys ~240 ns of edge speed that the deadband analysis shows is not
needed, and doubles dI/dt into a cable that runs alongside an inverter.

---

## 7. Enable architecture

```
  DRV_EN_3V3      (GPIO66)  ──┐ U8.1
  DRV_EN_AUX_3V3  (GPIO131) ──┤ U8.3   SN74LVC1G11    U8.4
                              │        3-input AND  ──────► GATE_EN_3V3 ──► ENA+ENB of U5, U6, U7
  SW_MAIN_3V3 ──[JP1 1-2]─────┘ U8.6                                   ├──► R33 1 kΩ to GND
   (vehicle_io)  ▲                                                     ├──► TP16
                 └── JP1 2-3 = bypass to +3V3 (BENCH ONLY)             └──► R34 680 Ω ► D9 "GATE EN"
```

- **JP1 is an exclusive 3-pad solder jumper**, common on U8's C input. Position 1-2 (default,
  factory bridge) takes the interlock from `vehicle_io`; position 2-3 bypasses it to +3V3 for
  bench work. Because it is exclusive, the two sources can never fight — which a 2-pad shorting
  jumper across a driven signal would allow. This is the same concept as 3.0's `BYPASS0` jumper,
  done safely.
- **`SW_MAIN_3V3` is deliberately unfiltered here.** Any RC on this path delays *de-assertion*,
  which is the unsafe direction. Contact conditioning belongs in `vehicle_io` (S8); chatter on this
  line can only cause a brief disable, never a brief enable.
- **`GATE_EN_3V3` pull-down R33 = 1 kΩ, not 100 kΩ.** Six enable pins in parallel present
  6 × 200 kΩ = 33.3 kΩ of internal pull-up to 13.5 V. To guarantee a disable when U8's output is
  high-Z the pull-down must win against that: 13.5 × 1/(1+33.3) = **0.39 V**, and even if the
  internal pull-ups were as low as 100 kΩ, 13.5 × 1/(1+16.7) = **0.76 V** — still under the 0.8 V
  worst-case enable-low threshold. A 10 kΩ pull-down would sit at 3.1 V and *enable* the drivers.
- **The status LED is on the enable net on purpose.** D9 lit = gates armed. 680 Ω → 2.1 mA; with
  R33's 3.3 mA and 0.3 mA of enable pull-up current, U8 sources 5.7 mA of its ±24 mA.

---

## 8. Fail-safe analysis

Every reachable degraded state must land **gates off**. The one that drove a design change is the
second row.

| Condition | Mechanism | Result |
|---|---|---|
| LaunchPad unplugged | PWM inputs: R36–R41 4.7 kΩ ∥ UCC27524's internal 120 kΩ to GND. U8 inputs: R30–R32 4.7 kΩ to GND | all LOW → EN LOW → **off** |
| **MCU held in reset** | F28379D GPIOs power up as **inputs with pull-ups enabled**. Worst-case pull-up ≈24 kΩ. PWM node = 3.3 × 4.52 k/28.5 k = **0.52 V**; U8 input = 3.3 × 4.7/28.7 = **0.54 V**. Both under the 0.8 V / 0.8 V worst-case low thresholds | **off** |
| +3V3 dead, +13V5 alive | U8 output high-Z (`Ioff`); R33 1 kΩ holds `GATE_EN_3V3` at 0.39 V | **off** |
| Board unpowered, module powered | UCC27524 output stage off; R24–R29 (+ the module's own 10 kΩ) hold the module inputs LOW | **off** |
| `+13V5_GATE` below UVLO (4.1 V rising / 3.8 V falling) | UCC27524 holds OUTA/OUTB LOW by design | **off** |
| Interlock opened (`SW_MAIN` low) | U8.6 LOW → AND output LOW → all six ENA/ENB LOW | **off** |
| Broken `GATE_EN_3V3` trace | R33 pulls the driver-side segment to 0.39 V | **off** |
| DB37 unplugged | fault lines pull HIGH through their (S5) pull-ups = fault asserted; gate lines irrelevant | **safe** |

> **The reset row is the reason R30–R32 and R36–R41 are 4.7 kΩ.** The first pass used 100 kΩ, which
> against a 24 kΩ internal pull-up would put the enable inputs at 2.66 V — a solid *enable* — and
> the PWM inputs at 2.75 V, a solid *high*. That combination arms all six gates while the MCU is in
> reset. ERC surfaced it (the pins had no driver on the net); the fix was sizing, not wiring.
> **Do not raise these resistors.** Cost of 4.7 kΩ: 0.70 mA per line sourced from a GPIO rated 4 mA.

---

## 9. Bill of materials added by S4

Only two new purchased lines; everything else comes from the S1/S3 vetted kit.

| Ref | Value | Package | LCSC | JLC | Stock | $ @100 |
|---|---|---|---|---|---|---|
| U5–U7 | UCC27524DR | SOIC-8 | **C465729** | Extended | 9 550 | 0.2294 |
| U8 | SN74LVC1G11DBVR | SOT-23-6 | **C22046** | Extended | 10 443 | 0.1391 @150 |

From the existing kit:

| Ref | Value | LCSC | Purpose |
|---|---|---|---|
| R18–R23 | 100 Ω 0603 1 % | C22775 | gate series damping |
| R24–R29 | 10 kΩ 0603 1 % | C25804 | module input network (datasheet-specified) |
| R30–R32, R36–R41 | 4.7 kΩ 0603 1 % | C23162 | reset-safe pull-downs (see §8) |
| R33 | 1 kΩ 0603 | C21190 | `GATE_EN_3V3` pull-down |
| R34 | 680 Ω 0603 | C23228 | D9 series |
| R35 | 1 MΩ 0603 | C22936 | shield bleed |
| C29, C31, C33 | 1 µF 0805 X7R 50 V | C28323 | driver VDD bulk |
| C30, C32, C34, C35 | 100 nF 0603 X7R 50 V | C14663 | driver / U8 decoupling |
| C36 | 10 µF 1206 X5R 50 V | C13585 | `+13V5_GATE` local bulk |
| C37–C43 | 1 nF 0603 C0G 50 V | C106246 | module input filter (×6) + shield (×1) |
| D9 | red LED 0603 | C2286 | GATE EN indicator |
| J2 | DSUB-37 socket | CONSIGNED | MPN still open (S2 item) |
| JP1, JP2 | solder jumpers | NOFIT | copper only |
| TP10–TP18 | test points | NOFIT | copper only |

C0G discipline (`CLAUDE.md` constraint #1): S4 adds **no new C0G value** — everything reuses the
1 nF line already in the kit.

**Total sheet: 56 components, 44 nets.** Whole project so far: 131 components, every one carrying
an `LCSC` field.

---

## 10. Verification performed

| Check | Result |
|---|---|
| ERC, whole hierarchy (`kicad-cli sch erc --severity-all`) | `gate_drive`: **0 violations**. Remainder is 90 `label_dangling` + 37 `isolated_pin_label` on the **root only** — the documented empty-hierarchy noise, down from the S2 baseline of 160 as sheets fill. |
| Netlist, node by node | All **44 nets** matched a hand-written expected-membership table with **0 mismatches**; `GND`(82 nodes), `+13V5_GATE`(21), `+3V3`(8), `+24V_MOD`(5), `PGND_MOD`(3) each verified to contain every intended node. |
| `GATE_EN_3V3` reaches all six enables | `['R33.1','R34.1','TP16.1','U5.1','U5.8','U6.1','U6.8','U7.1','U7.8','U8.4']` ✓ |
| Gate chain end to end (U leg) | `PWM_UH_3V3 = [R36.1, U5.2]` → `PWM_UH_DRV = [R18.1, U5.7]` → `PWM_UH_15V = [C37.1, J2.21, R18.2, R24.1, TP10.1]` ✓ |
| Symbol library parses | `kicad-cli sym export svg` → **46/46** |
| Footprint library parses | `kicad-cli fp export svg` → **40/40** |
| BOM | every refdes has `LCSC`; `CONSIGNED` / `NOFIT` used for hand-solder and copper-only parts |
| Datasheet pin table vs 3.0 as-built | **34 of 37 agree** (26 functional + 8 NC). Only pins 1, 9, 27 change and **none is in a signal path** — see §3.1. |

---

## 11. Firmware handoff deltas (for S12's `control_v2_pinmap.md`)

| Symbol | Today | Must become | Why |
|---|---|---|---|
| `MODULE_FAULT_ACTIVE_LOW` | `1` | **`0`** | datasheet p.2: "logic low = no fault". The Input X-BAR trip polarity inverts with it. |
| `GATE_DRV_EN_GPIO` (66) | assumed active-high | **confirmed active-HIGH** | board-local; U8 input A. No longer an assumption. |
| `GATE_DRV_EN2_GPIO` (131) | assumed active-high, and on Control_V2 it was an AND-gate *supply* | **confirmed active-HIGH logic input** | U8 input B. |
| NTC channels | "none today", plan for two | **one** channel, `NTC_1_RAW` on DB37 pin 29, 0–10 V raw | only one temperature pin exists |
| Gate polarity | active-high | unchanged, now datasheet-sourced | p.2 "logic high = on" |

---

## 12. Open items leaving S4

- **[S5]** Fault pull-up value against the 15 mA sink limit and the now-known HIGH-asserted polarity:
  R ≥ 13.5 / 0.015 = 900 Ω is the floor; 2.2–4.7 kΩ (3–6 mA) is the sensible band. 3.0's 82 kΩ is
  far too weak for a harness run. Also: the pull-up rail choice (`+13V5_GATE` vs dedicated) is now
  simply "whatever keeps the divider to 3.3 V simple", since the outputs are rated to 15 V.
- **[S5]** `NTC_1_RAW` divider must survive **10 V** continuously.
- **[S8]** `vehicle_io` must produce `SW_MAIN_3V3` as a clean 3.3 V logic level with the
  conditioning on *its* side, and the S8 pin-map cross-check must include it.
- **[S10]** Gate bus routed as one equal-length group; `PGND_MOD` on dedicated copper to NT2;
  Kelvin pairs kept out of the plane. Full list is written on the sheet as text note "S10 LAYOUT
  NOTES".
- **[S12]** Re-verify C465729 and C22046 against live stock; both are Extended, so both carry a
  per-reel setup fee.
- **[bench, non-blocking]** Confirm on the real module whether the 10 kΩ / 1 nF input network is
  internal or expected externally. Either way the fitted design is correct; the answer only changes
  the timing numbers between the two cases computed in §6.
- **[bench, non-blocking]** Measure pins 9/27 (expected ≈15 V) at TP17/TP18 and decide whether the
  15 V / 50 mA output is worth using for the Emrax motor PTC in a later revision.
