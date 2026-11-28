from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import Swapp

MATE = {"coincident": 0, "concentric": 1, "perpendicular": 2, "parallel": 3, "tangent": 4, "distance": 5, "angle": 6}


def select(m, name, kind, append, mark=1):
    return bool(m.Extension.SelectByID2(name, kind, 0, 0, 0, append, mark, Swapp.nothing(), 0))


def build(sw, spec, outdir):
    for p in spec["parts"]:
        shutil.copy2(p, outdir / Path(p).name)
    asm = sw.new_assembly()
    title = str(Swapp.cv(asm, "GetTitle"))
    comps = []
    for i, c in enumerate(spec["components"]):
        path = str(outdir / Path(spec["parts"][c["part"]]).name)
        m, e, w = sw.open(path)
        sw.app.ActivateDoc3(title, False, 0, Swapp.byref_long())
        x, y, z = (v / 1000.0 for v in c.get("at", (0, 0, 0)))
        comp = asm.AddComponent5(path, 0, "", False, "", x, y, z)
        if comp is None:
            raise RuntimeError(f"AddComponent5 failed for {path}")
        comps.append(str(Swapp.cv(comp, "Name2")))
        sw.close_doc(m)
    mates = []
    for mt in spec.get("mates", []):
        asm.ClearSelection2(True)
        a = select(asm, f"{mt['a'][1]}@{comps[mt['a'][0]]}@{title.split('.')[0]}", "PLANE", False)
        b = select(asm, f"{mt['b'][1]}@{comps[mt['b'][0]]}@{title.split('.')[0]}", "PLANE", True)
        err = Swapp.byref_long()
        f = asm.AddMate5(MATE[mt["type"]], mt.get("align", 0), False, mt.get("distance", 0) / 1000.0, 0, 0, 1, 1, mt.get("angle", 0), 0, 0, False, False, 0, err)
        mates.append({"selected": [a, b], "ok": f is not None, "error": int(err.value)})
    asm.ForceRebuild3(False)
    out = outdir / spec["name"]
    ok = sw.save_as(asm, out)
    rec = {"name": spec["name"], "components": comps, "mates": mates, "saved": ok, "whats_wrong": Swapp.rebuild_errors(asm)}
    sw.close_doc(asm)
    return rec


def main():
    spec = json.loads(Path(sys.argv[1]).read_text())
    outdir = Path(sys.argv[2])
    outdir.mkdir(parents=True, exist_ok=True)
    Swapp.sweep()
    res = []
    with Swapp.Dismisser() as dz:
        sw = Swapp.Sw()
        build_rev = sw.revision
        for a in spec["assemblies"]:
            try:
                r = build(sw, a, outdir)
            except Exception as ex:
                r = {"name": a["name"], "exception": repr(ex)}
                sw.close()
                Swapp.sweep()
                sw = Swapp.Sw()
            r["dialogs"] = list(dz.log)
            dz.log.clear()
            res.append(r)
        sw.close()
    (outdir / "manifest.json").write_text(json.dumps({"build": build_rev, "assemblies": res}, indent=1))
    Swapp.emit({"n": len(res), "saved": sum(1 for r in res if r.get("saved", (False,))[0])})


if __name__ == "__main__":
    main()
