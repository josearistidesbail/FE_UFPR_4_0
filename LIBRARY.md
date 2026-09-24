# FE_UFPR v4.0 — Symbol and footprint library inventory

Library additions are recorded **here** — never in `CLAUDE.md`. (Moved out of `CLAUDE.md` on 2026-09-17, verbatim.)

**Library rule:** nothing is ever placed from a global/system library. Standard KiCad parts are *re-exported* into `FE_UFPR_4_0.kicad_sym` / `.pretty`. This is the fix for 3.0, whose `sym-lib-table` and `fp-lib-table` point at files that do not exist — it only still opens because of embedded caches.

### Symbol library inventory

| Group | Symbols |
|---|---|
| Passive | `R` `C` `C_Polarized` `L` `FerriteBead` `Polyfuse` `Fuse` `Thermistor_NTC` |
| Semi | `LED` `D` `D_Schottky` `D_TVS` `D_Zener` |
| Power/flags | `GND` `PWR_FLAG` `+3V3` `+5V` `+12V` `+24V` `+15V_ISO` `-15V_ISO` |
| Connector | `DSUB-37_Socket` (generated) `Conn_02x10_Odd_Even` |
| Utility | `TestPoint` `MountingHole` `NetTie_2` `SolderJumper_2_Open` `SolderJumper_3_Open` |

**Appended 2026-09-23, S12.5 (47 → 49 footprints):** **`DEUTSCH_DT15-12P_Vertical`** (DT15-12PA/PB/PC/PD — one footprint, keys differ only in the moulding) and **`DEUTSCH_DT15-08P_Vertical`** (DT15-08PA/PB/PC/PD), hand-derived from TE drawings C-DT15-12PX rev D2 and C-DT15-08PX-XXXX rev A (`datasheets/TE-DT15-*_customer_drawing.pdf`; derivation in the `descr` strings and `DECISION_LOG.md`). The DTM13 footprints stay, now **unused**. No new symbols: `Conn_02x06_Counter_Clockwise` / `Conn_02x04_Counter_Clockwise` map 1:1 onto the DT cavity numbers printed on the drawings (the library symbol's default footprint for the 02x04 was moved to the DT15 8-way so the embedded copy matches). Both footprints render.

**Appended in S8 (51 → 57 symbols):** `SN65HVD230` (KiCad `Interface_CAN_LIN`), `LTV-817S`
(`Isolator`), `SolderJumper_2_Bridged` (`Jumper`), `D_TVS_Dual_CAN` (`Power_Protection:NUP2105L`
renamed — same SOT-23 pinout as the PSM712: 1/2 lines, 3 GND), `Conn_02x04_Counter_Clockwise`
(`Connector_Generic`, 1..4 / 8..5 = the DTM 8-way cavity order) and `L_CommonMode`
(`Filter:Choke_CommonMode_FerriteCore_1423` renamed — windings 1–4 / 2–3 = ACT45B pinout). All
standalone, copied by script, LCSC property added. New footprints (42 → 47):
**`DEUTSCH_DTM13-08PA-R004_Horizontal`** (hand-derived, `S8_INTEGRATION_DESIGN.md` §1.3),
**`Optocoupler_LTV-817S_SMD-4P`** (Lite-On land: 1.5 × 1.3 pads, 2.54 pitch, rows 9.0 apart),
**`L_CommonMode_TDK_ACT45B`** (TDK land: 1.35 × 0.9 pads, 5.9 × 3.4 outer), plus copies of
`SolderJumper-2_P1.3mm_Bridged_Pad1.0x1.5mm` and `D_SOD-123`. Library revalidated:
**57/57 symbols (59 SVGs) and 47/47 footprints**.

**Appended in S7 (49 → 51 symbols):** `Conn_02x06_Counter_Clockwise` (KiCad `Connector_Generic` —
its 1..6 / 12..7 numbering is exactly the DTM13 pin order) and `BAT54S` (KiCad `Diode`, 3-pin series
pair: 1=A 2=K 3=COM). Both are standalone definitions — checked for `extends` before copying, per
S6's lesson — and were copied by script rather than by the MCP `import_symbol`. New footprint:
**`DEUTSCH_DTM13-12P-R005_Horizontal`** (41 → 42), hand-derived from TE's customer drawings; full
derivation in `S7_ENCODER_DESIGN.md` §8.3. `BAT54S` reuses S3's `SOT-23`. Library revalidated:
**51/51 symbols (53 SVGs) and 42/42 footprints**.
⚠ **Footprint names in this library carry the metric suffix** — `R_0603_1608Metric`,
`C_0805_2012Metric`, `L_0805_2012Metric`. The inventory table below abbreviates them; assigning the
abbreviated name silently produces `footprint_link_issues` at ERC (S7 hit this on 33 parts).

**Appended in S6 (47 → 49 symbols):** `OPA2376` (dual precision RRIO op-amp) and
`Conn_02x04_Odd_Even` (KiCad `Connector_Generic`). New footprint:
`Molex_Micro-Fit_3.0_43045-0800_2x04_P3.00mm_Horizontal` (40 → 41). Library revalidated:
**49/49 symbols (51 SVGs) and 41/41 footprints**.
⚠ **`OPA2376` is a hand-flattened single-unit symbol**, like `UCC27524D` and `74LVC1G11` already
were — one body, all 8 pins. KiCad's `Amplifier_Operational:OPA2376xxD` is a *derived* symbol
(`extends "LM2904"`), and the MCP `import_symbol` copied it **without its parent**, producing a
library that would not load at all. `kicad-cli sym export svg` caught it in one command. **Always
re-export SVGs after any library edit, and never import a symbol whose definition contains
`extends` without its parent.**

**Appended in S5 (46 → 47 symbols):** `74LVC2G17` (KiCad `74xGxx`, dual non-inverting Schmitt buffer; DBV pinout 1=1A 2=GND 3=2A 4=2Y 5=VCC 6=1Y cross-checked against TI SCES381N). No new footprints — it reuses S4's `SOT-23-6`. Library re-validated: **47/47 symbols (49 SVGs, the 3-unit symbol renders 3) and 40/40 footprints**. S5 also normalised the leading-tab indentation of the four MCP-imported symbols (`UCC27524D`, `74LVC1G11`, `PGND_MOD`, `74LVC2G17`) — cosmetic only; KiCad's parser is whitespace-insensitive.

**Appended in S4 (43 → 46 symbols):** `UCC27524D` (KiCad `Driver_FET`), `74LVC1G11` (KiCad `74xGxx`, pinout cross-checked against TI SCES487I: 1=A 2=GND 3=B 4=Y 5=VCC 6=C), and power symbol `PGND_MOD` (KiCad `GNDPWR` renamed — kept for symmetry with the other rail symbols even though the sheets express power nets as **global labels**, which is the convention S3 established).

**Appended in S3 (28 → 43 symbols):** `LMR33640ADDA` + `LMR33630ADDA`, `TPS62933` + `TPS62933F`, `AP1117-15` + `AMS1117-3.3`, `Conn_01x02`, `MOSFET_P_GDS`, `D_TVS_Unidirectional`, `Converter_DCDC_URA-YMD_Dual`, `TPS54360DDA` (from the reverted detour, now unused), and power symbols `+24V_IN` `+24V_PROT` `+24V_MOD` `+13V5_GATE`.
- `MOSFET_P_GDS` is KiCad's `IRF9540N` renamed — it is the P-channel symbol with **numeric 1=G / 2=D / 3=S** pins that map to TO-252. `Device:Q_PMOS` uses letter pin *numbers* and cannot map to a footprint.
- `D_TVS_Unidirectional` is `D_Zener` renamed: KiCad ships only **bidirectional** TVS symbols (A1/A2 pins) and the SMCJ26A is unidirectional, so the zener glyph is both electrically correct and unambiguous about K/A polarity.
- `+12V` and `+24V` remain in the library but are now **unused** (superseded by `+13V5_GATE` / `+24V_IN`).

`+15V_ISO` / `-15V_ISO` are KiCad's `+15V` / `-15V` renamed so the power symbol drives the isolated-rail net names used in the net convention below. All BOM-bearing symbols carry an empty hidden **`LCSC`** property so the field is always present in the symbol-fields table.

### Footprint library inventory

`R_0603/0805/1206/2512` · `C_0603/0805/1206/1210` · `L_0805/1206` · `PinHeader_2x10_P2.54mm_Vertical` · `PinSocket_2x10_P2.54mm_Vertical` · `DSUB-37_Socket_Horizontal_P2.77x2.54mm_MountingHoles` · `TestPoint_Pad_D1.5mm` · `TestPoint_THTPad_D1.5mm_Drill0.7mm` · `MountingHole_3.2mm_M3` · `MountingHole_3.2mm_M3_Pad` · `MountingHole_4.3mm_M4_ISO7380` · `SolderJumper-2_P1.3mm_Open` · `SolderJumper-3_P1.3mm_Open_NumberLabels`

**Appended in S4 (38 → 40 footprints):** `SOIC-8_3.9x4.9mm_P1.27mm` · `SOT-23-6` — both straight re-exports of KiCad standards.

**Appended in S3 (19 → 38 footprints):** `Texas_HSOP-8-1EP_3.9x4.9mm_P1.27mm_ThermalVias` · `D_SMC` · `L_Sunlord_SWPA8040S` · `SOT-583-8` · `SOT-223-3_TabPin2` · `TO-252-2` · `SOT-23` · `D_SMA` · `D_SMB` · `Fuse_1206_3216Metric` · `CP_Elec_8x10.5` · `LED_0603_1608Metric` · `NetTie-2_SMD_Pad0.5mm` · `Molex_Mini-Fit_Jr_5566-02A_2x01_P4.20mm_Vertical` · `L_Changjiang_FNR8040S` · `L_Changjiang_FNR5040S` (exact matches for the chosen inductors) — plus two **derived** because KiCad ships neither:

- **`Fuse_2410_6125Metric`** — Littelfuse 451/453 recommended land: pads 1.96 × 3.15 mm, gap 2.95 mm, centres ±2.455 mm, span 6.86 mm; body 6.10 × 2.69 × 2.69 mm.
- **`Converter_DCDC_Mornsun_URA-YMD-6WR3_THT`** — from the URA_YMD-6WR3 datasheet Top View (PCB Layout): 25.40 × 25.40 mm, Ø1.0 mm pins / Ø1.5 mm holes, 2.54 mm grid, columns 20.32 mm apart, pins 3–5 spanning 20.32 mm, pins 1–2 5.08 mm apart straddling the centre. Pin-out **1=GND(−Vin) 2=Vin 3=+Vo 4=0V 5=−Vo**.

Both libraries were validated by a full KiCad parse — S1: `sym export svg` → 28/28, `fp export svg` → 19/19; **S3: 43/43 symbols and 38/38 footprints; S4: 46/46 and 40/40**. Note the MCP `import_symbol` writes imported symbols at column 0, so run `kicad-cli sym upgrade` afterwards to restore canonical formatting.

### 3D models (added 2026-09-17)

KiCad's own bodies come from the `kicad-library-3d` package (`/usr/share/kicad/3dmodels`, referenced as
`${KICAD10_3DMODEL_DIR}` — the package was **not installed** until 2026-09-17, which is why every render
before that was a bare board). The six footprints KiCad ships no model for carry project bodies in
`3dmodels/` (`${KIPRJMOD}/3dmodels/…`), generated by `tools/board_layout/gen_3d_models.py` (cadquery)
from the footprint `descr` strings and the TE customer drawings, and attached by
`tools/board_layout/attach_3d_models.py` (library **and** board instances; idempotent):

| Footprint | Body | Source / fidelity |
|---|---|---|
| `DEUTSCH_DTM13-12P-R005_Horizontal` | `3dmodels/DEUTSCH_DTM13-12P-R005_Horizontal.step` | envelope from TE drawing rev NC: 41.02 × 38.10 × 24.28 mm, plug cavity, 12 pins. Not the vendor STEP |
| `DEUTSCH_DTM13-08PA-R004_Horizontal` | `3dmodels/DEUTSCH_DTM13-08PA-R004_Horizontal.step` | TE drawing rev D: base block, **vertical 68.58 × 33.02 flange with the four slots, 4.4 mm below the board**, housing 32.64 × 20.22 |
| `DEUTSCH_DT15-12P_Vertical` | `3dmodels/DEUTSCH_DT15-12P_Vertical.step` | TE drawing rev D2: 35.26 × 59.21 block to the flange face at 15.52, 22.25 × 49.3 shroud to 30.12, plug cavity, 12 pins Ø1.57, screw holes. `gen_3d_dt15.py`, not the vendor STEP |
| `DEUTSCH_DT15-08P_Vertical` | `3dmodels/DEUTSCH_DT15-08P_Vertical.step` | TE drawing rev A: 35.26 × 55.12 block, 22.25 × 36.45 shroud, 8 pins — same generator |
| `Converter_DCDC_Mornsun_URA-YMD-6WR3_THT` | `3dmodels/Converter_DCDC_Mornsun_URA-YMD-6WR3_THT.step` | 25.4 × 25.4 × 11.7 box + 5 pins |
| `L_CommonMode_TDK_ACT45B` | `3dmodels/L_CommonMode_TDK_ACT45B.step` | 4.5 × 3.2 × 2.8 box + terminals |
| `Fuse_2410_6125Metric` | `3dmodels/Fuse_2410_6125Metric.step` | 6.10 × 2.69 × 2.69 ceramic + end caps |
| `Optocoupler_LTV-817S_SMD-4P` | KiCad `Package_DIP.3dshapes/SMDIP-4_W9.53mm.step` | stand-in; lead span 9.53 vs 10.16 mm |
| `PinHeader_2x10` **instance J20 only** | `3dmodels/LaunchPad_LAUNCHXL-F28379D_Shadow.step` (opacity 0.45) | LaunchPad envelope 129.9 × 58.4 × 1.6 at z = 11.0 mm + its four 2×10 sockets, relative to J20 pad 1 (`S9_BOARD_SETUP.md` §1.1). Replace with TI's STEP when downloaded |

Off-board and therefore not modelled: the LEM LA 100-P board, the DB37 90° adapter, the PrimeSTACK.

**2026-09-23 (S11):** `MountingHole_4.3mm_M4_ISO7380` — straight re-export of KiCad's MountingHole lib (Ø4.3 NPTH, button-head courtyard r 4.05); H1–H4 moved to it (M3 → M4, user). `MountingHole_3.2mm_M3` / `_Pad` stay in the lib, now unused. Renders (`kicad-cli fp export svg`).

**2026-09-17 (pre-S10):** `DSUB-37_Socket_Horizontal_P2.77x2.54mm_MountingHoles` shell pads renamed `SH`/`SH` → `G1`/`G2` so they match the `DSUB-37_Socket` symbol's shield pins (`SHIELD_DB37`); the six S8 symbols (SN65HVD230, LTV-817S, SolderJumper_2_Bridged, D_TVS_Dual_CAN, Conn_02x04_Counter_Clockwise, L_CommonMode) were restored from commit `9cf0c5a` after a restore had dropped them. 50 symbols / 59 units render.

**2026-09-17 (pre-S10):** added **`D_Zener_SOT-23`** — `D_Zener` with SOT-23 pin numbers (**1 = A, 3 = K**, pin 2 NC absent), default footprint `SOT-23`. Used by D2 (BZX84C15). The generic `D_Zener` (K = 1, A = 2) put the cathode on the anode pad and the anode on the NC pad. 51 symbols / 60 units render.

**2026-09-23 (post-routing):** added **`Logo_UFPR_Formula_32mm`**, the Fórmula UFPR logo from `logo.png` (154 × 50 px). It was upscaled ×10 (bicubic), thresholded, traced with `potrace -b geojson` (y-axis flipped), and fractured into 16 filled `fp_poly` on F.SilkS, 32 × 10.4 mm. Attributes are `board_only`, `exclude_from_bom` and `exclude_from_pos_files`, so there is no schematic symbol and no parity entry. Don't shrink it much below 30 mm: the car outline and "FÓRMULA" strokes are 1 source px ≈ 0.2 mm, and JLC's silk minimum is 0.15 mm. Placed as LOGO1.

**2026-09-23:** added **`Logo_UFPR_Formula_16mm`**, a half-size variant (16 × 5.2 mm, 15 polys, same attributes). Before tracing, the ×10 bitmap's ink was dilated by 3 px per side (`MinFilter(7)`), so the thinnest strokes are ≈ 0.17 mm rather than 0.10 mm, above JLC's 0.15 mm silk minimum. The cost is that some small counters and slits close up. It isn't placed; swap LOGO1 with *Change Footprint* if wanted.
