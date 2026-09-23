#!/bin/sh
# S12: rebuild the JLCPCB order package into fab/ from the committed KiCad files.
#   sh tools/fab/make_package.sh [boards]        (default 5)
# Writes fab/gerbers/ (11 gerbers + Excellon PTH/NPTH + maps), fab/FE_UFPR_4_0_BOM.csv, fab/FE_UFPR_4_0_CPL.csv,
# fab/jlc_verify.{json,md} (live JLCSearch stock/price/value check, ~1 min) and fab/FE_UFPR_4_0_gerbers.zip
# (zip is git-ignored; upload the zip + BOM + CPL).  Intermediate kicad-cli exports go to a temp dir.
# Refuses to run with the board or a sheet open in KiCad (lock files) so the exports match what is on disk.
set -e
cd "$(dirname "$0")/../.."
BOARDS=${1:-5}
# S12 decision D2: Economic single-side PCBA; the 12 B.Cu parts are hand-soldered by the team (empty this to order two-sided)
HAND=R2,R3,D17,C119,C25,C26,C27,C28,R118,R119,C113,C120
for l in ~FE_UFPR_4_0.kicad_pcb.lck ~*.kicad_sch.lck; do [ -e "$l" ] && { echo "KiCad has $l open - save and close first"; exit 1; }; done
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
mkdir -p fab/gerbers
rm -f fab/gerbers/*.gbr fab/gerbers/*.drl fab/gerbers/*.gbrjob

kicad-cli sch export bom --fields 'Reference,Value,Footprint,LCSC,${QUANTITY}' --labels 'Reference,Value,Footprint,LCSC,Qty' \
    --group-by 'Value,Footprint,LCSC' -o "$TMP/bom.csv" FE_UFPR_4_0.kicad_sch
kicad-cli pcb export pos --format csv --units mm --side both --use-drill-file-origin --exclude-dnp -o "$TMP/pos.csv" FE_UFPR_4_0.kicad_pcb
kicad-cli pcb export gerbers --board-plot-params --layers F.Cu,In1.Cu,In2.Cu,B.Cu,F.Mask,B.Mask,F.SilkS,B.SilkS,F.Paste,B.Paste,Edge.Cuts \
    --subtract-soldermask --use-drill-file-origin -o fab/gerbers/ FE_UFPR_4_0.kicad_pcb
kicad-cli pcb export drill --format excellon --excellon-units mm --excellon-separate-th --generate-map --map-format gerberx2 -o fab/gerbers/ FE_UFPR_4_0.kicad_pcb

# board corner = (127.95, 219.9) in KiCad page coordinates (Edge.Cuts bottom-left); the board has no aux origin
python3 tools/fab/jlc_bomcpl.py "$TMP/bom.csv" "$TMP/pos.csv" fab --rotations tools/fab/jlc_rotations.json --origin 127.95,219.9 ${HAND:+--hand-solder $HAND}
python3 tools/fab/jlc_verify.py "$TMP/bom.csv" --boards "$BOARDS" --out fab/jlc_verify.json --md fab/jlc_verify.md
cp "$TMP/bom.csv" fab/kicad_bom.csv

(cd fab/gerbers && rm -f ../FE_UFPR_4_0_gerbers.zip && zip -q ../FE_UFPR_4_0_gerbers.zip *.gbr *.drl *.gbrjob)
echo "package in fab/:"; ls -l fab | awk 'NR>1{print "  "$5"\t"$9}'
echo "gerbers: $(ls fab/gerbers | wc -l) files, zip $(stat -c %s fab/FE_UFPR_4_0_gerbers.zip) bytes"
