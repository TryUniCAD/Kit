from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import Swapp


def main():
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    Swapp.sweep()
    with Swapp.Dismisser() as dz:
        sw = Swapp.Sw()
        res = {"revision": sw.revision, "template": sw.template("part")}
        m = sw.new_part()
        ok = m.Extension.SelectByID2("Front Plane", "PLANE", 0, 0, 0, False, 0, Swapp.nothing(), 0)
        res["select"] = bool(ok)
        sm = m.SketchManager
        sm.InsertSketch(True)
        sm.CreateCornerRectangle(-0.02, -0.01, 0, 0.02, 0.01, 0)
        sm.InsertSketch(True)
        fm = m.FeatureManager
        f = fm.FeatureExtrusion3(True, False, False, 0, 0, 0.01, 0.0, False, False, False, False, 0.0, 0.0, False, False, False, False, True, True, True, 0, 0.0, False)
        res["extrude"] = f is not None
        target = out / "smoke_box.SLDPRT"
        res["save"] = sw.save_as(m, target)
        sw.close_doc(m)
        time.sleep(1)
        res["measure"] = Swapp.measure(sw, target)
        sw.close()
        res["dialogs"] = dz.log
    Swapp.emit(res)


if __name__ == "__main__":
    main()
