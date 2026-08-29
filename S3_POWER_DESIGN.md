# S3 — Power supplies: computed design

Working document for S3. Every value here is computed (no placeholders) and every part is
JLC-vetted against live stock on 2026-08-29. Implements the power tree frozen in
[`ARCHITECTURE.md`](ARCHITECTURE.md) §1–2. Deviations from S2 are flagged **[ARCH CHANGE]**
and are logged in `CLAUDE.md`.

---

## 0. Headline decisions

| # | Decision | Why |
|---|---|---|
| 1 | **Gate rail = 13.500 V**, not 12.0 V | User call (S3/S4 joint). Centres the rail in the module's 11–15 V HIGH window so S4 is free to pick any series damping resistor ≤100 Ω. |
| 2 | **Gate-rail buck = LMR33630ADDAR** (the roadmap's original choice) | See §1 — an interim swap to a 60 V TPS54360B was **reverted** once the real LV rail max was confirmed as ≤26 V. |
| 3 | **5 V buck = TPS62933F (FCCM)** | The 5 V rail feeds the analog front-ends. FCCM holds a fixed switching frequency at *any* load, incl. LaunchPad-unplugged. Independent of input voltage. See §5. |
| 4 | **L1 = 22 µH per TI's ripple rule**; the gate rail is allowed to PFM at light load | It feeds only gate drivers and U2's input, and U2's FCCM loop rejects it. See §1. |
| 5 | **TVS = SMCJ26A (1500 W), not SMBJ26A (600 W)** | The clamp must stay under the buck's 38 V absolute max at a realistic surge. See §3. |
| 6 | **±15 V = one 6 W isolated module** | Closes the S0 undersizing flag: 3× LA 100-P ≈ 4 W ≫ the 2 W A2415SDL. |
| 7 | **Rail renamed `+12V_GATE` → `+13V5_GATE`** **[ARCH CHANGE]** | The net regulates to 13.5 V. |
| 8 | **New global net `+24V_MOD`** **[ARCH CHANGE]** | The module-aux pass-through needs its own fused net to cross from `power` to `gate_drive`. |
| 9 | **Input range narrowed 18–30 V → 18–26 V** **[ARCH CHANGE]** | User-confirmed LV rail maximum. This is what makes a 36 V buck viable. |

---

## 1. Converter selection — and the correction that was needed

The roadmap named LMR33630 + TPS62153. During capture I swapped **both**. One of those swaps was
right; the other was not, and was reverted after user challenge. Recording the reasoning because
the failure mode is instructive.

### What is true about light-load mode

Neither original part can be forced out of light-load PFM:

- **LMR33630 has no MODE/SYNC pin** (pins: GND, VIN, EN, PG, FB, VCC, BOOT, SW + thermal pad).
  Its A/B/C suffixes differ **only** in switching frequency (400 k / 1.4 M / 2.1 MHz), not in mode.
- **TPS62153 has no MODE pin either** (SW, PG, FB, AGND, FSW, DEF, SS/TR, AVIN, PVIN, EN, VOS,
  PGND); its DCS-Control power-save mode cannot be defeated. It is also the *fixed 5.0 V* member of
  the family — TPS62150 is the adjustable one.

### Where that matters — and where it does not

**It matters on the 5 V rail**, which feeds every analog front-end, on a board where
*"noise >5 kHz aliases irrecoverably"* (CLAUDE.md conditioning targets). A load-dependent PFM burst
rate lands in the sampled band. So **+5V → TPS62933F**: the `F` suffix is FCCM (forced continuous
conduction, fixed frequency down to zero load), and it is the **only** member of that family
*without* spread spectrum, so its ripple is a single clean line at 1.2 MHz — 120× above the sampling
rate, where the analog branch's ferrite+RC filter and op-amp PSRR are very effective. **This swap
stands, and is independent of input voltage** (U2 runs off the regulated 13.5 V rail).

**It does not matter on the gate rail.** That rail feeds only the gate drivers — which do not care —
and U2's input, whose FCCM control loop rejects it. So light-load PFM on the gate rail was never a
real reason to abandon the LMR33630.

### The 60 V detour, and why it was reverted

I briefly replaced the LMR33630 with a 60 V TPS54360B. The stated reason was transient headroom,
and it rested on the S2 assumption `+24V_IN (vehicle LV, 18–30 V)` — a range I inherited from
`ARCHITECTURE.md` §1 and never confirmed against the actual vehicle. **The user corrected this: the
LV rail max is ≤26 V.**

The one genuinely valid finding from that detour is about the *TVS*, not the buck:

| | |
|---|---|
| SMBJ33A (the S2 TVS) breakdown V_BR | **36.7 – 40.6 V** @ 1 mA |
| LMR33630 **absolute max** V_IN | **38 V** |

The S2-chosen TVS does not even begin conducting until 36.7–40.6 V — a window that *straddles* the
buck's absolute maximum. **SMBJ33A + LMR33630 was a genuinely broken pair**, but the fix is a
lower-clamping TVS (§3), not a 60 V converter.

**Lesson recorded:** two justifications were stacked for one decision (PFM *and* voltage headroom)
when only one was load-bearing, and that one rested on an unverified inherited assumption. Check the
assumption before it drives a part change.

---

## 2. Power tree as built

```
Mini-Fit Jr (J1)  +24V_IN  18–26 V
   │
   ├─ F1  5 A  2410 125 V ──┐
   │                        Q1 P-FET (SQD50P06-15L, drain=in, source=load)
   │                        │   gate: R1 100 k to GND, D2 BZX84C15 15 V Zener gate↔source
   │                        ├─ D1 SMCJ26A TVS ─┬─ C1 100 µF/50 V elec ─┬─ +24V_PROT
   │                                            └─ 2× 10 µF/50 V 1206  ─┘
   ├─►F2 3 A 1206 ──────────────────────────────────────────►  +24V_MOD → DB37 8/26 (S4)
   │
   ├─►U1 LMR33630A  400 kHz  22 µH  synchronous ────────────►  +13V5_GATE  13.500 V
   │        │
   │        └─►U2 TPS62933F  1.2 MHz FCCM  3.3 µH ──────────►  +5V  4.984 V
   │               │                                              └─ SS34 (S8, launchpad sheet)
   │               └─►U3 AMS1117-3.3 ──────────────────────►  +3V3  3.3 V
   │
   └─►U4 URA2415YMD-6WR3  isolated 6 W ─────────────────────►  +15V_ISO / −15V_ISO
```

## 2.1 Power budget (computed, replaces the S2 estimate)

| Rail | Load | Current | Notes |
|---|---|---|---|
| `+24V_MOD` | PrimeSTACK aux 40 W | 1.7 A @24 V / **2.2 A @18 V** | pass-through only, no regulator |
| `+13V5_GATE` | 2× TC4468 + 8 module inputs (~100 mA), 5 fault pull-ups (~30 mA), +5 V buck input (0.31 A) | **≈0.44 A** | 0.25 A typical |
| `+5V` | LaunchPad ≤500 mA (budget cap), op-amps 20 mA, encoder 60 mA, 3V3 LDO in 90 mA | **≈0.75 A** | |
| `+3V3` | CAN transceiver ~70 mA, Schmitt + logic | **≈0.15 A** | |
| `±15V_ISO` | 3× LA 100-P (10 mA idle + Ip/2000 each) | **≈180 mA / ≈4 W** | drives the 6 W module choice |
| **Input total** | | **≈2.9 A @18 V worst case** | F1 = 5 A, contacts ≥8 A |

---

## 3. Input protection

| Ref | Part | LCSC | JLC | Stock | Notes |
|---|---|---|---|---|---|
| F1 | 0451005.MRL 5 A 125 V 2410 | **C48467** | Ext | 47 295 | only in-stock 5 A SMD fuse with an adequate voltage rating |
| F2 | 12H1300C 3 A 63 V 1206 | **C182445** | Ext | 43 246 | module-aux pass-through |
| Q1 | SQD50P06-15L −60 V −50 A 15.5 mΩ TO-252 | **C3281500** | Ext | 7 471 | reverse polarity |
| D1 | **SMCJ26A** TVS 1500 W, SMC | **C310042** | Ext | 7 293 | see below |
| D2 | BZX84C15 15 V Zener SOT-23 | **C19077472** | **Preferred** | 11 303 | clamps Q1 Vgs |
| C1 | 100 µF 50 V elec D8×10.2 | **C2836439** | Ext | 42 082 | 146 mA ripple; damps harness LC |

### Why the TVS is an SMCJ and not an SMBJ

The clamp has to stay below the buck's **38 V absolute max** at a realistic surge current.
Both parts quote the same 42.1 V maximum clamping voltage — but at very different currents:

| Part | Power | Stand-off | V_BR | V_C | at I_PP |
|---|---|---|---|---|---|
| SMBJ26A | 600 W | 26 V | 28.9–31.9 V | 42.1 V | **14.3 A** |
| **SMCJ26A** | **1500 W** | 26 V | 28.9–31.9 V | 42.1 V | **35.6 A** |

At any realistic surge current the SMCJ sits far lower on its curve — around 30–34 V at the sort of
current that would push the SMBJ to its 42.1 V limit. Stand-off 26 V is at/above the confirmed 26 V
rail maximum, so it does not leak in normal operation. **Do not substitute an SMBJ here, and do not
raise the stand-off without re-checking the buck's absolute max.**

**Fuse voltage rating matters too.** The two 1206 5 A alternatives are rated 32 V and unrated. A fuse
must interrupt the arc at the applied voltage. That is why the 2410 part is used despite needing a
derived footprint.

**Q1 orientation (easy to get backwards):** P-channel body diode runs drain→source, so
**drain = input side, source = load side**. Normal polarity: body diode forward, gate pulled to GND
⇒ Vgs ≈ −24 V ⇒ hard on. Reverse polarity: Vgs ≈ 0 ⇒ off, body diode blocks. The 15 V Zener is
mandatory — unclamped Vgs would be −24…−26 V against a ±20 V limit.
**Dissipation:** 15.5 mΩ × (2.9 A)² = **0.13 W** — negligible in TO-252.

---

## 4. +13V5_GATE — LMR33630A

**U1 = LMR33630ADDAR, LCSC C841384**, Extended, 9 908 stock, HSOIC-8 with PowerPAD.
3.8–36 V in (abs max 38 V), 3 A, **synchronous**, **internally compensated**,
V_FB = **1.000 V** (0.985–1.015), fixed **400 kHz** (A suffix).

| Item | Value | Derivation |
|---|---|---|
| f_sw | **400 kHz**, fixed | A variant — **no R_T resistor needed** |
| FB top | **150 kΩ** — **C22807, Basic**, 414 154 stock | TI: `RFBB = RFBT/(VOUT/VREF − 1)`, RFBT recommended 100 kΩ, max 1 MΩ |
| FB bottom | **12 kΩ** — **C22790, Basic**, 442 690 stock | |
| **V_out** | **13.500 V exactly** | `1.0 × (1 + 150 k/12 k)` = 1 × 13.5. Divider current 83 µA |
| UVLO | R2 = **100 kΩ** (C25803), R3 = **10 kΩ** (C25804) — both Basic, both already in the S1 kit | divider ratio 11; `V_EN-H` = 1.231 V → **rising 13.5 V**; `V_EN-HYS` = 100 mV → **falling 12.4 V** |
| L1 | **22 µH** SWPA8040S220MT — **C15857**, 4 688 stock, 2.1 A/2.4 A, **69 mΩ**, shielded 8×8 | TI ripple rule using the *device* max (3 A) per the datasheet note |
| C_VCC | **1 µF** 0603 X5R 50 V (C15849, Basic, in kit) | datasheet: "high-quality 1-µF capacitor from VCC to GND" |
| C_BOOT | 100 nF 50 V 0603 (C14663) | datasheet: "high-quality 100-nF capacitor" BOOT→SW |
| C_in | C2,C3 = 2× 10 µF 50 V 1206 (C13585) + C4 100 nF (C14663) | on `+24V_PROT` |
| C_out | C9,C10 = 2× 10 µF 50 V 1206 (C13585) + C11 100 nF | ≈16 µF effective after DC-bias derating |
| PG | pin 4 — **no-connect flag placed** | open-drain power-good, "can be left open when not used" |

**No catch diode, no compensation network, no timing resistor** — the LMR33630 is synchronous,
internally compensated and fixed-frequency. That is 5 fewer parts than the TPS54360B detour and
better efficiency.

### Ripple and mode

`ΔI_L = V_out·(V_in − V_out) / (V_in·L·f_sw)`

| V_in | ΔI_L | % of device 3 A | DCM boundary |
|---|---|---|---|
| 24 V | 0.671 A | 22.4 % | 0.336 A |
| 26 V | **0.737 A** | **24.6 %** | 0.369 A |

TI's rule is 20–40 % ripple, and the datasheet explicitly says to use the **device** maximum current
(3 A) — not the application load — when the application load is much smaller. 22 µH lands at 24.6 %,
squarely inside that band. The rail therefore runs **PWM above ≈0.35 A and PFM below**, which is
accepted per §1.

> **S10:** do *not* chase CCM by fitting a bigger inductor. Peak current at the 0.5 A worst-case load
> is 0.5 + 0.37 = **0.87 A**, well inside the 2.1 A rms / 2.4 A saturation rating.

**Output ripple:** `ΔI_L/(8·f_sw·C_out)` = 0.737 / (8 × 400 kHz × 16 µF) = **14.4 mV** (0.11 %).

**Rail margin at the module** (±2 % rail, −0.55 V worst-case S4 drop):

| | rail | at module | window |
|---|---|---|---|
| nom | 13.500 V | 12.95 V | 11–15 V ✓ |
| +2 % | 13.770 V | 13.22 V | ✓ |
| −2 % | 13.230 V | 12.68 V | ✓ |

---

## 5. +5V — TPS62933F (FCCM)

**U2 = TPS62933FDRLR, LCSC C5219272**, Extended, 2 255 stock, SOT-583 (1.6 × 2.1 mm).
3.8–30 V in, 3 A, V_FB = 0.8 V ±1.5 %.

| Item | Value | Derivation |
|---|---|---|
| f_sw | **1200 kHz** | **R_T pin tied to GND** — no resistor needed (datasheet Table 9-1) |
| FB top | **52.3 kΩ** — **C23198**, 50 873 stock | TI Table 10-2 gives 52.5 k; 52.3 k is nearest E96 |
| FB bottom | **10.0 kΩ** — C25804, Basic *(kit)* | |
| **V_out** | **4.984 V** | `0.8 × (1 + 52.3 k / 10 k)` |
| L2 | **3.3 µH** FNR5040S3R3NT — **C167960**, 5 331 stock, 3.9 A/4.45 A, 31 mΩ, shielded 5×5 | TI Table 10-2 for 5 V @ 1.2 MHz |
| C_in | 10 µF 50 V 1206 (C13585) + 100 nF (C14663) | Vin 13.57 V |
| C_out | C16–C18 = 3× 10 µF 25 V 0805 (C15850) + C19 100 nF | TI: 20 µF typical, 10 µF minimum effective |
| **EN divider** | R8 = **100 kΩ** (C25803), R9 = **33 kΩ** (C4216) — both already in the S1 kit | **EN abs max is 6.0 V.** 13.566 × 33/133 = **3.37 V** at EN. Tying EN to the 13.5 V rail would destroy the part. |
| **SS** | C13 = **47 nF** (C1622) | **The SS pin must NOT float** — datasheet minimum 6.8 nF. 33 nF → 5 ms, so 47 nF → ≈7 ms soft start. Reuses the same Basic part as C6. |
| **BST** | C12 = 100 nF (C14663) + R12 = **0 Ω** (C21189) | TI recommends a <10 Ω BST resistor to damp the SW spike. Fitted at 0 Ω; populate 2.2–10 Ω at bench if SW ringing is a problem. |

ΔI_L = 5 × 8.57 / (13.57 × 3.3 µH × 1.2 MHz) = **0.797 A** (27 % of the device's 3 A) — and in
FCCM this stays constant down to zero load, with inductor current simply going negative.
**There is no mode transition to design around.** Duty = 0.37, t_on = 307 ns, comfortably above
the minimum on-time.

## 5.1 +3V3 — AMS1117-3.3

**U3 = AMS1117-3.3, LCSC C6186, JLC Basic**, 2 007 447 stock, SOT-223.
Drop (4.984 − 3.3) × 0.15 A = **0.25 W**; SOT-223 θ_JA ≈ 62 °C/W → ≈15 °C rise → ≈85 °C junction
at the 70 °C worst-case local ambient (ARCHITECTURE §7). Within the 125 °C limit. ✓
Feeds CAN + fault logic only, so its mediocre HF PSRR is irrelevant — no analog hangs on 3V3.

## 5.2 LaunchPad feed

**D3 = SS34, LCSC C8678, JLC Basic**, 3 557 042 stock, SMA. Series into the BoosterPack 5 V pins
per ARCHITECTURE §3. At ≈200 mA its V_f ≈ 0.35 V ⇒ LaunchPad sees ≈4.63 V, ample for its own
3.3 V LDO. Header 3V3 pins stay unconnected (explicit no-connects in S8).

---

## 6. ±15 V isolated — U4

**URA2415YMD-6WR3, LCSC C5369735**, 362 stock, DIP 25.4 × 25.4 mm, Mornsun.
18–36 V in (our 18–30 V sits inside), ±15 V out, **6 W** — against the ≈4 W / 180 mA load of
3× LA 100-P. This closes the S0 flag that the ±66 mA A2415SDL-2W was undersized.
Isolation is *kept* even though the secondary commons to GND at one point, because it forces
the ±15 V return current to stay inside the analog partition instead of sharing the 24 V return.

⚠ **Consigned / hand-solder** (through-hole module, and 362 stock is thin — S12 must re-check).
Needs a derived symbol + footprint.

---

## 7. Rail indicators

One LED per rail, ≈2 mA. **All use KT-0603R red, LCSC C2286, JLC Basic**, 8 154 450 stock —
a single Basic part number for all five, silkscreen naming each rail. (A green LED would
need an Extended line, and at V_f ≈ 3.1 V it is marginal off the 3.3 V rail anyway.)

| Rail | Series R | From kit | Result |
|---|---|---|---|
| +24V_PROT | 10 kΩ | C25804 | 2.19 mA |
| +13V5_GATE | 4.7 kΩ | C23162 | 2.44 mA |
| +5V | 1.5 kΩ | C22843 | 1.93 mA |
| +3V3 | 680 Ω | C23228 | 1.76 mA |
| +15V_ISO | 6.8 kΩ | C23212 | 1.90 mA |

All five series resistors are already in the S1 vetted kit. ✓

---

## 8. New parts appended to the S1 vetted kit

Every value below was checked against **live JLC stock on 2026-08-29**.

| Value / part | LCSC | JLC | Stock | Used as |
|---|---|---|---|---|
| R 12 kΩ 0603 1 % | C22790 | **Basic** | 442 690 | R6 — U1 FB bottom |
| R 150 kΩ 0603 1 % | C22807 | **Basic** | 414 154 | R5 — U1 FB top |
| R 52.3 kΩ 0603 1 % | C23198 | Extended | 50 873 | R10 — U2 FB top |
| C 47 nF 50 V X7R 0603 | C1622 | **Basic** | 757 584 | C13 — U2 soft-start |
| C 100 µF 50 V elec D8×10.2 | C2836439 | Extended | 42 082 | C1 — input bulk |
| L 22 µH SWPA8040S220MT 2.1/2.4 A, 69 mΩ | C15857 | Extended | 4 688 | L1 |
| L 3.3 µH FNR5040S3R3NT 3.9/4.45 A, 31 mΩ | C167960 | Extended | 5 331 | L2 |
| Fuse 5 A 125 V 2410 | C48467 | Extended | 47 295 | F1 |
| Fuse 3 A 63 V 1206 | C182445 | Extended | 43 246 | F2 |
| LED red 0603 KT-0603R | C2286 | **Basic** | 8 154 450 | D4–D8, all five rails |
| SQD50P06-15L P-FET −60 V 15.5 mΩ TO-252 | C3281500 | Extended | 7 471 | Q1 |
| SMCJ26A TVS 1500 W SMC | C310042 | Extended | 7 293 | D1 |
| BZX84C15 15 V Zener SOT-23 | C19077472 | **Preferred** | 11 303 | D2 |
| SS34 40 V 3 A Schottky SMA | C8678 | **Basic** | 3 557 042 | LaunchPad feed — *placed in S8* |
| LMR33630ADDAR | C841384 | Extended | 9 908 | U1 |
| TPS62933FDRLR | C5219272 | Extended | 2 255 | U2 |
| AMS1117-3.3 | C6186 | **Basic** | 2 007 447 | U3 |
| URA2415YMD-6WR3 | C5369735 | Extended | 362 | U4 — consigned THT |

R 100 kΩ (C25803), 10 kΩ (C25804), 33 kΩ (C4216), 4.7 kΩ, 1.5 kΩ, 680 Ω, 6.8 kΩ, 0 Ω and the
100 nF / 1 µF / 10 µF capacitors all come from the existing S1 kit unchanged.

### Values that looked right but are NOT purchasable — check stock, not just E96 tables

| Value | LCSC | Stock |
|---|---|---|
| 162 kΩ | C22815 | **1** |
| 10.2 kΩ | C22772 | **3** |
| 5.49 kΩ | C23069 | **19** |
| 604 kΩ | C23216 | 3 434 |

These were all "obvious" E96 picks during design. Every divider in this sheet was ultimately chosen
from **Basic, high-stock** parts instead.

## 9. Library work (done this session)

**Re-exported from KiCad standard libs** into `FE_UFPR_4_0.kicad_sym` / `.pretty`:
`LMR33640ADDA` + `LMR33630ADDA`, `TPS62933` + `TPS62933F`, `AP1117-15` + `AMS1117-3.3`,
`Conn_01x02`, `MOSFET_P_GDS` (from `IRF9540N` — the P-channel symbol with **numeric 1=G/2=D/3=S**
pins that map to TO-252; `Device:Q_PMOS` uses *letter* pin numbers and cannot map to a footprint),
and `D_TVS_Unidirectional` (from `D_Zener` — KiCad ships only **bidirectional** TVS symbols with
A1/A2 pins, and the SMCJ26A is unidirectional, so the zener glyph is both electrically correct and
unambiguous about K/A polarity).

Footprints: `Texas_HSOP-8-1EP_3.9x4.9mm_P1.27mm_ThermalVias`, `SOT-583-8`, `SOT-223-3_TabPin2`,
`TO-252-2`, `SOT-23`, `D_SMA`, `D_SMB`, `D_SMC`, `Fuse_1206_3216Metric`, `CP_Elec_8x10.5`,
`LED_0603_1608Metric`, `NetTie-2_SMD_Pad0.5mm`, `Molex_Mini-Fit_Jr_5566-02A_2x01_P4.20mm_Vertical`,
`L_Sunlord_SWPA8040S` and `L_Changjiang_FNR5040S` — exact matches for the two chosen inductors.
(`TI_SO-PowerPAD-8_ThermalVias`, `D_SMB` and `L_Changjiang_FNR8040S` remain in the library from the
reverted TPS54360B design; they are unused but harmless.)

**Derived (KiCad ships neither):**

1. **`Fuse_2410_6125Metric`** — Littelfuse 451/453 "Recommended pad layout": pads
   **1.96 × 3.15 mm**, gap **2.95 mm**, centres **±2.455 mm**, span 6.86 mm; body
   6.10 × 2.69 × 2.69 mm. (Self-consistent: 2 × 1.96 + 2.95 = 6.87 ≈ 6.86.)
2. **`Converter_DCDC_Mornsun_URA-YMD-6WR3_THT`** + **`Converter_DCDC_URA-YMD_Dual`** symbol —
   from the URA_YMD-6WR3 datasheet (2024.09.06-B/4) Top View (PCB Layout): 25.40 × 25.40 mm body,
   Ø1.0 mm pins, Ø1.5 mm recommended holes, 2.54 mm grid, column separation 20.32 mm, pins 3–5
   spanning 20.32 mm, pins 1–2 5.08 mm apart straddling the centre. Dual pin-out
   **1=GND(−Vin) 2=Vin 3=+Vo 4=0V 5=−Vo**. Datasheet also confirms a **9–36 V** input range and
   ±200 mA per rail.
3. **Power symbols** `+24V_IN`, `+24V_PROT`, `+24V_MOD`, `+13V5_GATE`, derived by renaming KiCad's
   `+24V`, exactly as S1 derived `+15V_ISO` from `+15V`.

Library validated end-to-end: **43/43 symbols and 38/38 footprints render** via
`kicad-cli sym/fp export svg`. Note the MCP `import_symbol` writes imported symbols at column 0, so
run `kicad-cli sym upgrade` afterwards to restore canonical formatting.

## 10. As-built verification

- **ERC: 0 violations on `/power/`.** Project total is unchanged at 160 `label_dangling`, all on the
  root sheet — the documented empty-sub-sheet baseline from S2, which burns down as S4–S8 fill their
  sheets.
- **Netlist verified node by node** (`kicad-cli sch export netlist`): **29 nets, no stranded nets.**
  Spot checks: `PWR_U1_SW = {U1.8, C8.2, L1.1}`, `PWR_U1_FB = {U1.5, R5.2, R6.1}`,
  `PWR_U1_VCC = {U1.6, C6.1}`, `PWR_QGATE = {Q1.1, R1.1, D2.2}`, `+24V_PROT` = 15 nodes,
  `GND` = 40 nodes (including both `U1.1` and the stacked exposed-pad pin `U1.9`).
  The only single-node net is the intentional `unconnected-(U1-PG-Pad4)`.
- **75 components placed; 60 carry an `LCSC` field** (the rest are test points, PWR_FLAGs and the
  net tie, which have no part number). Refdes numbering has gaps at D3/R4/R7/C7 where the TPS54360B
  support parts were removed — normal, and left rather than renumbering.

### Hardware-destroying traps caught during capture

1. **U2 (TPS62933F) EN pin absolute max = 6.0 V.** Tying it to the 13.5 V rail would destroy it.
   Now divided by R8/R9 = 100 k/33 k → 3.37 V.
2. **U2 SS pin cannot float** — datasheet requires ≥6.8 nF. C13 = 47 nF fitted.
3. **SMBJ33A + LMR33630 is a broken pair** (TVS V_BR 36.7–40.6 V straddles the buck's 38 V absolute
   max) — resolved with the SMCJ26A, §3.

*(U1's EN pin is rated to VIN + 0.3 V on the LMR33630, so it is not a trap here — but it was on the
TPS54360B, whose EN is limited to 8.4 V. Worth remembering if that part ever returns.)*

## 11. Follow-ups this session creates

- **[S4]** Series damping resistor ≤100 Ω keeps the module inside 11–15 V; log the value chosen.
- **[S4]** `+24V_MOD` is the fused (F2, 3 A) pass-through — land it on DB37 pins 8/26 on `gate_drive`.
- **[S8]** Place the LaunchPad 5 V series Schottky **SS34 (C8678, JLC Basic)** at the BoosterPack
  header on the `launchpad` sheet; header 3V3 pins get explicit no-connects.
- **[S9/S10]** Bucks diagonally opposite the analog partition (frozen floorplan). Keep L1 at 22 µH —
  see §4. Both bucks' datasheet layout rules are written on the schematic itself as text notes.
- **[S12]** Re-verify **C5369735** (isolated module — only 362 in stock, consigned through-hole) and
  every other LCSC line against live stock before ordering.
- **[cosmetic]** The `power` sheet wires connectivity with net labels at pins rather than drawn
  wires. Electrically verified but visually dense around U1/U2 where 8–9 labels converge. A wire-stub
  pass would make it presentation-quality.
- **[bench]** Confirm no back-feed with the ARCHITECTURE §3 jumper set; measure the real LaunchPad
  5 V draw (the 500 mA in the budget is a cap, not a measurement); and **confirm the LV rail maximum
  of 26 V** under charging/regen/contactor switching, since the whole 36 V-buck choice rests on it.
