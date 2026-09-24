# S9.6 — Vertical mount, top-side LaunchPad, re-placement (2026-09-14)

**Status: done.** Board re-placed for a **vertical** installation directly on the PrimeSTACK's X1
connector through a DB37 right-angle adapter, **every connector on the top side**, the LaunchPad
**above** the board on male pin headers. 379 footprints placed, `kicad-cli pcb drc --severity-all`
**0 errors** (403 silkscreen warnings, S11's), schematic parity 0, ERC 0. The schematic changed in
exactly one respect (the four header footprints and their LCSC field); `golden.net` was re-baselined
with that delta and nothing else (219 nets, node sets identical). **The user routes S10/S11.**
The precharge/contactor request is **not** in this change — and was **dropped 2026-09-17** (see §5).

---

## 1. What changed and why

| Requirement (user, 2026-09-14) | Consequence |
|---|---|
| The board stands **vertical**; no cable to the module; direct mount on X1, which is on the module's top face and **faces the 3-phase terminal side** (user-verified on the module — an earlier in-session reading of the drawing as "DC-link side" was wrong) | The board sits **above the module**, DB37 edge down, on a **90° adapter**. First choice: **L-com DG9037MF1/MF2/MF3** (low-profile right-angle DB37 M/F adapter, shielded, ~25 mm, ≈ $46–54; the three variants differ only in exit direction). Fallback: a passive two-D-sub adapter PCB. The board is **agnostic**: its right-angle DB37 socket accepts the adapter's male end or the cable plug identically, so prototyping with the cable needs no change. |
| Vertical connectors preferred | Not needed once the board is vertical: a **right-angle** connector on a **side** edge has a horizontal mating axis. J3/J4 (left edge) and J5 (top edge) keep the DTM13 right-angle parts — there is no vertical board-mount DTM13 in TE's repository (S7 probe). J1 (Mini-Fit 5566) was already a vertical part. The DB37 stays right-angle so the plug/adapter arrives from below. | **Superseded 2026-09-23: J3/J4/J5 are vertical DT15 headers (sample-program constraint); TE does list vertical DTM as DTM15, the S7 probe missed the name — `DECISION_LOG.md`.**
| **All connectors top side** — no bottom clearance | The BoosterPack sockets were the only bottom-side parts. They become **`PinHeader_2x10_P2.54mm_Vertical` on F.Cu**, male pins up; the LaunchPad sits on them on **its own bottom-side receptacles** (the user's 3.0 board mated exactly this way). **S2's premise "the stock LaunchPad has male pins on top only" was wrong.** |

### 1.1 The LaunchPad on top — geometry

Same XY grid as S9 (J1-pin-1 = J20 pad 1 at board-local (66, 14), 43.18 × 63.5 mm), component side
up, USB end at the service edge. Because the LaunchPad is 129.9 mm long and the board 130 mm, it
**overhangs the top edge by 17.9 mm, above the board** (it cannot be moved down: its far end would
meet the DB37 body). Its shadow, x 59.6–118.0 / y −17.9–112.0 board-local, is drawn on **Dwgs.User**
(`tools/board_layout/add_lp_shadow.py`). Stack ≈ 2.5 mm header base + ~8.5 mm receptacle = **~11 mm**;
anything under the shadow must stay **≤ 8 mm** tall — C1 (Ø8 × 10.5 electrolytic) is the only part
that mattered and the power column now starts at x = 120. **Test points under the shadow are
unreachable with the LaunchPad fitted** (TP20/23, TP36, TP42–TP50, TP53/54 among others) — S11 decides
which to pull out.

### 1.2 Pad map verification (the S9 method, repeated)

The header footprint at rotation 0 on F.Cu has pad 1 → pad 2 = +x and pad 1 → pad 3 = +y, read back
from the board file — the same relation S9 verified for the bottom sockets, so the pin table in
`S9_BOARD_SETUP.md` §1 holds unchanged. Nets were then checked from KiCad's own **IPC-D-356 export**
(`kicad-cli pcb export ipcd356`) against `golden.net`: **35 netted pads match, 45 no-connects
match, 80/80.**

### 1.3 Floorplan deltas (board-local mm, `tools/board_layout/place_s9.py`)

| Item | S9 | S9.6 | Why |
|---|---|---|---|
| J5 (vehicle 8-way) | x 72, top edge | **x 39.5**, top edge | its vertical flange (off-board, x −11.7…57.4) must clear the LaunchPad overhang (x ≥ 59.6). The flange now protrudes 11.7 mm past the board's top-left corner, in the air. |
| J4 / J3 / U4 | y 29.7 / 78.8 / 114.0 | **32.9 / 82.0 / 116.2** | J4 must clear J5's housing (y ≤ 11.8); H5 (Ø6.9 courtyard) keeps its place between J4 and J3 at **y 57.3**; U4's courtyard ends 0.6 mm from the bottom edge, pads 2.9 mm |
| power column | x 115–145 | **x 120–145** | LaunchPad shadow ends at 118; `entry` packs C1 first (sort=True) |
| `can_end` block | — | x 40–58, y 12.4–18.6 | D13/R122/JP6/TP49/50 under J5's CAN cavities (x 45.8) |
| `mot` block | hand-placed S9.5 | x 40–64, y 48–56.4 | the S9.5 parts (R129–R132, C120–C122, D18, TP53/54) plus the J4 shield tie (R118/R119/C113) now in the generator; C120 is beside J4 |
| C54–C57 | fell back to `ldo` (overflowed) | `ms_flt` / `db_misc` | they decouple U9–U11 |
| J20–J23 | PinSocket, B.Cu | **PinHeader, F.Cu**, same XY | LaunchPad above |

The generator now places **370/370** from the netlist with no overflow (S9's file overflowed by 10
once the S9.5 parts existed — S9.5 had placed them by hand).

## 2. Verification

- `kicad-cli pcb drc --severity-all`: **0 errors**, 403 warnings (199 silk-over-copper, 199 silk
  overlap, 5 silk-edge — S11), 499 "unconnected" (unrouted; see the S9.5 caveat on that figure).
- `kicad-cli sch erc --severity-all`: **0**.
- Netlist diff vs golden: **only** the four `Footprint` and four `LCSC` fields of J20–J23 → re-baselined.
- IPC-D-356 header pads: 80/80.
- Rendered and looked at (`kicad-cli pcb export svg` → PNG).

## 3. Parts

| Part | LCSC | JLC | Stock | Notes |
|---|---|---|---|---|
| **2×10 male pin header 2.54 mm, PZ254V-12-20P** | **C492427** | Ext | 98 935 (`/api/search`) | J20–J23. No Basic 2×10 male exists; highest stock of the vertical 2×10 lines. Replaces C5116528 (female, now unused). S12 verifies. |

## 4. Tooling notes

- `tools/board_layout/swap_lp_headers.py` rebuilds the four header footprints from the library
  into the board file, copying properties and the pad→net map. The board's footprints carry **no
  `(path …)`** — the MCP placed them, so schematic↔board linkage is **by reference**.
- Moving a footprint by editing its `(at x y r)` line is safe **only when the rotation does not
  change** — pads and texts store absolute angles. Rotation changes go through the MCP mover.
- The kicad-cli subcommand is `pcb export ipcd356` (no hyphen).
- L-com's site returns an HTML page for the `DG9037MFx_2D.pdf` drawings to a non-browser client;
  the user pulls them.

## 5. Not done: the precharge / DC-bus contactor — DROPPED

> **2026-09-17 (user): dropped — precharge is handled externally.** Nothing below was built; kept as the
> record of why the in-inverter form was rejected.

Request: the board supplies 24 V to a contactor that enables the DC bus once the bus voltage reaches a
threshold (the accumulator's precharge would move into the inverter). The 2026 rulebook
(`datasheets/FSAE_Rules_2026_V1.pdf`) does not allow that form:

- **EV.5.6.1** — the precharge circuit is *in the Tractive Battery Pack* and *supplied from the Shutdown Circuit*;
- **EV.5.6.2** — end of precharge by feedback from the intermediate-circuit voltage; ≥ 90 % of TS voltage before the second IR closes;
- **EV.5.6.5** — the precharge relay is a mechanical relay;
- **EV.7.1.2** — the Shutdown Circuit *directly carries* the current driving the IRs and the precharge relay;
- **EV.5.4.3** — no HV outside the container while the IRs are open.

So the contactor, precharge relay and resistor stay in the pack, fed by the shutdown loop, whose
voltage is the GLV voltage (a 24 V coil implies a 24 V GLV/shutdown circuit; our floating 24 V cannot
feed it, and powering the shutdown loop from our battery would bond our island to car ground through
the BMS/IMD/BSPD). **What the board can legitimately add:** one mechanical PCB relay, coil on our
side from a GPIO, **contact in series with the shutdown-circuit feed to the second IR's coil**, closed
when firmware sees V_bus ≥ 0.9 × V_pack (V_pack from the BMS over CAN). Fail-open on CAN loss, reset
or dead board. Needs a two-way connector (J5 is full) and reopens S8's checklist. **Waits for the
team's decision.**

## 6. Open items created here

- **[user]** Pick the L-com variant whose male end exits away from the module top face with the female end on X1; check its ~25 mm body against the phase terminals. Fallback: passive adapter PCB.
- **[user]** Bracket the board — the two jackscrew joints must carry no load. J5's flange slots are now at the top-left, one ear 11.7 mm past the board corner.
- **[user]** Height check above the module: adapter ~25 mm + board 130 + LaunchPad overhang 17.9.
- **[user]** Caliper the LaunchPad's receptacle height (sets the ~11 mm stack) — replaces the socket-insulator item.
- **[S11]** Test points under the LaunchPad shadow; 403 silk warnings.
- ~~**[team]** Precharge architecture (§5); GLV / shutdown-circuit voltage vs the 24 V coil.~~ Dropped 2026-09-17 — external.
