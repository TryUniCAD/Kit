from __future__ import annotations

import json
import sys
from pathlib import Path


def rect_sketch(name, plane, x0, y0, w, h, dims=True):
    x1, y1 = x0 + w, y0 + h
    ents = [
        {"t": "line", "p": [x0, y0, x1, y0]},
        {"t": "line", "p": [x1, y0, x1, y1]},
        {"t": "line", "p": [x1, y1, x0, y1]},
        {"t": "line", "p": [x0, y1, x0, y0]},
    ]
    d = []
    if dims:
        d = [
            {"ents": [0], "at": [(x0 + x1) / 2, y0 - 5], "value": w},
            {"ents": [1], "at": [x1 + 5, (y0 + y1) / 2], "value": h},
        ]
    return {"op": "sketch", "name": name, "plane": plane, "entities": ents, "dims": d}


def polygon_sketch(name, plane, pts, dims=False):
    n = len(pts)
    ents = [{"t": "line", "p": [*pts[i], *pts[(i + 1) % n]]} for i in range(n)]
    return {"op": "sketch", "name": name, "plane": plane, "entities": ents, "dims": []}


def ladder():
    out = []
    for n in range(1, 5):
        ops = [rect_sketch("Sketch1", "front", -20, -10, 40, 20), {"op": "extrude", "sketch": "Sketch1", "depth": 10}]
        for k in range(1, n):
            sk = f"Sketch{k + 1}"
            ops.append(rect_sketch(sk, "front", -18 + 9 * (k - 1), -5, 6, 6))
            ops.append({"op": "extrude", "sketch": sk, "depth": 4 + k})
        out.append({"name": f"L{n}_boss", "ops": ops})
    base = [rect_sketch("Sketch1", "front", -20, -10, 40, 20), {"op": "extrude", "sketch": "Sketch1", "depth": 10}]
    out.append({"name": "C1a_control", "ops": base})
    out.append({"name": "C1b_control", "ops": base})
    out.append({"name": "P0_plain", "ops": [polygon_sketch("Sketch1", "front", [(-20, -10), (20, -10), (20, 10), (-20, 10)]), {"op": "extrude", "sketch": "Sketch1", "depth": 10}]})
    out.append({"name": "E0_empty", "ops": []})
    return out


if __name__ == "__main__":
    which = sys.argv[1]
    dst = Path(sys.argv[2])
    dst.write_text(json.dumps(globals()[which](), indent=1))
    print(dst)
