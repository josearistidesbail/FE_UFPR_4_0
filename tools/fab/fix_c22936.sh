#!/bin/sh
# S12: R35 R67 R77 R89 R104 R118 (all "1M") carry LCSC C22936 = 1 ohm (Uniroyal 0603WAF100KT5E).
# The 1 Mohm part is C22935 (0603WAF1004T5E, Basic).  Idempotent; touches only the LCSC property lines.
# Also rewrites the six footprints' LCSC field on the board (DRC --schematic-parity compares the two).
# Run from the project dir with eeschema AND pcbnew CLOSED (no ~*.lck).
set -e
for f in current_sense.kicad_sch encoder.kicad_sch gate_drive.kicad_sch FE_UFPR_4_0.kicad_pcb; do
  [ -e "~${f}.lck" ] && { echo "$f is open in KiCad - close it first"; exit 1; }
  n=$(grep -c '(property "LCSC" "C22936"' "$f" || true)
  sed -i 's/(property "LCSC" "C22936"/(property "LCSC" "C22935"/' "$f"
  echo "$f: $n occurrence(s) rewritten"
done
grep -c 'C22936' current_sense.kicad_sch encoder.kicad_sch gate_drive.kicad_sch FE_UFPR_4_0.kicad_pcb || true
