#!/usr/bin/env python3
"""Generate the project's own STEP bodies (3dmodels/) for the footprints KiCad ships no model for.
Run with the cadquery venv: /tmp/.../cqenv/bin/python gen_3d_models.py   (any python with cadquery >= 2.4).
Coordinates below are FOOTPRINT coordinates (x right, y DOWN, mm); KiCad's model space has y UP,
so every y is negated on the way in (helper `B`). z = 0 is the board top surface. Sources: the
footprint (descr) strings + TE customer drawings DTM13-12PA-R005 rev NC / DTM13-08PA-R004 rev D,
Mornsun URA_YMD-6WR3 DS, TDK ACT45B, Littelfuse Nano2, S9_BOARD_SETUP.md 1.1 (LaunchPad)."""
import os, sys
import cadquery as cq
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '3dmodels')
os.makedirs(OUT, exist_ok=True)
BLACK, GREY, WHITE, METAL, RED, BROWN = ((.12,.12,.12), (.55,.55,.55), (.92,.92,.88), (.80,.76,.62), (.75,.15,.15), (.35,.25,.18))

def B(x0, x1, y0, y1, z0, z1):
    """box spanning footprint x0..x1, y0..y1 (y down), z0..z1"""
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, -y1, z0))

def pin(x, y, d, z0, z1):
    return cq.Workplane("XY").circle(d / 2).extrude(z1 - z0).translate((x, -y, z0))

def save(name, parts):
    a = cq.Assembly(name=name)
    for i, (shape, col) in enumerate(parts):
        a.add(shape, name=f"{name}_{i}", color=cq.Color(*col))
    p = os.path.join(OUT, name + '.step')
    a.save(p)
    print('wrote', os.path.relpath(p))

# --- DEUTSCH DTM13-12P-R005: right-angle 12-way, mates toward +y, base flange with two Ø2 bosses on y=0
name = 'DEUTSCH_DTM13-12P-R005_Horizontal'
base = B(-20.51, 20.51, -8.5, 6.5, 0, 3.05).edges("|Z").fillet(3.0)
for hx in (-17.145, 17.145):
    base = base.cut(pin(hx, 0, 2.01, -1, 4))
housing = B(-17.41, 17.41, -8.5, 29.6, 0, 24.28).edges("|Y").fillet(2.5)
housing = housing.cut(B(-14.37, 14.37, 16.6, 30, 3.5, 20.5))          # plug cavity, 13 mm deep
pins = [(pin(x, y, 1.04, -2.79, 3.05), METAL) for x in (-10.4775, -6.2865, -2.0955, 2.0955, 6.2865, 10.4775) for y in (-2.0955, 2.0955)]
save(name, [(base, BLACK), (housing, BLACK)] + pins)

# --- DEUTSCH DTM13-08PA-R004: base block on the board, VERTICAL flange (68.58 x 33.02, 2.29 thick,
# centre 16.61 toward +x, 4.4 mm below the board top), housing beyond the flange, mates toward +y
name = 'DEUTSCH_DTM13-08PA-R004_Horizontal'
base = B(-12.105, 12.105, -5.2, 7.495, 0, 5.18)
zc = (-4.4 + 28.62) / 2
flange = B(-17.68, 50.9, 7.495, 9.785, -4.4, 28.62).edges("|Y").fillet(6.0)
for sx in (-12.07, 12.07):
    for sz in (-15.37, 15.37):
        flange = flange.cut(B(16.61 + sx - 4.445, 16.61 + sx + 4.445, 7, 10.5, zc + sz - 1.27, zc + sz + 1.27))
housing = B(-16.32, 16.32, 9.785, 25.5, zc - 10.11, zc + 10.11).edges("|Y").fillet(2.5)
housing = housing.cut(B(-13.5, 13.5, 13.5, 26, zc - 7.6, zc + 7.6))     # plug cavity, 12 mm deep
pins = [(pin(x, y, 1.04, -3.47, 5.18), METAL) for x in (-6.2865, -2.0955, 2.0955, 6.2865) for y in (-3.175, 3.175)]
save(name, [(base, GREY), (flange, GREY), (housing, GREY)] + pins)

# --- Mornsun URA_YMD-6WR3: 25.4 x 25.4 x 11.7 DIP, five Ø1.0 pins
name = 'Converter_DCDC_Mornsun_URA-YMD-6WR3_THT'
body = B(-12.7, 12.7, -12.7, 12.7, 0, 11.7).edges("|Z").fillet(1.0)
pins = [(pin(x, y, 1.0, -3.0, 0.5), METAL) for x, y in ((-10.16, -2.54), (-10.16, 2.54), (10.16, 10.16), (10.16, 0), (10.16, -10.16))]
save(name, [(body, BLACK)] + pins)

# --- TDK ACT45B common-mode choke: 4.5 x 3.2 x 2.8 body, four terminals
name = 'L_CommonMode_TDK_ACT45B'
body = B(-2.25, 2.25, -1.6, 1.6, 0.3, 2.8)
terms = [(B(x - 0.55, x + 0.55, y - 0.4, y + 0.4, 0, 0.4), METAL) for x in (-2.15, 2.15) for y in (-1.25, 1.25)]
save(name, [(body, BROWN)] + terms)

# --- 2410 (6125 metric) fuse: 6.10 x 2.69 x 2.69 ceramic, 0.9 mm metallised ends
name = 'Fuse_2410_6125Metric'
body = B(-3.05, 3.05, -1.345, 1.345, 0, 2.69).edges("|X").fillet(0.3)
caps = [(B(-3.06, -2.15, -1.35, 1.35, 0, 2.7), METAL), (B(2.15, 3.06, -1.35, 1.35, 0, 2.7), METAL)]
save(name, [(body, WHITE)] + caps)

# --- LaunchPad shadow, relative to J20 pad 1 (S9_BOARD_SETUP.md 1.1 / add_lp_shadow.py): 129.9 x 58.4 x 1.6
# slab whose underside sits 11.0 mm above the board (2.5 mm male-header base + 8.5 mm female socket),
# plus the four 2x10 sockets. J21 = J20 + (43.18, 0); J22 = J20 + (0, 63.5); J23 = J20 + (43.18, 63.5).
name = 'LaunchPad_LAUNCHXL-F28379D_Shadow'
slab = B(-6.43, 52.0, -31.9, 98.0, 11.0, 12.6)
socks = [(B(cx - 2.54, cx + 2.54, cy - 12.7, cy + 12.7, 2.5, 11.0), BLACK) for cx, cy in ((1.27, 11.43), (44.45, 11.43), (1.27, 74.93), (44.45, 74.93))]
save(name, [(slab, RED)] + socks)
