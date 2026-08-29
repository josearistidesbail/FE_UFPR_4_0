# FE_UFPR 4.0 — System architecture (S2)

Frozen 2026-08-25 (S2). Scope: power tree + budget, LaunchPad power-domain policy,
grounding/shield policy, floorplan + connector plan, mechanical/mounting status, and the
root-sheet interface net table.

> **Amended 2026-08-29 (S3)** — three changes, all logged in the `CLAUDE.md` Decision Log:
> gate rail renamed `+12V_GATE` → **`+13V5_GATE`** (regulates to 13.566 V), new global net
> **`+24V_MOD`** for the fused module-aux pass-through, and **both switching converters replaced**
> (LMR33630 → TPS54360B, TPS62153 → TPS62933F) because neither original part can be forced out
> of light-load PFM. Derivations: [`S3_POWER_DESIGN.md`](S3_POWER_DESIGN.md).

Component-level design happens in S3–S8; this file is the contract those sessions implement.
Changes here after S2 require a Decision Log entry.

Sources: `../foc-f28379d-fsae/foc_f28379d/docs/infineon.md` (module electrical interface),
`datasheets/SPRUI77_LAUNCHXL-F28379D_users_guide.pdf` (LaunchPad UG, fetched in S2 —
jumper table §5.2, pinout tables 1–4, PCB layout §6.3), 3.0 as-built board file
(outline/connector geometry), CLAUDE.md conditioning targets.

---

## 1. Power domains & tree

```
+24V_IN  (vehicle LV, 18–30 V — Deutsch DT vehicle side / Mini-Fit Jr on board)
  │
  ├─ input protection (S3): fuse ~5 A → reverse-polarity P-FET → SMBJ33A TVS → bulk
  │      = +24V_PROT
  │
  ├─►[pass-through] +24V_PROT → F2 (3 A) → **+24V_MOD** → DB37 pins 8/26 (module aux, 40 W)
  │                  return: DB37 pins 10/28 → star point at 24 V entry   (no regulator in path)
  │
  ├─►Buck 1 **TPS54360B, 60 V** (S3):  +24V_PROT → **+13V5_GATE = 13.566 V**  (500 kHz, 47 µH)
  │      loads: 2× TC4468 gate drivers, PrimeSTACK PWM/EN inputs, (option) fault pull-up rail
  │      │
  │      └─►Buck 2 **TPS62933F, FCCM** (S3): +13V5_GATE → **+5V = 4.984 V** (1.2 MHz, 3.3 µH)
  │             loads: LaunchPad (via series Schottky), op-amp rail (ferrite/RC → clean 5 V),
  │                    encoder supply (filtered branch, S7), +3V3 LDO input
  │             │
  │             └─►LDO (S3): +5V → +3V3
  │                    loads: CAN transceiver, fault Schmitt/logic, GPIO-side pull-ups
  │
  └─►Isolated DC/DC **Mornsun URA2415YMD-6WR3, 6 W, 9–36 V in** (S3): +24V_PROT → +15V_ISO / −15V_ISO
         loads: 2–3× LEM LA 100-P (closed-loop). Secondary common ties to GND at ONE point
         in the analog partition (burden resistors are board-GND-referenced by necessity).
         **S3 CLOSED: one 6 W module, ±200 mA/rail** vs the ≈180 mA / 4 W load. Isolation kept
         so the ±15 V return stays inside the analog partition. Secondary commons to GND at NT1.
```

Rationale for the cascade (24→13.5→5→3.3 instead of parallel bucks off 24 V): the 5 V converter
is limited to 30 V in, the gate rail must exist anyway for the gate drivers, and the 5 V load
(~0.75 A) is small enough that double conversion loss (~0.5 W) is irrelevant next to the
noise benefit of one hot 24 V switcher instead of two.

**S3 amendment — light-load mode is the reason both converters changed.** The roadmap's
LMR33630 and TPS62153 both turned out to have **no MODE pin**, so neither can be forced out of
PFM/power-save, and a *load-dependent* burst rate lands in the band this board samples. The 5 V
rail feeds every analog front-end, so it now uses **TPS62933F (FCCM**, fixed 1.2 MHz at any load,
and the only family member without spread spectrum**)**. The gate rail uses **TPS54360B**, chosen
for its **60 V input rating** — the SMBJ33A TVS clamps at 53.3 V, which a 36 V part does not
survive — and sized (47 µH) to stay in CCM at the real 0.25–0.5 A load. Full derivation in
[`S3_POWER_DESIGN.md`](S3_POWER_DESIGN.md).

## 2. Power budget (S2 estimates — S3 replaces with computed numbers)

| Rail | Loads | Est. draw | Notes |
|---|---|---|---|
| 24 V pass-through | PrimeSTACK aux | **1.7 A @ 24 V, 2.2 A @ 18 V** (40 W) | copper + connector rating only, not through regulators |
| +13V5_GATE | 2× TC4468 quiescent+switching, 6 PWM + 2 EN module inputs, 5 fault pull-ups, **+5 V buck input (0.32 A)** | **~0.45 A** (0.25 A typ) | module input current unspecified in `infineon.md` — assumed ≤5 mA/input, bench-confirm during S4 |
| +5V | LaunchPad ≤500 mA (dual-core @200 MHz + its own 3V3 LDO), op-amps ~20 mA, encoder ~60 mA (bench item #8), 3V3 LDO input ~90 mA | ~0.7 A (3.5 W) | LaunchPad figure is a budget cap, not a measurement |
| +3V3 (board) | CAN transceiver (~70 mA dominant-TX), Schmitt + misc logic | ~90 mA | from +5V LDO |
| ±15V_ISO | per LA 100-P: 10 mA idle + Ip/2000 compensation (50 mA @ 100 Arms; 75 mA pk @ 150 A) | 3 sensors ≈ 180 mA avg → **~4 W in** | **S3 closed: URA2415YMD-6WR3, 6 W, ±200 mA/rail, 9–36 V in** |
| **Total input** | | **≈ 2.1 A @ 24 V / ≈ 2.9 A @ 18 V** | design current 3 A; fuse ~5 A; entry contacts ≥8 A (Mini-Fit Jr 9 A ✓, DT 13 A ✓) |

## 3. LaunchPad power-domain policy  **[DECIDED]**

3.0 hard-paralleled LaunchPad and board regulators. v4.0 uses TI's documented external-power
configuration (SPRUI77 §5.2 + Fig. 1 note):

- **Board powers the LaunchPad at 5 V** into the BoosterPack 5 V pins (J3-21, bridged to
  site 2 by JP5) **through a series Schottky** (S3 picks the part; SS34 class). The diode is
  belt-and-braces so a mis-jumpered LaunchPad + USB can never back-feed the board rail.
- **Jumper configuration (goes on silkscreen next to the headers, S8/S11):**

  | JP1 | JP2 | JP3 | JP4 | JP5 | JP6 |
  |---|---|---|---|---|---|
  | ✗ out | ✗ out | ✗ out | ✓ in | ✓ in | ✗ out |

  JP1/JP2/JP3 out = USB 3.3 V / **GND** / 5 V links opened → the XDS100v2 debugger side is
  fully galvanically isolated from the target while USB is plugged (TI's stated intent).
  JP4/JP5 in = MCU 3.3 V/5 V bridged to site-2 headers. JP6 stays out (only for USB-5V mode).
- **LaunchPad makes its own 3.3 V** from our 5 V (its TPS7B LDO). The header 3V3 pins
  (J1-1/J5-41) are **left unconnected** on the board (explicit no-connects in S8) — two
  regulators are never paralleled.
- **Board has its own small +3V3 LDO** so CAN + fault logic work with the LaunchPad removed
  (bench safety) and don't lean on the LaunchPad's LDO budget.
- SCI-A debug stays on the LaunchPad USB backchannel (GPIO42/43 via J11/J13 routing jumpers)
  — no board connector, as in the firmware docs.
- Bench item #10 is now a *verification* of the documented behavior (check no back-feed with
  the exact jumper set above), no longer a design input. **Bench item #11 is resolved on
  paper**: SPRUI77 Table 4 puts GPIO131 on header J6 pin 58 (GPIO66 on J6-59, GPIO130 on
  J6-57); only a continuity sanity check remains.

## 4. Grounding & returns  **[DECIDED — implements CLAUDE.md §Design rules]**

1. **One `GND` net, solid L2 plane.** No `A_GND` net anywhere. Analog integrity is layout
   discipline: the analog partition (current sense, encoder, Vbus front-ends) occupies its
   own plane region and no power/gate/digital return current may cross it (S9/S10 check).
2. **Star at the 24 V entry.** The module aux return (DB37 pins 10/28, the old `P_GND`) is
   routed as dedicated copper (L3 island/pour) from the DB37 straight to the entry-connector
   return pin — its ~2 A never flows through the plane under anything analog.
3. **Kelvin pairs** (S5/S6 implement, S11 routes as pairs):
   - `VBUS_SNS_RAW` + `VBUS_RTN` (dedicated DB37 return pin — fixes the measured −52 mV
     IR-drop offset of 3.0).
   - `ISNS_A/B/C_RAW` + `ISNS_RTN` (DB37 pins 30/31/32 + return on the old 11/12/13 group).
   - Encoder signal return lands in the analog region with the SIN/COS pair.
4. **Ties are explicit:** any deliberate return-to-GND junction uses the `NetTie_2` symbol
   so DRC can police it (star point, iso-secondary common, shield terminations).

## 5. Shield / chassis tie policy  **[DECIDED]**

Every off-board connector shell or shield pin gets the same footprint pattern: pad → GND via
**1 nF C0G ∥ 1 MΩ** with a solder-jumper position to short it direct. Defaults:

| Connector | Default tie | Why |
|---|---|---|
| DB37 shell (G1/G2) | RC (soft) | avoids a second DC return in parallel with signal returns; module end owns the cable shield (bench item #6 records the as-built termination) |
| Encoder connector shield | **direct** | receiver-end single-point termination of the sensor cable shield |
| LEM secondary cables (if shielded) | direct | same, analog receiver end |
| CAN / vehicle connectors | RC (soft) | chassis ESD drain without creating a ground loop through the harness |

All changeable at the bench (solder jumper / DNP) without a respin.

## 6. Floorplan & connector plan  **[DECIDED at region level — S9 executes]**

Inherits the 3.0 arrangement that already fits the harness: DB37 centered on one short edge
(faces the PrimeSTACK driver connector), LaunchPad grid mid-board with its long axis
perpendicular to that edge. 3.0 as-built: 91.9 × 121.7 mm outline; v4.0 targets a similar
envelope (grows only if S9 placement demands).

```
                SERVICE EDGE (vehicle side)
   ┌─[LaunchPad USB overhang]──[24V entry]──[CAN + switch conn]─┐
   │                            [protection]                    │
   │  ENC conn                  [buck 12V → 5V → 3V3]  POWER    │
   │ ┌─ ANALOG PARTITION ─┐                            REGION   │
 A │ │ encoder front-end  │   ┌──────────────────┐              │ P
 N │ │ Vbus front-end     │   │ LaunchPad site   │              │ W
 A │ │ current sense ×3   │   │ 4× 2×10 SOCKETS  │              │ R
 L │ └────────────────────┘   │ on BOTTOM side;  │              │
 O │  LEM conns ×3            │ LaunchPad hangs  │              │
 G │ [iso ±15V island]        │ below the board  │              │
   │                          └──────────────────┘              │
   │        [gate drivers ×2] [fault receivers]                 │
   └───────────────[ DB37, centered, jackscrews ]───────────────┘
                MODULE EDGE (faces PrimeSTACK connector)
```

- **BoosterPack headers: `PinSocket_2x10` (female), mounted on the BOTTOM side.**
  The stock LaunchPad only has male pins on its top face, so the interface board is
  mechanically the "BoosterPack on top": board on standoffs above the inverter, LaunchPad
  plugged in from below with its component side up and pins up into the sockets; the
  USB/XDS end overhangs the service edge and stays reachable. LaunchPad's own mounting
  holes get nylon standoffs up to the board (vibration support).
  This closes S1's gender question; the S1-imported `PinHeader_2x10` stays in the library
  unused.
- **Connector edges:** module edge = DB37 only. Service edge = power entry (Mini-Fit Jr on
  board; vehicle harness adapts from Deutsch DT) + CAN/cockpit-switch connector (team
  standard, S8). Analog edge = encoder connector + 3× LEM secondary connectors (Deutsch
  DT/DTM direction, S6/S7 finalize).
- **DB37 physical part:** female right-angle DC-37, 2.77 × 2.54 mm grid, 63.5 mm jackscrews
  — geometry is de-facto validated because 3.0's identical geometry mated the actual module
  cable. Open item: purchasable MPN for the consigned-parts list (user confirms).
- Bucks live in the power region top-right, diagonal to the analog partition; gate drivers
  sit between the LaunchPad grid and the DB37; fault receivers next to them.

## 7. Mechanical / mounting  **[PENDING USER MEASUREMENT — logged per S2 exit criteria]**

- The 6PS04512E43W39693 mechanical drawing is gated behind a myInfineon login (S2 tried;
  the public product page carries no documents). Known envelope: **215 × 280 × 120 mm**,
  7.7 kg, water-cooled, IP00 — the top face is far larger than the board, so area is not a
  constraint.
- **Leading plan: decouple from module geometry with an adapter plate.** The board gets its
  own regular pattern (4× M3 corner holes + 2 LaunchPad-standoff holes, exact in S9); a
  laser-cut aluminum plate maps that pattern onto whatever hole/rail features the real
  module top face offers. S9 needs only the *plate*, not the board, to change if the
  measurement surprises.
- **User action before S9:** photograph + measure the module top face (hole positions,
  threads, flatness obstructions, DB37 cable arrival point), or export the drawing from a
  myInfineon account.
- Thermal note for S3: the board hangs above a water-cooled cold plate (coolant ≤ 40 °C,
  ambient ≤ 55 °C) with the LaunchPad sandwiched beneath — the X5R (+85 °C) vs X7R decision
  should assume ~70 °C local ambient worst case.

## 8. Root-sheet interface nets (captured as sheet pins in S2)

Rails (`+24V_IN`, `+24V_PROT`, **`+24V_MOD`**, **`+13V5_GATE`**, `+5V`, `+3V3`, `+15V_ISO`, `−15V_ISO`, `GND`, **`ISO_COM`**)
are global power nets — no sheet pins. The DB37 lives on `gate_drive` (the gate bus is its
dominant, layout-critical cargo); module-side raw signals export from there.

| Net | From → To | Level / notes |
|---|---|---|
| `PWM_UH_3V3` `PWM_UL_3V3` `PWM_VH_3V3` `PWM_VL_3V3` `PWM_WH_3V3` `PWM_WL_3V3` | launchpad → gate_drive | GPIO6–11, active-HIGH |
| `DRV_EN_3V3` `DRV_EN_AUX_3V3` | launchpad → gate_drive | GPIO66 / GPIO131 (J6-59 / J6-58) |
| `FLT_OC_A_15V` `FLT_OC_B_15V` `FLT_OC_C_15V` `FLT_OT_15V` `FLT_OV_15V` | gate_drive (DB37 2/22/5/6/16) → module_status | open-collector, ≤15 V, polarity = bench item #1 |
| `FLT_OC_A_3V3` `FLT_OC_B_3V3` `FLT_OC_C_3V3` `FLT_OT_3V3` `FLT_OV_3V3` | module_status → launchpad | GPIO25/27/26, GPIO64, GPIO52 |
| `VBUS_SNS_RAW` + `VBUS_RTN` | gate_drive (DB37 7 + Kelvin pin) → module_status | 6.5 V @ 900 V, Kelvin pair |
| `VBUS_ADC` | module_status → launchpad | ADCINC2, ~1000 V full scale @ 3.0 V |
| `NTC_1_RAW` `NTC_2_RAW` | gate_drive (DB37 29 / 9) → module_status | NTC#2 reaches 10 V — divider rating (S5) |
| `NTC_1_ADC` `NTC_2_ADC` | module_status → launchpad | ADC pins chosen in S5 |
| `ISNS_A_RAW` `ISNS_B_RAW` `ISNS_C_RAW` + `ISNS_RTN` | gate_drive (DB37 30/31/32 + return) → current_sense | internal sensors ~8 mV/A, bias bench item #3 |
| `ISNS_A_ADC` `ISNS_B_ADC` `ISNS_C_ADC` | current_sense → launchpad | ADCINB4 / ADCINC4 / S8 pin; 1.5 V ± 1.4 V @ ≥±300 A |
| `ISNS_REF_A_ADC` `ISNS_REF_B_ADC` | current_sense → launchpad | ADCINA4 / ADCINB5 bias taps (keep/drop S6) |
| `ENC_SIN_ADC` `ENC_COS_ADC` | encoder → launchpad | ADCINA2 / ADCINB2, 1.5 V ± 1.4 V matched |
| `CAN_TX_3V3` / `CAN_RX_3V3` | launchpad ↔ vehicle_io | GPIO pair chosen in S8 |
| `SW_MAIN_3V3` `SW_START_3V3` | vehicle_io → launchpad | conditioned cockpit inputs (S8); S4 may also tap SW_MAIN for the hardware enable interlock |

80 sheet pins total (40 nets × 2 endpoints); every sub-sheet carries matching hierarchical
labels so S3–S8 wire into a pre-declared interface. ERC note: this KiCad build reports
`label_dangling` for any label whose net contains no component pin yet, so the empty
hierarchy shows exactly 160 such errors (80 root labels + 80 hierarchical labels) and zero
warnings — they clear organically as S3–S8 attach circuits.
