from __future__ import annotations

import hashlib
import json
import math
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import Swapp
from Swapp import cv, nothing

PLANES = {"front": "Front Plane", "top": "Top Plane", "right": "Right Plane"}
END = {
    "blind": 0,
    "through": 1,
    "through_next": 2,
    "up_to_vertex": 3,
    "up_to_surface": 4,
    "offset_from_surface": 5,
    "midplane": 6,
    "up_to_body": 7,
}
INPUT_DIM_ON_CREATE = 10


def sel(m, name, kind, append=False, mark=0):
    return bool(m.Extension.SelectByID2(name, kind, 0, 0, 0, append, mark, nothing(), 0))


def clear(m):
    m.ClearSelection2(True)


def mm(v):
    return float(v) / 1000.0


class Builder:
    def __init__(self, sw, spec):
        self.sw = sw
        self.spec = spec
        self.m = None
        self.segs = {}
        self.log = []

    def run(self):
        app = self.sw.app
        app.SetUserPreferenceToggle(INPUT_DIM_ON_CREATE, False)
        self.m = self.sw.new_part()
        for op in self.spec["ops"]:
            getattr(self, "op_" + op["op"])(op)
            self.log.append(op["op"])
        return self.m

    def select_plane(self, op):
        plane = op.get("plane", "front")
        name = PLANES.get(plane, plane)
        kind = op.get("plane_kind", "PLANE")
        if not sel(self.m, name, kind):
            raise RuntimeError(f"cannot select {name}")

    def op_sketch(self, op):
        m = self.m
        clear(m)
        self.select_plane(op)
        sm = m.SketchManager
        sm.InsertSketch(True)
        sm.AddToDB = bool(op.get("add_to_db", False))
        segs = []
        for e in op["entities"]:
            t = e["t"]
            if t == "line":
                x1, y1, x2, y2 = (mm(v) for v in e["p"])
                s = sm.CreateLine(x1, y1, 0, x2, y2, 0)
            elif t == "centerline":
                x1, y1, x2, y2 = (mm(v) for v in e["p"])
                s = sm.CreateCenterLine(x1, y1, 0, x2, y2, 0)
            elif t == "circle":
                cx, cy = (mm(v) for v in e["c"])
                s = sm.CreateCircleByRadius(cx, cy, 0, mm(e["r"]))
            elif t == "arc":
                cx, cy = (mm(v) for v in e["c"])
                x1, y1 = (mm(v) for v in e["p1"])
                x2, y2 = (mm(v) for v in e["p2"])
                s = sm.CreateArc(cx, cy, 0, x1, y1, 0, x2, y2, 0, int(e.get("dir", 1)))
            elif t == "rect":
                x1, y1, x2, y2 = (mm(v) for v in e["p"])
                s = sm.CreateCornerRectangle(x1, y1, 0, x2, y2, 0)
            elif t == "polygon":
                x1, y1 = (mm(v) for v in e["c"])
                x2, y2 = (mm(v) for v in e["v"])
                s = sm.CreatePolygon(x1, y1, 0, x2, y2, 0, int(e["n"]), bool(e.get("inscribed", True)))
            elif t == "ellipse":
                cx, cy = (mm(v) for v in e["c"])
                ax, ay = (mm(v) for v in e["major"])
                bx, by = (mm(v) for v in e["minor"])
                s = sm.CreateEllipse(cx, cy, 0, ax, ay, 0, bx, by, 0)
            elif t == "spline":
                pts = []
                for x, y in e["points"]:
                    pts += [mm(x), mm(y), 0.0]
                s = sm.CreateSpline2(pts, False)
            elif t == "point":
                x, y = (mm(v) for v in e["p"])
                s = sm.CreatePoint(x, y, 0)
            else:
                raise ValueError(t)
            if s is None:
                raise RuntimeError(f"sketch entity {t} failed")
            if e.get("construction"):
                try:
                    s.ConstructionGeometry = True
                except Exception:
                    pass
            segs.append(s)
        sm.AddToDB = False
        for d in op.get("dims", []):
            self.dimension(segs, d)
        sm.InsertSketch(True)
        name = op.get("name")
        feat = cv(m, "FeatureByPositionReverse", 0)
        if name and feat is not None:
            feat.Name = name
        clear(m)

    def dimension(self, segs, d):
        m = self.m
        clear(m)
        for i in d["ents"]:
            s = segs[i]
            s.Select4(True, nothing())
        x, y = (mm(v) for v in d.get("at", (0, 0)))
        kind = d.get("kind", "smart")
        if kind == "smart":
            dd = m.AddDimension2(x, y, 0)
        elif kind == "horizontal":
            dd = m.AddHorizontalDimension2(x, y, 0)
        elif kind == "vertical":
            dd = m.AddVerticalDimension2(x, y, 0)
        elif kind == "diameter":
            dd = m.AddDiameterDimension2(x, y, 0)
        elif kind == "radial":
            dd = m.AddRadialDimension2(x, y, 0)
        else:
            raise ValueError(kind)
        if dd is None:
            raise RuntimeError(f"dimension failed {d}")
        if "value" in d:
            dim = dd.GetDimension2(0)
            dim.SetSystemValue3(mm(d["value"]) if d.get("unit", "mm") == "mm" else math.radians(d["value"]), 1, nothing())
        clear(m)

    def select_sketch(self, name):
        if not sel(self.m, name, "SKETCH"):
            raise RuntimeError(f"cannot select sketch {name}")

    def op_extrude(self, op):
        m = self.m
        clear(m)
        self.select_sketch(op["sketch"])
        fm = m.FeatureManager
        cut = bool(op.get("cut", False))
        e1 = END[op.get("end", "blind")]
        d1 = mm(op.get("depth", 10))
        two = "end2" in op
        e2 = END[op.get("end2", "blind")]
        d2 = mm(op.get("depth2", 0))
        flip = bool(op.get("flip", False))
        draft1 = math.radians(op.get("draft", 0.0))
        draft2 = math.radians(op.get("draft2", 0.0))
        dr1 = bool(op.get("draft_out", False))
        dr2 = bool(op.get("draft_out2", False))
        if cut:
            f = fm.FeatureCut4(
                not two, flip, bool(op.get("flip_side", False)), e1, e2, d1, d2,
                draft1 != 0, draft2 != 0, dr1, dr2, draft1, draft2,
                False, False, False, False, False, True, True, True, True, False, 0, 0.0, False, False,
            )
        else:
            f = fm.FeatureExtrusion3(
                not two, flip, bool(op.get("flip2", False)), e1, e2, d1, d2,
                draft1 != 0, draft2 != 0, dr1, dr2, draft1, draft2,
                False, False, False, False, bool(op.get("merge", True)), True, True, 0, 0.0, False,
            )
        if f is None:
            raise RuntimeError("extrude failed")
        if op.get("name"):
            f.Name = op["name"]

    def op_revolve(self, op):
        m = self.m
        clear(m)
        self.select_sketch(op["sketch"])
        fm = m.FeatureManager
        cut = bool(op.get("cut", False))
        ang = math.radians(op.get("angle", 360.0))
        ang2 = math.radians(op.get("angle2", 0.0))
        rtype = {"blind": 0, "midplane": 6, "two": 0}.get(op.get("end", "blind"), 0)
        two = "angle2" in op
        f = fm.FeatureRevolve2(
            not two, True, False, cut, bool(op.get("flip", False)), False,
            rtype, 0, ang, ang2, False, False, 0.0, 0.0, 0, 0.0, 0.0, True, True, True,
        )
        if f is None:
            raise RuntimeError("revolve failed")
        if op.get("name"):
            f.Name = op["name"]

    def op_fillet(self, op):
        m = self.m
        clear(m)
        for x, y, z in op["edges"]:
            m.Extension.SelectByID2("", "EDGE", mm(x), mm(y), mm(z), True, 1, nothing(), 0)
        fm = m.FeatureManager
        f = fm.FeatureFillet3(195, mm(op["radius"]), 0, 0, 0, 0, 0, nothing(), nothing(), nothing(), nothing(), nothing(), nothing(), nothing())
        if f is None:
            raise RuntimeError("fillet failed")

    def op_chamfer(self, op):
        m = self.m
        clear(m)
        for x, y, z in op["edges"]:
            m.Extension.SelectByID2("", "EDGE", mm(x), mm(y), mm(z), True, 1, nothing(), 0)
        f = m.FeatureManager.InsertFeatureChamfer(4, 1, mm(op["distance"]), math.radians(op.get("angle", 45.0)), 0, 0, 0, 0)
        if f is None:
            raise RuntimeError("chamfer failed")

    def op_rename(self, op):
        f = cv(self.m, "FeatureByName", op["from"])
        f.Name = op["to"]


def author(sw, spec, outdir):
    rec = {"name": spec["name"], "spec": spec}
    b = Builder(sw, spec)
    try:
        m = b.run()
        m.ForceRebuild3(False)
        target = Path(outdir) / (spec["name"] + ".SLDPRT")
        rec["save"] = sw.save_as(m, target)
        rec["features"] = Swapp.features(m)
        rec["mass"] = Swapp.mass(m)
        rec["bodies"] = Swapp.bodies(m)
        sw.close_doc(m)
        data = target.read_bytes()
        rec["sha256"] = hashlib.sha256(data).hexdigest()
        rec["path"] = str(target)
    except Exception as ex:
        rec["error"] = repr(ex)
        rec["trace"] = traceback.format_exc()
        try:
            sw.app.CloseAllDocuments(True)
        except Exception:
            pass
    return rec


def main():
    specfile = Path(sys.argv[1])
    outdir = Path(sys.argv[2])
    outdir.mkdir(parents=True, exist_ok=True)
    specs = json.loads(specfile.read_text())
    restart_every = 20
    results = []
    Swapp.sweep()
    with Swapp.Dismisser() as dz:
        sw = Swapp.Sw()
        n = 0
        for spec in specs:
            if n and n % restart_every == 0:
                sw.close()
                Swapp.sweep()
                sw = Swapp.Sw()
            r = author(sw, spec, outdir)
            r["revision"] = sw.revision
            results.append(r)
            n += 1
        sw.close()
        dialogs = dz.log
    manifest = outdir / (specfile.stem + ".manifest.json")
    manifest.write_text(json.dumps({"results": results, "dialogs": dialogs, "time": time.time()}, indent=1))
    Swapp.emit({"ok": sum(1 for r in results if "error" not in r), "n": len(results), "errors": [(r["name"], r.get("error")) for r in results if "error" in r]})


if __name__ == "__main__":
    main()
