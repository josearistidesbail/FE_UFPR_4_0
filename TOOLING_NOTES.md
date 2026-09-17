# FE_UFPR v4.0 — Tooling notes (KiCad, MCP server, kicad-cli, JLCSearch, TE)

New tool quirks go **here**; `CLAUDE.md` keeps only the handful of hard gates.
(Moved out of `CLAUDE.md` on 2026-09-17, verbatim.)

## Tooling notes

- **S9.6:** the LaunchPad now sits on TOP; J20–J23 are `PinHeader_2x10` on F.Cu. `tools/board_layout/place_s9.py` reproduces the whole placement (370/370) — re-run it rather than hand-moving blocks; `add_lp_shadow.py` redraws the LaunchPad shadow on `Dwgs.User`. `kicad-cli pcb export ipcd356` checks pad nets against `golden.net`. Moving footprints by file edit is safe only with unchanged rotation.

- KiCad **10.0.5**; MCP server for schematic/PCB editing, ERC/DRC, BOM/gerber export, `snapshot_project`.
- `kicad-cli sym export svg` / `fp export svg` is the fastest way to prove a library actually parses — use it after any hand-edit of `.kicad_sym` / `.kicad_mod`.
- Datasheets via WebFetch/WebSearch (RM44AC, 6PS04512E43W39693, LA 100-P, TC4468, LAUNCHXL-F28379D).
- Temp exports go to the session scratchpad, not the project directory.
- **Never trust a hand-generated `.kicad_sch` until `kicad-cli sch export netlist` agrees with a golden baseline.** KiCad fails silently on a malformed token (it drops the rest of the sheet and still exits 0), and its connectivity rules are stricter than they look — see the four S7.5 behaviours in the Decision Log. The generator scripts and the checker live in the session scratchpad; the invariant they enforce is **149 nets / 745 nodes, node sets identical**.
- `kicad-cli sch erc --severity-all` groups some sub-sheet violations under the root's section — read the coordinates, not the section header, to attribute them.
- **PCB session workflow (S9):** MCP `sync_schematic_to_board` imports the netlist (equivalent of F8); `batch_move_components` places (flip with `layer: "B.Cu"` — reported as rotation 180, geometry correct); `place_component` with `boardPath` + `FE_UFPR_4_0:` prefix adds library footprints. **Edge.Cuts by file edit** — `replace_board_outline`/`clear_board_outline` crash on the SWIG backend. **After ANY external edit of the `.kicad_pcb`, call `open_project` before the next MCP write** or its auto-save is refused and the change lives only in memory. The gate is `kicad-cli pcb drc --severity-all --format json`; the MCP `check_courtyard_overlaps` is bounding-box only (phantoms on L-shaped courtyards) and a *malformed* courtyard is skipped by KiCad's overlap test — DRC must report zero `malformed_courtyard` before its overlap result means anything.
- **Render and look** applies to the board too: `get_board_2d_view` (file mode) after every placement pass; the KiCad GUI holding the project open (`~*.lck`) does not see file-level edits until the board is reloaded.
- **Render and look** after any regeneration: `kicad-cli sch export svg` → `rsvg-convert` → crop. The netlist gate cannot see labels drawn over parts or scrambled notes (S8 found both, a session late).
- **KiCad label/field orientation rules** (measured S8, encoded in `layoutlib`/`sheetedit`): a vertical global label's *justify* picks the side of the anchor (`right` = hangs below); field justification is transformed by the symbol's mirror/180° rotation; `(text …)` file order changes on every regeneration, so address notes by content.
- `dump.py`/`conncheck` reported both S8 sheets as "1 net, 87 unlabelled pins" while `kicad-cli` proved them fully connected — a known false alarm, still not the gate.
- **TE `DocumentDelivery` rate-limits**: a 222-request burst earned a ~1 h 403 for this address. Probe a few names with a pause between them. A missing drawing answers HTTP 500 + HTML.
- **JLCSearch**: `/api/search?q=<LCSC or MPN>` gives `is_basic`/`is_preferred`/stock/price for ICs too (the category endpoints only cover passives), but the two disagree on stock — treat both as snapshots.
  ⚠ **`/api/search` silently returns `{"components":[]}` for passives that exist** (2026-09-17: `C25804`,
  10 k 0603 Basic with **37 M in stock**, and its MPN `0603WAF1002T5E`, both come back empty). The search
  index is incomplete. **Never conclude a part is delisted from `/api/search` alone** — cross-check
  `/resistors/list.json?package=0603&resistance=10000` (or `/capacitors/list.json`), which is authoritative
  for passives and returns `is_basic`/`tolerance_fraction`/`stock`/`price1`.
  Also: **`urllib` gets HTTP 403** — the endpoint requires a `User-Agent`. Use `curl`, or set the header.
- The MCP `batch_add_components` does not add the library symbol's `LCSC` property to every instance — `vio_layout.py` sets it for its own parts; check `grep -c '(property "LCSC"'` equals the symbol count after any MCP add.
