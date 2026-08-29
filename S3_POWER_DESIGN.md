# S3 — Power supplies: computed design

Working document for S3. Every value here is computed (no placeholders) and every part is
JLC-vetted against live stock on 2026-08-29. Implements the power tree frozen in
[`ARCHITECTURE.md`](ARCHITECTURE.md) §1–2. Deviations from S2 are flagged **[ARCH CHANGE]**
and are logged in `CLAUDE.md`.

---

## 0. Headline decisions

| # | Decision | Why |
|---|---|---|
| 1 | **Gate rail = 13.57 V**, not 12.0 V | User call (S3/S4 joint). Centres the rail in the module's 11–15 V HIGH window so S4 is free to pick any series damping resistor ≤100 Ω. |
| 2 | **12 V buck = TPS54360B (60 V)**, not LMR33630 (36 V) | Survives the TVS clamp (SMBJ33A clamps at 53.3 V — a 36 V part does not). 31 k stock, SOIC-8-EP. |
| 3 | **5 V buck = TPS62933F (FCCM)** | The 5 V rail feeds the analog front-ends. FCCM holds a fixed switching frequency at *any* load, incl. LaunchPad-unplugged. See §5. |
| 4 | **12 V rail sized for CCM at real load** (47 µH) | Keeps the gate rail out of pulse-skip at 0.25–0.5 A. See §4. |
| 5 | **±15 V = one 6 W isolated module** | Closes the S0 undersizing flag: 3× LA 100-P ≈ 4 W ≫ the 2 W A2415SDL. |
| 6 | **Rail renamed `+12V_GATE` → `+13V5_GATE`** **[ARCH CHANGE]** | The net regulates to 13.57 V; calling it `+12V` on a schematic is actively misleading. |
| 7 | **New global net `+24V_MOD`** **[ARCH CHANGE]** | The module-aux pass-through needs its own fused net to cross from `power` to `gate_drive`. |

---

## 1. Why the converter choice changed (the PFM problem)

The roadmap named LMR33630 + TPS62153. Both were **rejected on light-load behaviour**, which
matters here more than on a normal board because every analog channel is sampled at 10 kHz
and *"noise >5 kHz aliases irrecoverably"* (CLAUDE.md conditioning targets).

- **LMR33630 has no MODE/SYNC pin** (pins: PGND, VIN, EN, PG, FB, VCC, BOOT, SW + AGND pad).
  It is auto-mode only → PFM bursts at light load, at a *load-dependent* repetition rate that
  can land in the kHz band. Its A/B/C suffixes differ **only** in switching frequency
  (400 k / 1.4 M / 2.1 MHz), not in mode.
- Worse, TI's own sizing rule (ripple = 30 % of the **device** max current, i.e. 3 A) puts the
  PFM/PWM boundary at ≈0.45 A — and the 12 V rail load *is* ≈0.45 A. A stock LMR33630 design
  would sit exactly on the mode boundary. That is a part-sizing mismatch, not a tuning problem.
- **TPS62153 has no MODE pin either** (SW, PG, FB, AGND, FSW, DEF, SS/TR, AVIN, PVIN, EN, VOS,
  PGND). Its DCS-Control power-save mode cannot be defeated. It is also the *fixed 5.0 V*
  member of the family — TPS62150 is the adjustable one.

**Resolution.** Forced-PWM is a hard requirement only on the rail that feeds analog:

- **+5V → TPS62933F.** The `F` suffix is FCCM (forced continuous conduction) — fixed frequency
  down to zero load. It is also the *only* member of the family **without** spread spectrum
  (TPS62932/62933/P/O all have it), so its ripple is a single clean line at 1.2 MHz, 120× above
  the sampling rate, where the analog branch's ferrite+RC filter and the op-amp PSRR are very
  effective.
- **+13V5_GATE → TPS54360B**, sized so it stays in CCM at the real load anyway (§4). Its rail
  feeds only gate drivers (which do not care) and the 5 V buck input (whose FCCM loop rejects
  it). Layout is the primary defence and the frozen floorplan already puts the bucks
  diagonally opposite the analog partition.

> **S10 layout note:** the 12 V rail drops out of CCM below ≈0.13 A (LaunchPad removed +
> gate drivers idle). Nothing is being sampled in that state, so it is accepted — but do not
> "optimise" the 47 µH inductor downward, which would raise that threshold into the working
> load range.

---

## 2. Power tree as built

```
Mini-Fit Jr (J1)  +24V_IN  18–30 V
   │
   ├─ F1  5 A  2410 125 V ──┐
   │                        Q1 P-FET (SQD50P06-15L, drain=in, source=load)
   │                        │   gate: R1 100 k to GND, D2 BZX84C15 15 V Zener gate↔source
   │                        ├─ D1 SMBJ33A TVS ─┬─ C1 100 µF/50 V elec ─┬─ +24V_PROT
   │                                            └─ 2× 10 µF/50 V 1206  ─┘
   ├─►F2 3 A 1206 ──────────────────────────────────────────►  +24V_MOD → DB37 8/26 (S4)
   │
   ├─►U1 TPS54360B  500 kHz  47 µH  ────────────────────────►  +13V5_GATE  13.566 V
   │     └─ D3 SS36 catch diode
   │        │
   │        └─►U2 TPS62933F  1.2 MHz FCCM  3.3 µH ──────────►  +5V  4.984 V
   │               │                                              └─ SS34 (S8, on launchpad sheet)
   │               └─►U3 AMS1117-3.3 ──────────────────────►  +3V3  3.3 V
   │
   └─►U4 URA2415YMD-6WR3  isolated 6 W ─────────────────────►  +15V_ISO / −15V_ISO
```

## 2.1 Power budget (computed, replaces the S2 estimate)

| Rail | Load | Current | Notes |
|---|---|---|---|
| `+24V_MOD` | PrimeSTACK aux 40 W | 1.7 A @24 V / **2.2 A @18 V** | pass-through only, no regulator |
| `+13V5_GATE` | 2× TC4468 + 8 module inputs (~100 mA), 5 fault pull-ups (~30 mA), +5V buck input (0.32 A) | **≈0.45 A** | 0.25 A typical |
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
| D1 | SMBJ33A TVS SMB | **C19077586** | **Preferred** | 56 846 | 33 V standoff, 53.3 V clamp |
| D2 | BZX84C15 15 V Zener SOT-23 | **C19077472** | **Preferred** | 11 303 | clamps Q1 Vgs |
| C1 | 100 µF 50 V elec D8×10.2 | **C2836439** | Ext | 42 082 | 146 mA ripple; damps harness LC |

**Fuse voltage rating matters.** The two 1206 5 A alternatives are rated 32 V and unrated. A
fuse must interrupt the arc at the applied voltage; with the TVS clamping to 53.3 V a 32 V fuse
can sustain an arc. That is why the 2410 part is used despite needing a derived footprint.

**Q1 orientation (easy to get backwards):** P-channel body diode runs drain→source, so
**drain = input side, source = load side**. Normal polarity: body diode forward, gate pulled to
GND ⇒ Vgs ≈ −24 V ⇒ hard on. Reverse polarity: Vgs ≈ 0 ⇒ off, body diode blocks. The 15 V
Zener is mandatory — unclamped Vgs would be −24…−30 V against a ±20 V limit.

**Dissipation:** 15.5 mΩ × (2.9 A)² = **0.13 W** — negligible in TO-252. (The AOD407 alternative
at 90 mΩ would have dissipated 0.76 W in the same package.)

---

## 4. +13V5_GATE — TPS54360B

**U1 = TPS54360BDDAR, LCSC C524806**, Extended, 31 101 stock, SOIC-8-EP.
60 V / 3.5 A, V_REF = 0.8 V ±1 %, f_sw adjustable 100 k–2500 kHz.

| Item | Value | Derivation |
|---|---|---|
| f_sw | **500 kHz** | R_T = 200 kΩ is the datasheet-characterised point (450/500/550 kHz) |
| R_T | **200 kΩ** 0603 1 % — **C25811, Basic**, 840 942 stock | `RT(kΩ) = 101756 / f^1.008` → 193.7 k; 200 k is the spec'd value |
| FB top | **75 kΩ** — **C23242, Basic**, 239 001 stock | |
| FB bottom | **4.7 kΩ** — C23162, Basic *(already in kit)* | |
| **V_out** | **13.566 V** | `0.8 × (1 + 75 k / 4.7 k)` |
| L1 | **47 µH** FNR8040S470MT — **C168137**, 31 624 stock, 1.7 A/2 A, 177 mΩ, shielded 8×8 | `L = (Vin−Vout)/(Iout·K) · Vout/(Vin·f)` with Iout 1 A, K 0.3, Vin 30 V → 49.5 µH |
| D2 | **SS36** 60 V 3 A SMA — **C7420367, Preferred**, 392 333 stock | catch diode (async buck) |
| C_BOOT | 100 nF 50 V 0603 — C14663 *(kit)* | datasheet fixed value |
| C_in | 2× 10 µF 50 V 1206 (C13585) + 100 nF (C14663) | I_rms = Iout·√(D(1−D)) = 0.25 A |
| C_out | C9,C10 = 2× 10 µF 50 V 1206 (C13585) + C11 100 nF | ≈16 µF effective after DC-bias derating; requirement ≈6 µF |
| **UVLO** | R2 = **620 kΩ** (C23219, 49 411 stk), R3 = **49.9 kΩ** (C23184, **Basic**, 399 243 stk) | **EN abs max is 8.4 V — EN must NEVER be tied to the 24 V rail.** `R1=(V_START−V_STOP)/I_HYS`, `R2=V_ENA/((V_START−V_ENA)/R1+I_1)`, I_HYS 3.4 µA, V_ENA 1.2 V, I_1 1.2 µA → **start 15.37 V, stop 13.26 V** |
| **Compensation** | R7 = **5.6 kΩ** (C23189, **Basic**), C6 = **47 nF** (C1622, **Basic**), C7 = **120 pF NP0** (C107035) | see below — TPS54360 is *externally* compensated |
| C_BOOT | C8 = 100 nF 50 V 0603 (C14663) | datasheet fixed value, BOOT→SW |

**Divider stock check — this bit nearly went wrong.** The clean-looking 13.5 V pair
162 kΩ / 10.2 kΩ is *unbuyable*: C22815 has **1** in stock and C22772 has **3**. The chosen
75 k / 4.7 k pair is **both JLC Basic**, both with >200 k stock, and lands 13.566 V.

**Ripple / mode check** (the point of §1):

| Vin | ΔI_L | CCM boundary (ΔI_L/2) | Load 0.25–0.5 A |
|---|---|---|---|
| 24 V | 0.251 A | 0.126 A | **CCM ✓** |
| 30 V | 0.316 A | 0.158 A | **CCM ✓** |

**Compensation derivation** (datasheet Eq. 44–51; the TPS54360 is *not* internally compensated).
Design load 1.0 A (2× the real 0.5 A worst case, so the loop is designed at the highest pole it will see);
C_out derated 16 µF; R_ESR ≈ 2 mΩ.

- `f_p(mod) = I_out / (2π·V_out·C_out)` = 1.0 / (2π × 13.566 × 16 µF) = **733 Hz**
- `f_z(mod) = 1/(2π·R_ESR·C_out)` = **4.97 MHz**
- `f_co = √(f_p·f_z)` = 60.4 kHz; `f_co = √(f_p·f_sw/2)` = **13.5 kHz** → take the lower, 13.5 kHz
- `R7 = (2π·f_co·C_out/gm_ps)·(V_out/(V_REF·gm_ea))` with gm_ps 12 A/V, gm_ea 350 µA/V = 5.50 kΩ → **5.6 kΩ**
- `C6 = 1/(2π·R7·f_p)` = 38.8 nF. **47 nF is used instead of 39 nF**: it is JLC **Basic** (757 k stock vs 43 k
  Extended), and it places the compensation zero at 605 Hz, *below* the 733 Hz modulator pole — slightly more
  phase margin, i.e. the conservative direction. X7R part tolerance (±10 % plus bias/tempco) is comparable to
  the 39↔47 nF step anyway, so chasing the exact value would be false precision.
- `C7 = max(C_out·R_ESR/R7, 1/(R7·f_sw·π))` = max(5.7 pF, 114 pF) = **120 pF**

⚠ **5.49 kΩ — the "exact" E96 value — has 19 units in stock (C23069).** 5.6 kΩ is Basic with 559 k.

**Output-cap sizing** (datasheet Eq. 32/33/34, ΔI 0.4 A, ΔV 2 %): transient 5.9 µF, overshoot
1.5 µF, ripple 3.8 µF → **≥6 µF**; 2× 10 µF/50 V gives ≈16 µF after bias derating. ✓

**Rail margin at the module** (±2 % rail, −0.55 V worst-case S4 drop):

| | rail | at module | window |
|---|---|---|---|
| nom | 13.566 V | 13.02 V | 11–15 V ✓ |
| +2 % | 13.837 V | 13.29 V | ✓ |
| −2 % | 13.295 V | 12.75 V | ✓ |

**Frequency headroom:** min-on-time and frequency-foldback limits compute to 3.08 MHz and
2.95 MHz respectively — 500 kHz is far below both, so there is no pulse-skipping from duty
limits (the step-down ratio is mild).

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

Every value below was checked against live JLC stock on 2026-08-29.

| Value / part | LCSC | JLC | Stock | Used as |
|---|---|---|---|---|
| R 75 kΩ 0603 1 % | C23242 | **Basic** | 239 001 | R5 — U1 FB top |
| R 200 kΩ 0603 1 % | C25811 | **Basic** | 840 942 | R4 — U1 R_T |
| R 49.9 kΩ 0603 1 % | C23184 | **Basic** | 399 243 | R3 — U1 UVLO bottom |
| R 5.6 kΩ 0603 1 % | C23189 | **Basic** | 559 518 | R7 — U1 compensation |
| R 620 kΩ 0603 1 % | C23219 | Extended | 49 411 | R2 — U1 UVLO top |
| R 52.3 kΩ 0603 1 % | C23198 | Extended | 50 873 | R10 — U2 FB top |
| C 47 nF 50 V X7R 0603 | C1622 | **Basic** | 757 584 | C6 comp zero, C13 soft-start |
| C 120 pF 50 V NP0 0603 | C107035 | Extended | 138 411 | C7 — U1 comp pole |
| C 100 µF 50 V elec D8×10.2 | C2836439 | Extended | 42 082 | C1 — input bulk |
| L 47 µH FNR8040S470MT | C168137 | Extended | 31 624 | L1 — 1.7 A/2 A, 177 mΩ, shielded 8×8 |
| L 3.3 µH FNR5040S3R3NT | C167960 | Extended | 5 331 | L2 — 3.9 A/4.45 A, 31 mΩ, shielded 5×5 |
| Fuse 5 A 125 V 2410 | C48467 | Extended | 47 295 | F1 |
| Fuse 3 A 63 V 1206 | C182445 | Extended | 43 246 | F2 |
| LED red 0603 KT-0603R | C2286 | **Basic** | 8 154 450 | D4–D8, all five rails |

### Values that looked right but are NOT purchasable — do not "restore" them

| Value | LCSC | Stock | Was going to be used for |
|---|---|---|---|
| 162 kΩ | C22815 | **1** | 13.5 V FB top (162 k/10.2 k) |
| 10.2 kΩ | C22772 | **3** | 13.5 V FB bottom |
| 5.49 kΩ | C23069 | **19** | U1 compensation resistor (exact E96 value) |
| 604 kΩ | C23216 | 3 434 | U1 UVLO top (exact value for 15.0 V start) |

## 9. Library work (done this session)

**Re-exported from KiCad standard libs** into `FE_UFPR_4_0.kicad_sym` / `.pretty`:
`TPS54360DDA`, `TPS62933` + `TPS62933F`, `AP1117-15` + `AMS1117-3.3`, `Conn_01x02`,
`MOSFET_P_GDS` (from `IRF9540N` — P-channel with numeric 1=G/2=D/3=S pins matching TO-252),
`D_TVS_Unidirectional` (from `D_Zener` — KiCad ships only *bidirectional* TVS symbols with
A1/A2 pins, and SMBJ33A is unidirectional, so the zener glyph is both electrically correct and
unambiguous about polarity).
Footprints: `TI_SO-PowerPAD-8_ThermalVias`, `SOT-583-8`, `SOT-223-3_TabPin2`, `TO-252-2`,
`SOT-23`, `D_SMA`, `D_SMB`, `Fuse_1206_3216Metric`, `CP_Elec_8x10.5`, `LED_0603_1608Metric`,
`NetTie-2_SMD_Pad0.5mm`, `Molex_Mini-Fit_Jr_5566-02A_2x01_P4.20mm_Vertical`, and
`L_Changjiang_FNR8040S` / `L_Changjiang_FNR5040S` — which are *exact* matches for the two
chosen inductors.

**Derived (KiCad ships neither):**

1. **`Fuse_2410_6125Metric`** — Littelfuse 451/453 "Recommended pad layout": pads
   **1.96 × 3.15 mm**, gap **2.95 mm**, centres **±2.455 mm**, span 6.86 mm; body
   6.10 × 2.69 × 2.69 mm. (Self-consistent: 2 × 1.96 + 2.95 = 6.87 ≈ 6.86.)
2. **`Converter_DCDC_Mornsun_URA-YMD-6WR3_THT`** + **`Converter_DCDC_URA-YMD_Dual`** symbol —
   from the URA_YMD-6WR3 datasheet (2024.09.06-B/4) Top View (PCB Layout): 25.40 × 25.40 mm
   body, Ø1.0 mm pins, Ø1.5 mm recommended holes, 2.54 mm grid, column separation 20.32 mm,
   pins 3–5 spanning 20.32 mm, pins 1–2 5.08 mm apart straddling the centre.
   Dual pin-out **1=GND(−Vin) 2=Vin 3=+Vo 4=0V 5=−Vo**. Datasheet also confirms a **9–36 V**
   input range (wider than the 18–36 V assumed) and ±200 mA per rail.
3. **Power symbols** `+24V_IN`, `+24V_PROT`, `+24V_MOD`, `+13V5_GATE`, derived by renaming
   KiCad's `+24V`, exactly as S1 derived `+15V_ISO` from `+15V`.

Library validated end-to-end: **41/41 symbols and 35/35 footprints render** via
`kicad-cli sym/fp export svg`. The library was re-normalised to KiCad canonical formatting
(`kicad-cli sym upgrade`) because the MCP importer writes imported symbols at column 0.

## 10. As-built verification

- **ERC: 0 violations on `/power/`.** The project total is unchanged at 160 `label_dangling`,
  all on the root sheet — the documented empty-sub-sheet baseline from S2, which burns down as
  S4–S8 fill their sheets.
- **Netlist verified node by node** (`kicad-cli sch export netlist`): 30 nets, e.g.
  `PWR_U1_SW = {U1.8, C8.2, D3.1, L1.1}`, `PWR_QGATE = {Q1.1, R1.1, D2.2}`,
  `+24V_PROT` = 15 nodes, `GND` = 43 nodes.
- 79 components placed; **64 carry an `LCSC` field** (the rest are test points, PWR_FLAGs and
  the net tie, which have no part number).

### Three hazards caught during capture — all would have destroyed hardware

1. **U1 EN pin absolute max = 8.4 V.** The obvious "tie EN to VIN" (which the datasheet permits
   on *some* TI parts) would have put 24–30 V on it. Now divided by R2/R3 → 2.23 V at 30 V in.
2. **U2 EN pin absolute max = 6.0 V.** Same trap off the 13.57 V rail. Now divided by R8/R9.
3. **U2 SS pin cannot float** — datasheet requires ≥6.8 nF. C13 = 47 nF fitted.

## 11. Follow-ups this session creates

- **[S4]** Series damping resistor ≤100 Ω keeps the module inside 11–15 V; log the value chosen.
- **[S4]** `+24V_MOD` is the fused pass-through — connect it to DB37 pins 8/26 on `gate_drive`.
- **[S8]** Place the LaunchPad 5 V series Schottky **SS34 (C8678, JLC Basic)** at the BoosterPack
  header on the `launchpad` sheet; header 3V3 pins get explicit no-connects.
- **[S9/S10]** Bucks diagonally opposite the analog partition (already in the frozen floorplan);
  keep L1 at 47 µH — see the CCM note in §1. Both bucks' datasheet layout rules are written on
  the schematic itself as text notes.
- **[S12]** Re-verify **C5369735** (isolated module — only 362 in stock, and it is a consigned
  through-hole part) and every other LCSC line against live stock before ordering.
- **[cosmetic]** The `power` sheet wires connectivity with net labels at pins rather than drawn
  wires. It is electrically verified but visually dense around U1/U2, where 8–9 labels converge.
  A tidy-up pass (wire stubs fanning the IC pins out) would make it presentation-quality.
- **[bench]** Confirm no back-feed with the ARCHITECTURE §3 jumper set, and measure the real
  LaunchPad 5 V draw — the 500 mA in the budget is a cap, not a measurement.
