# S8 — LaunchPad interface, vehicle I/O, integration and pin-map freeze

**Deliverable of session S8 (2026-08-31 / 2026-09-01).** This session closes the schematic:
the `launchpad` sheet (four BoosterPack sockets, captured on 2026-08-31) and the `vehicle_io`
sheet (CAN transceiver, two isolated cockpit inputs, the ECU 5 V feed, the vehicle connector,
captured on 2026-09-01), the netlist-side pin-map cross-check, the BOM / JLCPCB audit, and the
`v4.0-schematic-freeze` tag. The launchpad-side findings (socket grouping, CAN-A choice,
SPRUI77 verification) are recorded in `CLAUDE.md`'s Decision Log under S8 and are not repeated
here except where the cross-check depends on them.

Every number below is either computed in this document or points at the datasheet page it
came from. Where a claim could not be verified it says so.

---

## 1. The vehicle connector J5 — DEUTSCH DTM13-08PA-R004

### 1.1 Why an 8-way

The board already carries two `DTM13-12P-R005` receptacles, J3 (LEM, key A) and J4 (encoder,
key B). S7 established that TE's board-mount DTM13 family exists **only in 8-way and 12-way**,
keys A and B. A third 12-way would necessarily share a key with J3 or J4, and a mis-mated
plug would put ±15 V onto the CAN lines or car 12 V onto the LEM secondaries. The 8-way is
therefore not a preference but the only member of the family that a 12-way plug physically
cannot enter. Mis-mate protection comes from **way-count**, which survives any re-pinning.

S8 re-tested the S7 premise instead of inheriting it: TE's `DocumentDelivery` repository was
probed for `DTM13-12PC/12PD` (both `-R004` and `-R005`), `DTM13-08PB-R004`, and the larger
`DT13-08PA` / `DT13-12PA` (bare and with `-R004` / `-R008`). **None exist there**;
`DTM13-08PA-R004` and the two 12-way drawings answer, every other name returns TE's "500"
not-found page. (A burst of 222 probes got this address blocked with 403 for about an hour —
probe TE slowly, a few names with a pause between them.)

### 1.2 What the drawing actually shows — the `-R004` is NOT a flat-base part

`datasheets/TE-DTM13-08PA-R004_customer_drawing.pdf` (rev D) was read view by view, with
pixel measurements scaled from the known 4.191 mm pitch as a cross-check on every printed
figure:

| Feature | Printed | Measured | Note |
|---|---|---|---|
| Column pitch | .165 [4.191] (from .495 = 3 pitches, .330 = 2 pitches) | 4.19 | as the 12-way |
| **Row spacing on the PCB** | **.250 ± .010 [6.35 ± .25]** (section B-B, tail to tail) | **6.30** | ⚠ **not 4.19** — `S7_ENCODER_DESIGN.md` §8.1's "4 × 2, 4.191 mm" was wrong for this part and is corrected there |
| Pin Ø | .041 ± .002 [1.04 ± .05] | — | drill 1.3, pad 2.0 as S7 |
| Near row to flange rear face | .170 ± .015 [4.32 ± .38] | — | |
| Flange | 2.700 × 1.300 [68.58 × 33.02] + four R.250 ears | 68.6 | **vertical plate, 2.29 thick** |
| Slots | 4 × (8.89 × 2.54, R1.27) at ±12.07 (x) about the flange centre, ±15.37 (z) | 12.13 / 11.93 | for panel screws |
| Flange centre vs pin-field centre | .654 [16.61] | 16.42 | the housing sits at one end of the flange |
| Housing | 1.285 × .796 [32.64 × 20.22], .620 [15.75] beyond the flange front | — | |
| Base block on the board | .953 [24.21] wide, ~12.7 deep, .204 [5.18] high | 12.7 | |
| Pin tail below the base | .137 ± .015 [3.47 ± .38] | — | 1.9 mm through a 1.6 mm board |

The decisive difference from the 12-way: **the `-R004` flange stands perpendicular to the
board**. Section B-B shows the pins leaving the rear of the flange horizontally and bending
down into the board; the flange itself reaches **4.4 mm below the board's top surface**
(flange centre 12.1 mm above the base, half-height 16.5). The board edge must therefore lie
between the rear pad row and the flange rear face, and the flange plus housing hang beyond
the edge. **Nothing but the eight pins retains the connector on the board**; the four slots
are panel-mount features. S9 has to provide a bracket or panel for them (the adapter-plate
idea in `ARCHITECTURE.md` §7 can grow a tab).

### 1.3 Footprint `DEUTSCH_DTM13-08PA-R004_Horizontal`

Origin at the pin-field centre, mating face toward +y (same convention as S7's 12-way):

- pads: row 1–4 at y = **+3.175** (nearer the flange), row 5–8 at y = **−3.175**;
  x = −6.2865 / −2.0955 / +2.0955 / +6.2865 for pins 1→4 and 8→5. Drill 1.3, pad 2.0, pin 1 square.
- flange rear face at y = +7.495 (3.175 + 4.32); flange x = −17.68 … +50.90; housing to y = +25.5.
- `Dwgs.User` line at **y = +6.35 = the recommended board edge** (1.15 mm from the nominal
  flange face, which covers the drawing's ±0.64 general tolerance plus the ±0.38 on the pin
  offset); pad copper ends at y = 4.175.
- courtyard = on-board base block **and** the overhang envelope, so a wrongly placed edge
  shows up in DRC.

**Cavity numbering** comes straight from the 8-way drawing, which — unlike the 12-way — labels
the pins: rear view (looking at the flange from inside the board) bottom row 1–4 left→right,
top row 8–5 left→right. Mapped through the section (the lower cavity row exits nearer the
flange) and the view transform, that puts pin 1 at −x in the near row. Like J3/J4 it should be
confirmed on a real `DTM06-08SA` before a harness is crimped; the board, symbol and footprint
are self-consistent either way.

### 1.4 Pin assignment

Physically adjacent cavity pairs in a 4 × 2 DTM are (1,8), (2,7), (3,6), (4,5). Every function
gets one such pair so its return is next to it:

| Cav | Net | Cav | Net | Function |
|---|---|---|---|---|
| 1 | `CAN_H` | 8 | `CAN_L` | CAN pair, unshielded twisted pair |
| 2 | `+5V_VEH` | 7 | `GND` | ECU isolated-side supply (**provisional**) |
| 3 | `SW_MAIN_IN` | 6 | `SW_MAIN_RTN` | FSAE shutdown circuit, car-referenced, hardwired (not via the ECU) |
| 4 | `SW_START_IN` | 5 | `SW_START_RTN` | start button, car-referenced |

No shield pin: the CAN link is a ~1 m in-car twisted pair and the DTM has no shell. If a
shielded cable is ever used, its shield terminates at the ECU end only — our domain floats.

---

## 2. CAN

### 2.1 Topology (provisional, from the S8 user decisions)

Dedicated 2-node link to the ECU; the galvanic barrier is on the ECU side (AM06 used an
ISO1050; the next revision may use ISO1042 or an ISOW1044 with its own DC/DC). Our node is
the non-isolated reference that the ECU's bus side follows. Two nodes ⇒ both ends terminated
⇒ our 120 Ω is **fitted by default**.

### 2.2 Parts and values

| Ref | Part | Why |
|---|---|---|
| U18 | **SN65HVD230DR** (C12084, JLC **Preferred**, 91 835 in stock) | 3.3 V CAN transceiver, no 5 V rail needed, RS pin. TCAN332/337 are 5–10× the price with 3–5 k stock; SN65HVD232 has no RS pin |
| R120 | 10 kΩ on RS → GND | **slope-control mode, ≈15 V/µs** (datasheet §10.4.2 and Fig. 33). 0 Ω = high-speed mode, 100 kΩ = 2 V/µs. RS > 0.75 V_CC = standby, never wanted here |
| R121 | 10 kΩ TXD pull-up to +3V3 | datasheet §10.4 layout note: the internal bias on D is weak; with the LaunchPad unplugged a floating D could hold the bus **dominant**. Pull-up = recessive = bus free |
| R122 + JP6 | 120 Ω through a **bridged** solder jumper | fitted at assembly, cut the bridge to remove. A split termination (2 × 60 Ω + C) was rejected: with a single series jumper it degenerates into an asymmetric 60 Ω + C stub on one line when opened |
| L3 | **ACT45B-101-2P-TL003** (C88056), 100 µH common-mode, 150 mA, AEC-Q200 | the board sits on a 900 V inverter; TDK's CAN-bus part. Windings 1–4 / 2–3, in line between U18 and the connector |
| D13 | **PSM712** (C32677, JLC **Basic**) | dual asymmetric TVS, +12 V / −7 V standoff on each line = exactly the ISO 11898 common-mode window. At the connector side of L3 |
| C116 / C117 | 100 nF + 1 µF on V_CC | datasheet §11 |
| R121, U18 pin 5 | V_ref left no-connect | not used |

Nets: `CAN_H`/`CAN_L` (connector side, with TVS, termination, TP49/TP50) and
`CAN_H_XCVR`/`CAN_L_XCVR` (transceiver side of the choke). `CAN_TX_3V3` = GPIO4 (J4-36),
`CAN_RX_3V3` = GPIO5 (J4-35), both on J21 with the two switch inputs — the one socket that
carries no analog.

---

## 3. The two isolated cockpit inputs

### 3.1 What they see

The AM06 ECU schematic (reference only) runs on **+12 V**, so the car's GLV and the shutdown
circuit are 12 V nominal (10–14.4 V on a lead-acid / LiFePO4 pack). Our logic 24 V is a
separate battery not bonded to the car (S8 user statement), so both inputs are **car-referenced
signals crossing into a floating domain** and must be optically isolated. Their returns are
their own connector pins (car GND) and touch nothing on the board.

### 3.2 Opto and drive

| Candidate | Result |
|---|---|
| PC817C | Extended at JLC, 3–4 µs at 100 Ω |
| **LTV-817S-TA1-C** (C109227) | **JLC Basic**, 598 k stock, SMD, 5 kV, **CTR rank C = 200–400 %** at 5 mA, same tr/tf. **Chosen** |
| TLP2361 / 6N137 / H11L1 | logic-output optos: fast, but all **inverting** (LED on → output LOW). Fail-safe needs "no light = LOW" and a non-inverting path from pin to GPIO (S5's hidden-inversion rule), so an inverter would be needed. Rejected |

LED chain: **2 × 2.2 kΩ (4.4 kΩ)** in series with the LED, **1N4148W anti-parallel** across the
LED (its reverse rating is 6 V; a reversed harness must not kill it):

| V_in | I_F | P per 0603 (0.1 W) | I_C available (CTR 200 %, worst case ~70 % of the 5 mA figure at low I_F) |
|---|---|---|---|
| 8 V | 1.55 mA | 5 mW | ≈ 2.2 mA |
| 12 V | 2.45 mA | 13 mW | ≈ 3.7 mA |
| 14.4 V | 3.0 mA | 20 mW | ≈ 4.5 mA |
| 24 V | 5.2 mA | 59 mW | 10 mA |
| 30 V | 6.5 mA | 93 mW (edge of rating — use 2 × 3.3 kΩ if the car ever runs 24 V GLV) | 13 mA |

### 3.3 Output side — fail-safe by construction

**High-side phototransistor**: collector to +3V3, emitter to the node, **2.2 kΩ pull-down**.
Saturation needs 3.1 V / 2.2 kΩ = **1.4 mA**; the 8 V worst case supplies ≥ 2.2 mA (1.5×),
12 V gives 2.6×. LED off, harness unplugged, wire broken, opto dead — every failure reads
**0 V = LOW = `SW_MAIN_3V3` LOW = gate enable withheld** at `gate_drive` U8 input C. A
common-emitter arrangement would have inverted that.

**Timing.** S4 banned filtering on this path because it delays de-assertion, the unsafe
direction. The only delay here is the phototransistor's own fall time into 2.2 kΩ: the
datasheet specifies 3/4 µs at R_L = 100 Ω and the fall time scales roughly with R_L, so expect
**a few tens of microseconds** — under one 100 µs PWM period, and orders of magnitude under the
contactor drop-out the shutdown circuit actually commands. No RC anywhere on the path.

**Schmitt buffer U21 (SN74LVC2G17, C10429, one dual package for both channels).** A 20 µs
edge into a plain LVC input violates the family's 10 ns/V input transition-rate limit by
three orders of magnitude and can cause multiple output transitions; the Schmitt input turns
it into one clean edge. Non-inverting, so pin polarity = GPIO polarity. Its two outputs are
`SW_MAIN_3V3` (→ `launchpad` J21-20 = GPIO29 **and** `gate_drive` JP1) and `SW_START_3V3`
(→ J21-14 = GPIO59), each with a test point.

Both channels are drawn geometrically identical (S7.5 rule); the START input is meant to be
driven from car GLV through the button — **never from `+5V_VEH`**, which would bond the
domains through the LED.

---

## 4. `+5V_VEH` — the ECU isolated-side supply (PROVISIONAL)

If the ECU powers its isolated transceiver's bus side from us (AM06 did: `VCC2` ← inverter
+5 V), cavity 2/7 is that feed. Budget ≈ 75 mA worst case on `+5V` (S8 log).

`+5V` → **D16 SS34** (C8678, Basic) → **F3 polyfuse 1206L020/30NR** (C7542932, 0.2 A hold /
0.46 A trip, 30 V) → node with **D17 SMAJ5.0A** (C2925443, Preferred) and **C119 100 nF** → J5.2.

- **Short tolerance**: the polyfuse. Its initial resistance (~0.9 Ω typ, 2.7 Ω max after a
  trip) drops 0.07 V at 75 mA.
- **Why D16 exists**: without it a mis-wired 12 V on the pin reaches the `+5V` rail — the
  polyfuse only limits current, and the TVS at the pin would hold the rail near 6.4–7 V
  (OPA2376, LVC parts and the buck are all over their absolute maximum there). With D16 nothing
  on the harness can back-feed the board; the TVS clamps surges on the pin side.
- **The price**: SS34 V_F ≈ 0.25–0.3 V at 75 mA. Expect **4.6–4.75 V at the connector**
  (4.984 − 0.07 − 0.27 − harness). That is inside **ISO1042 / ISOW1044 (4.5–5.5 V)** but
  **below ISO1050's 4.75 V minimum**. Publish this to the ECU team as part of the interface
  contract; fit 0 Ω in D16's place only if they need a full 5 V and guarantee no back-feed.

---

## 5. Library additions (S8)

Six symbols (51 → 57, all standalone definitions, each checked for `extends` before copying,
LCSC property added) and five footprints (42 → 47). Validated **57/57 symbols (59 SVGs) and
47/47 footprints** with `kicad-cli … export svg`.

| Symbol | Source | Footprint |
|---|---|---|
| `SN65HVD230` | KiCad `Interface_CAN_LIN` | `SOIC-8_3.9x4.9mm_P1.27mm` (existing) |
| `LTV-817S` | KiCad `Isolator` | **`Optocoupler_LTV-817S_SMD-4P`** — land from Lite-On BNS-OD-C131/A4 p.12: pads 1.5 × 1.3, 2.54 pitch, rows 9.0 mm apart; body 4.6 × 6.5 |
| `SolderJumper_2_Bridged` | KiCad `Jumper` | `SolderJumper-2_P1.3mm_Bridged_Pad1.0x1.5mm` (copied) |
| `D_TVS_Dual_CAN` | KiCad `Power_Protection:NUP2105L` renamed (same SOT-23 pinout as PSM712: 1/2 lines, 3 GND) | `SOT-23` (existing) |
| `Conn_02x04_Counter_Clockwise` | KiCad `Connector_Generic` — 1..4 / 8..5 = the DTM 8-way cavity order | **`DEUTSCH_DTM13-08PA-R004_Horizontal`** (§1.3) |
| `L_CommonMode` | KiCad `Filter:Choke_CommonMode_FerriteCore_1423` renamed — windings 1–4 / 2–3 = ACT45B | **`L_CommonMode_TDK_ACT45B`** — land from TDK `cmf_automotive_signal_act45b` p.5: four pads 1.35 × 0.9, outer 5.9 × 3.4, inner 3.2 × 1.6 |
| (1N4148W uses `D`) | — | `D_SOD-123` (copied) |

Datasheets saved: `datasheets/LiteOn-LTV-817-series.pdf`, `datasheets/TDK-ACT45B_cmf_automotive_signal.pdf`, `datasheets/TI-SN65HVD230.pdf`.

---

## 6. Capture and verification

`vehicle_io`: 30 components (32 symbol instances, U21 has three units), 71 wire segments,
38 labels, five text notes. Parts were added through the MCP server, normalised with
`canon.py`, and laid out by `tools/schematic_layout/vio_layout.py` under the S7.5 rules
(signal flow left → right, J5 at the left as the vehicle side, the MCU-side labels at the right,
both switch channels drawn identically, labels only where a wire would have to cross).

**Netlist** (`kicad-cli sch export netlist`, diffed with `netcmp.py`): 201 → **220 nets,
835 → 914 nodes**. +79 nodes = every pin of the 32 instances; +19 nets = 18 real + one
no-connect pseudo-net (U18 V_ref). Every new net's membership, node by node:

| Net | Members |
|---|---|
| `/vehicle_io/+5V_VEH` | C119.1, D17.1 (K), F3.1, J5.2 |
| `/vehicle_io/CAN_H` | D13.1, J5.1, L3.1, R122.2, TP49.1 |
| `/vehicle_io/CAN_L` | D13.2, J5.8, JP6.1, L3.2, TP50.1 |
| `/vehicle_io/CAN_H_XCVR` / `CAN_L_XCVR` | L3.4 + U18.7 / L3.3 + U18.6 |
| `/vehicle_io/CAN_RS` | R120.1, U18.8 |
| `/vehicle_io/SW_MAIN_RTN` / `SW_START_RTN` | D14.2 (A), J5.6, U19.2 (K) / D15.2, J5.5, U20.2 |
| `Net-(D14-K)` / `Net-(D15-K)` | D14.1, R124.2, U19.1 (A) / D15.1, R127.2, U20.1 |
| `Net-(J5-Pin_3)` → `Net-(R123-Pad2)` | J5.3 + R123.1 → R123.2 + R124.1 (START: J5.4/R126/R127) |
| `Net-(R125-Pad1)` / `Net-(R128-Pad1)` | R125.1, U19.3 (E), U21.1 / R128.1, U20.3, U21.3 |
| `Net-(JP6-B)` / `Net-(D16-K)` | JP6.2 + R122.1 / D16.1 + F3.2 |
| `+3V3` gained | C116.1, C117.1, C118.1, R121.1, U18.3, U19.4, U20.4, U21.5 |
| `+5V` gained / `GND` gained | D16.2 / C116-119.2, D13.3, D17.2, J5.7, R120.2, R125.2, R128.2, U18.2, U21.2 |
| `/CAN_TX_3V3` / `/CAN_RX_3V3` gained | R121.2 + U18.1 / U18.4 |
| `/SW_MAIN_3V3` / `/SW_START_3V3` gained | TP51.1 + U21.6 / TP52.1 + U21.4 |

**ERC** (`kicad-cli sch erc --severity-all`): **0 violations on the whole project** — the 13
root-sheet label warnings that were waiting for this sheet are gone, and no other class appeared.
`golden.net` re-baselined to 220 / 914 in the same commit.

---

## 7. Pin-map cross-check — netlist side

Method: from the exported netlist, every net touching a socket pin `J2x.n` was mapped to its
TI header pin through the S8 socket rule (symbol pin 2k−1 / 2k = row k of the SPRUI77 table
printed for that socket: J20 = J1 + J3, J21 = J4 + J2, J22 = J5 + J7, J23 = J8 + J6), then to
the MCU function printed in SPRUI77 Tables 1–4 (transcribed from `pdftotext`), and compared
with the firmware pin map. **29 of 29 expected signals found on the expected MCU pin, 0
mismatches; the remaining 47 socket pins are explicit no-connects.** The table:

| Net | MCU pin (SPRUI77) | BoosterPack pin | Socket.pin | Check | Other members |
|---|---|---|---|---|---|
| `+5V_LP` | 5V | J3-21 | J20.2 | OK | C114.1, C115.1, D12.2, TP45.1 |
| `+5V_LP` | 5V | J7-61 | J22.2 | OK | C114.1, C115.1, D12.2, TP45.1 |
| `CAN_RX_3V3` | GPIO5 | J4-35 | J21.11 | OK | U18.4 |
| `CAN_TX_3V3` | GPIO4 | J4-36 | J21.9 | OK | R121.2, U18.1 |
| `DRV_EN_3V3` | GPIO66 | J6-59 | J23.4 | OK | R30.1, U8.1 |
| `DRV_EN_AUX_3V3` | GPIO131 | J6-58 | J23.6 | OK | R31.1, U8.3 |
| `ENC_COS_ADC` | ADCINB2 | J3-28 | J20.16 | OK | C110.1, D11.3, R117.2, TP41.1 |
| `ENC_SIN_ADC` | ADCINA2 | J3-29 | J20.18 | OK | C107.1, D10.3, R112.2, TP40.1 |
| `FLT_OC_A_3V3` | GPIO25 | J6-51 | J23.20 | OK | TP24.1, U9.6 |
| `FLT_OC_B_3V3` | GPIO27 | J6-52 | J23.18 | OK | TP25.1, U9.4 |
| `FLT_OC_C_3V3` | GPIO26 | J6-53 | J23.16 | OK | TP26.1, U10.6 |
| `FLT_OT_3V3` | GPIO64 | J6-54 | J23.14 | OK | TP27.1, U10.4 |
| `FLT_OV_3V3` | GPIO52 | J5-48 | J22.15 | OK | TP28.1, U11.6 |
| `GND` | GND | J3-22 | J20.4 | OK | C1.2, C10.2, C100.2, C101.2, C102.2, C103.2 … |
| `GND` | GND | J2-20 | J21.2 | OK | C1.2, C10.2, C100.2, C101.2, C102.2, C103.2 … |
| `GND` | GND | J7-62 | J22.4 | OK | C1.2, C10.2, C100.2, C101.2, C102.2, C103.2 … |
| `GND` | GND | J6-60 | J23.2 | OK | C1.2, C10.2, C100.2, C101.2, C102.2, C103.2 … |
| `ISNS_A_ADC` | ADCINB4 | J7-68 | J22.16 | OK | C68.1, R74.2 |
| `ISNS_B_ADC` | ADCINC4 | J7-67 | J22.14 | OK | C75.1, R86.2 |
| `ISNS_C_ADC` | ADCINA5 | J7-66 | J22.12 | OK | C82.1, R98.2 |
| `ISNS_REF_A_ADC` | ADCINA4 | J7-69 | J22.18 | OK | C85.1, R101.2 |
| `ISNS_REF_B_ADC` | ADCINB5 | J7-65 | J22.10 | OK | C86.1, R102.2 |
| `ISR_PROBE_3V3` | GPIO67 | J1-5 | J20.9 | OK | TP48.1 |
| `NTC_1_ADC` | ADCINC3 | J3-24 | J20.8 | OK | C61.1, R62.2, TP23.1 |
| `PWM_UH_3V3` | GPIO6 | J8-80 | J23.1 | OK | R36.1, U5.2 |
| `PWM_UL_3V3` | GPIO7 | J8-79 | J23.3 | OK | R37.1, U5.4 |
| `PWM_VH_3V3` | GPIO8 | J8-78 | J23.5 | OK | R38.1, U6.2 |
| `PWM_VL_3V3` | GPIO9 | J8-77 | J23.7 | OK | R39.1, U6.4 |
| `PWM_WH_3V3` | GPIO10 | J8-76 | J23.9 | OK | R40.1, U7.2 |
| `PWM_WL_3V3` | GPIO11 | J8-75 | J23.11 | OK | R41.1, U7.4 |
| `SW_MAIN_3V3` | GPIO29 | J2-11 | J21.20 | OK | JP1.1, TP51.1, U21.6 |
| `SW_START_3V3` | GPIO59 | J2-14 | J21.14 | OK | TP52.1, U21.4 |
| `VBUS_ADC` | ADCINC2 | J3-27 | J20.14 | OK | C59.1, R59.2, TP20.1 |

`hw_control_v2.h` at HEAD still carries `MODULE_FAULT_ACTIVE_LOW 1U`, `ISENSE_NUM_CHANNELS 2`,
`RES_SINCOS_BIAS_CODE 3072` / `AMPL_CODE 990` and no CAN or switch pins — all already listed
as S12 handoff items; nothing new.

---

## 8. BOM / JLCPCB audit (live query, 2026-09-01)

`kicad-cli sch export bom --group-by LCSC,Value --exclude-dnp`, every `C…` code resolved
against the JLCSearch API (`/api/search?q=<code>`; `C25804` only answers through the
resistors endpoint):

| | |
|---|---|
| BOM lines (grouped) | 135 |
| Purchasable placements / unique LCSC codes | **293 / 63** |
| Unique codes by JLC type | **29 Basic · 4 Preferred · 30 Extended** (≈ $90 of Extended setup fees) |
| Part cost, one board, qty-1 prices | ≈ $28 |
| `NOFIT` placements (test points, jumpers, net ties, holes, flags) | 62 |
| `CONSIGNED` | J1 Mini-Fit Jr, J2 DB37, J3/J4 DTM13-12P, J5 DTM13-08P |
| Empty `LCSC` fields | **0** (U9–U11 units 2/3 lacked the field; fixed) |

**Findings**

1. **`C107043` (2.2 nF C0G 0603, used ×10 on the matched anti-alias RCs of `current_sense`
   and `encoder`) shows 4 in stock** in both the `/api/search` snapshot and the MCP's local
   database, while the `capacitors/list` endpoint reports 88 976. The two endpoints disagree on
   every part checked (e.g. the Murata alternative: 2 265 vs 24 839). Rather than guess which
   is current, the ten parts were moved to **`C77033` GRM1885C1H222JA01D** (Murata C0G 50 V 5 %,
   the same family as the kit's 4.7 nF and 22 nF lines), which is the better of the two under
   the pessimistic source. **S12 verifies live** before ordering.
2. Low stock under the pessimistic source, for S12: `C5369735` URA2415YMD-6WR3 **362**
   (known), `C5219272` TPS62933F 2 255, `C870760` 47.0 Ω 0.1 % 4 210, `C15857` L1 22 µH 4 688.
3. Value-string hygiene: the encoder and launchpad sheets used `10u` / `100n` / `1nF` where the
   rest of the project writes `10uF 25V` / `100nF 50V` / `1nF C0G`; normalised per LCSC line so
   the grouped BOM has one line per part.

Full table:

| Refs | Value | LCSC | MPN | Pkg | JLC | Stock | $ (1 pc) | Qty |
|---|---|---|---|---|---|---|---|---|
| FB1 | 600R@100MHz | C1017 | GZ2012D601TF | 0805 | Basic | 369732 | 0.0326 | 1 |
| U19,U20 | LTV-817S-TA1-C | C109227 | LTV-817S-TA1-C | SMD-4P | Basic | 597938 | 0.0749 | 2 |
| C2,C3,C5,C9,C10,C14,C23,C36,C92,C94 | 10uF 50V | C13585 | CL31A106KBHNNNE | 1206 | Basic | 1877266 | 0.1757 | 10 |
| C4,C8,C11,C12,C15,C19,C22,C24,C26,C28,C30,C32,C34,C35,C54-C56,C84,C87-C90,C93,C95,C98,C103,C111,C115,C116,C118,C119 | 100nF 50V | C14663 | CC0603KRX7R9BB104 | 0603 | Basic | 12618106 | 0.0106 | 31 |
| C6 | 1uF 50V | C15849 | CL10A105KB8NNNC | 0603 | Basic | 5979916 | 0.0297 | 1 |
| C16-C18,C20,C21,C25,C27,C97,C114 | 10uF 25V | C15850 | CL21A106KAYNNNE | 0805 | Basic | 3505306 | 0.0773 | 9 |
| C13 | 47nF 50V | C1622 | CL10B473KB8NNNC | 0603 | Basic | 414711 | 0.0087 | 1 |
| R12,R103,R119 | 0R | C21189 | 0603WAF0000T5E | 0603 | Basic | 6153233 | 0.0019 | 3 |
| R33 | 1k | C21190 | 0603WAF1001T5E | 0603 | Basic | 8013731 | 0.0039 | 1 |
| R18-R23,R74,R86,R98,R101,R102,R112,R117 | 100R | C22775 | 0603WAF1000T5E | 0603 | Basic | 7325193 | 0.0023 | 13 |
| R122 | 120R | C22787 | 0603WAF1200T5E | 0603 | Basic | 1475830 | 0.0016 | 1 |
| R6,R60 | 12k | C22790 | 0603WAF1202T5E | 0603 | Basic | 442690 | 0.0035 | 2 |
| R5 | 150k | C22807 | 0603WAF1503T5E | 0603 | Basic | 414154 | 0.0014 | 1 |
| R15 | 1.5k | C22843 | 0603WAF1501T5E | 0603 | Basic | 1163865 | 0.0012 | 1 |
| D4 | red +24V_PROT | C2286 | KT-0603R | 0603 | Basic | 8154450 | 0.0073 | 1 |
| D5 | red +13V5_GATE | C2286 | KT-0603R | 0603 | Basic | 8154450 | 0.0073 | 1 |
| D6 | red +5V | C2286 | KT-0603R | 0603 | Basic | 8154450 | 0.0073 | 1 |
| D7 | red +3V3 | C2286 | KT-0603R | 0603 | Basic | 8154450 | 0.0073 | 1 |
| D8 | red +15V_ISO | C2286 | KT-0603R | 0603 | Basic | 8154450 | 0.0073 | 1 |
| D9 | RED GATE_EN | C2286 | KT-0603R | 0603 | Basic | 8154450 | 0.0073 | 1 |
| R35,R67,R77,R89,R104,R118 | 1M | ⚠ C22936 → **C22935** | ~~0603WAF100KT5E~~ **0603WAF1004T5E** | 0603 | Basic | 8062164 | 0.00096 | 6 |
<!-- 2026-09-17: C22936 is 1 Ω, NOT 1 MΩ. Corrected part is C22935. See JLC_PARTS.md. -->
| R59,R62 | 3.3k | C22978 | 0603WAF3301T5E | 0603 | Basic | 1199741 | 0.0019 | 2 |
| R14,R30-R32,R36-R46,R52-R56,R61 | 4.7k | C23162 | 0603WAF4701T5E | 0603 | Basic | 7433362 | 0.0015 | 21 |
| R17 | 6.8k | C23212 | 0603WAF6801T5E | 0603 | Basic | 368873 | 0.0018 | 1 |
| R16,R34 | 680R | C23228 | 0603WAF6800T5E | 0603 | Basic | 923432 | 0.0013 | 2 |
| R1,R2,R8 | 100k | C25803 | 0603WAF1003T5E | 0603 | Basic | 7990119 | 0.0016 | 3 |
| R3,R11,R13,R24-R29,R47-R51,R120,R121 | 10k | C25804 | 0603WAF1002T5E | 0603 | Basic | 37165617 | 0.0039 | 16 |
| C29,C31,C33,C57,C83,C91,C101,C102,C104,C112,C117 | 1uF 50V | C28323 | CL21B105KBFNNNE | 0805 | Basic | 2084641 | 0.0469 | 11 |
| D13 | PSM712 | C32677 | PSM712-LF-T7 | SOT-23 | Basic | 317834 | 0.3233 | 1 |
| R123-R128 | 2.2k | C4190 | 0603WAF2201T5E | 0603 | Basic | 2001135 | 0.0014 | 6 |
| R9 | 33k | C4216 | 0603WAF3302T5E | 0603 | Basic | 696981 | 0.0013 | 1 |
| U3 | AMS1117-3.3 | C6186 | AMS1117-3.3 | SOT-223 | Basic | 2007447 | 0.2003 | 1 |
| D14,D15 | 1N4148W | C81598 | 1N4148W | SOD-123 | Basic | 3538406 | 0.0113 | 2 |
| D12,D16 | SS34 | C8678 | SS34 | SMA(DO-214AC) | Basic | 3557042 | 0.0303 | 2 |
| U18 | SN65HVD230DR | C12084 | SN65HVD230DR | SOIC-8 | Preferred | 91835 | 0.6898 | 1 |
| D2 | BZX84C15 | C19077472 | BZX84C15 | SOT-23 | Preferred | 11303 | 0.0193 | 1 |
| D17 | SMAJ5.0A | C2925443 | SMAJ5.0A | SMA(DO-214AC) | Preferred | 64985 | 0.0388 | 1 |
| D10,D11 | BAT54S | C7420333 | BAT54S | SOT-23 | Preferred | 314690 | 0.0126 | 2 |
| U9-U11,U21 | SN74LVC2G17DBVR | C10429 | SN74LVC2G17DBVR | SOT-23-6 | Extended | 107122 | 0.3346 | 4 |
| C37-C53,C58,C60,C64,C65,C70,C72,C77,C79,C96,C99,C100,C113 | 1nF C0G | C106246 | CC0603JRNPO9BN102 | 0603 | Extended | 127722 | 0.0075 | 29 |
| R105 | 3.00k 0.1% | C136963 | RT0603BRD073KL | 0603 | Extended | 30010 | 0.0287 | 1 |
| L1 | 22uH | C15857 | SWPA8040S220MT | SMD,8x8mm | Extended | 4688 | 0.1601 | 1 |
| L2 | 3.3uH | C167960 | FNR5040S3R3NT | SMD,5x5mm | Extended | 5331 | 0.0599 | 1 |
| F2 | 3A 63V | C182445 | 12H1300C | 1206 | Extended | 43061 | 0.0384 | 1 |
| U8 | SN74LVC1G11DBVR | C22046 | SN74LVC1G11DBVR | SOT-23-6 | Extended | 10443 | 0.1829 | 1 |
| R10 | 52.3k | C23198 | 0603WAF5232T5E | 0603 | Extended | 151199 | 0.000985714 | 1 |
| C1 | 100uF 50V | C2836439 | RVT100UF50V67RV0040 | SMD,D8xL10.2mm | Extended | 42082 | 0.0842 | 1 |
| D1 | SMCJ26A | C310042 | SMCJ26A/TR13 | SMC(DO-214AB) | Extended | 7293 | 0.1444 | 1 |
| R65,R66,R70,R71,R76,R79,R82,R83,R88,R91,R94,R95,R99,R107,R109,R111,R114,R116 | 12.0k 0.1% | C326735 | RT0603BRD0712KL | 0603 | Extended | 10395 | 0.0321 | 18 |
| Q1 | SQD50P06-15L | C3281500 | SQD50P06-15L_GE3 | TO-252 | Extended | 7471 | 1.4259 | 1 |
| U12-U17 | OPA2376 | C46316 | OPA2376AIDR | SOIC-8 | Extended | 10213 | 0.9762 | 6 |
| U5-U7 | UCC27524DR | C465729 | UCC27524DR | SOIC-8 | Extended | 9550 | 0.4035 | 3 |
| F1 | 5A 125V | C48467 | 0451005.MRL | 2410 | Extended | 28138 | 0.2563 | 1 |
| J20 | LaunchPad J1+J3 | C5116528 | PM2.54-2*10 | 插件,P=2.54mm | Extended | 10241 | 0.2185 | 1 |
| J21 | LaunchPad J4+J2 | C5116528 | PM2.54-2*10 | 插件,P=2.54mm | Extended | 10241 | 0.2185 | 1 |
| J22 | LaunchPad J5+J7 | C5116528 | PM2.54-2*10 | 插件,P=2.54mm | Extended | 10241 | 0.2185 | 1 |
| J23 | LaunchPad J8+J6 | C5116528 | PM2.54-2*10 | 插件,P=2.54mm | Extended | 10241 | 0.2185 | 1 |
| U2 | TPS62933FDRLR | C5219272 | TPS62933FDRLR | SOT-583 | Extended | 2255 | 1.0787 | 1 |
| U4 | URA2415YMD-6WR3 | C5369735 | URA2415YMD-6WR3 | DIP,25.4x25.4mm | Extended | 362 | 6.3753 | 1 |
| R58 | 1.50k 0.1% | C705741 | RT0603BRD071K5L | 0603 | Extended | 8319 | 0.0318 | 1 |
| R72,R73,R84,R85,R96,R97,R100,R106 | 4.99k 0.1% | C723532 | RT0603BRD074K99L | 0603 | Extended | 47194 | 0.0318 | 8 |
| R63,R64,R75,R78,R87,R90 | 20.0k 0.1% | C723637 | RT0603BRD0720KL | 0603 | Extended | 121239 | 0.0316 | 6 |
| F3 | 0.2A 30V 1206L020 | C7542932 | 1206L020/30NR | 1206 | Extended | 141752 | 0.0393 | 1 |
| C62,C63,C69,C71,C76,C78,C105,C106,C108,C109 | 2.2nF C0G | C77033 | GRM1885C1H222JA01D | 0603 | Extended | 2265 | 0.0228 | 10 |
| C59,C61,C68,C75,C82,C85,C86,C107,C110 | 22nF C0G | C77069 | GRM21B5C1H223JA01L | 0805 | Extended | 48685 | 0.0759 | 9 |
| U1 | LMR33630ADDAR | C841384 | LMR33630ADDAR | ESOP-8 | Extended | 9908 | 0.6947 | 1 |
| C66,C67,C73,C74,C80,C81 | 4.7nF C0G | C85980 | GRM1885C1H472JA01D | 0603 | Extended | 49830 | 0.0222 | 6 |
| R57 | 2.20k 0.1% | C861295 | RT0603BRD072K2L | 0603 | Extended | 78470 | 0.0329 | 1 |
| R68,R69,R80,R81,R92,R93 | 47.0R 0.1% | C870760 | RT1206BRD0747RL | 1206 | Extended | 4210 | 0.0809 | 6 |
| L3 | ACT45B-101-2P-TL003 | C88056 | ACT45B-101-2P-TL003 | SMD-4P,4.5x3.2mm | Extended | 38604 | 0.3396 | 1 |
| R108,R110,R113,R115 | 10.0k 0.1% | C95204 | RT0603BRD0710KL | 0603 | Extended | 389486 | 0.0241 | 4 |

**Not purchasable at JLC (consigned / no part):**

| Refs | Value |
|---|---|
| J1 | Mini-Fit Jr 5566-02A |
| J2 | DSUB-37_Socket |
| J3 | LEM DTM13-12PA-R005 key A |
| J4 | ENC DTM13-12PB-R005 key B |
| J5 | VEH DTM13-08PA-R004 key A |

**NOFIT (test points, jumpers, net ties, mounting holes, flags): 62 placements**
- JP1 — ILOCK_SEL
- JP2 — SHLD_TIE
- JP3 — SRC SEL A
- JP4 — SRC SEL B
- JP5 — SRC SEL C
- JP6 — CAN TERM bridged=120R
- NT1 — ISO_COM-GND
- NT2 — PGND_MOD-GND star
- NT3 — VBUS_RTN_TIE
- NT4 — ISNS_RTN-GND
- TP1 — +24V_PROT
- TP2 — +13V5_GATE
- TP3 — +5V
- TP4 — +3V3
- TP5 — +24V_MOD
- TP6 — +15V_ISO
- TP7 — -15V_ISO
- TP8,TP37 — ISO_COM
- TP9,TP46,TP47 — GND
- TP10 — TP_PWM_UH
- TP11 — TP_PWM_UL
- TP12 — TP_PWM_VH
- TP13 — TP_PWM_VL
- TP14 — TP_PWM_WH
- TP15 — TP_PWM_WL
- TP16 — TP_GATE_EN
- TP17 — TP_MOD15V_1
- TP18 — TP_MOD15V_2
- TP19 — TP_VBUS_RAW
- TP20 — TP_VBUS_ADC
- TP21 — TP_VBUS_RTN
- TP22 — TP_NTC_RAW
- TP23 — TP_NTC_ADC
- TP24 — TP_FLT_OC_A
- TP25 — TP_FLT_OC_B
- TP26 — TP_FLT_OC_C
- TP27 — TP_FLT_OT
- TP28 — TP_FLT_OV
- TP29 — TP_FLT_OC_A_15V
- TP30 — ISNS_A_INT
- TP31 — ISNS_A_LEM
- TP32 — ISNS_B_INT
- TP33 — ISNS_B_LEM
- TP34 — ISNS_C_INT
- TP35 — ISNS_C_LEM
- TP36 — ISNS_VREF
- TP38 — ENC_SIN_RAW
- TP39 — ENC_COS_RAW
- TP40 — ENC_SIN_ADC
- TP41 — ENC_COS_ADC
- TP42 — ENC_VREF3V
- TP43 — ENC_VREF_HI
- TP44 — ENC_VDD
- TP45 — +5V_LP
- TP48 — ISR_PROBE_3V3
- TP49 — CAN_H
- TP50 — CAN_L
- TP51 — SW_MAIN_3V3
- TP52 — SW_START_3V3

---

## 9. Tooling findings (all fixed in `tools/schematic_layout/`)

1. **Vertical global labels: the justification, not the rotation, decides which side of the
   anchor the flag sits on.** Measured with a four-label test sheet: `(at x y 90) (justify left)`
   and `(… 270) (justify left)` both put the body *above* the anchor; `(justify right)` puts it
   *below*. The S7.5 helper `gnd(up=False)` emitted `90 / left`, so **every downward GND flag on
   every regenerated sheet was drawn over the part it hung from** — visible in the committed
   renders, unnoticed for a session because the netlist gate is blind to cosmetics. Fixed in
   `layoutlib.gnd()` / `shunt()` and in the two scripts that called `glab(…, 90)` by hand.
2. **KiCad transforms a field's justification with the symbol**: on a `mirror y` or 180°
   instance, `(justify right)` renders left-justified. `sheetedit.place()` now flips it.
3. **Inserting a missing `(justify …)` never worked** — the code searched for the closing
   line it had already cut off. MCP-written fields usually carry one, hand-written ones did not,
   which is why it was never noticed. Fixed.
4. **Note texts were addressed by file index**, and the file order of `(text …)` records
   changes on every regeneration. Re-running any S7.5 script on its own output scrambled the
   notes (10 of 10 on `module_status`). Now content-addressed: `Builder.text_by(prefix)` /
   `notes_by([...])`, with the prefixes derived from the committed positions. All six older
   sheets regenerate to **note positions identical to HEAD, netlist identical, ERC 0**.
5. `dump.py` reported the new sheet as "1 net, 87 unlabelled pins" — the same false alarm as
   on `launchpad`. `kicad-cli` is the gate; the local checker is not.
6. **Look at the rendered sheet.** `kicad-cli sch export svg` → `rsvg-convert` → crop and view.
   Two sessions of netlist-identical regenerations had shipped the label defect above.

---

## 10. Open items this session leaves

- **[S9] J5 retention and board edge** — bracket/panel for the four flange slots; board edge
  on the footprint's `Dwgs.User` line; the flange hangs 4.4 mm below the board.
- **[S9] CAN pair routing** as a pair from U18 through L3 to J5, D13 and R122 at the connector.
- **[S9] Netclass** — `CAN_*` nets sit on `Default`; decide whether they want a differential
  class. `*PWM_*_3V3` (S8 open item) unchanged.
- **[user / ECU team] `+5V_VEH` delivers 4.6–4.75 V** — ISO1042/ISOW1044 class only; confirm
  with the three provisional S8 interface decisions.
- **[user] Shutdown-circuit voltage** — designed for 8–30 V, sized for 12 V; if the car runs
  24 V GLV, change R123/R124/R126/R127 to 3.3 kΩ.
- **[user, before crimping] DTM 8-way cavity numbering** — confirm on a `DTM06-08SA`, like J3/J4.
- **[S12] JLC stock** — the C0G 2.2 nF line and the four low-stock lines above; the two
  JLCSearch endpoints disagree, verify against JLCPCB itself.
- **[cosmetic] `current_sense`** — the upward `ISO_COM` flags on R68/R69/C65/R73/C67 cross the
  wire of the row above; pre-existing, untouched here.
