# FE_UFPR v4.0 — JLC-vetted parts, sourcing constraints and JLCPCB workflow

New parts vetted in a session are appended **here**, in a `### Parts appended in S<n>` table —
never in `CLAUDE.md`. (Moved out of `CLAUDE.md` on 2026-09-17, verbatim.)

## JLC-vetted passive kit (S1)

Place from these lines by default. Any new value in a later session gets vetted the same way and appended here. **`LCSC` field is mandatory on every placed symbol.** Stock/price snapshot: 2026-08-18 — S12 re-verifies everything live before ordering.

### Resistors — 0603, ±1%, 100 mW, thick film — **all JLC Basic**

All are the Uniroyal `0603WAF…T5E` series (one manufacturer across the kit ⇒ consistent TCR and one reel family).

> 🛑 **`C22936` IS 1 Ω, NOT 1 MΩ — the kit row above is corrected to `C22935` (2026-09-17).**
> Uniroyal `0603WAF100KT5E` (`C22936`) is a **1 Ω ±1 % ±400 ppm** part — JLC's own description says so and
> JLCSearch confirms it. The 1 MΩ part is `0603WAF1004T5E` = **`C22935`**, Basic, 8 062 164 stock, $0.00096.
> Adjacent codes, easy transposition. **Six placements still carry the wrong code: R35, R67, R77, R89,
> R104, R118** — all signal-to-GND bleed/shield resistors, so 1 Ω would (a) hard-short `SHIELD_DB37`,
> `SHIELD_LEM` and `SHIELD_ENC` to GND, wrecking the single-point shield scheme and recreating exactly the
> harness ground loop 3.0 suffered, and (b) short `ISNS_A/B/C_RAW` — the module's **5 mA-limited** sensor
> outputs — to ground at 4.7 A demanded. **Fix the six symbols before ordering.**

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
| 220 | C22962 | 10 k | C25804 | 1 M | **C22935** ⚠ |
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
| ~~**DEUTSCH DTM13-08PA-R004** 8-way, key A~~ → **DT15-08PD** (vertical, key D, TE sample) | — | **CONSIGNED** | — | J5 vehicle connector — swapped 2026-09-23, `DECISION_LOG.md`; plug DT06-08SD not sampleable |

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
| ~~**DEUTSCH DTM13-12PA-R005** (key A) / **-12PB-R005** (key B)~~ → **DT15-12PA** (sample) / **DT15-12PB** (not sampleable) | — | **CONSIGNED** | — | J3 (LEM) / J4 (encoder) — vertical DT15 since 2026-09-23; plugs DT06-12SA (sample) / DT06-12SB (buy), W12S, size-16 contacts |

⚠ **Fourth time: pick the value from live stock, not the E96 table.** 3.01 kΩ 0.1 % (C705772) has
**1 175** in stock and 3.09 kΩ (C861371) **2 980**; the E24 value **3.00 kΩ** has 116 222.

Everything else S7 places comes from the existing kit: 4.99 k 0.1 % `C723532`, 12.0 k 0.1 %
`C326735`, 100 Ω `C22775`, 1 MΩ **`C22935`** (was `C22936` = 1 Ω — see the kit-table warning), 0 Ω `C21189`, 1 nF C0G `C106246`, 2.2 nF C0G `C107043`,
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

Everything else S6 places comes from the S1/S3 kit: 1 MΩ **`C22935`** (was `C22936` = 1 Ω — see the kit-table warning), 100 Ω `C22775`, 0 Ω `C21189`,
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
**4.7 kΩ `C23162`**, 1 kΩ `C21190`, 680 Ω `C23228`, 1 MΩ **`C22935`** (was `C22936` = 1 Ω — see the kit-table warning), 1 µF/0805 `C28323`,
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

### Keep the placement single-sided

**Economic PCBA assembles one side only.** A double-sided placement forces **Standard PCBA, double-side**:
setup $51.12 + stencil $16.42 + $1.53 × 63 lines + $3.58 = **$167.51** one-time, against Economic's
**$105.39** — a flat **+$62.12**, with per-board cost unchanged. A 212 / 162 double-sided experiment on
2026-09-17 was reverted the same day; the board is **370 F.Cu / 4 B.Cu**. Decide this on whether you need
**B.Cu as a clean signal layer** (L2 is a solid GND plane and L3 a power pour, so F.Cu and B.Cu are the only
signal layers), not on the $62.

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


### S12 re-verification (2026-09-23, after the `C22936` → `C22935` fix; `fab/jlc_verify.md` is the live copy)

71 real LCSC lines / 63 codes, 0 NOT_FOUND / OUT_OF_STOCK / LOW_STOCK / VALUE_MISMATCH; 1 PACKAGE_MISMATCH (U1: JLC "ESOP-8" = HSOP-8, naming only). 37 Basic/Preferred, 33 Extended lines = 30 codes × $3.07 = **$92.10** feeder fees; parts **$140.62 / 5 boards**. U4 stock **304**. Rebuild with `sh tools/fab/make_package.sh` on order day.

| LCSC | Refs | Value | Pkg (KiCad) | Pkg (JLC) | Stock | Need | Price | Basic/Pref | Flags |
|---|---|---|---|---|---|---|---|---|---|
| `C10429` | U9-U11,U21 | SN74LVC2G17DBVR | SOT-23-6 | SOT-23-6 | 107122 | 20 | 0.3346 |  | EXTENDED |
| `C106246` | C37-C53,C58,C60,C64,C65,C70,C7 | 1nF C0G | C_0603_1608Metric | 0603 | 127722 | 150 | 0.0075 |  | EXTENDED |
| `C136963` | R105 | 3.00k 0.1% | R_0603_1608Metric | 0603 | 30010 | 5 | 0.0287 |  | EXTENDED |
| `C15857` | L1 | 22uH | L_Sunlord_SWPA8040S | SMD,8x8mm | 4688 | 5 | 0.1601 |  | EXTENDED |
| `C167960` | L2 | 3.3uH | L_Changjiang_FNR5040S | SMD,5x5mm | 5331 | 5 | 0.0599 |  | EXTENDED |
| `C182445` | F2 | 3A 63V | Fuse_1206_3216Metric | 1206 | 43061 | 5 | 0.0384 |  | EXTENDED |
| `C22046` | U8 | SN74LVC1G11DBVR | SOT-23-6 | SOT-23-6 | 10443 | 5 | 0.1829 |  | EXTENDED |
| `C23198` | R10 | 52.3k | R_0603_1608Metric | 0603 | 50873 | 5 | 0.0014 |  | EXTENDED |
| `C2836439` | C1 | 100uF 50V | CP_Elec_8x10.5 | SMD,D8xL10.2mm | 42082 | 5 | 0.0842 |  | EXTENDED |
| `C310042` | D1 | SMCJ26A | D_SMC | SMC(DO-214AB) | 7293 | 5 | 0.1444 |  | EXTENDED |
| `C326735` | R65,R66,R70,R71,R76,R79,R82,R8 | 12.0k 0.1% | R_0603_1608Metric | 0603 | 10395 | 90 | 0.0321 |  | EXTENDED |
| `C3281500` | Q1 | SQD50P06-15L | TO-252-2 | TO-252 | 7471 | 5 | 1.4259 |  | EXTENDED |
| `C46316` | U12-U17 | OPA2376 | SOIC-8_3.9x4.9mm_P1.27 | SOIC-8 | 10213 | 30 | 0.9762 |  | EXTENDED |
| `C465729` | U5-U7 | UCC27524DR | SOIC-8_3.9x4.9mm_P1.27 | SOIC-8 | 9550 | 15 | 0.4035 |  | EXTENDED |
| `C48467` | F1 | 5A 125V | Fuse_2410_6125Metric | 2410 | 28138 | 5 | 0.2563 |  | EXTENDED |
| `C492427` | J20 | LaunchPad J1+J3 | PinHeader_2x10_P2.54mm | 插件,P=2.54mm | 98935 | 5 | 0.1377 |  | EXTENDED |
| `C492427` | J21 | LaunchPad J4+J2 | PinHeader_2x10_P2.54mm | 插件,P=2.54mm | 98935 | 5 | 0.1377 |  | EXTENDED |
| `C492427` | J22 | LaunchPad J5+J7 | PinHeader_2x10_P2.54mm | 插件,P=2.54mm | 98935 | 5 | 0.1377 |  | EXTENDED |
| `C492427` | J23 | LaunchPad J8+J6 | PinHeader_2x10_P2.54mm | 插件,P=2.54mm | 98935 | 5 | 0.1377 |  | EXTENDED |
| `C5219272` | U2 | TPS62933FDRLR | SOT-583-8 | SOT-583 | 3486 | 5 | 1.0787 |  | EXTENDED |
| `C5369735` | U4 | URA2415YMD-6WR3 | Converter_DCDC_Mornsun | DIP,25.4x25.4mm | 304 | 5 | 6.3753 |  | EXTENDED |
| `C705741` | R58 | 1.50k 0.1% | R_0603_1608Metric | 0603 | 8319 | 5 | 0.0318 |  | EXTENDED |
| `C723532` | R72,R73,R84,R85,R96,R97,R100,R | 4.99k 0.1% | R_0603_1608Metric | 0603 | 47194 | 40 | 0.0318 |  | EXTENDED |
| `C723637` | R63,R64,R75,R78,R87,R90 | 20.0k 0.1% | R_0603_1608Metric | 0603 | 121239 | 30 | 0.0316 |  | EXTENDED |
| `C7542932` | F3 | 0.2A 30V 1206L020 | Fuse_1206_3216Metric | 1206 | 141752 | 5 | 0.0393 |  | EXTENDED |
| `C77033` | C62,C63,C69,C71,C76,C78,C105,C | 2.2nF C0G | C_0603_1608Metric | 0603 | 2265 | 50 | 0.0228 |  | EXTENDED |
| `C77069` | C59,C61,C68,C75,C82,C85,C86,C1 | 22nF C0G | C_0805_2012Metric | 0805 | 48685 | 55 | 0.0759 |  | EXTENDED |
| `C841384` | U1 | LMR33630ADDAR | Texas_HSOP-8-1EP_3.9x4 | ESOP-8 | 9908 | 5 | 0.6947 |  | EXTENDED PACKAGE_MISMATCH ESOP-8 |
| `C85980` | C66,C67,C73,C74,C80,C81 | 4.7nF C0G | C_0603_1608Metric | 0603 | 49830 | 30 | 0.0222 |  | EXTENDED |
| `C861295` | R57,R129 | 2.20k 0.1% | R_0603_1608Metric | 0603 | 78470 | 10 | 0.0329 |  | EXTENDED |
| `C870760` | R68,R69,R80,R81,R92,R93 | 47.0R 0.1% | R_1206_3216Metric | 1206 | 4210 | 30 | 0.0809 |  | EXTENDED |
| `C88056` | L3 | ACT45B-101-2P-TL003 | L_CommonMode_TDK_ACT45 | SMD-4P,4.5x3.2mm | 38604 | 5 | 0.3396 |  | EXTENDED |
| `C95204` | R108,R110,R113,R115,R131,R132 | 10.0k 0.1% | R_0603_1608Metric | 0603 | 389486 | 30 | 0.0241 |  | EXTENDED |
| `CONSIGNED` | J1 | Mini-Fit Jr 5566-02A | Molex_Mini-Fit_Jr_5566 |  |  | 5 |  |  | PLACEHOLDER |
| `CONSIGNED` | J2 | DSUB-37_Socket | DSUB-37_Socket_Horizon |  |  | 5 |  |  | PLACEHOLDER |
| `CONSIGNED` | J3 | LEM DTM13-12PA-R005 key A | DEUTSCH_DTM13-12P-R005 |  |  | 5 |  |  | PLACEHOLDER |
| `CONSIGNED` | J4 | ENC DTM13-12PB-R005 key B | DEUTSCH_DTM13-12P-R005 |  |  | 5 |  |  | PLACEHOLDER |
| `CONSIGNED` | J5 | VEH DTM13-08PA-R004 key A | DEUTSCH_DTM13-08PA-R00 |  |  | 5 |  |  | PLACEHOLDER |
| `NOFIT` | JP1 | ILOCK_SEL | SolderJumper-3_P1.3mm_ |  |  | 5 |  |  | PLACEHOLDER |
| `NOFIT` | JP2 | SHLD_TIE | SolderJumper-2_P1.3mm_ |  |  | 5 |  |  | PLACEHOLDER |
| `NOFIT` | JP3 | SRC SEL A | SolderJumper-3_P1.3mm_ |  |  | 5 |  |  | PLACEHOLDER |
| `NOFIT` | JP4 | SRC SEL B | SolderJumper-3_P1.3mm_ |  |  | 5 |  |  | PLACEHOLDER |
| `NOFIT` | JP5 | SRC SEL C | SolderJumper-3_P1.3mm_ |  |  | 5 |  |  | PLACEHOLDER |
| `NOFIT` | JP6 | CAN TERM bridged=120R | SolderJumper-2_P1.3mm_ |  |  | 5 |  |  | PLACEHOLDER |
| `NOFIT` | NT1 | ISO_COM-GND | NetTie-2_SMD_Pad0.5mm |  |  | 5 |  |  | PLACEHOLDER |
| `NOFIT` | NT2 | PGND_MOD-GND star | NetTie-2_SMD_Pad0.5mm |  |  | 5 |  |  | PLACEHOLDER |
| `NOFIT` | NT3 | VBUS_RTN_TIE | NetTie-2_SMD_Pad0.5mm |  |  | 5 |  |  | PLACEHOLDER |
| `NOFIT` | NT4 | ISNS_RTN-GND | NetTie-2_SMD_Pad0.5mm |  |  | 5 |  |  | PLACEHOLDER |
| `NOFIT` | TP1 | +24V_PROT | TestPoint_Pad_D1.5mm |  |  | 5 |  |  | PLACEHOLDER |
| `NOFIT` | TP2 | +13V5_GATE | TestPoint_Pad_D1.5mm |  |  | 5 |  |  | PLACEHOLDER |
| `NOFIT` | TP3 | +5V | TestPoint_Pad_D1.5mm |  |  | 5 |  |  | PLACEHOLDER |
| `NOFIT` | TP4 | +3V3 | TestPoint_Pad_D1.5mm |  |  | 5 |  |  | PLACEHOLDER |
| `NOFIT` | TP5 | +24V_MOD | TestPoint_Pad_D1.5mm |  |  | 5 |  |  | PLACEHOLDER |
| `NOFIT` | TP6 | +15V_ISO | TestPoint_Pad_D1.5mm |  |  | 5 |  |  | PLACEHOLDER |
| `NOFIT` | TP7 | -15V_ISO | TestPoint_Pad_D1.5mm |  |  | 5 |  |  | PLACEHOLDER |
| `NOFIT` | TP8 | ISO_COM | TestPoint_Pad_D1.5mm |  |  | 5 |  |  | PLACEHOLDER |
| `NOFIT` | TP9 | GND | TestPoint_Pad_D1.5mm |  |  | 5 |  |  | PLACEHOLDER |
| `NOFIT` | TP10 | TP_PWM_UH | TestPoint_Pad_D1.5mm |  |  | 5 |  |  | PLACEHOLDER |
| `NOFIT` | TP11 | TP_PWM_UL | TestPoint_Pad_D1.5mm |  |  | 5 |  |  | PLACEHOLDER |
| `NOFIT` | TP12 | TP_PWM_VH | TestPoint_Pad_D1.5mm |  |  | 5 |  |  | PLACEHOLDER |
| `NOFIT` | TP13 | TP_PWM_VL | TestPoint_Pad_D1.5mm |  |  | 5 |  |  | PLACEHOLDER |
| `NOFIT` | TP14 | TP_PWM_WH | TestPoint_Pad_D1.5mm |  |  | 5 |  |  | PLACEHOLDER |
| `NOFIT` | TP15 | TP_PWM_WL | TestPoint_Pad_D1.5mm |  |  | 5 |  |  | PLACEHOLDER |
| `NOFIT` | TP16 | TP_GATE_EN | TestPoint_Pad_D1.5mm |  |  | 5 |  |  | PLACEHOLDER |
| `NOFIT` | TP17 | TP_MOD15V_1 | TestPoint_Pad_D1.5mm |  |  | 5 |  |  | PLACEHOLDER |
| `NOFIT` | TP18 | TP_MOD15V_2 | TestPoint_Pad_D1.5mm |  |  | 5 |  |  | PLACEHOLDER |
| `NOFIT` | TP19 | TP_VBUS_RAW | TestPoint_Pad_D1.5mm |  |  | 5 |  |  | PLACEHOLDER |
| `NOFIT` | TP21 | TP_VBUS_RTN | TestPoint_Pad_D1.5mm |  |  | 5 |  |  | PLACEHOLDER |
| `NOFIT` | TP22 | TP_NTC_RAW | TestPoint_Pad_D1.5mm |  |  | 5 |  |  | PLACEHOLDER |
| `NOFIT` | TP24 | TP_FLT_OC_A | TestPoint_Pad_D1.5mm |  |  | 5 |  |  | PLACEHOLDER |
| `NOFIT` | TP25 | TP_FLT_OC_B | TestPoint_Pad_D1.5mm |  |  | 5 |  |  | PLACEHOLDER |
| `NOFIT` | TP26 | TP_FLT_OC_C | TestPoint_Pad_D1.5mm |  |  | 5 |  |  | PLACEHOLDER |
| `NOFIT` | TP27 | TP_FLT_OT | TestPoint_Pad_D1.5mm |  |  | 5 |  |  | PLACEHOLDER |
| `NOFIT` | TP28 | TP_FLT_OV | TestPoint_Pad_D1.5mm |  |  | 5 |  |  | PLACEHOLDER |
| `NOFIT` | TP29 | TP_FLT_OC_A_15V | TestPoint_Pad_D1.5mm |  |  | 5 |  |  | PLACEHOLDER |
| `NOFIT` | TP30 | ISNS_A_INT | TestPoint_Pad_D1.5mm |  |  | 5 |  |  | PLACEHOLDER |
| `NOFIT` | TP31 | ISNS_A_LEM | TestPoint_Pad_D1.5mm |  |  | 5 |  |  | PLACEHOLDER |
| `NOFIT` | TP32 | ISNS_B_INT | TestPoint_Pad_D1.5mm |  |  | 5 |  |  | PLACEHOLDER |
| `NOFIT` | TP33 | ISNS_B_LEM | TestPoint_Pad_D1.5mm |  |  | 5 |  |  | PLACEHOLDER |
| `NOFIT` | TP34 | ISNS_C_INT | TestPoint_Pad_D1.5mm |  |  | 5 |  |  | PLACEHOLDER |
| `NOFIT` | TP35 | ISNS_C_LEM | TestPoint_Pad_D1.5mm |  |  | 5 |  |  | PLACEHOLDER |
| `NOFIT` | TP36 | ISNS_VREF | TestPoint_Pad_D1.5mm |  |  | 5 |  |  | PLACEHOLDER |
| `NOFIT` | TP38 | ENC_SIN_RAW | TestPoint_Pad_D1.5mm |  |  | 5 |  |  | PLACEHOLDER |
| `NOFIT` | TP39 | ENC_COS_RAW | TestPoint_Pad_D1.5mm |  |  | 5 |  |  | PLACEHOLDER |
| `NOFIT` | TP40 | ENC_SIN_ADC | TestPoint_Pad_D1.5mm |  |  | 5 |  |  | PLACEHOLDER |
| `NOFIT` | TP41 | ENC_COS_ADC | TestPoint_Pad_D1.5mm |  |  | 5 |  |  | PLACEHOLDER |
| `NOFIT` | TP44 | ENC_VDD | TestPoint_Pad_D1.5mm |  |  | 5 |  |  | PLACEHOLDER |
| `NOFIT` | TP45 | +5V_LP | TestPoint_Pad_D1.5mm |  |  | 5 |  |  | PLACEHOLDER |
| `NOFIT` | TP46,TP47 | GND | TestPoint_THTPad_D1.5m |  |  | 10 |  |  | PLACEHOLDER |
| `NOFIT` | TP48 | ISR_PROBE_3V3 | TestPoint_Pad_D1.5mm |  |  | 5 |  |  | PLACEHOLDER |
| `NOFIT` | TP49 | CAN_H | TestPoint_Pad_D1.5mm |  |  | 5 |  |  | PLACEHOLDER |
| `NOFIT` | TP50 | CAN_L | TestPoint_Pad_D1.5mm |  |  | 5 |  |  | PLACEHOLDER |
| `NOFIT` | TP51 | SW_MAIN_3V3 | TestPoint_Pad_D1.5mm |  |  | 5 |  |  | PLACEHOLDER |
| `NOFIT` | TP52 | SW_START_3V3 | TestPoint_Pad_D1.5mm |  |  | 5 |  |  | PLACEHOLDER |
| `NOFIT` | TP53 | MOT_TEMP_RAW | TestPoint_Pad_D1.5mm |  |  | 5 |  |  | PLACEHOLDER |
| `C1017` | FB1 | 600R@100MHz | L_0805_2012Metric | 0805 | 369732 | 5 | 0.0326 | B |  |
| `C109227` | U19,U20 | LTV-817S-TA1-C | Optocoupler_LTV-817S_S | SMD-4P | 597938 | 10 | 0.0749 | B |  |
| `C12084` | U18 | SN65HVD230DR | SOIC-8_3.9x4.9mm_P1.27 | SOIC-8 | 91835 | 5 | 0.6898 | P |  |
| `C13585` | C2,C3,C5,C9,C10,C14,C23,C36,C9 | 10uF 50V | C_1206_3216Metric | 1206 | 1877266 | 50 | 0.1757 | B |  |
| `C14663` | C4,C8,C11,C12,C15,C19,C22,C24, | 100nF 50V | C_0603_1608Metric | 0603 | 12618106 | 155 | 0.0106 | B |  |
| `C15849` | C6 | 1uF 50V | C_0603_1608Metric | 0603 | 5979916 | 5 | 0.0297 | B |  |
| `C15850` | C16-C18,C20,C21,C25,C27,C97,C1 | 10uF 25V | C_0805_2012Metric | 0805 | 3505306 | 45 | 0.0773 | B |  |
| `C1622` | C13 | 47nF 50V | C_0603_1608Metric | 0603 | 414711 | 5 | 0.0087 | B |  |
| `C19077472` | D2 | BZX84C15 | SOT-23 | SOT-23 | 11303 | 5 | 0.0193 | P |  |
| `C21189` | R12,R103,R119 | 0R | R_0603_1608Metric | 0603 | 6153233 | 15 | 0.0019 | B |  |
| `C21190` | R33 | 1k | R_0603_1608Metric | 0603 | 8013731 | 5 | 0.0039 | B |  |
| `C22775` | R18-R23,R74,R86,R98,R101,R102, | 100R | R_0603_1608Metric | 0603 | 7325193 | 65 | 0.0023 | B |  |
| `C22787` | R122 | 120R | R_0603_1608Metric | 0603 | 1475830 | 5 | 0.0016 | B |  |
| `C22790` | R6,R60 | 12k | R_0603_1608Metric | 0603 | 442690 | 10 | 0.0035 | B |  |
| `C22807` | R5 | 150k | R_0603_1608Metric | 0603 | 414154 | 5 | 0.0014 | B |  |
| `C22843` | R15 | 1.5k | R_0603_1608Metric | 0603 | 1163865 | 5 | 0.0012 | B |  |
| `C2286` | D4 | red +24V_PROT | LED_0603_1608Metric | 0603 | 8154450 | 5 | 0.0073 | B |  |
| `C2286` | D5 | red +13V5_GATE | LED_0603_1608Metric | 0603 | 8154450 | 5 | 0.0073 | B |  |
| `C2286` | D6 | red +5V | LED_0603_1608Metric | 0603 | 8154450 | 5 | 0.0073 | B |  |
| `C2286` | D7 | red +3V3 | LED_0603_1608Metric | 0603 | 8154450 | 5 | 0.0073 | B |  |
| `C2286` | D8 | red +15V_ISO | LED_0603_1608Metric | 0603 | 8154450 | 5 | 0.0073 | B |  |
| `C2286` | D9 | RED GATE_EN | LED_0603_1608Metric | 0603 | 8154450 | 5 | 0.0073 | B |  |
| `C22935` | R35,R67,R77,R89,R104,R118 | 1M | R_0603_1608Metric | 0603 | 2601258 | 30 | 0.0019 | B |  |
| `C22978` | R59,R62,R130 | 3.3k | R_0603_1608Metric | 0603 | 1199741 | 15 | 0.0019 | B |  |
| `C23162` | R14,R30-R32,R36-R46,R52-R56,R6 | 4.7k | R_0603_1608Metric | 0603 | 7433362 | 105 | 0.0015 | B |  |
| `C23212` | R17 | 6.8k | R_0603_1608Metric | 0603 | 368873 | 5 | 0.0018 | B |  |
| `C23228` | R16,R34 | 680R | R_0603_1608Metric | 0603 | 923432 | 10 | 0.0013 | B |  |
| `C25803` | R1,R2,R8 | 100k | R_0603_1608Metric | 0603 | 7990119 | 15 | 0.0016 | B |  |
| `C25804` | R3,R11,R13,R24-R29,R47-R51,R12 | 10k | R_0603_1608Metric | 0603 | 37165617 | 80 | 0.000842857 | B |  |
| `C28323` | C29,C31,C33,C57,C83,C91,C101,C | 1uF 50V | C_0805_2012Metric | 0805 | 2084641 | 55 | 0.0469 | B |  |
| `C2925443` | D17 | SMAJ5.0A | D_SMA | SMA(DO-214AC) | 64985 | 5 | 0.0388 | P |  |
| `C32677` | D13 | PSM712 | SOT-23 | SOT-23 | 317834 | 5 | 0.3233 | B |  |
| `C4190` | R123-R128 | 2.2k | R_0603_1608Metric | 0603 | 2001135 | 30 | 0.0014 | B |  |
| `C4216` | R9 | 33k | R_0603_1608Metric | 0603 | 696981 | 5 | 0.0013 | B |  |
| `C6186` | U3 | AMS1117-3.3 | SOT-223-3_TabPin2 | SOT-223 | 2007447 | 5 | 0.2003 | B |  |
| `C7420333` | D10,D11,D18 | BAT54S | SOT-23 | SOT-23 | 314690 | 15 | 0.0126 | P |  |
| `C81598` | D14,D15 | 1N4148W | D_SOD-123 | SOD-123 | 3538406 | 10 | 0.0113 | B |  |
| `C8678` | D12,D16 | SS34 | D_SMA | SMA(DO-214AC) | 3557042 | 10 | 0.0303 | B |  |
