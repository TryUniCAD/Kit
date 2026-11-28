from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import Swapp

RESTART_EVERY = 20


def main():
    job = json.loads(Path(sys.argv[1]).read_text())
    out = Path(sys.argv[2])
    control = job["control"]
    files = job["files"]
    edits = job.get("edits", {})
    every = int(job.get("restart_every", RESTART_EVERY))
    results = []
    launches = 0
    Swapp.sweep()
    with Swapp.Dismisser() as dz:
        sw = Swapp.Sw()
        build = sw.revision
        ctrl = []

        def restart():
            nonlocal sw
            sw.close()
            Swapp.sweep()
            sw = Swapp.Sw()

        def control_run():
            try:
                return Swapp.measure(sw, control)
            except Exception as ex:
                restart()
                r = Swapp.measure(sw, control)
                r["after_restart"] = repr(ex)
                return r

        ctrl.append(control_run())
        for i, f in enumerate(files):
            if launches and launches % every == 0:
                ctrl.append(control_run())
                restart()
            try:
                r = Swapp.measure(sw, f)
                if f in edits and r.get("opened"):
                    r["edit"] = edit(sw, f, edits[f])
            except Exception as ex:
                r = {"path": f, "exception": repr(ex)}
                try:
                    restart()
                    c = control_run()
                    r["control_after"] = {k: c.get(k) for k in ("opened", "bodies", "mass", "after_restart")}
                except Exception as ex2:
                    r["restart_exception"] = repr(ex2)
            r["dialogs"] = list(dz.log)
            dz.log.clear()
            results.append(r)
            launches += 1
        ctrl.append(control_run())
        sw.close()
    payload = {"build": build, "controls": ctrl, "results": results, "time": time.time()}
    out.write_text(json.dumps(payload, indent=1))
    ok = all(c.get("opened") and c.get("bodies", 0) > 0 for c in ctrl)
    Swapp.emit({"controls_ok": ok, "n": len(results), "opened": sum(1 for r in results if r.get("opened"))})


def edit(sw, path, spec):
    m, e, w = sw.open(path)
    res = {"open_errors": e}
    if m is None:
        return res
    try:
        before = Swapp.mass(m)
        for name, value in spec["dims"].items():
            d = Swapp.cv(m, "Parameter", name)
            if d is None:
                res.setdefault("missing", []).append(name)
                continue
            d.SetSystemValue3(float(value), 1, Swapp.nothing())
        res["rebuilt"] = bool(m.ForceRebuild3(False))
        res["whats_wrong"] = Swapp.rebuild_errors(m)
        res["before"] = before
        res["after"] = Swapp.mass(m)
        res["bodies"] = Swapp.bodies(m)
        res["features"] = [f for f in Swapp.features(m) if "error" in f and f["error"]]
    finally:
        sw.app.CloseDoc(str(Swapp.cv(m, "GetTitle")))
    return res


if __name__ == "__main__":
    main()
