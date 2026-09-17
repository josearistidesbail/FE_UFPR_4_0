# FE_UFPR v4.0 — DB37 pinout, controller interface, and the 3.0 as-built comparison

(Moved out of `CLAUDE.md` on 2026-09-17, verbatim. `CLAUDE.md` keeps the pin table itself.)

## DB37 — v4.0 pin table (AUTHORITATIVE, from the datasheet, frozen S4)

Source: `datasheets/Infineon-6PS04512E43W39693-DS-v02_00-en-1840455.pdf` **p.6 circuit diagram**.
Module connector is **SUB-D 37 male, UNC 4-40 female thread**; the board carries the socket.
Full derivation, level maths and timing budget: [`S4_GATE_DRIVE_DESIGN.md`](S4_GATE_DRIVE_DESIGN.md).

| Pin | Module function | v4.0 net | Pin | Module function | v4.0 net |
|---|---|---|---|---|---|
| 1 | True earth / shield | `SHIELD_DB37` | 20 | HB A IGBT **BOT** | `PWM_UL_15V` |
| 2 | HB A error | `FLT_OC_A_15V` | 21 | HB A IGBT **TOP** | `PWM_UH_15V` |
| 3 | HB B IGBT **BOT** | `PWM_VL_15V` | 22 | HB B error | `FLT_OC_B_15V` |
| 4 | HB B IGBT **TOP** | `PWM_VH_15V` | 23 | HB C IGBT **BOT** | `PWM_WL_15V` |
| 5 | HB C error | `FLT_OC_C_15V` | 24 | HB C IGBT **TOP** | `PWM_WH_15V` |
| 6 | Temp. error | `FLT_OT_15V` | 25 | GND digital | `GND` |
| 7 | Voltage DC-link | `VBUS_SNS_RAW` | 26 | 13–30 V supply in | `+24V_MOD` |
| 8 | 13–30 V supply in | `+24V_MOD` | 27 | **15 V/50 mA OUT** | `MOD_AUX15V_2` (TP18) |
| 9 | **15 V/50 mA OUT** ¹ | `MOD_AUX15V_1` (TP17) | 28 | GND (supply return) | `PGND_MOD` |
| 10 | GND (supply return) | `PGND_MOD` | 29 | Temperature (NTC) | `NTC_1_RAW` — **rate 10 V** |
| 11 | GND analog | `VBUS_RTN` (Kelvin) | 30 | HB A current | `ISNS_A_RAW` |
| 12 | GND analog | `ISNS_RTN` | 31 | HB B current | `ISNS_B_RAW` |
| 13 | GND analog | `ISNS_RTN` | 32 | HB C current | `ISNS_C_RAW` |
| 14 | NC | no-connect | 33 | NC | no-connect |
| 15 | NC | no-connect | 34 | NC | no-connect |
| 16 | Voltage error | `FLT_OV_15V` | 35 | NC | no-connect |
| 17 | NC | no-connect | 36 | NC | no-connect |
| 18 | NC | no-connect | 37 | GND digital | `GND` |
| 19 | GND digital | `GND` | G1/G2 | shell | `SHIELD_DB37` |

¹ **Pins 9 and 27 are two pins of the SAME 15 V / 50 mA auxiliary rail, and "PTC" is the FUSE that
protects it — not a temperature sensor.** The p.6 "Out" group draws the IEC **fuse symbol labelled
PTC** in a legend box, in exactly the same style and position as the *two solid fuse symbols* the
"In" group draws for the 13–30 V feed on pins 8/26. A PTC resettable fuse (polyfuse) is what limits
that output to 50 mA. Infineon presumably names it PTC because the rail is *intended* for exciting a
customer-built motor-PTC circuit — which is very likely how "PTC" became a signal name on 3.0's
schematic. **There is no PTC/thermistor interface on this connector**; the module's only temperature
output is pin 29. Duplicated pins are this connector's habit (8/26, 10/28, 19/25/37, 11/12/13).
v4.0 still keeps `MOD_AUX15V_1`/`_2` as **two separate nets**: merging them would be correct and
would share current, but at 50 mA that buys nothing, whereas separate nets stay safe even if this
reading is wrong.

**Controller interface, datasheet p.2 — the numbers every downstream sheet needs:**

| Parameter | Value |
|---|---|
| Aux supply | 18–30 V, 40 W max (connector itself accepts 13–30 V) |
| Digital input | `0–1.5 V` LOW / `11–15 V` HIGH, **logic high = on**, network **10 kΩ to GND + 1 nF to GND** |
| Digital output | open collector, **logic low = no fault** ⇒ **FAULT = HIGH**, sink ≤ **15 mA**, ≤ 15 V |
| Current sensors | 4.7 / 4.9 / 5.0 V at 300 A_RMS, **load max 5 mA** |
| DC-link sensor | 6.4 / 6.5 / 6.6 V at 900 V, **load max 5 mA** |
| NTC (inverter section) | **10 V** at T_NTC = 82 °C, **load max 5 mA** |
| Over-current shutdown | 625 A_peak within 15 µs (module's own) |
| EMC | 1 kV burst on the control interface, 1 kV surge on the 24 V aux |

### 3.0 as-built map (SUPERSEDED — kept only to show what changed)

**34 of 37 pins agree with the datasheet** — the 26 functional pins plus the 8 NC pins 3.0 correctly
left dangling. **Every pin that carries traffic was right in 3.0** (6 gates incl. TOP/BOT within each
leg, 5 faults, 3 phase currents, Vbus, temperature, 24 V in + return, all grounds) and v4.0 keeps
them identical. The interface working on the bench is fully consistent with this.

Only **three** pins change, and none of them are in a signal path:

| Pin | 3.0 did | Reality | What it actually was |
|---|---|---|---|
| **27** | tied to GND | 15 V/50 mA supply **output** | The one genuine electrical mistake — a supply output shorted to ground. **Self-protecting and symptomless**: that output's own PTC resettable fuse (see ¹) trips, goes high-resistance and holds at a small leakage current. Nothing in the signal chain depends on the rail. |
| **9** | divided → header, read as a "PTC" temperature | same 15 V/50 mA output | Dead circuit — reads a constant, not a temperature. Firmware never sampled it (`NTC channels: none today`). Harmless. |
| **1** | tied to GND | "True earth/shield", bonded to module chassis internally | **Not an error.** A hard chassis-to-signal-GND bond is a legitimate choice; it only conflicts with the *soft-tie* policy S2 adopted for v4.0. |

The phantom **NTC#2 channel was an S2 error of ours**, in `ARCHITECTURE.md` §8 — inferred from
`infineon.md`'s spec table listing two NTC part numbers. 3.0 never claimed a second temperature pin.

| Pin | 3.0 net | Pin | 3.0 net | Pin | 3.0 net |
|---|---|---|---|---|---|
| 1 | GND | 14 | — | 27 | GND |
| 2 | FLT_A_IN ✓ | 15 | — | 28 | P_GND |
| 3 | BL15 (gate B low) | 16 | FLT_V_IN ✓ | 29 | TEMP_IN |
| 4 | BH15 (gate B high) | 17 | — | 30 | IA_IN ✓ |
| 5 | FLT_C_IN ✓ | 18 | — | 31 | IB_IN ✓ |
| 6 | OV_TEMP_IN ✓ | 19 | GND | 32 | IC_IN ✓ (left dangling in 3.0) |
| 7 | VDC_IN | 20 | AL15 (gate A low) | 33 | — |
| 8 | +24V ✓ | 21 | AH15 (gate A high) | 34 | — |
| 9 | PTC+ | 22 | FLT_B_IN ✓ | 35 | — |
| 10 | P_GND | 23 | CL15 (gate C low) | 36 | — |
| 11 | A_GND | 24 | CH15 (gate C high) | 37 | GND |
| 12 | A_GND | 25 | GND | G1/G2 | shell, unconnected in 3.0 |
| 13 | A_GND | 26 | +24V ✓ | | |

✓ = independently confirmed by `infineon.md` / firmware pin map.
