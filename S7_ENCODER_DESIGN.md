# S7 — Encoder front-end (RM44AC) + connector

**Deliverable of session 7.** Sheet: `encoder.kicad_sch` — 46 components, 16 nets, netlist verified
node-by-node (16/16 exact, 0 mismatches), ERC clean of every class except the two documented
cosmetic ones. Also **revises S6's J3** from Micro-Fit to Deutsch (§8).

Everything here is computed from the RM44AC datasheet fetched this session
(`datasheets/RLS-RM44_RM58-RM4458D01_01.pdf`) and from the firmware's own sin/cos handling
(`sensor_rm44ac.h`). Where a number is *assumed* rather than measured, it says so.

---

## 1. The source — what the RM44AC actually is

Bench items #7–#9 ("differential vs single-ended, supply V/I, true output levels") were listed as
**blocking S7**. The datasheet answers all three, so the bench now only confirms them.

| Parameter | Value | Consequence for this sheet |
|---|---|---|
| Output form | **2 channels VA/VB, sinusoids 90° apart, SINGLE ENDED** | No INA/differential receive. The roadmap's preferred topology is not available. |
| Amplitude | **2.2 ± 0.2 Vpp** (1.0–1.2 V peak) | ±9 % source spread — the gain must be sized for the **max**, see §3. |
| Offset | **(3/5)·Vdd ± 5 mV** | Ratiometric to its own supply ⇒ cancellable for free, see §4. |
| Internal series impedance | **720 Ω** | Not negligible: it sits in series with our input resistor and sets a 3.2 % gain correction. |
| Supply | 5 V ± 5 %, **13 mA** | ARCHITECTURE.md §2 budgeted ~60 mA — a 47 mA windfall on the +5 V rail. |
| Max speed | 60 000 rpm | Far above the Emrax's 6 000 rpm limit. |
| Cable | **LiYCY 4 × 0.20 mm², shielded**, 1 m standard / 3 m max | Only 4 cores: Vdd, GND, VA, VB. |
| Resolution code | `01S` = **one sin/cos period per mechanical revolution** | Confirms `SENSOR_RES_SENSOR_POLES = 1`. |
| Ordering | Output `AC`; connector option **A (9-way D-sub) or F (flying leads)** | User confirmed **flying leads**. |

### 1.1 A Kelvin ground return is physically impossible

The natural way to reject harness ground shift is to receive the signal differentially against the
encoder's own ground. **The RM44AC's factory cable has four cores and no spare conductor**, so there
is nowhere to put a sense wire. This is not a design choice we get to make.

What it costs is bounded and small: the return carries the encoder's 13 mA through
0.0873 Ω/m × 3 m = 0.262 Ω, i.e. **3.4 mV** of static offset. The encoder's current draw is
essentially constant, so this is a DC offset — and DC offsets are captured and removed by the ALIGN
bias sweep at every alignment. The braid, terminated at our end per the S2 shield policy, handles
the dynamic part.

### 1.2 What could NOT be back-calculated

`hw_control_v2.h` records a bench measurement at the ADC pin on the 3.0 board: **DC 2.25 V,
1.45 Vpp**. It is tempting to divide by 3.0's front-end gain and recover the encoder's real
installed amplitude. **That is not sound and was not done.** 3.0's schematic shows an intended
difference amp at 121 k/100 k (G = 1.21), but CLAUDE.md records channel A as *"half-reworked outside
the board outline"* and channel B as deleted, so the circuit that produced 1.45 Vpp is not the
circuit on the schematic. The two numbers are inconsistent with each other under any single gain
(2.25/3.00 = 0.750 against 1.45/2.2 = 0.659), which is itself evidence of the rework.

**Conclusion: the installed encoder's amplitude is unknown between the datasheet's 2.0 and 2.4 Vpp,
and the design is sized so that it does not matter** (§3).

---

## 2. Topology

Per channel: **one non-inverting difference amplifier** (4 resistors + 2 matched caps), half an
OPA2376. Both channels live in one package (`U16`) so they share a die and a thermal environment.
Two more halves (`U17`) buffer the two references.

```
 ENC_x_RAW --[R1' 10.0k]--+-- (+) \
                          |        >-- ENC_x_OUT --[100R]--+-- ENC_x_ADC --> BoosterPack
              [R2' 12.0k] |    (-) /                       |
                    |     |     |                        [22nF]  [BAT54S to +3V3/GND]
              ENC_VREF3V  |     +--[R1 10.0k]-- ENC_VREF_HI
                          |     +--[R2 12.0k ‖ C2 2.2nF]-- ENC_x_OUT
                    C2' 2.2nF across R2'
```

Transfer function, with `Rs` = the encoder's 720 Ω:

```
a    = R2' / (R1' + Rs + R2') = 12.0 / (10.0 + 0.72 + 12.0) = 0.5281690
G    = R2 / R1                = 12.0k / 10.0k               = 1.200
Vout = (1+G)·[a·Vin + (1−a)·ENC_VREF3V] − G·ENC_VREF_HI
dVout/dVin = (1+G)·a = 1.1619718 V/V
```

### 2.1 Why the reference sits at the *bottom* of the + divider

The textbook arrangement puts the encoder's bias reference on the inverting input
(`V1 = ENC_VREF3V`) and the wanted ADC bias at the bottom of the + divider (`V_bot = 1.500 V`).
That works, costs exactly the same parts, and gives a bias that is independent of gain.

**We do the opposite** — `V_bot = ENC_VREF3V` (3.0 V) and `V1 = ENC_VREF_HI` (0.8495·Vdd) — for one
reason: **what the sheet does when the encoder is unplugged.**

| | textbook (`V_bot` = 1.5 V) | **chosen** (`V_bot` = ENC_VREF3V) |
|---|---|---|
| Unplugged output | rails to ~0 V | **exactly the ADC bias**, 1.4974 V |
| Normalised sin, cos | −1.07, −1.07 | 0.000, 0.000 |
| `sin²+cos²` | 2.29 | **≈ 0** |
| Firmware verdict | loss **only if** ampl < 1930 codes | loss, unconditionally |
| Margin against threshold | 1.8 % (`MAG_HIGH` = 2.25) | the full distance to `MAG_LOW` = 0.25 |

With an open input no current flows in `R1'`/`R2'`, so the + node sits at `V_bot`; with `V_bot`
equal to the encoder's own quiescent bias the output lands on the ADC bias and the sin/cos **vector
collapses to the origin**. The firmware's loss-of-signal check (`SENSOR_RES_MAG_LOW/HIGH`) then fires
with the largest possible margin, and — crucially — the detection no longer depends on the
calibrated amplitude. Under the textbook arrangement a strong encoder (2.4 Vpp → 1904 codes) sits
close to the 1930-code limit above which an unplugged connector reads as a **valid, frozen angle**.
A frozen angle at speed is an uncontrolled-torque condition; this is a safety property, not a
convenience.

The cost is that the bias now depends on gain: `Vout_q = Vdd·[0.6 + G·(0.6 − k)]`, so changing G
requires re-splitting the reference chain (§9 gives the table). That is a one-time bench operation;
the failure mode above is permanent.

### 2.2 Why not an inverting stage, and why not a buffer first

An inverting stage would load the 720 Ω source directly at the summing junction (gain becomes
`R2/(R1+720)`, fully source-dependent) and would mirror the angle. A unity buffer ahead of the
difference amp removes the 720 Ω from the equation but costs two more op-amp halves — i.e. a third
package — to remove a **3.2 % gain correction that is deterministic, identical on both channels, and
calibrated out at every ALIGN anyway.** Not worth it.

---

## 3. Gain and range — sized for the worst-case source

The conditioning target in CLAUDE.md is *"1.5 V bias, ~1.4 V amplitude"*, with
`RES_SINCOS_AMPL_CODE ≈ 1911`. **S7 deliberately lands 1.278 V / 1745 codes instead.**

The reason is arithmetic. At 1.400 V nominal the gain is 1.2727 V/V; a legal max-amplitude encoder
(2.4 Vpp = 1.2 V peak) then produces **1.527 V**, and 2039 + 2085 = **4124 codes > 4095** — it
clips. Clipping is one of the three defects the firmware logbook explicitly blames for the old
board's 26° electrical angle noise, so trading 6 % of ADC range to make it impossible is the right
trade.

| Source | Amplitude at ADC | Codes | Range used | Peak codes |
|---|---|---|---|---|
| min, 2.0 Vpp | 1.1620 V | 1586 | 77.5 % | 625 … 3453 |
| **nominal, 2.2 Vpp** | **1.2782 V** | **1745** | **85.2 %** | 466 … 3612 |
| max, 2.4 Vpp | 1.3944 V | 1904 | 93.0 % | 135 … 3943 |

Worst-case excursion **0.099 … 2.888 V** against a 0–3.000 V window: 99 mV of margin at each end,
symmetric. Compare 3.0: **48 % of range with the positive peak 25 mV below VREFHI and noise peaks
clipping.**

Angle-noise improvement from amplitude alone: 1745/990 = **1.76×**. With the firmware's existing
200 Hz matched IIR (~4× on broadband noise, lag-compensated) the 26.5° electrical RMS of the old
board projects to roughly **3.8° electrical**, comfortably inside the ≤10 mV-at-the-pin target.

---

## 4. References — and why they are 0.1 %

```
ENC_VDD ──[R105 3.00k]──┬──[R106 4.99k]──┬──[R107 12.0k]── GND
                        │                │
                   ENC_VREF_HI_UB   ENC_VREF3V_UB
                        │                │
                  U17B buffer       U17A buffer
                        │                │
                   ENC_VREF_HI      ENC_VREF3V
```

Total 19.99 kΩ, 249 µA. Taps: **0.6003 · ENC_VDD** and **0.8499 · ENC_VDD**.

Two properties make this work:

1. **The chain hangs off `ENC_VDD` — the same node that feeds the encoder**, downstream of the
   ferrite. So the encoder's offset (3/5 of *its* Vdd) and our subtraction reference (0.6003 of
   *the same* node) track each other exactly. The ferrite's 4.9 mV drop, the buck's tolerance and
   its line/load regulation all cancel. Only the cable's 3.4 mV survives, and that is static.
   *A series R in the encoder supply would break this and must never be substituted for FB1* — a
   10 Ω resistor at 13 mA would shift the output bias by 94 mV and clip the bottom of the swing.
2. **0.1 %, one family (Yageo RT0603BRD07, 25 ppm/K).** The tolerance is bought for **TCR tracking,
   not accuracy.** A static reference error is removed by the ALIGN bias capture; *drift between
   ALIGNs is not*. Because both channels share these references, a reference shift `δ` is a
   **common** shift on sin and cos — a translation of the vector, not a scale — giving an angle
   error of `δ·√2/A`. At 1 % ratio drift that is ~6° electrical. Same-family 0.1 % parts hold it
   near 0.5°.

Both taps are RC-filtered (1 µF, corners 33 Hz and 62 Hz) *before* the buffers, so +5 V rail ripple
never reaches the summing nodes; the buffers keep the reference impedance low enough that the
signal current through `R2'` (≈5 µA/channel) causes no error.

`ENC_VREF_HI` = 4.232 V on a 4.979 V rail is why the op-amps must be rail-to-rail on the output;
`V+` swings 2.35 … 3.65 V, which is why they must be rail-to-rail on the input too. The OPA2376
already vetted in S6 (C46316) satisfies both.

---

## 5. Anti-alias, phase, and the one error nothing can fix

Pole in the feedback: **R2 · C2 = 12.0 kΩ × 2.2 nF → fc = 6.03 kHz**, with `C2'` across `R2'` so the
bridge stays balanced at HF. Same corner as S6's current channels; **no new C0G value** — this closes
S7's half of the standing "standardise C0G values" item using `C107043` (2.2 nF) from the existing set.

The governing insight comes from the firmware, not from filter theory. `sensor_rm44ac.h` already runs
a **matched 200 Hz IIR on sin and cos and compensates its lag analytically** (`lag_elec ≈ f_elec/fc`,
`SENSOR_RES_FILT_COMP`). So:

- a **matched** lag is a pure angle *delay* — systematic, known, already corrected;
- a **mismatched** lag between SIN and COS is an angle *error* — and nothing in the firmware or the
  calibration can remove it.

That is why the RC values are identical per channel and C0G, and why matching matters far more than
the corner frequency does.

Phase budget at 6 000 rpm (f_mech = 100 Hz, f_elec = 1 000 Hz):

| Pole | fc | Lag (mech) | Lag (elec) |
|---|---|---|---|
| Input EMC, 720 Ω × 1 nF | 221 kHz | 0.026° | 0.26° |
| **Active pole, R2·C2** | **6.03 kHz** | **0.950°** | **9.50°** |
| ADC bucket, 100 Ω × 22 nF | 72.3 kHz | 0.079° | 0.79° |
| **Total, uncompensated** | | **1.055°** | **10.55°** |
| **Differential SIN↔COS** (1 % R, 5 % C0G) | | | **≈ 0.5°** |

10.55° electrical at maximum speed, falling linearly with speed (1.06° at 600 rpm), is acceptable
uncompensated. If it is ever worth reclaiming, it is a **one-constant firmware change**, not a board
change: fold the hardware pole into the existing compensator via `1/fc_eff = 1/200 + 1/6030`
→ 193.5 Hz. This is offered as optional precisely so the board does not depend on a live-tunable
debug parameter (`res_filt_hz`) staying at its default — a bench trap of the kind S5 logged.

Attenuation at 10 kHz is −5.8 dB. As in S6, a single pole is a weak anti-alias filter at any usable
corner; the real rejection of switching noise is the firmware's synchronous sampling at the PWM peak,
which folds 10 kHz-family pickup to a static offset that the bias calibration removes.

---

## 6. Protection and failure modes

| Condition | What happens | Verdict |
|---|---|---|
| **Encoder unplugged** | both outputs land on the ADC bias, `sin²+cos²` ≈ 0 | detected unconditionally (§2.1) |
| Signal line shorted to encoder Vdd | `Vout` would reach **3.89 V**, over the F28379D's VDDA+0.3 = **3.6 V** abs max | **D10/D11 BAT54S clamp** to +3V3/GND; the Schottky takes the current, not the MCU's ESD diode |
| Encoder connector mis-mated with the LEM harness (±15 V) | op-amp input current limited to 0.34 mA by `R1'` (OPA2376 limit ±10 mA); output rails, clamp holds the ADC pin | **now also prevented mechanically** — J3 is key A, J4 is key B (§8) |
| Signal shorted to GND | `Vout` rails low, both channels → `sin²+cos²` high | detected |
| Board +3V3 dead, +5 V alive | clamp drags both ADC lines to ~0.3 V | signal destroyed → detected as loss |
| Board +5 V dead | op-amps off, no drive | LaunchPad is fed from the same +5 V (S2 policy) so this cannot occur in isolation |

The clamp goes to the **board's** +3V3: the LaunchPad's 3V3 header pins are left NC by the S2 power
policy, so there is no other 3.3 V available. Under the worst fault the Schottky conducts ~14 mA and
holds the pin near 3.6 V.

**Input ESD** is handled the way the rest of the board handles connector-facing lines — 1 nF C0G at
the connector plus a 10 kΩ-class series resistor into the amplifier (here `R1'` = 10 kΩ) — matching
S4's DB37 network and S6's LEM inputs. No TVS is fitted on signal lines anywhere on this board; that
consistency is deliberate.

---

## 7. Supply

`+5V` → **FB1 (GZ2012D601TF, 600 Ω @ 100 MHz, 0805, JLC Basic)** → `ENC_VDD`, bulk 10 µF + 100 nF at
the connector. Load: encoder 13 mA + chain 0.25 mA + two OPA2376 ≈ 3.0 mA = **16.3 mA**, giving
4.9 mV across the bead's 300 mΩ DCR — and, per §4, that drop cancels.

A ferrite and not a resistor: the DCR must stay small enough that the encoder and the reference chain
see the same node. FB1's rating (500 mA) is 30× the load.

---

## 8. The connector — correcting S6

**S6 put a Micro-Fit 3.0 2×4 on the board for the LEM harness even though the argument it recorded
had chosen Deutsch**, on the stated grounds that TE's product drawing for the DTM13 was
"login-gated" and a footprint could not be derived honestly. S7 re-tested that premise and **it is
false**: TE's `DocumentDelivery` endpoint serves the dimensioned customer drawings with no
authentication.

```
https://www.te.com/commerce/DocumentDelivery/DDEController?Action=srchrtrv
    &DocNm=DTM13-12PA-R005&DocType=Customer+Drawing&DocLang=English
```

Three drawings now sit in `datasheets/` (8-way key A, 12-way keys A and B).

### 8.1 What the drawings say

Probing that repository across 2/3/4/6/8/12 ways × keys A/B × 11 flange suffixes returned **exactly
three documents**, which is itself the finding:

> **The DTM13 board-mount family exists only in 8-way and 12-way.** There is no 4-way or 6-way PCB
> header, so a 5-wire encoder cannot have a small Deutsch.

| | DTM13-08PA-R004 | **DTM13-12PA / 12PB-R005** |
|---|---|---|
| Flange envelope | 68.58 × 33.02 mm (4 ears) | **38.10 × 41.02 mm** (2 × Ø2.01 mm) |
| PCB grid | 4 × 2, 4.191 mm | **6 × 2, 4.19 × 4.19 mm** |
| Pin Ø | 1.04 ± 0.05 mm | 1.04 ± 0.05 mm |
| Keys | A only | **A and B** |
| Mates | DTM06-08SA | DTM06-12SA / -12SB |

Two consequences decided the outcome. First, the compact `-R005` 12-way is **smaller than the
8-way**, whose `-R004` flange is a wide four-ear plate — so 12-way costs less board edge, not more.
Second, `-12PA-R005` and `-12PB-R005` are **dimensionally identical**; only the key arrangement
differs. One derived footprint therefore serves both, and **keying comes from the connector's own
key rather than from way-count** — which is a stronger guarantee, because it survives any future
re-pinning of either harness.

### 8.2 Decision (user)

| | Part | Key | Ways used |
|---|---|---|---|
| **J3** LEM harness | `DTM13-12PA-R005` | **A** | 11 of 12 |
| **J4** encoder | `DTM13-12PB-R005` | **B** | 5 of 12 |

This closes the standing open item *"[user, if wanted] Board-mounted Deutsch instead of J3's
Micro-Fit"* and the S6/S7 pair item *"key or size the LEM connector differently from the encoder
connector"* — the latter now answered mechanically rather than by convention.

J3's four spare ways are spent on `ISO_COM` so that **every rail and every sensor output has its
return on the physically adjacent contact** (1–12, 2–11, 3–10, 4–9, 5–8). The 2×4 could not do that.

### 8.3 Footprint derivation

`FE_UFPR_4_0.pretty/DEUTSCH_DTM13-12P-R005_Horizontal.kicad_mod`, hand-derived from the printed
dimensions only:

- pads at **x = ±2.0955, ±6.2865, ±10.4775 mm**, **y = ±2.0955 mm** — a uniform 4.191 mm grid.
  The drawing prints ±0.083″/±0.248″/±0.413″; exact half-pitch multiples are used instead of the
  rounded 2.10/6.29/10.48 mm so the pitch cannot accumulate error, which is the S1 lesson from
  3.0's DB37.
- drill **1.3 mm**, pad **2.0 mm** (pin Ø 1.04 + 0.25 clearance, IPC).
- mounting holes **Ø2.2 mm NPTH at x = 0, y = ±17.145 mm** (34.29 mm apart). The drawing's Ø2.01
  feature is ambiguous between a locating peg and an M2 screw hole; Ø2.2 NPTH serves either.
- body/courtyard from the printed 38.10 × 41.02 mm envelope.

Cross-checked by pixel measurement of the 300 dpi drawing, scaled from the known 4.191 mm pitch:
mounting-hole spacing measured **34.42 mm** against the printed 34.29 mm (0.4 %, within scan
distortion), pin-field centre coincident with the mounting-hole axis to under a pixel. Library
re-validated: **42/42 footprints and 51/51 symbols export.**

### 8.4 ⚠ The one thing that is NOT verified

**TE's 12-way drawing does not label the cavities.** The numbering used here is *extrapolated* from
the 8-way drawing of the same family, which does (bottom row L→R = 1–4, top row R→L = 5–8), giving
1–6 / 12–7 for the 12-way. It is consistent with the footprint and the symbol
(`Conn_02x06_Counter_Clockwise`), so the board is self-consistent either way — but **the mapping to
the molded cavity numbers must be confirmed before a harness is crimped.** Logged as an open item and
written on both sheets.

---

## 9. Parts

New JLC lines (stock checked 2026-08-30):

| Part | LCSC | JLC | Stock | Use |
|---|---|---|---|---|
| **10.0 kΩ 0603 0.1 %** Yageo RT0603BRD0710KL | C95204 | Ext | 546 640 | R108/110/113/115 — gain inputs |
| **3.00 kΩ 0603 0.1 %** Yageo RT0603BRD073KL | C136963 | Ext | 116 222 | R105 — chain top |
| **BAT54S** dual series Schottky, SOT-23 | C7420333 | **Preferred** | 314 690 | D10/D11 ADC clamp |
| **Ferrite 600 Ω @100 MHz** GZ2012D601TF, 0805 | C1017 | **Basic** | 369 732 | FB1 — encoder supply |
| DEUTSCH DTM13-12PB-R005 / -12PA-R005 | — | **CONSIGNED** | — | J4 / J3 |

Everything else comes from the existing kit: 4.99 k 0.1 % `C723532`, 12.0 k 0.1 % `C326735`,
100 Ω `C22775`, 1 MΩ `C22936`, 0 Ω `C21189`, 1 nF C0G `C106246`, 2.2 nF C0G `C107043`,
22 nF 0805 C0G `C77069`, 100 nF `C14663`, 1 µF/0805 `C28323`, 10 µF/0805 `C15850`,
OPA2376 `C46316`. **S7 introduces no new C0G value.**

⚠ **3.09 kΩ 0.1 % (C861371) has 2 980 in stock and 3.01 kΩ (C705772) only 1 175.** The E24 value
**3.00 kΩ** was chosen over both E96 neighbours because it has 116 222 — the fourth time this project
has had to pick a value from live stock rather than from a table (S3, S5, S6, S7).

### 9.1 Bench gain adjustment

If the installed encoder measures low, raise the gain **and re-split the chain to keep the bias**
(`k = 0.6 + 0.3/G`, chain total 20.0 kΩ with R107 = 12.0 kΩ fixed):

| G | R1, R1′ | R2, R2′ | R106 (mid) | R105 (top) | Ampl at 2.2 Vpp |
|---|---|---|---|---|---|
| **1.20** | **10.0 k** | **12.0 k** | **4.99 k** | **3.00 k** | **1.278 V (1745 codes)** |
| 1.30 | 9.31 k | 12.1 k | 4.64 k | 3.40 k | 1.380 V (1884) |
| 1.40 | 8.66 k | 12.1 k | 4.32 k | 3.74 k | 1.478 V — **clips at 2.4 Vpp source** |

Changing R2/C2 instead would move the anti-alias pole; change **R1/R1′** and leave the pole alone.

---

## 10. Firmware handoff (for S12)

```c
// hw_control_v2.h -- encoder front-end rebuilt in S7
#define RES_SINCOS_BIAS_CODE    2039.0f   // 1.4934 V at VREFHI 3.0 V  (was 3072 = 2.25 V)
#define RES_SINCOS_AMPL_CODE    1745.0f   // 1.2782 V nominal          (was  990 = 0.725 V)
```

- Both are **boot** values; `SENSOR_RES_CAL_DEFAULT_EN = 1` re-measures them at every ALIGN. They
  matter because the angle is unusable until an align succeeds.
- Expected range use **85.2 %**; the front end **cannot clip** for any source between 2.0 and
  2.4 Vpp. `SENSOR_RES_CAL_CLIP_LO/HI_CODE` should never trip.
- **Loss-of-signal now works unconditionally**: an unplugged encoder puts both channels on the bias,
  so `sin²+cos²` → 0 and `SENSOR_RES_MAG_LOW` (0.25) fires with full margin, independent of the
  calibrated amplitude. This is a hardware property (§2.1) — do not "optimise" the window.
- **Optional**: the hardware adds a matched 6.03 kHz pole. To compensate it with the existing
  machinery, use `1/fc_eff = 1/res_filt_hz + 1/6030` (193.5 Hz at the 200 Hz default). Uncorrected
  it is 10.55° electrical at 6 000 rpm and proportionally less below.
- `SENSOR_RES_SENSOR_POLES = 1` is **confirmed by the datasheet** (order code `01S`), not just by the
  hand-turn bench test.
- ADC pins unchanged: SIN → `ADCINA2`, COS → `ADCINB2`.

---

## 11. Open items this session leaves

- **[user, before harness crimp] Confirm the DTM 12-way cavity numbering** against the molded
  numbers (§8.4). Board is self-consistent; only the harness mapping is at risk.
- **[user] The DTM13 mounting feature** — Ø2.01 mm peg or M2 screw. Footprint uses Ø2.2 mm NPTH,
  which serves either; confirm before S9 finalises mechanical.
- **[bench] Measure the installed encoder's amplitude at the connector.** Not blocking — the design
  spans the full datasheet range — but it tells you whether the §9.1 gain bump is worth fitting.
- **[S9] Board edge budget.** Two DTM13-12P flanges are 2 × 41.02 mm of edge plus the DB37 and the
  power entry, against 3.0's inherited 91.9 × 121.7 mm outline. S9 must confirm the analog edge
  actually holds both, or grow the outline.
- **[S12] The DTM contacts and wedgelocks** (DTM06-12SA / -12SB plugs, size-20 contacts, W12S
  wedgelocks) are consigned and are not on the JLC BOM.
