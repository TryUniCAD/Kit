from __future__ import annotations

import json
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import Swapp

RESTART_EVERY = 20
SAVE_SILENT = 1


def main():
    src = Path(sys.argv[1])
    dst = Path(sys.argv[2])
    out = Path(sys.argv[3])
    dst.mkdir(parents=True, exist_ok=True)
    files = sorted(p for p in src.iterdir() if p.suffix.lower() in (".sldprt", ".sldasm") and not p.name.startswith("~$"))
    for p in files:
        shutil.copy2(p, dst / p.name)
    order = [dst / p.name for p in files if p.suffix.lower() == ".sldprt"]
    order += [dst / p.name for p in files if p.suffix.lower() == ".sldasm"]
    results = []
    Swapp.sweep()
    with Swapp.Dismisser() as dz:
        sw = Swapp.Sw()
        build = sw.revision
        launches = 0
        for f in order:
            if launches and launches % RESTART_EVERY == 0:
                sw.close()
                Swapp.sweep()
                sw = Swapp.Sw()
            rec = {"path": str(f)}
            t0 = time.time()
            try:
                m, e, w = sw.open(f)
                rec["open_errors"], rec["open_warnings"], rec["opened"] = e, w, m is not None
                if m is not None:
                    try:
                        rec["rebuilt"] = bool(m.ForceRebuild3(False))
                        rec["whats_wrong"] = Swapp.rebuild_errors(m)
                        rec["bodies"] = Swapp.bodies(m)
                        rec["mass"] = Swapp.mass(m)
                        rec["features"] = Swapp.features(m)
                        e2, w2 = Swapp.byref_long(), Swapp.byref_long()
                        rec["saved"] = bool(m.Save3(SAVE_SILENT, e2, w2))
                        rec["save_errors"], rec["save_warnings"] = int(e2.value), int(w2.value)
                    finally:
                        sw.close_doc(m)
            except Exception as ex:
                rec["exception"] = repr(ex)
                try:
                    sw.close()
                except Exception:
                    pass
                Swapp.sweep()
                sw = Swapp.Sw()
            rec["seconds"] = round(time.time() - t0, 2)
            rec["dialogs"] = list(dz.log)
            dz.log.clear()
            results.append(rec)
            launches += 1
            out.write_text(json.dumps({"build": build, "results": results}, indent=1))
        sw.close()
    Swapp.emit({"n": len(results), "saved": sum(1 for r in results if r.get("saved"))})


if __name__ == "__main__":
    main()
