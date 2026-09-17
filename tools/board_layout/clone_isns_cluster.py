#!/usr/bin/env python3
"""Clone the hand-made ISNS_B placement onto the ISNS_A and ISNS_C channels.

The three current-sense channels are electrically identical (S6), so the board
convention "repeated channels drawn geometrically identical" applies to the
layout too.  Channel B was placed by hand around U13; this script copies every
B passive's offset *relative to U13* onto the matching A part relative to U12
and the matching C part relative to U14.  Rotations and the Reference/Value
silkscreen text offsets are copied verbatim, so the three clusters are
translations of one another - a mismatch is then visible by eye.

The anchors (U12/U13/U14) are NEVER moved: the user places the op-amps, this
script only arranges the parts around them.

Run from anywhere:  python3 tools/board_layout/clone_isns_cluster.py [--dry-run]
"""
import re
import sys
from pathlib import Path

PCB = Path(__file__).resolve().parents[2] / "FE_UFPR_4_0.kicad_pcb"

SRC_ANCHOR = "U13"
DST_ANCHORS = {"A": "U12", "C": "U14"}

# B refdes -> (A refdes, C refdes).  Derived from the pad nets: every entry was
# checked to carry the same net roles (ISNS_x_INT_P, LEM_x_M, ...) and the same
# value + footprint in all three channels.  The two 47R LEM burden resistors are
# interchangeable (same net pair); they are mapped in index order.
MAP = {
    "C69": ("C62", "C76"),   # 2.2nF  INT integrator/feedback
    "C70": ("C64", "C77"),   # 1nF    RAW anti-alias
    "C71": ("C63", "C78"),   # 2.2nF  INT_P bucket
    "C72": ("C65", "C79"),   # 1nF    LEM_x_M input filter
    "C73": ("C66", "C80"),   # 4.7nF  LEM feedback
    "C74": ("C67", "C81"),   # 4.7nF  LEM_P / ISNS_VREF
    "C75": ("C68", "C82"),   # 22nF   ADC charge bucket (0805)
    "R75": ("R63", "R87"),   # 20.0k  RAW -> INT_P
    "R76": ("R65", "R88"),   # 12.0k  INT feedback
    "R77": ("R67", "R89"),   # 1M     RAW bleed
    "R78": ("R64", "R90"),   # 20.0k  ISNS_RTN -> INT_N
    "R79": ("R66", "R91"),   # 12.0k  INT_P -> GND
    "R80": ("R68", "R92"),   # 47.0R  LEM burden (1206)
    "R81": ("R69", "R93"),   # 47.0R  LEM burden (1206)
    "R82": ("R70", "R94"),   # 12.0k  LEM_M -> LEM_P
    "R83": ("R71", "R95"),   # 12.0k  ISO_COM -> LEM_N
    "R84": ("R72", "R96"),   # 4.99k  LEM feedback
    "R85": ("R73", "R97"),   # 4.99k  LEM_P -> ISNS_VREF
    "R86": ("R74", "R98"),   # 100R   ADC series
    "JP4": ("JP3", "JP5"),   # source select INT/LEM
}

AT_RE = re.compile(r'^(\s*)\(at (-?[\d.]+) (-?[\d.]+)(?: (-?[\d.]+))?\)\s*$')


def split_footprints(lines):
    """Yield (ref, start, end) for every top-level footprint block."""
    out = []
    i = 0
    while i < len(lines):
        if lines[i].startswith("\t(footprint "):
            start = i
            depth = 0
            j = i
            while j < len(lines):
                depth += lines[j].count("(") - lines[j].count(")")
                if depth == 0:
                    break
                j += 1
            block = lines[start:j + 1]
            ref = None
            for k, ln in enumerate(block):
                m = re.match(r'\s*\(property "Reference" "([^"]+)"', ln)
                if m:
                    ref = m.group(1)
                    break
            out.append((ref, start, j))
            i = j + 1
        else:
            i += 1
    return out


def block_info(lines, start, end):
    """Footprint (at) line index, plus every *child* (at) line index.

    Inside a footprint, pad / text / property coordinates are stored in the
    footprint's own unrotated frame, but their ANGLE token is absolute (board
    frame).  Rotating a footprint by editing only its own (at ...) therefore
    leaves every pad turned the wrong way - KiCad flags it as
    lib_footprint_mismatch and rectangular pads really do end up rotated
    wrongly (it made the JP5 jumper pads short in a first attempt).  Since
    source and destination are the same library footprint placed at the same
    rotation, every child (at ...) line can simply be copied verbatim.
    """
    info = {"lib": lines[start].strip(), "at_idx": None, "children": []}
    depth = 0
    for i in range(start, end + 1):
        ln = lines[i]
        before = depth
        depth += ln.count("(") - ln.count(")")
        m = AT_RE.match(ln)
        if not m:
            continue
        if before == 1 and info["at_idx"] is None:
            info["at_idx"] = i
            info["at"] = (float(m.group(2)), float(m.group(3)),
                          float(m.group(4)) if m.group(4) else 0.0)
        elif before > 1:
            info["children"].append((i, ln))
    return info


def main():
    dry = "--dry-run" in sys.argv
    lines = PCB.read_text().splitlines(keepends=True)
    fps = split_footprints(lines)
    by_ref = {}
    for ref, s, e in fps:
        if ref:
            by_ref[ref] = (s, e)

    missing = [r for r in [SRC_ANCHOR, *DST_ANCHORS.values(), *MAP,
                           *[x for p in MAP.values() for x in p]] if r not in by_ref]
    if missing:
        sys.exit("refdes not on the board: %s" % ", ".join(missing))

    anchors = {}
    for tag, ref in [("B", SRC_ANCHOR)] + list(DST_ANCHORS.items()):
        s, e = by_ref[ref]
        inf = block_info(lines, s, e)
        anchors[tag] = inf
        print("anchor %-4s %-5s at (%.3f, %.3f, %.1f)" % (tag, ref, *inf["at"]))
    if anchors["B"]["at"][2] != anchors["A"]["at"][2] or \
       anchors["B"]["at"][2] != anchors["C"]["at"][2]:
        sys.exit("anchor op-amps are not at the same rotation - a pure "
                 "translation would not reproduce the cluster; aborting.")

    bx, by, _ = anchors["B"]["at"]
    edits = {}          # line index -> new text
    moved = 0
    for src, dsts in MAP.items():
        ss, se = by_ref[src]
        sinf = block_info(lines, ss, se)
        dx, dy, rot = sinf["at"][0] - bx, sinf["at"][1] - by, sinf["at"][2]
        for tag, dst in zip(("A", "C"), dsts):
            ds, de = by_ref[dst]
            dinf = block_info(lines, ds, de)
            if dinf["lib"] != sinf["lib"]:
                sys.exit("%s and %s use different footprints:\n  %s\n  %s"
                         % (src, dst, sinf["lib"], dinf["lib"]))
            ax, ay, _ = anchors[tag]["at"]
            nx, ny = round(ax + dx, 4), round(ay + dy, 4)
            indent = AT_RE.match(lines[dinf["at_idx"]]).group(1)
            edits[dinf["at_idx"]] = "%s(at %s %s%s)\n" % (
                indent, fmt(nx), fmt(ny),
                "" if rot == 0 else " " + fmt(rot))
            # same library footprint at the same rotation => every child (at)
            # line (pads, silk text, property fields) is identical; copy them
            # so the pads are turned the right way and the silkscreen matches.
            if len(sinf["children"]) != len(dinf["children"]):
                sys.exit("%s and %s have %d vs %d child (at) lines - refusing "
                         "to copy blind" % (src, dst, len(sinf["children"]),
                                            len(dinf["children"])))
            for (_, stext), (didx, _) in zip(sinf["children"], dinf["children"]):
                edits[didx] = stext
            print("  %-4s %-5s -> %-5s (%9.3f, %9.3f, %6.1f)"
                  % (tag, src, dst, nx, ny, rot))
            moved += 1

    if dry:
        print("\n--dry-run: %d footprints would move, %d lines touched"
              % (moved, len(edits)))
        return
    for i, txt in edits.items():
        lines[i] = txt
    PCB.write_text("".join(lines))
    print("\n%d footprints moved, %d lines rewritten in %s" % (moved, len(edits), PCB.name))


def fmt(v):
    s = ("%.4f" % v).rstrip("0").rstrip(".")
    return s if s not in ("", "-0") else "0"


if __name__ == "__main__":
    main()
