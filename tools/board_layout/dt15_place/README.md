# dt15_place — the 2026-09-24 re-placement/re-route for the vertical DT15 headers (applied, kept for the record)

Run on a scratch copy of the board (same stem, `.kicad_pro` beside it, `FE_UFPR_4_0.pretty` + `3dmodels` symlinked), never in the project dir.
Order: `1_place.py` (outline −32 mm, zones, moves, 12 B.Cu screw-head keepouts) → DRC/`clean_dangling.py` loop → `2_purge.py` (orphan vias, shorts, refill)
→ loop again → `3_route.py` (satellite fine placement, restore the eastern parts of the old routes from the pre-swap board, new tracks, refill)
→ loop → `5_silk.py` (silk outline polygons, hidden refs, text moves) → `6_exchange.py` (re-import the three footprints from the library) → hide the
LCSC/MPN/Manufacturer fields on F.Fab. Result: DRC 5 by-design silk warnings, 0 unconnected, 0 parity. Details in `DECISION_LOG.md` (2026-09-24).
The absolute coordinates inside are for this board only; the scripts are not generic tools.
