from __future__ import annotations

import glob
import json
import sys
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "src"))

from convert.adapters.solidworks.container.Container import SldprtArchive
from Core import ArchiveError
import Streams
import Classes

PLANS = {
    "Contents/Config-0-ResolvedFeatures": ("resolved", None),
    "Contents/CMgr": ("rooted", 3),
    "Contents/Config-0-ModelHeader": ("rooted", 1),
    "Header2": ("rooted", 1),
    "Contents/Config-0": ("rooted", 4),
}


def hexctx(b, p, n=48):
    lo = max(0, p - 16)
    return b[lo:p].hex(" ") + " | " + b[p:p + n].hex(" ")


def one(path, names, reg):
    arc = SldprtArchive.open(path)
    out = {}
    for name in names:
        data = arc.get(name)
        if data is None:
            continue
        kind, base = PLANS[name]
        rec = {"bytes": len(data)}
        ar = None
        try:
            if kind == "resolved":
                doc, ar = Streams.load_resolved(data, reg)
                again = Streams.store_resolved(doc, reg)
            elif kind == "custom":
                doc, ar = base[0](data, reg)
                again = base[1](doc, reg)
            else:
                doc, ar = Streams.load_rooted(data, reg, base)
                again = Streams.store_rooted(doc, reg)
            rec["roots"] = len(doc.roots)
            rec["tail"] = len(doc.tail)
            rec["identical"] = again == data
            if again != data:
                k = next((i for i in range(min(len(again), len(data))) if again[i] != data[i]), min(len(again), len(data)))
                rec["first_diff"] = k
                rec["ctx_src"] = hexctx(data, k)
                rec["ctx_out"] = hexctx(again, k)
            if doc.tail:
                rec["tail_at"] = len(data) - len(doc.tail)
                rec["tail_ctx"] = hexctx(data, len(data) - len(doc.tail))
        except (ArchiveError, KeyError, Exception) as ex:
            rec["error"] = repr(ex)
            if ar is not None:
                rec["at"] = ar.p
                rec["ctx"] = hexctx(data, ar.p)
            rec["trace"] = traceback.format_exc(limit=3)
        out[name] = rec
    return out


def main():
    pattern = sys.argv[1]
    reg = Classes.registry()
    PLANS.update(Classes.PLANS)
    names = sys.argv[2].split(",") if len(sys.argv) > 2 and not sys.argv[2].startswith("-") else list(PLANS)
    total = ok = 0
    for path in sorted(p for p in glob.glob(pattern, recursive=True) if not Path(p).name.startswith("~$")):
        res = one(path, names, reg)
        for n, r in res.items():
            total += 1
            ok += bool(r.get("identical")) and not r.get("tail")
            flag = "OK " if r.get("identical") and not r.get("tail") else "BAD"
            print(flag, Path(path).name, n, {k: v for k, v in r.items() if k != "trace"})
            if "trace" in r and "-v" in sys.argv:
                print(r["trace"])
    print(f"{ok}/{total} streams round-trip with no tail")


if __name__ == "__main__":
    main()
