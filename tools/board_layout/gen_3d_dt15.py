#!/usr/bin/env python3
"""STEP bodies for the two vertical DEUTSCH DT15 footprints (3dmodels/), same conventions as gen_3d_models.py:
footprint coordinates (x right, y DOWN, mm), y negated on the way in, z = 0 = board top. Sources: TE customer
drawings C-DT15-12PX rev D2 and C-DT15-08PX-XXXX rev A (datasheets/), see the footprint (descr) strings.
Run with the cadquery venv: <scratch>/cqenv/bin/python gen_3d_dt15.py"""
import os
import cadquery as cq
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '3dmodels')
os.makedirs(OUT, exist_ok=True)
GREY, BLACK, METAL = (.55, .55, .55), (.12, .12, .12), (.80, .76, .62)

def B(x0, x1, y0, y1, z0, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, -y1, z0))

def pin(x, y, d, z0, z1):
    return cq.Workplane("XY").circle(d / 2).extrude(z1 - z0).translate((x, -y, z0))

def save(name, parts):
    a = cq.Assembly(name=name)
    for i, (shape, col) in enumerate(parts):
        a.add(shape, name=f"{name}_{i}", color=cq.Color(*col))
    p = os.path.join(OUT, name + '.step'); a.save(p); print('wrote', os.path.relpath(p))

def dt15(name, L, pins_xy, screw_y, panel_y, panel_d, shroud_L, colour):
    W = 35.26
    body = B(-W / 2, W / 2, -L / 2, L / 2, 0, 15.52).edges("|Z").fillet(6.35)      # base block up to the flange face
    for sx in (-10.67, 10.67):
        for sy in (-screw_y, screw_y):
            body = body.cut(pin(sx, sy, 2.79, -1, 8.0))                              # #4-20 blind holes from the PCB side
    for py in (-panel_y, panel_y):
        body = body.cut(pin(0, py, panel_d, 11, 16))                                 # #6-19 panel screw holes in the flange
    shroud = B(-11.125, 11.125, -shroud_L / 2, shroud_L / 2, 15.52, 30.12).edges("|Z").fillet(2.0)
    shroud = shroud.cut(B(-9.4, 9.4, -shroud_L / 2 + 1.8, shroud_L / 2 - 1.8, 18.0, 31))   # plug cavity
    pins = [(pin(x, y, 1.57, -3.10, 18.0), METAL) for x, y in pins_xy]
    save(name, [(body, colour), (shroud, colour)] + pins)

rows12 = (11.11, 6.67, 2.22, -2.22, -6.67, -11.11)
dt15('DEUTSCH_DT15-12P_Vertical', 59.21, [(x, y) for x in (-4.56, 4.56) for y in rows12], 17.54, 20.28, 3.10, 49.3, GREY)
rows8 = (7.175, 2.73, -2.73, -7.175)
dt15('DEUTSCH_DT15-08P_Vertical', 55.12, [(x, y) for x in (-4.56, 4.56) for y in rows8], 13.6, 22.605, 3.30, 36.45, GREY)
