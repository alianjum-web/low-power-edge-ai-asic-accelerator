"""Render a GDSII file to PNG screenshots using KLayout's Python bindings.

Run inside the OpenLane KLayout environment (it ships klayout.db), e.g.:

    docker run --rm -v "$PWD":/project -w /project \\
        ghcr.io/the-openroad-project/openlane:<tag> \\
        python3 scripts/render_gds_screenshots.py <gds_file> <out_dir> <label>

Produces <out_dir>/<label>_full_chip.png plus placement/routing detail crops.
"""
import sys
import struct
import zlib
import os

import klayout.db as db

# SKY130 GDS layer/datatype -> RGB, purely for visual distinction (not a DRC tool).
LAYER_COLORS = {
    (64, 20): (255, 100, 100),   # diff
    (64, 16): (220, 80, 80),
    (65, 20): (200, 200, 240),   # nwell
    (65, 44): (200, 200, 240),
    (66, 20): (220, 40, 40),     # poly
    (66, 16): (200, 30, 30),
    (66, 44): (180, 20, 20),
    (67, 20): (180, 255, 180),   # pselect/nselect
    (68, 20): (0, 80, 255),      # met1
    (68, 44): (0, 60, 220),
    (68, 16): (0, 70, 240),
    (69, 20): (0, 200, 255),     # met2
    (69, 44): (0, 170, 230),
    (69, 16): (0, 180, 240),
    (70, 20): (0, 220, 100),     # met3
    (70, 44): (0, 190, 80),
    (70, 16): (0, 200, 90),
    (71, 20): (255, 180, 0),     # met4
    (71, 44): (220, 150, 0),
    (71, 16): (240, 165, 0),
    (72, 20): (200, 0, 200),     # met5
    (72, 44): (170, 0, 170),
    (72, 16): (185, 0, 185),
    (235, 20): (180, 180, 0),    # via1
    (236, 20): (0, 180, 180),    # via2
    (237, 20): (180, 0, 180),    # via3
    (238, 20): (180, 100, 0),    # via4
    (36, 20): (0, 0, 0),         # die boundary
    (36, 44): (0, 0, 0),
}
SKIP_LAYER_NUMS = {67, 78, 93, 94, 95, 122}  # select/well-fill layers that flood-fill the die


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


def render(gds_file, out_dir, label, w=1600, h=1200):
    layout = db.Layout()
    layout.read(gds_file)
    cell = layout.top_cell()
    assert cell, "No top cell in GDS"

    bb = cell.bbox()
    bw, bh = bb.width(), bb.height()
    print(f"Top cell: {cell.name}  Die: {bw} x {bh} db units")

    margin = 10
    scale = min((w - 2 * margin) / bw, (h - 2 * margin) / bh)
    bl, bt = bb.left, bb.top

    def tx(x):
        return int((x - bl) * scale + margin)

    def ty(y):
        return int((bt - y) * scale + margin)

    pixels = bytearray([255, 255, 255] * w * h)

    def fill_rect(x1, y1, x2, y2, r, g, b):
        x1c, x2c = max(0, min(x1, x2)), min(w - 1, max(x1, x2))
        y1c, y2c = max(0, min(y1, y2)), min(h - 1, max(y1, y2))
        for y in range(y1c, y2c + 1):
            row = y * w * 3
            for x in range(x1c, x2c + 1):
                idx = row + x * 3
                pixels[idx], pixels[idx + 1], pixels[idx + 2] = b, g, r

    total = 0
    for layer_idx in layout.layer_indices():
        ln = layout.get_info(layer_idx)
        if ln.layer in SKIP_LAYER_NUMS:
            continue
        color = LAYER_COLORS.get((ln.layer, ln.datatype), (180, 180, 180))
        r, g, b = color
        count = 0
        it = cell.begin_shapes_rec(layer_idx)
        while not it.at_end():
            shape = it.shape()
            if shape.is_box():
                box = shape.box
                fill_rect(tx(box.left), ty(box.top), tx(box.right), ty(box.bottom), r, g, b)
                count += 1
            elif shape.is_polygon():
                pts = [(tx(p.x), ty(p.y)) for p in shape.polygon.each_point_hull()]
                if len(pts) >= 3:
                    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
                    fill_rect(min(xs), min(ys), max(xs), max(ys), r, g, b)
                    count += 1
            elif shape.is_path():
                path = shape.path
                pw = max(int(path.width * scale), 1)
                pts = [(tx(p.x), ty(p.y)) for p in path.each_point()]
                for i in range(len(pts) - 1):
                    x1, y1 = pts[i]
                    x2, y2 = pts[i + 1]
                    fill_rect(min(x1, x2) - pw, min(y1, y2) - pw, max(x1, x2) + pw, max(y1, y2) + pw, r, g, b)
                count += 1
            it.next()
        total += count

    print(f"Total shapes rendered: {total}")
    os.makedirs(out_dir, exist_ok=True)
    save_png(os.path.join(out_dir, f"{label}_full_chip.png"), w, h, pixels)

    # Center crop: placement/CTS detail
    cx, cy = w // 2, h // 2
    zw, zh = w // 3, h // 3
    crop = bytearray(zw * zh * 3)
    for y in range(zh):
        for x in range(zw):
            sx, sy = cx - zw // 2 + x, cy - zh // 2 + y
            si, di = (sy * w + sx) * 3, (y * zw + x) * 3
            crop[di:di + 3] = pixels[si:si + 3]
    save_png(os.path.join(out_dir, f"{label}_placement_detail.png"), zw, zh, crop)

    # Corner crop: routing detail
    crop2 = bytearray(zw * zh * 3)
    for y in range(zh):
        for x in range(zw):
            sx, sy = x, h - zh + y
            si, di = (sy * w + sx) * 3, (y * zw + x) * 3
            crop2[di:di + 3] = pixels[si:si + 3]
    save_png(os.path.join(out_dir, f"{label}_routing_detail.png"), zw, zh, crop2)

    print(f"Saved {label}_full_chip.png, {label}_placement_detail.png, {label}_routing_detail.png to {out_dir}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(f"Usage: {sys.argv[0]} <gds_file> <out_dir> <label>")
        sys.exit(1)
    render(sys.argv[1], sys.argv[2], sys.argv[3])
