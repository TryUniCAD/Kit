from __future__ import annotations

import json
import sys
from pathlib import Path

SLOT = 5


def tables(path):
    return list(_tables(path))


def _tables(path):
    cur = None
    with open(path, errors="replace") as source:
        for line in source:
            if line.startswith("VT "):
                head, _, rest = line[3:].partition(" @ ")
                cur = (head.strip(), rest.split()[0], [])
                yield cur
            elif cur and line.startswith("  "):
                p = line.strip().split("|")
                if len(p) >= 3 and p[0].isdigit():
                    cur[2].append((int(p[0]), p[1], p[2]))


def build(dumps):
    out = {}
    for dll, path in dumps:
        for name, addr, rows in tables(path):
            if not rows or rows[0][2].split("::")[-1] != "GetRuntimeClass":
                continue
            hit = [r for r in rows if r[0] == SLOT]
            if not hit:
                continue
            key = name
            if key in out and out[key]["dll"] != dll:
                out[key].setdefault("also", []).append({"dll": dll, "serialize_addr": hit[0][1], "serialize_name": hit[0][2]})
                continue
            out[key] = {"dll": dll, "serialize_addr": hit[0][1], "serialize_name": hit[0][2], "vtable": addr, "vtable_slots": len(rows)}
    return out


if __name__ == "__main__":
    dumps = [(a.split("=")[0], a.split("=")[1]) for a in sys.argv[2:]]
    m = build(dumps)
    Path(sys.argv[1]).write_text(json.dumps(m, indent=1, sort_keys=True))
    print(len(m))
