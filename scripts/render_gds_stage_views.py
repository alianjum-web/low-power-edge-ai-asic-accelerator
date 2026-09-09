"""Render layer-filtered PNG views from a signed-off GDSII to illustrate
floorplan (die + power straps), placement (std-cell front-end-of-line
footprint), routing (signal metals + vias), and the full final layout.

These are honest layer-filtered views of the final, DRC/LVS-clean GDSII
(this project did not separately snapshot intermediate floorplan/placement
OpenROAD stages) -- captioned as such in docs/report/report.md and
docs/figures/README.md. Companion to render_gds_screenshots.py (which
renders all layers at once); this one renders the same GDS through
different layer filters to approximate each flow stage.

Requires the `klayout` pip package (python bindings only, not the full
KLayout GUI app) and does not need OpenLane or a PDK install:

    python3 -m venv /tmp/gdsview-venv && /tmp/gdsview-venv/bin/pip install klayout
    /tmp/gdsview-venv/bin/python3 scripts/render_gds_stage_views.py \\
        results/int8_parallel/accelerator_top_project_run_02.gds /tmp/out int8_parallel

Produces <out_dir>/<label>_{floorplan,placement,routing,final}.png.
"""
import sys
import struct
import zlib
import os

import klayout.db as db

LAYER_COLORS = {
    (64, 20): (255, 100, 100), (64, 16): (220, 80, 80),
    (65, 20): (200, 200, 240), (65, 44): (200, 200, 240),
    (66, 20): (220, 40, 40), (66, 16): (200, 30, 30), (66, 44): (180, 20, 20),
    (67, 20): (180, 255, 180),
    (68, 20): (0, 80, 255), (68, 44): (0, 60, 220), (68, 16): (0, 70, 240),
    (69, 20): (0, 200, 255), (69, 44): (0, 170, 230), (69, 16): (0, 180, 240),
    (70, 20): (0, 220, 100), (70, 44): (0, 190, 80), (70, 16): (0, 200, 90),
    (71, 20): (255, 180, 0), (71, 44): (220, 150, 0), (71, 16): (240, 165, 0),
    (72, 20): (200, 0, 200), (72, 44): (170, 0, 170), (72, 16): (185, 0, 185),
    (235, 20): (180, 180, 0), (236, 20): (0, 180, 180),
    (237, 20): (180, 0, 180), (238, 20): (180, 100, 0),
    (36, 20): (0, 0, 0), (36, 44): (0, 0, 0),
}
SKIP_LAYER_NUMS = {67, 78, 93, 94, 95, 122}

STAGE_LAYER_NUMS = {
    "floorplan": {36, 71, 72},        # die boundary + top power straps/rings (met4/met5)
    "placement": {36, 64, 65, 66},    # die boundary + diff/nwell/poly (std-cell FEOL footprint)
    "routing":   {36, 68, 69, 70, 235, 236, 237},  # die boundary + met1-3 + vias
    "final":     None,                # everything (skip list still applies)
}

BG = {
    "floorplan": (250, 250, 252),
    "placement": (250, 250, 245),
    "routing":   (245, 248, 250),
    "final":     (255, 255, 255),
}


def save_png(filename, w, h, pixel_data):
    row_size = w * 3
    img_data = bytearray()
    for y in range(h):
        img_data += b"\x00"
        row_start = y * row_size
        img_data += bytes(pixel_data[row_start:row_start + row_size])

    def make_chunk(ctype, data):
        c = ctype + data
        crc = zlib.crc32(c) & 0xffffffff
        return struct.pack(">I", len(data)) + c + struct.pack(">I", crc)

    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    compressed = zlib.compress(bytes(img_data), 6)
    with open(filename, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(make_chunk(b"IHDR", ihdr))
        f.write(make_chunk(b"IDAT", compressed))
        f.write(make_chunk(b"IEND", b""))


def render_stage(layout, cell, stage, out_path, w=1400, h=1050):
    full_bb = cell.bbox()
    if stage == "placement":
        # Diffusion/poly/nwell shapes are ~0.15-0.5 um standard-cell
        # features; at full-die scale they alias into unreadable noise.
        # Zoom into a fixed-size window (a few standard-cell rows, sky130
        # row height is ~2.72 um) around the die center instead of a
        # fraction of the die, so individual placed cells are visible.
        cx = (full_bb.left + full_bb.right) // 2
        cy = (full_bb.top + full_bb.bottom) // 2
        half = 17000  # dbu (~17 um square window => roughly 6 cell rows)
        bb = db.Box(cx - half, cy - half, cx + half, cy + half)
    else:
        bb = full_bb
    bw, bh = bb.width(), bb.height()
    margin = 20
    scale = min((w - 2 * margin) / bw, (h - 2 * margin) / bh)
    bl, bt = bb.left, bb.top

    def tx(x):
        return int((x - bl) * scale + margin)

    def ty(y):
        return int((bt - y) * scale + margin)

    br, bgc, bb_ = BG[stage]
    pixels = bytearray([br, bgc, bb_] * w * h)

    def fill_rect(x1, y1, x2, y2, r, g, b):
        x1c, x2c = max(0, min(x1, x2)), min(w - 1, max(x1, x2))
        y1c, y2c = max(0, min(y1, y2)), min(h - 1, max(y1, y2))
        for y in range(y1c, y2c + 1):
            row = y * w * 3
            for x in range(x1c, x2c + 1):
                idx = row + x * 3
                pixels[idx], pixels[idx + 1], pixels[idx + 2] = b, g, r

    allow = STAGE_LAYER_NUMS[stage]
    total = 0
    for layer_idx in layout.layer_indices():
        ln = layout.get_info(layer_idx)
        if ln.layer in SKIP_LAYER_NUMS:
            continue
        if allow is not None and ln.layer not in allow:
            continue
        color = LAYER_COLORS.get((ln.layer, ln.datatype), (180, 180, 180))
        r, g, b = color
        it = cell.begin_shapes_rec(layer_idx)
        count = 0
        while not it.at_end():
            shape = it.shape()
            trans = it.trans()  # shapes inside placed std-cell instances are
                                 # in local coordinates -- must apply the
                                 # recursive iterator's cumulative transform
                                 # to get top-cell (die) coordinates.
            if shape.is_box():
                box = shape.box.transformed(trans)
                fill_rect(tx(box.left), ty(box.top), tx(box.right), ty(box.bottom), r, g, b)
                count += 1
            elif shape.is_polygon():
                poly = shape.polygon.transformed(trans)
                pts = [(tx(p.x), ty(p.y)) for p in poly.each_point_hull()]
                if len(pts) >= 3:
                    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
                    fill_rect(min(xs), min(ys), max(xs), max(ys), r, g, b)
                    count += 1
            elif shape.is_path():
                path = shape.path.transformed(trans)
                pw = max(int(path.width * scale), 1)
                pts = [(tx(p.x), ty(p.y)) for p in path.each_point()]
                for i in range(len(pts) - 1):
                    x1, y1 = pts[i]
                    x2, y2 = pts[i + 1]
                    fill_rect(min(x1, x2) - pw, min(y1, y2) - pw, max(x1, x2) + pw, max(y1, y2) + pw, r, g, b)
                count += 1
            it.next()
        total += count
    save_png(out_path, w, h, pixels)
    print(f"{stage}: {total} shapes -> {out_path}")


def main(gds_file, out_dir, label):
    layout = db.Layout()
    layout.read(gds_file)
    cell = layout.top_cell()
    assert cell, "No top cell in GDS"
    bb = cell.bbox()
    print(f"{label}: top cell {cell.name}, die {bb.width()} x {bb.height()} db units")
    os.makedirs(out_dir, exist_ok=True)
    for stage in ("floorplan", "placement", "routing", "final"):
        render_stage(layout, cell, stage, os.path.join(out_dir, f"{label}_{stage}.png"))


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(f"Usage: {sys.argv[0]} <gds_file> <out_dir> <label>")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2], sys.argv[3])
