# FE_UFPR v4.0 — JLC-vetted parts, sourcing constraints and JLCPCB workflow

New parts vetted in a session are appended **here**, in a `### Parts appended in S<n>` table —
never in `CLAUDE.md`. (Moved out of `CLAUDE.md` on 2026-09-17, verbatim.)

## JLC-vetted passive kit (S1)

Place from these lines by default. Any new value in a later session gets vetted the same way and appended here. **`LCSC` field is mandatory on every placed symbol.** Stock/price snapshot: 2026-08-18 — S12 re-verifies everything live before ordering.

### Resistors — 0603, ±1%, 100 mW, thick film — **all JLC Basic**

All are the Uniroyal `0603WAF…T5E` series (one manufacturer across the kit ⇒ consistent TCR and one reel family).

> ✅ **`C25804` (10 k, 16 placements) re-verified live 2026-09-17: Basic, 37 165 617 in stock, $0.00084.**
> ⚠ But `/api/search?q=C25804` returns **an empty result** for it — see the JLCSearch quirk in
> [`TOOLING_NOTES.md`](TOOLING_NOTES.md). Always cross-check a "missing" passive against
> `/resistors/list.json` or `/capacitors/list.json` before believing it is gone.

| Ω | LCSC | Ω | LCSC | Ω | LCSC |
|---|---|---|---|---|---|
| 0 (jumper) | C21189 | 680 | C23228 | 22 k | C31850 |
| 10 | C22859 | 1 k | C21190 | 33 k | C4216 |
| 22 | C23345 | 1.5 k | C22843 | 47 k | C25819 |
| 33 | C23140 | 2.2 k | C4190 | 68 k | C23231 |
| 47 | C23182 | 3.3 k | C22978 | 100 k | C25803 |
| 100 | C22775 | 4.7 k | C23162 | 220 k | C22961 |
| 150 | C22808 | 6.8 k | C23212 | 470 k | C23178 |
| 220 | C22962 | 10 k | C25804 | 1 M | C22936 |
| 330 | C23138 | 15 k | C22809 | | |
| 470 | C23179 | | | | |

**Appended in S3** (same 0603 ±1 % family; all stock-checked 2026-08-29):

| Ω | LCSC | JLC | Used for |
|---|---|---|---|
| 12 k | C22790 | **Basic** | U1 FB divider bottom |
| 150 k | C22807 | **Basic** | U1 FB divider top (13.500 V) |
| 52.3 k | C23198 | Extended | U2 FB divider top (4.984 V) |

*(5.6 k C23189, 49.9 k C23184, 75 k C23242, 200 k C25811 and 620 k C23219 were vetted for the
reverted TPS54360B design and are no longer used — all Basic/high-stock, kept here as pre-vetted
spares.)*

⚠ **Do not "correct" these to the exact E96 values** — 162 kΩ (C22815) has **1** in stock, 10.2 kΩ (C22772) has **3**, 5.49 kΩ (C23069) has **19**, and 604 kΩ (C23216) only 3 434. See `S3_POWER_DESIGN.md` §8.

Price ≈ $0.85–1.46 / 1000, stock 0.5 M–37 M on every line. **0.1 % gain/divider resistors are deliberately NOT in this kit** — their values are computed in S5/S6/S7 and vetted there.

### Capacitors

| Value | Pkg | Dielectric | V | LCSC | MPN | JLC | Use |
|---|---|---|---|---|---|---|---|
| 100 pF | 0603 | C0G | 50 | C14858 | CL10C101JB8NNNC | **Basic** | filter / compensation |
| 220 pF | 0603 | NP0 | 50 | C106210 | CC0603JRNPO9BN221 | Extended | filter |
| 470 pF | 0603 | NP0 | 50 | C106211 | CC0603JRNPO9BN471 | Extended | filter |
| 1 nF | 0603 | NP0 | 50 | C106246 | CC0603JRNPO9BN102 | Extended | charge bucket / filter |
| 2.2 nF | 0603 | C0G | 50 | **C77033** (was C107043, see the S8 stock note) | GRM1885C1H222JA01D | Extended | filter |
| 4.7 nF | 0603 | C0G | 50 | C85980 | GRM1885C1H472JA01D | Extended | filter |
| 10 nF | 0603 | NP0 | 50 | C389113 | CC0603JRNPO9BN103 | Extended | filter (C0G ceiling in 0603) |
| 22 nF | 0805 | C0G | 50 | C77069 | GRM21B5C1H223JA01L | Extended | filter (C0G ceiling overall) |
| 10 nF | 0603 | X7R | 50 | C57112 | 0603B103K500NT | **Basic** | *non-critical* bypass only |
| 100 nF | 0603 | X7R | 50 | C14663 | CC0603KRX7R9BB104 | **Basic** | decoupling workhorse |
| 1 µF | 0603 | X5R | 50 | C15849 | CL10A105KB8NNNC | **Basic** | local bypass |
| 1 µF | 0805 | X7R | 50 | C28323 | CL21B105KBFNNNE | **Basic** | bypass where X7R tempco matters |
| 4.7 µF | 0805 | X5R | 25 | C1779 | CL21A475KAQNNNE | **Basic** | rail bulk |
| 10 µF | 0805 | X5R | 25 | C15850 | CL21A106KAYNNNE | **Basic** | rail bulk |
| 10 µF | 1206 | X5R | 50 | C13585 | CL31A106KBHNNNE | **Basic** | 24 V-side bulk |
| 22 µF | 1206 | X5R | 25 | C12891 | CL31A226KAHNNNE | **Basic** | buck output bulk |

**Appended in S3:**

| Value | Pkg | Dielectric | V | LCSC | JLC | Use |
|---|---|---|---|---|---|---|
| 47 nF | 0603 | X7R | 50 | **C1622** | **Basic** | U2 soft-start |
| 100 µF | D8×10.2 elec | — | 50 | C2836439 | Extended | 24 V input bulk / harness LC damping |

### Parts appended in S4

| Part | LCSC | JLC | Stock | Notes |
|---|---|---|---|---|
| **UCC27524DR** dual 5 A driver, SOIC-8 | C465729 | Ext | 9 550 | U5–U7. VDD 4.5–18 V; TTL input/enable thresholds **independent of VDD**; IN pins pull DOWN 120 kΩ, EN pins pull UP 200 kΩ; outputs LOW during UVLO |
| **SN74LVC1G11DBVR** 3-in AND, SOT-23-6 | C22046 | Ext | 10 443 | U8 enable combiner. Pinout 1=A 2=GND 3=B 4=Y 5=VCC 6=C |

### Parts appended in S9.6

| Part | LCSC | JLC | Stock | Notes |
|---|---|---|---|---|
| **2×10 male pin header 2.54 mm** PZ254V-12-20P | C492427 | Ext | 98 935 | J20–J23 (LaunchPad now sits ABOVE the board on its own receptacles). No Basic 2×10 male exists; highest-stock vertical line. **C5116528 (female) is no longer used.** |

### Parts appended in S8

| Part | LCSC | JLC | Stock | Notes |
|---|---|---|---|---|
| **2×10 female header, 2.54 mm** PM2.54-2*10 | C5116528 | Ext | 15 698 | J20–J23, the four BoosterPack sockets. **No Basic or Preferred 2×10 female exists** — every 20-pin 2-row line at JLC is Extended. Highest-stock of the four straight/direct-insert candidates (C7499346 11 814, C2897411 9 858, C92266 3 330). ⚠ **Insulator height not yet checked** against the LaunchPad standoffs — S9 |
| **SN65HVD230DR** 3.3 V CAN transceiver, SOIC-8 | C12084 | **Preferred** | 91 835 | U18. RS pin → 10 k = slope control ≈15 V/µs; V_ref NC |
| **LTV-817S-TA1-C** phototransistor opto, SMD-4P, CTR 200–400 % | C109227 | **Basic** | 597 938 | U19/U20 — the two car-referenced inputs. PC817C is Extended; TLP2361/6N137/H11L1 are inverting |
| **PSM712** dual asymmetric CAN TVS, SOT-23 | C32677 | **Basic** | 317 834 | D13, +12/−7 V standoff = the CAN common-mode window |
| **ACT45B-101-2P-TL003** 100 µH CM choke, 4.5 × 3.2 | C88056 | Ext | 38 604 | L3, AEC-Q200 |
| **1N4148W** SOD-123 | C81598 | **Basic** | 3.5 M | D14/D15 anti-parallel across the opto LEDs (LED V_R max 6 V) |
| **SMAJ5.0A** TVS, SMA | C2925443 | **Preferred** | 64 985 | D17 on `+5V_VEH` |
| **1206L020/30NR** polyfuse 0.2 A hold / 0.46 A trip, 30 V | C7542932 | Ext | 141 752 | F3 on `+5V_VEH` |
| **120 Ω 0603 1 %** 0603WAF1200T5E | C22787 | **Basic** | 1.34 M | R122 CAN termination (new kit line) |
| **DEUTSCH DTM13-08PA-R004** 8-way, key A | — | **CONSIGNED** | — | J5 vehicle connector — a **vertical-flange** part, see the S8 doc |

Everything else S8 places comes from the existing kit: SS34 `C8678` (the LaunchPad 5 V feed
resolved in S3, placed on `launchpad`, and a second one as the `+5V_VEH` back-feed block), 10 µF/0805
`C15850`, 100 nF `C14663`, 1 µF/0805 `C28323`, 10 kΩ `C25804`, 2.2 kΩ `C4190`, 74LVC2G17 `C10429`.
**S8 introduces no new C0G value**; it adds one passive line (120 Ω).

⚠ **S8 BOM audit: the 2.2 nF C0G line `C107043` reports 4 in stock** in two of three sources
(JLCSearch `/api/search` and the MCP local snapshot; the `capacitors/list` endpoint says 88 976 — the
endpoints disagree on every part). The ten anti-alias caps (C62/63/69/71/76/78 on `current_sense`,
C105/106/108/109 on `encoder`) were moved to **`C77033` GRM1885C1H222JA01D** (Murata C0G 50 V 5 %,
2 265 / 24 839 by the same two sources — the same family as the kit's 4.7 nF and 22 nF). **S12 verifies
live.** Other low-stock lines under the pessimistic source: `C5369735` 362, `C5219272` 2 255,
`C870760` 4 210, `C15857` 4 688.

### Parts appended in S7

| Part | LCSC | JLC | Stock | Notes |
|---|---|---|---|---|
| **10.0 kΩ 0603 0.1 %** Yageo RT0603BRD0710KL | C95204 | Ext | 546 640 | R108/110/113/115 — difference-amp input resistors |
| **3.00 kΩ 0603 0.1 %** Yageo RT0603BRD073KL | C136963 | Ext | 116 222 | R105 — reference-chain top |
| **BAT54S** dual series Schottky, SOT-23 | C7420333 | **Preferred** | 314 690 | D10/D11 — ADC clamp to +3V3/GND |
| **Ferrite 600 Ω @100 MHz** GZ2012D601TF, 0805 | C1017 | **Basic** | 369 732 | FB1 — encoder supply. **Must be a ferrite, not a resistor**: the reference chain hangs off the same node, so only a near-zero DCR keeps the bias cancellation exact |
| **DEUTSCH DTM13-12PA-R005** (key A) / **-12PB-R005** (key B) | — | **CONSIGNED** | — | J3 (LEM) / J4 (encoder) |

⚠ **Fourth time: pick the value from live stock, not the E96 table.** 3.01 kΩ 0.1 % (C705772) has
**1 175** in stock and 3.09 kΩ (C861371) **2 980**; the E24 value **3.00 kΩ** has 116 222.

Everything else S7 places comes from the existing kit: 4.99 k 0.1 % `C723532`, 12.0 k 0.1 %
`C326735`, 100 Ω `C22775`, 1 MΩ `C22936`, 0 Ω `C21189`, 1 nF C0G `C106246`, 2.2 nF C0G `C107043`,
22 nF 0805 C0G `C77069`, 100 nF `C14663`, 1 µF/0805 `C28323`, 10 µF/0805 `C15850`, OPA2376 `C46316`.
**S7 introduces no new C0G value** — it reuses 1 nF, 2.2 nF and 22 nF, which **closes the standing
"standardise C0G values" item**: the set is still exactly four (1 nF, 2.2 nF, 4.7 nF, 22 nF).

### Parts appended in S6

| Part | LCSC | JLC | Stock | Notes |
|---|---|---|---|---|
| **OPA2376AIDR** dual precision RRIO op-amp, SOIC-8 | C46316 | Ext | 10 213 | U12–U15. Chosen for output swing (the internal stage must reach **0.060 V**), 25 µV V_os / 0.25 µV/°C (drift *between* calibrations does not cancel), RRI for the 0.04 V common mode. Gain is resistor-set, so precision was not the binding constraint |
| **20.0 kΩ 0603 0.1 %** Yageo RT0603BRD0720KL | C723637 | Ext | 210 576 | internal-stage input resistors |
| **12.0 kΩ 0603 0.1 %** Yageo RT0603BRD0712KL | C326735 | Ext | 38 454 | internal-stage feedback + LEM-stage input + reference divider top |
| **4.99 kΩ 0603 0.1 %** Yageo RT0603BRD074K99L | C723532 | Ext | 92 725 | LEM-stage feedback + reference divider bottom |
| **47.0 Ω 1206 0.1 %** Yageo RT1206BRD0747RL | C870760 | Ext | 5 052 | LEM burden, **two in parallel per channel** = 23.5 Ω |
| **Micro-Fit 3.0 2×4 right-angle** HC-MX3.0-2*4AW | C3294385 | Ext | 14 802 | J3, LEM harness. ⚠ Micro-Fit-compatible clone, not genuine Molex (43045-0812 has **8** in stock) — S12 must check its drawing against the footprint |

⚠ **Do not consolidate the two 12 kΩ lines.** `C22790` (1 %, S3, U1's FB divider) and `C326735`
(0.1 %, S6 gain positions) are different parts for different jobs.

⚠ **Same trap as S3/S5, third time.** The "natural" 0.583 gain pair needs 5.76 kΩ (**3** in stock)
or 5.90 kΩ (1 879). **20.0 k / 12.0 k** was picked from live stock — and happens to give
G = 0.600 exactly, landing the ADC bias on exactly 1.500 V. See `S6_CURRENT_SENSE_DESIGN.md` §6.

Everything else S6 places comes from the S1/S3 kit: 1 MΩ `C22936`, 100 Ω `C22775`, 0 Ω `C21189`,
2.2 nF C0G `C107043`, 4.7 nF C0G `C85980`, 1 nF C0G `C106246`, 22 nF 0805 C0G `C77069`,
100 nF `C14663`, 1 µF/0805 `C28323`, 10 µF/1206 `C13585`.
**S6 introduces no new C0G value** — it reuses four existing lines, closing its half of the
standing "standardise C0G values" item.

### Parts appended in S5

| Part | LCSC | JLC | Stock | Notes |
|---|---|---|---|---|
| **SN74LVC2G17DBVR** dual non-inverting Schmitt buffer, SOT-23-6 | C10429 | Ext | 107 122 | U9–U11 fault receivers. V_CC 1.65–5.5 V; inputs accept 5.5 V; **Ioff** (partial power down) — the property that makes a dead board-3V3 read as FAULT |
| **2.20 kΩ 0603 0.1 %** Yageo RT0603BRD072K2L | C861295 | Ext | 38 458 | R57, Vbus divider top |
| **1.50 kΩ 0603 0.1 %** Yageo RT0603BRD071K5L | C705741 | Ext | 33 446 | R58, Vbus divider bottom — same RT0603B family as R57 so the *ratio* tracks over temperature |

⚠ **There is no hex non-inverting Schmitt at JLC.** `SN74LVC17A` returns **zero** results, which
is why the design is 3 × dual instead of 1 × hex. The hex *inverting* parts do exist
(`SN74LVC14APWR` C7663, 87 k; `74HC14D` C5605 **Basic**, 323 k) and using one would even have
preserved `MODULE_FAULT_ACTIVE_LOW = 1` — rejected because hidden inversion between connector and
GPIO is a bench trap, and because 74HC has no `Ioff`.

⚠ **Do not "improve" the Vbus divider to 2.32 k / 1.65 k.** That pair gives a closer ratio
(999.4 V full scale vs 1024.6 V) but the 1.65 k 0.1 % line has **673** in stock against 33 446 —
the same trap as the S3 divider values. See `S5_MODULE_STATUS_DESIGN.md` §2.2.

Everything else S5 places comes from the S1/S3 kit: 4.7 kΩ `C23162`, 10 kΩ `C25804`,
12 kΩ `C22790`, 3.3 kΩ `C22978`, 1 nF C0G `C106246`, **22 nF 0805 C0G `C77069`**,
100 nF `C14663`, 1 µF/0805 `C28323`. **S5 introduces no new C0G value.**

⚠ **The roadmap's TC4468 is unbuildable at JLC** — 14 in stock (TC4468COE: 4, TC4469COE: 18,
MIC4468ZWM: 25, UCC27523D: 79). The whole TC446x quad family is out. That, not a technical
preference, is why the design is 3× dual instead of 2× quad.

Everything else S4 places comes from the S1/S3 kit: 100 Ω `C22775`, 10 kΩ `C25804`,
**4.7 kΩ `C23162`**, 1 kΩ `C21190`, 680 Ω `C23228`, 1 MΩ `C22936`, 1 µF/0805 `C28323`,
100 nF `C14663`, 10 µF/1206 `C13585`, 1 nF C0G `C106246`, red LED `C2286`.
**S4 introduces no new C0G value** — it reuses the 1 nF line.

### Other parts appended in S3

| Part | LCSC | JLC | Notes |
|---|---|---|---|
| SQD50P06-15L P-FET, −60 V, 15.5 mΩ, TO-252 | C3281500 | Ext | reverse polarity |
| **SMCJ26A** TVS 1500 W, SMC | C310042 | Ext | 26 V standoff; 42.1 V clamp at 35.6 A ⇒ ~30–34 V at realistic surge, under the buck's 38 V abs max |
| BZX84C15 15 V Zener, SOT-23 | C19077472 | **Preferred** | Q1 Vgs clamp |
| SS34 40 V 3 A Schottky, SMA | C8678 | **Basic** | LaunchPad 5 V feed (placed in S8) |
| Fuse 5 A 125 V 2410 | C48467 | Ext | F1 — only in-stock 5 A with adequate V rating |
| Fuse 3 A 63 V 1206 | C182445 | Ext | F2 — module-aux pass-through |
| L 22 µH SWPA8040S220MT 2.1/2.4 A, 69 mΩ | C15857 | Ext | L1 |
| L 3.3 µH FNR5040S3R3NT 3.9/4.45 A | C167960 | Ext | L2 |
| LED red 0603 KT-0603R | C2286 | **Basic** | D4–D8, all five rails |
| LMR33630ADDAR | C841384 | Ext | U1 |
| TPS62933FDRLR | C5219272 | Ext | U2 |
| AMS1117-3.3 | C6186 | **Basic** | U3 |
| URA2415YMD-6WR3 | C5369735 | Ext | U4 — consigned THT, only 362 stock |

### Two hard capacitor constraints found in S1 (they shape S3 and S5–S7)

1. **JLC has no Basic C0G/NP0 part above 100 pF in 0603 — at any voltage.** (220 pF…10 nF: 0 Basic, 0 Preferred, out of 10–46 in-stock C0G options each.) Every anti-alias/filter cap therefore costs a $3 Extended setup fee, so **minimise the number of distinct C0G values board-wide** — reuse one or two filter values everywhere rather than optimising each RC independently.
2. **The practical C0G ceiling at 50 V is ~10 nF (0603) / ~22 nF (0805);** 47 nF and up simply do not exist in stock. A passive anti-alias pole at a *low* source resistance is therefore impossible (a 2 kHz corner at 1 kΩ would need 80 nF of C0G). **Consequence:** put the anti-alias pole in the op-amp feedback network (active filter) and keep only the `100 Ω + 1–10 nF C0G` charge bucket at the ADC pin, exactly as the conditioning targets above describe.
3. Related: **JLC Basic bulk capacitors ≥1 µF are X5R, not X7R** (X7R Basic exists only at 1 µF/0805/50 V). X5R is +85 °C rated, X7R +125 °C. The board sits on top of the inverter — S3 must decide per rail whether X5R's temperature range is acceptable or whether Extended X7R is bought.

## JLCPCB workflow

Board is fabbed + assembled by JLCPCB (4-layer, JLC04161H-7628 stackup).

- **Every part gets an `LCSC` field in its symbol before its session ends.** No unvetted parts survive a session.
- Local DB (`search_jlcpcb_parts` / `get_jlcpcb_part`) finds candidates, **but it cannot answer Basic-vs-Extended, stock, or price** — its Basic count is literally 0 of 7.16 M parts. Use the JLCSearch API for those:
  ```bash
  curl -s "https://jlcsearch.tscircuit.com/resistors/list.json?package=0603&resistance=10000&limit=100"
  curl -s "https://jlcsearch.tscircuit.com/capacitors/list.json?package=0603&capacitance=1e-7&limit=200"
  ```
  Returns `is_basic`, `is_preferred`, `stock`, `price1`, `tolerance_fraction`, `voltage_rating`, `temperature_coefficient`. `curl` works and gives raw JSON — prefer it over WebFetch for this. Endpoint index: `https://jlcsearch.tscircuit.com/`.
- Prefer Basic **and Preferred Extended** parts — both are exempt from the **$3.07/line feeder-loading fee** on Economic PCBA. Plain Extended parts cost $3.07 per BOM line, once per order, regardless of how many are placed. S12 re-verifies every LCSC line against live stock before ordering (stock rots).
- **Consigned / hand-solder list** (not in JLC catalog — expect to solder these): DB37, Deutsch DT/DTM connectors, LEM transducers, possibly the isolated DC/DC module.

## PCBA cost model — Basic/Extended audit (2026-09-17)

Every one of the 63 real LCSC lines queried live against JLCSearch. Placeholders excluded (`NOFIT` ×64,
`CONSIGNED` ×5). Fee schedule read from JLCPCB's own price page the same day.

### Part-category split

| Category | Distinct lines | Placements | Feeder fee |
|---|---|---|---|
| Basic | 29 | 159 | exempt |
| Preferred Extended | 4 | 6 | **exempt** |
| Extended | **30** | 144 | **$3.07 each = $92.10** |

### Cost, Economic PCBA, single-side (370 of 374 parts on F.Cu)

| Item | Cost |
|---|---|
| Setup | $8.18 |
| Stencil | $1.53 |
| Feeder loading, 30 Extended lines | $92.10 |
| Hand-soldering labour | $3.58 |
| **One-time** | **$105.39** |
| SMT, 700 joints × $0.0016 | $1.12 /board |
| Manual (THT), 85 joints × $0.0164 | $1.39 /board |
| Components (unit price × qty) | $30.79 /board |
| **Per board** | **$33.30** |

**5 boards ≈ $272**, plus the bare 4-layer 159.6 × 147.9 mm board. ⚠ The component figure is unit-price ×
quantity; at qty 5 you actually buy JLC's minimum pack per line (often 50–100 for 0603s), so the real
component invoice lands well above 5 × $30.79. It only converges at volume.

**Joint counts are not raw pad counts.** U1's `HSOP-8-1EP_ThermalVias` footprint declares 8 *thermal vias*
as through-hole pads (not joints); the 64 `NOFIT` positions are not placed (76 SMD pads); the 4 test points
are not parts; the 5 consigned connectors (J1–J5, 72 THT joints) are hand-soldered by the team. JLC places
**301 parts = 700 SMD + 85 THT joints** (the 85 = four 2×10 headers + U4).

### Economic vs Standard

- Economic: `8.18 + 1.53 + 30 × 3.07` = **$101.81**
- Standard, single-side: `25.56 + 8.21 + 63 × 1.53` = **$130.16**

**Economic wins.** Standard charges $1.53 per line for Basic *and* Extended alike, so it only overtakes
Economic above **39 Extended lines**. Re-check this if the Extended count grows.

### Assembly quantity ≠ PCB quantity

Economic PCBA accepts **2–50 pcs** (Standard: 2–80 000). The bare-board minimum is 5, so **assembling 2 of
5 boards** costs ≈ $172 + bare PCB instead of ≈ $272 and leaves 3 bare boards for rework and for the
consigned-connector work. Recommended for the first article.

### Feeder-fee reduction: audited, nothing cuttable — **do not re-attempt**

$92.10 is 87 % of the one-time assembly cost, and all 30 lines are justified:

| Group | Lines | Why it must stay Extended |
|---|---|---|
| Thin-film 0.1 % `RT0603BRD07…` (12 k ×18, 4.99 k ×8, 20 k ×6, 10 k ×6, 2.2 k ×2, 3 k, 1.5 k) + 47 R 0.1 % 1206 ×6 | 8 | Bought for **TCR tracking, not accuracy.** Encoder sheet note: a 1 % ratio drift = **~6° electrical**, *"never substitute a mixed-family divider here."* S5 §2.2: a thick-film Vbus pair drifts **0.6 % differentially over 60 °C = 6 V of bus error**, which matters to a UV/OV trip. The 47 R are in the current-sense difference-amp networks, where the target table demands matching. |
| C0G (1 nF ×30, 2.2 nF ×10, 4.7 nF ×6, 22 nF ×6) | 4 | No JLC Basic C0G exists above 100 pF (S1 hard constraint). |
| ICs (`SN74LVC2G17` ×12, `OPA2376` ×6, `UCC27524` ×3, `LMR33630`, `TPS62933`, `SN74LVC1G11`, `SQD50P06`) | 7 | No Basic equivalents; each is function-specific. |
| Through-hole and specialty (2×10 headers ×4, `URA2415YMD-6WR3`, fuse `0451005`, PTC `1206L020`, TVS `SMCJ26A`, 100 µF elec, 22 µH `SWPA8040S`, 3.3 µH `FNR5040`, `ACT45B` CAN choke, 52.3 k 1 %) | 11 | **No through-hole part can ever be Basic** — JLC's Basic catalogue *is* the pre-loaded SMT feeder set. Checked: not one 2×10 2.54 mm header and not one 100 µF 50 V electrolytic in the catalogue is Basic. |

Substitutions were actually made for R57/R58 (Vbus → `C4190`/`C22843`) and R105 (encoder chain → `C4211`)
and then **reverted** when the sheet notes and S5 §2.2 were read; both sheets verified byte-identical
afterwards. The only remaining lever on assembly cost is **order quantity**, and on board cost the outline
area — 100 × 100 mm is unreachable (sum of all 374 courtyards = 11 213 mm² > 10 000 mm², and the five fixed
connectors plus the LaunchPad header block alone are 8381 mm²).

### Low-stock watch list (2026-09-17)

| LCSC | Part | Stock | Used |
|---|---|---|---|
| `C5369735` | URA2415YMD-6WR3 | **304** | U4 (consigned anyway) |
| `C5219272` | TPS62933FDRLR | 2 255 | 1 |
| `C77033` | 2.2 nF C0G 0603 | 2 265 | 10 |
| `C870760` | 47 R 0.1 % 1206 | 4 210 | 6 |
| `C15857` | SWPA8040S220MT 22 µH | 4 688 | 1 |

Fine for a 5-board run; re-check before any batch. ⚠ `CLAUDE.md` lists URA2415YMD-6WR3 as
consigned/hand-solder, but U4 carries a real LCSC line — **decide explicitly**: consigning it drops $3.07 of
feeder fee and $6.38/board of component cost.

### Is there an API?

Official: <https://api.jlcpcb.com/> — free after signup. **PCB API** (real-time bare-board quote + order +
tracking), **Components API** (live price/stock/specs), Stencil and 3D-printing APIs. **There is no
assembly-quote endpoint** — PCBA service fees must be computed from the table above, or read off
<https://jlcpcb.com/quote> by uploading Gerbers + BOM + CPL (free, instant, no commitment). JLCSearch stays
the quicker route for per-part Basic/stock/price.

