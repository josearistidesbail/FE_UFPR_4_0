# S9.5 — Motor temperature channel (EMRAX 208 stator KTY81-210)

**Status: captured, ERC/DRC clean, and GATED on one answer from EMRAX.** See §6.

Added mid-S9 because the board had **no motor-temperature channel at all**, and the EMRAX
manual does not treat that as optional.

---

## 1. Why this exists — the manufacturer requires it

`datasheets/` does not hold the EMRAX manual (fetched online this session, v5.1 Aug 2018).
Two statements from it drive the whole design:

> §13 Motor cooling — "In every case, the temperature sensor that is mounted in the motor
> **must be connected to the controller**… The standard temperature sensor mounted into the
> motor is **KTY 81-210**"

> "The EMRAX motor must not exceed the temperature below −40 °C and above **120 °C** on cooper
> windings and on the magnets… If the temperature exceeds these values, it causes a **void of
> warranty**. In case of **disconnection of the temperature sensor**, which has to be on the
> cooper windings, **the controller has to stop the motor**. The motor temperature sensor
> detector in the controller must always be enabled, during motor operation."

So the requirement is not just "read it" — it is **read it, derate on it, and stop the motor
if the sensor disconnects**. The topology in §3 is chosen to make that last part free.

⚠ The 208 spec table lists `kty 81/210`, but NXP has since discontinued the KTY81 family and
newer EMRAX builds ship **PT1000**. **Measure the installed sensor cold before ordering
parts**: ≈2.0 kΩ = KTY81-2xx, ≈1.1 kΩ = PT1000, ≈110 Ω = PT100. Everything below assumes the
KTY. A PT1000 would need R129 re-picked (and a PT100 would need a different topology — its
0.385 Ω/K against harness resistance is not negligible the way the KTY's 20 Ω/K is).

## 2. The sensor — KTY81-210 (Philips/NXP data sheet, `Icont = 1 mA`)

Silicon PTC, 2000 Ω ±1 % at 25 °C, operating −55…+150 °C, `R100/R25 = 1.696`.

| T (°C) | −40 | 0 | 25 | 50 | 80 | 100 | **120** | 150 |
|---|---|---|---|---|---|---|---|---|
| R (Ω) typ | 1135 | 1630 | 2000 | 2417 | 2980 | 3392 | **3817** | 4280 |
| datasheet temp error (K) | ±2.74 | ±1.91 | ±1.27 | ±1.91 | ±2.8 | ±3.46 | **±4.7** | ±14.63 |

**The sensor's own ±4.7 K at the 120 °C limit is the error floor.** Nothing in the front end is
worth designing below it — see §4, which is the whole reason the rail monitor exists and the
reason no op-amp does.

## 3. Topology — the sensor is the BOTTOM leg, and that is the safety argument

```
+3V3 ──[R129 2.20k 0.1%]──┬── MOT_TEMP_RAW ──[R130 3.3k]──┬── MOT_TEMP_ADC → J20 pad 10
                          │                               │
                     J4 cav 6                       C121 22nF C0G
                          │                         D18 BAT54S → +3V3 / GND
                 (KTY81-210, in the motor)
                          │
                     J4 cav 7 ── GND        C120 1nF C0G at the connector, TP53 on RAW
```

- **Open circuit** (broken wire, unplugged, dead sensor) → node pulled to **3.30 V**
- **Short circuit** → node at **0 V**
- Valid band is **1.12 … 2.18 V**

Both faults land outside the band, so "sensor disconnected" is unambiguous and the EMRAX
stop-the-motor clause costs no extra hardware. This is S7's unplugged-encoder argument reused:
a fault must land somewhere firmware cannot mistake for data.

**Excitation is +3V3, not +5V, deliberately.** An open sensor rails the node to the excitation
rail; at 3.3 V that is inside the F28379D's `VDDA + 0.3 = 3.6 V` absolute maximum, so the
fault state cannot damage the ADC. From +5 V it would be an over-voltage on every open circuit.

Hotter = higher resistance = **higher code**. ⚠ This is the opposite direction to the module
NTC on `ADCINC3`, whose divider puts the thermistor on top. Easy firmware bug.

### Transfer function (VREFHI = 3.0 V, 12-bit, rail 3.30 V, R129 = 2.20 kΩ)

| T (°C) | −40 | 0 | 25 | 50 | 80 | 100 | **120** | 150 | open | short |
|---|---|---|---|---|---|---|---|---|---|---|
| V (V) | 1.123 | 1.404 | 1.571 | 1.728 | 1.898 | 2.002 | **2.093** | 2.180 | 3.30 | 0 |
| code | 1533 | 1917 | 2145 | 2358 | 2591 | 2732 | **2857** | 2975 | 4095 clip | 0 |

**6.25 codes/K at the limit** — far more resolution than a thermal loop needs, which is why
§4 rejects an amplifier. Sensor current **0.99 mA at −40 °C** falling to **0.51 mA at 150 °C**:
under the datasheet's 1 mA characterisation current everywhere, and far under its 2 mA ceiling
at 150 °C, so self-heating is not a term. Anti-alias corner ≈1.5–1.7 kHz, the same
`series R + C0G bucket` pattern S5 used for the module NTC.

## 4. Accuracy — the rail was the dominant error, and it is removed

The divider compresses, so `dV/V = (dR/R)·R129/(R129+R) = 0.194 %/K` at 120 °C. Therefore
**1 % of excitation-rail error ≈ 5 K**, and an AMS1117-3.3 at ±1.5–2 % contributes **±8–10 K** —
*larger than the sensor's own ±4.7 K*. That is not acceptable against a 120 °C hard limit where
every kelvin of margin is endurance performance.

**Fix: R131/R132 read the same +3V3 through a 10.0 k/10.0 k 0.1 % divider on `ADCINA3`
(J20 pad 12).** Firmware then computes

```
R_KTY = R129 · V / (V_rail − V)
```

and the rail cancels exactly. Residual: R129's 0.1 % → 0.19 K, the divider ratio's 0.14 % →
0.7 K. Total ≈ **±5 K, dominated by the sensor itself** — which is where it should sit.

**No op-amp.** Range use is only ~35 %, and that is fine: an amplifier would buy resolution
nobody needs while adding offset drift, and the sensor's ±4.7 K makes the extra precision
meaningless. Same reasoning as S5's decision not to buffer the Vbus divider.

## 5. Connector, ADC pin, and why they are what they are

**J4 cavities 6 and 7**, the outermost column pair, **16.8 mm from the SIN cavity**, with
cavities **5 and 8 deliberately left empty as a guard column** (fit sealing plugs). Own twisted
pair, **not inside the encoder shield** — the KTY leads sit in a stator slot beside conductors
slewing at kV/µs, and putting that inside the sin/cos shield would undo S7's noise budget.

There was no alternative connector: TE's board-mount DTM13 family exists only in 8- and
12-way, keys A and B are spent on J3/J4, and J5's eight cavities are full. A third look-alike
12-way is exactly the mis-mate hazard S8 designed out.

**ADC = `ADCINB3` → J3-25 → J20 pad 10**; the rail monitor is `ADCINA3` → J3-26 → J20 pad 12.
Free pins were verified by mapping every socket pad through SPRUI77's tables and checking that
all 29 known signals land where the frozen pin map says. `ADCINC5` (J7-64) was the alternative
and would have kept both thermal channels on ADC-C with S5's SOC ordering — rejected because
J7 is the *current-sense* socket on the far side of the board, and S9's placement rule is that
a block's traffic must reach its pads without crossing a socket column. SOC assignment is free
in firmware; routing is not.

## 6. ⚠ THE GATE — this design is only legal if the sensor is isolated

The KTY is potted **on the stator windings** with no isolation rating stated anywhere in the
EMRAX manual. Under **FSAE 2026**:

> **EV.1.6** Tractive System – TS: Every part **electrically connected** to the Motor(s) and/or
> Tractive Battery(s). The Tractive System is always High Voltage
>
> **EV.6.5.1a** The entire Tractive System and GLV System must be completely galvanically separated
>
> **EV.6.5.3** Tractive System and GLV circuits **must not be in the same conduit or connector**

So: **if the KTY has reinforced or double insulation from the windings, it is GLV and everything
above is legal.** If it has only basic insulation, it is a TS conductor, EV.6.5.3 forbids it
sharing J4 with the encoder, and this block must be replaced by an isolated front end on its own
connector (EV.7.5.7's second option, "isolation in the sensing circuit") plus a marked TS board
area with EV.6.5.7 spacing — 12.7 mm over surface at 300–600 V.

**Ask EMRAX exactly this:** *is the KTY 81-210 in the EMRAX 208 installed with reinforced or
double insulation from the stator winding per EN 61800-5-1, for a working voltage of 600 V DC?*
Lenze's application note is the precedent for the question's shape: in their **servo** motors
KTY/PT1000 are "installed with a reinforced insulation" and may be connected via the encoder
inputs, while in their **standard** motors PTC/TCO "are not designed with a reinforced insulation"
and may only go to a basic-insulated input. **Same sensor technology, two different isolation
classes, decided by how the motor was built** — so this cannot be reasoned out, and a megger
reading cannot substitute for the spec (a DMM continuity test proves nothing at all: it applies
~3 V to insulation that has to hold off hundreds).

Lenze also notes the whole path must hold the class — "cables, terminals, plug-in connectors,
and the cable routing" — so even in the good case the harness wire insulation and the DTM cavity
block are part of the answer, not a detail.

## 7. Parts — zero new BOM lines

| Ref | Value | LCSC | Note |
|---|---|---|---|
| R129 | 2.20k 0.1 % | C861295 | same part as R57, S5's Vbus divider top |
| R130 | 3.3k | C22978 | S1 kit |
| R131, R132 | 10.0k 0.1 % | C95204 | same part as S7's difference-amp inputs |
| C120 | 1nF C0G | C106246 | connector EMC, house pattern |
| C121, C122 | 22nF C0G 0805 | C77069 | ADC charge buckets, S5 pattern |
| D18 | BAT54S | C7420333 | same clamp as D10/D11 |
| TP53, TP54 | — | NOFIT | RAW and rail-monitor test points |

Every line already existed, so **no new reel fee and nothing new to stock-check**.

## 8. Capture and verification

- `encoder` sheet: 10 parts added, three blocks (connector end at J4, front end and rail
  monitor in the free upper-left region). J4 cavities 6/7 removed from the no-connect list.
- `launchpad`: J20 pads 10 and 12 un-no-connected and labelled.
- Root: 4 sheet pins, 4 stubs, 4 labels for `MOT_TEMP_ADC` / `MOT_TEMP_REF_ADC`.
- `.kicad_pro`: pattern **`*MOT_TEMP_*` → Analog** (leading `*` mandatory, S5 lesson).
  Verified from `kicad-cli`'s own `(class …)` output: all three nets Analog, Analog 58 → 61.
- **Netlist re-baselined** 220/914 → **219 nets / 933 nodes**, delta fully accounted:
  −4 no-connect pseudo-nets (J4.6, J4.7, J20.10, J20.12), +3 real nets, +19 nodes = the 10 new
  parts' pins.
- **ERC `--severity-all` = 0. DRC `--severity-all` = 0 errors**, `schematic_parity` 0.
  Silk warnings 386 → 394, deferred to S11's silk pass with the rest.

### Two things the gates caught

1. **A purely cosmetic re-spacing shorted R130.** Collapsing the signal row into one wire ran it
   straight across the resistor; the netlist diff caught it immediately. The netlist gate is not
   ceremony even for a "layout-only" edit.
2. **Rendering the sheet caught four text collisions** the netlist is blind to — the S7.5 rule
   again. `C101`/`C102`'s own value text reaches to x 89, which is what pushed the D18 clamp onto
   its own row.

### ⚠ A pre-existing defect found while verifying the board

`sync_schematic_to_board` reports nets in `nets_added` that it then **never assigns to any pad**.
Three *real* nets had **zero pad assignments** on the board:

| Net | Pads it should have | Introduced |
|---|---|---|
| `+5V_VEH` | C119.1, D17.1, F3.1, J5.2 | **S8 — missing since S9's sync** |
| `CAN_RS` | R120.1, U18.8 | **S8 — missing since S9's sync** |
| `MOT_TEMP_RAW` | C120.1, J4.6, R129.2, R130.1, TP53.1 | this session |

`+5V_VEH` and `CAN_RS` are **not mine** — they were absent from the S9 commit's board too.
S10 would have routed the board with the ECU supply feed and the CAN slope-control resistor
silently unconnected. All twelve pad assignments were written directly into the `.kicad_pcb` and
confirmed present via KiCad's own **IPC-D-356 export**, which lists all three as board nets.

⚠ Also note: the DRC's `unconnected_items` count sits at **499** and did not move when nets were
added, while the board's own pad data implies **705** connections on 146 multi-pad nets. **Do not
treat "499 unrouted connections" as an exact figure** — S9's note in CLAUDE.md inherits it.
Re-derive from the board before using it as a routing metric.

## 9. Firmware handoff (S12)

- New constants: `MOT_TEMP_R_TOP = 2200.0`, and the KTY81-210 R(T) table or its
  `R(T) = R25·(1 + α(T−25) + β(T−25)²)` fit.
- **Fault window: reject `code < 1400` or `code > 3100` → stop the motor** (EMRAX requirement).
- Rail cancellation: `R = R_TOP · V / (V_rail − V)` with `V_rail = 2 ·` the `ADCINA3` reading.
- Derate above ~90 °C; hard limit 120 °C. With the rail corrected budget ±5 K and set the trip
  near **114 °C**.
- Suggested SOC: append to the ADC-B chain after the existing conversions — it is a slow channel
  and must not delay the 10 kHz ISR.
- ⚠ **PTC, not NTC** — hotter is a higher code, opposite to `NTC_1_ADC` on `ADCINC3`.

## 10. Open items this leaves

- **[user, BLOCKING] EMRAX insulation class** — §6. Everything here depends on it.
- **[user] Confirm the installed sensor is a KTY81-210 and not a PT1000** — measure cold.
- **[S10] Pull C120 to J4's cavity-6 pad.** It is currently at (99, 69.5); the cavity 6 pad is at
  (78.5, 69.22) but J4's courtyard polygon blocks the space between. Placement here is provisional
  — S10/S11 refine within blocks, as S9 intended.
- **[S10] Route `+5V_VEH` and `CAN_RS`** — newly connected, previously invisible to the router.
- **[S11] +8 silk warnings** from the new references, into the silk pass.
