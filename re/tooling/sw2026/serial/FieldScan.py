from __future__ import annotations

import collections
import glob
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "src"))

from convert.adapters.solidworks.container.Container import SldprtArchive
from Core import Obj, ExtRef
import Streams
import Classes
import RoundTrip


def walk(v, path, out, seen, owner):
    if isinstance(v, Obj):
        if id(v) in seen:
            out[(owner, path)].append(("ref", v.cls))
            return
        seen.add(id(v))
        for k, x in v.f.items():
            walk(x, k, out, seen, v.cls)
        return
    if isinstance(v, ExtRef):
        out[(owner, path)].append(("ext", v.index))
        return
    if isinstance(v, dict):
        for k, x in v.items():
            walk(x, f"{path}.{k}", out, seen, owner)
        return
    if isinstance(v, list):
        out[(owner, path + "#n")].append(len(v))
        for i, x in enumerate(v):
            walk(x, f"{path}[]", out, seen, owner)
        return
    if isinstance(v, bytes):
        out[(owner, path)].append(("bytes", len(v)))
        return
    out[(owner, path)].append(v)


def load(name, data, reg):
    kind, base = RoundTrip.PLANS[name]
    if kind == "resolved":
        return Streams.load_resolved(data, reg)[0]
    if kind == "custom":
        return base[0](data, reg)[0]
    return Streams.load_rooted(data, reg, base)[0]


def main():
    pattern, name = sys.argv[1], sys.argv[2]
    reg = Classes.registry()
    RoundTrip.PLANS.update(Classes.PLANS)
    per = {}
    files = sorted(p for p in glob.glob(pattern) if not Path(p).name.startswith("~$"))
    for path in files:
        data = SldprtArchive.open(path).get(name)
        if data is None:
            continue
        doc = load(name, data, reg)
        out = collections.defaultdict(list)
        seen = set()
        for r in doc.roots:
            walk(r, "root", out, seen, "<stream>")
        for k, x in doc.head.items():
            out[("<head>", k)].append(x)
        per[Path(path).stem] = out
    keys = sorted({k for o in per.values() for k in o}, key=lambda k: (k[0], k[1]))
    rows = []
    for k in keys:
        vals = {f: tuple(map(repr, o.get(k, []))) for f, o in per.items()}
        distinct = sorted(set(vals.values()))
        rows.append({"cls": k[0], "field": k[1], "distinct": len(distinct), "values": {f: list(v)[:6] for f, v in vals.items()} if len(distinct) > 1 else list(distinct[0])[:6]})
    if "--json" in sys.argv:
        print(json.dumps(rows, indent=1))
        return
    for r in rows:
        v = r["values"]
        if r["distinct"] == 1:
            print(f"{r['cls']}.{r['field']}  const  {v}")
        else:
            print(f"{r['cls']}.{r['field']}  vary({r['distinct']})")
            for f, x in v.items():
                print(f"    {f}: {x}")


if __name__ == "__main__":
    main()
