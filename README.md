# FE_UFPR 4.0 — motor-controller interface board (Formula UFPR)

KiCad 10 project for the board that sits between a **TI LAUNCHXL-F28379D** (runs the FOC firmware) and an
**Infineon PrimeSTACK 6PS04512E43W39693** inverter driving an **EMRAX 208** motor. It replaces the 2-layer
FE_UFPR 3.0 board (kept next to this repo as `../FE_UFPR_3_0`, reference only).

## What the board does

| Block | What it carries | Design doc |
|---|---|---|
| Power | 18–26 V input on J1 → `+13V5_GATE` (LMR33630, 400 kHz) → `+5V` (TPS62933F, 1.2 MHz) → `+3V3` (AMS1117); isolated ±15 V for the LEMs (URA2415YMD) | [`S3_POWER_DESIGN.md`](S3_POWER_DESIGN.md) |
| Gate drive | Six 3.3 V PWM lines → UCC27524 → 13.5 V module inputs on the DB37 (J2); hardware enable = GPIO66 AND GPIO131 AND the cockpit main switch | [`S4_GATE_DRIVE_DESIGN.md`](S4_GATE_DRIVE_DESIGN.md) |
| Module status | OC A/B/C, over-temperature and DC-link OV flags into the MCU trip zones; module NTC and DC-link voltage into the ADC | [`S5_MODULE_STATUS_DESIGN.md`](S5_MODULE_STATUS_DESIGN.md) |
| Current sense | Three LEM LA 100-P on J3 (burdens on this board), or the module's own sensors; JP3–JP5 pick the source per phase | [`S6_CURRENT_SENSE_DESIGN.md`](S6_CURRENT_SENSE_DESIGN.md) |
| Encoder | Renishaw RM44AC analog sin/cos receiver on J4, matched SIN/COS chains, 1.5 V bias at the ADC | [`S7_ENCODER_DESIGN.md`](S7_ENCODER_DESIGN.md) |
| Motor temperature | EMRAX KTY81-210 on J4, with a +3V3 rail monitor so the firmware cancels the excitation | [`S9_5_MOTOR_TEMP_DESIGN.md`](S9_5_MOTOR_TEMP_DESIGN.md) |
| Vehicle I/O | CAN-A, opto-isolated main-switch and start inputs, `+5V_VEH`, all on J5 | [`S8_INTEGRATION_DESIGN.md`](S8_INTEGRATION_DESIGN.md) |

The LaunchPad plugs into the board's BoosterPack sockets (J20–J23). Pin map, scaling constants and the DB37 table:
[`CLAUDE.md`](CLAUDE.md) (authoritative) and [`DB37_PINOUT.md`](DB37_PINOUT.md). System-level choices (power tree,
grounding, LaunchPad jumpers): [`ARCHITECTURE.md`](ARCHITECTURE.md).

**Board:** 178 × 130 mm, 4 layers (JLC04161H-7628, 1.6 mm, 1 oz outer), one solid GND plane on L2. All connectors on
the top face; J3/J4/J5 are vertical Deutsch DT15 headers. JLC economic PCBA, plus a hand-soldered set (bottom-side
parts, connectors, op-amps, a few cost-cut lines): [`fab/FE_UFPR_4_0_HANDSOLDER_BOM.csv`](fab/FE_UFPR_4_0_HANDSOLDER_BOM.csv),
Deutsch parts in [`DEUTSCH_BOM.csv`](DEUTSCH_BOM.csv).

## Status (2026-11-05)

Two boards built. Board 1 is in bring-up (sequence in [`S12_FAB_PACKAGE.md`](S12_FAB_PACKAGE.md) §5): power, gate
enable, PWM, the trip path (OC A/B) and the analog front ends pass; the motor runs closed-loop current and speed control
on a 31 V bench link. Board 1 needed four reworks for design defects, all listed with their rev 4.1 fix in
[`OPEN_ITEMS.md`](OPEN_ITEMS.md):

- D12 (the LaunchPad 5 V feed diode) is drawn backwards: refit it rotated.
- The board doesn't supply the LaunchPad's 3.3 V: wire U3's tab to J20 pin 1 and remove LaunchPad JP1–JP3.
- The F1 → Q1 24 V link is a 0.25 mm track: bridge it with a wire.
- The PrimeSTACK's current outputs idle at 0 V, so the internal current path clips: run on the LEMs (JP3–JP5 at 2-3).

Still open: the DC-link reading (about 4× low at 31 V), the OC C / OT / OV checks, the start input, and an ADC
interference shared by every input that the firmware currently works around. What is measured and what is still
assumed: [`VERIFIED_FACTS.md`](VERIFIED_FACTS.md).

## Repository layout

| Path | Contents |
|---|---|
| `FE_UFPR_4_0.kicad_{pro,sch,pcb,dru}` | The project: root sheet, board, design rules |
| `power`, `gate_drive`, `module_status`, `current_sense`, `encoder`, `launchpad`, `vehicle_io` `.kicad_sch` | The seven sub-sheets |
| `FE_UFPR_4_0.kicad_sym`, `FE_UFPR_4_0.pretty/`, `3dmodels/` | Project libraries: every part placed comes from these, nothing from global libraries ([`LIBRARY.md`](LIBRARY.md)) |
| `FE_UFPR_4_0.step` | 3D export of the assembled board |
| `fab/` | JLCPCB order package (gerbers, BOM, CPL, hand-solder BOM, assembly tracker); generated, see [`fab/README.md`](fab/README.md) |
| `tools/schematic_layout/` | Sheet generators and the netlist gate (`golden.net`, `netcmp.py`) |
| `tools/board_layout/` | Placement and board-edit scripts from the layout sessions |
| `tools/fab/` | `make_package.sh` and the JLC stock/rotation helpers |
| `datasheets/` | PrimeSTACK, LaunchPad (SPRUI77), RM44, LEM LA 100-P, Deutsch drawings, other part datasheets |
| `*.md` | Design notes per session (`S3_…` to `S12_…`), decisions, open items, verified facts, tooling notes |

## Working on the design

You need KiCad 10 (`kicad-cli` 10.0.x). Open `FE_UFPR_4_0.kicad_pro`; the libraries resolve through `${KIPRJMOD}`.
Before committing a change, run the checks the project relies on:

```sh
kicad-cli sch erc --severity-all FE_UFPR_4_0.kicad_sch
kicad-cli pcb drc --severity-all --schematic-parity FE_UFPR_4_0.kicad_pcb

# layout-only changes must leave the netlist identical
kicad-cli sch export netlist --format kicadsexpr -o /tmp/new.net FE_UFPR_4_0.kicad_sch
python3 tools/schematic_layout/netcmp.py tools/schematic_layout/golden.net /tmp/new.net
```

Rebuild the order package with KiCad closed: `sh tools/fab/make_package.sh`. The rest of the rules (netclasses,
part selection, schematic drawing style, the traps that have bitten earlier sessions) are in [`CLAUDE.md`](CLAUDE.md)
and [`TOOLING_NOTES.md`](TOOLING_NOTES.md).

## Documents

| File | Use it for |
|---|---|
| [`REDESIGN_PLAN.md`](REDESIGN_PLAN.md) | The session-by-session roadmap and its exit criteria |
| [`DECISION_LOG.md`](DECISION_LOG.md) | Every design decision with its reason (append-only) |
| [`OPEN_ITEMS.md`](OPEN_ITEMS.md) | What is still open, who owns it, and the rev 4.1 list |
| [`VERIFIED_FACTS.md`](VERIFIED_FACTS.md) | Bench and datasheet facts vs assumptions; the board 1 bring-up log |
| [`S12_FIRMWARE_HANDOFF.md`](S12_FIRMWARE_HANDOFF.md) | The board-to-firmware contract: pins, ADC map, scaling constants |
| [`S12_FAB_PACKAGE.md`](S12_FAB_PACKAGE.md) | Fab package, CPL audit, assembly and the bring-up sequence |
| [`JLC_PARTS.md`](JLC_PARTS.md) | Vetted LCSC parts and stock findings |
| [`CLAUDE.md`](CLAUDE.md) | Current state and working rules, kept for the Claude Code sessions used on this project |

## Firmware

The FOC firmware lives in [`foc-f28379d-fsae`](https://github.com/josearistidesbail/foc-f28379d-fsae) (branch
`sensorless-observer`, build configuration `Production_CtrlV2_EMRAX_Resolver`). Its pin map and constants are in
`foc_f28379d/config/hw/hw_control_v2.h`; this board's side of the contract is
[`S12_FIRMWARE_HANDOFF.md`](S12_FIRMWARE_HANDOFF.md).

## Branches and tags

Current work is on `dt15-vertical` (the DT15 connector swap and everything since). Tags: `v4.0-schematic-freeze`,
`v4.0-fab-candidate`.
