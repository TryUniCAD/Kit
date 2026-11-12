"""Native acceptance of Kit-authored feature documents.

For every case in Authored/Manifest.json this script:
1. builds the same part natively through the Fusion API as the control;
2. opens the Kit document and observes it before any recompute;
3. walks every timeline rollback marker and compares with the control;
4. runs computeAll and compares again;
5. applies the driving parameter edits to both and compares;
6. exports the edited Kit document, reopens it and compares again.

Run only through RunLocked.mjs. Every document opened here is closed.
"""

import hashlib
import json
from math import isclose
from pathlib import Path
import traceback

import adsk.core
import adsk.fusion


root = Path(__file__).resolve().parent / "Authored"
manifest = json.loads((root / "Manifest.json").read_text())
app = adsk.core.Application.get()
original = app.activeDocument
FO = adsk.fusion.FeatureOperations
HEALTHY = adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState
report = {
    "fusion_version": app.version,
    "documents_before": app.documents.count,
    "scope": "Kit-authored fillet, chamfer and shell documents compared with same-script native API controls: open without recompute, every rollback marker, computeAll, driving parameter edits, export and reopen",
    "cases": [],
}
open_docs = []


def checkpoint():
    (root / "NativeAcceptance.json").write_text(json.dumps(report, indent=2).replace(str(Path(__file__).resolve().parents[4]) + "/", "").replace(str(Path.home()), "~") + "\n")


def vi(text):
    return adsk.core.ValueInput.createByString(text)


def pt(x, y, z=0.0):
    return adsk.core.Point3D.create(x, y, z)


def coll(*items):
    value = adsk.core.ObjectCollection.create()
    for item in items:
        value.add(item)
    return value


def vertical_edge(body, x, y):
    for edge in body.edges:
        s, e = edge.startVertex.geometry, edge.endVertex.geometry
        if abs(s.x - x) < 1e-6 and abs(e.x - x) < 1e-6 and abs(s.y - y) < 1e-6 and abs(e.y - y) < 1e-6:
            return edge
    raise RuntimeError("Vertical edge not found")


def top_face(body):
    best = None
    for face in body.faces:
        if face.geometry.surfaceType == adsk.core.SurfaceTypes.PlaneSurfaceType:
            ok, normal = face.evaluator.getNormalAtPoint(face.pointOnFace)
            if normal.z > 0.999 and (best is None or face.pointOnFace.z > best.pointOnFace.z):
                best = face
    return best


def build_control(comp, steps):
    sketch = comp.sketches.add(comp.xYConstructionPlane)
    sketch.name = "Base Sketch"
    sketch.sketchCurves.sketchLines.addTwoPointRectangle(pt(0, 0), pt(4, 3))
    extrude = comp.features.extrudeFeatures.addSimple(sketch.profiles.item(0), vi("20 mm"), FO.NewBodyFeatureOperation)
    extrude.name = "Base Extrude"
    body = extrude.bodies.item(0)
    for step in steps:
        if step["kind"] == "fillet":
            feats = comp.features.filletFeatures
            inp = feats.createInput()
            inp.edgeSetInputs.addConstantRadiusEdgeSet(coll(vertical_edge(body, *step["corner_cm"])), vi(step["amount"]), True)
            feature = feats.add(inp)
        elif step["kind"] == "chamfer":
            feats = comp.features.chamferFeatures
            inp = feats.createInput2()
            inp.chamferEdgeSets.addEqualDistanceChamferEdgeSet(coll(vertical_edge(body, *step["corner_cm"])), vi(step["amount"]), True)
            feature = feats.add(inp)
        else:
            feats = comp.features.shellFeatures
            inp = feats.createInput(coll(top_face(body)), False)
            inp.insideThickness = vi(step["amount"])
            feature = feats.add(inp)
        feature.name = step["name"]
        body = comp.bRepBodies.item(0)


def observe(design):
    comp = design.rootComponent
    bodies = []
    for b in comp.bRepBodies:
        bb = b.boundingBox
        props = b.physicalProperties
        bodies.append({
            "name": b.name,
            "solid": b.isSolid,
            "volume_cm3": b.volume,
            "area_cm2": b.area,
            "faces": b.faces.count,
            "edges": b.edges.count,
            "vertices": b.vertices.count,
            "min_cm": list(bb.minPoint.asArray()),
            "max_cm": list(bb.maxPoint.asArray()),
            "center_cm": list(props.centerOfMass.asArray()),
            "surface_types": sorted(f.geometry.surfaceType for f in b.faces),
        })
    timeline = [{"name": i.name, "health": i.healthState, "message": i.errorOrWarningMessage, "rolled_back": i.isRolledBack} for i in design.timeline]
    params = []
    for p in design.allParameters:
        owner = None
        try:
            owner = p.createdBy.name if p.createdBy else None
        except Exception:
            owner = None
        params.append({"name": p.name, "expression": p.expression, "value": p.value, "unit": p.unit, "owner": owner})
    return {"timeline": timeline, "bodies": bodies, "parameters": params, "marker": design.timeline.markerPosition}


def healthy(observed):
    return all(i["health"] == HEALTHY and not i["message"] for i in observed["timeline"] if not i["rolled_back"])


def same_geometry(left, right):
    if len(left["bodies"]) != len(right["bodies"]):
        return False
    for a, b in zip(left["bodies"], right["bodies"]):
        if (a["faces"], a["edges"], a["vertices"], a["solid"], a["surface_types"]) != (b["faces"], b["edges"], b["vertices"], b["solid"], b["surface_types"]):
            return False
        if not isclose(a["volume_cm3"], b["volume_cm3"], rel_tol=1e-8, abs_tol=1e-9) or not isclose(a["area_cm2"], b["area_cm2"], rel_tol=1e-8, abs_tol=1e-9):
            return False
        bounds = zip(a["min_cm"] + a["max_cm"] + a["center_cm"], b["min_cm"] + b["max_cm"] + b["center_cm"])
        if not all(isclose(x, y, rel_tol=1e-7, abs_tol=1e-7) for x, y in bounds):
            return False
    return True


def walk_markers(design):
    result = []
    for position in range(design.timeline.count + 1):
        design.timeline.markerPosition = position
        result.append(observe(design))
    if not design.timeline.moveToEnd():
        raise RuntimeError("Timeline did not return to the end")
    return result


def apply_edits(design, edits):
    comp = design.rootComponent
    for edit in edits:
        if edit["feature"] == "height":
            extent = adsk.fusion.DistanceExtentDefinition.cast(comp.features.extrudeFeatures.item(0).extentOne)
            extent.distance.expression = edit["expression"]
            continue
        matches = [p for p in comp.modelParameters if p.unit == "mm" and p.createdBy is not None and p.createdBy.name == edit["feature"]]
        if len(matches) != 1:
            raise RuntimeError("Driving parameter not unique for " + edit["feature"] + ": " + str(len(matches)))
        matches[0].expression = edit["expression"]
    if not design.computeAll():
        raise RuntimeError("computeAll failed after parameter edits")


def open_archive(path):
    doc = app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(str(path)))
    if doc is None:
        raise RuntimeError("Document did not open: " + path.name)
    open_docs.append(doc)
    return doc, adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))


def close(doc):
    if doc in open_docs:
        open_docs.remove(doc)
    doc.close(False)


def native_control(entry):
    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    open_docs.append(doc)
    design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
    design.designType = adsk.fusion.DesignTypes.ParametricDesignType
    build_control(design.rootComponent, entry["steps"])
    built = observe(design)
    markers = walk_markers(design)
    apply_edits(design, entry["edits"])
    edited = observe(design)
    close(doc)
    return {"built": built, "markers": markers, "edited": edited}


def compare(case, label, observed, expected):
    result = {"healthy": healthy(observed), "matches_control": same_geometry(observed, expected)}
    case["checks"][label] = result
    return result["healthy"] and result["matches_control"]


try:
    for name, entry in manifest.items():
        source = root / entry["file"]
        case = {"name": name, "file": entry["file"], "sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "steps": entry["steps"], "edits": entry["edits"], "kit_states": entry["kit_states"], "checks": {}, "stage": "control"}
        report["cases"].append(case)
        checkpoint()
        doc = None
        before = list(app.documents)
        try:
            if case["sha256"] != entry["sha256"]:
                raise RuntimeError("Authored digest differs from the manifest")
            control = native_control(entry)
            case["control"] = control
            case["stage"] = "opening"
            checkpoint()
            doc, design = open_archive(source)
            case["opened"] = observe(design)
            ok = compare(case, "opened", case["opened"], control["built"])
            case["stage"] = "markers"
            checkpoint()
            markers = walk_markers(design)
            case["markers"] = markers
            marker_ok = []
            for position, (kit, native) in enumerate(zip(markers, control["markers"])):
                marker_ok.append(healthy(kit) and same_geometry(kit, native))
            case["checks"]["markers"] = {"positions": len(markers), "control_positions": len(control["markers"]), "each": marker_ok}
            ok = ok and len(markers) == len(control["markers"]) and all(marker_ok)
            case["computed"] = design.computeAll()
            case["recomputed"] = observe(design)
            ok = compare(case, "recomputed", case["recomputed"], control["built"]) and case["computed"] and ok
            case["stage"] = "editing"
            checkpoint()
            apply_edits(design, entry["edits"])
            case["edited"] = observe(design)
            ok = compare(case, "edited", case["edited"], control["edited"]) and ok
            saved = root / ("vendor_" + name + ".f3d")
            if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(saved))):
                raise RuntimeError("Export failed")
            close(doc)
            doc = None
            case["stage"] = "reopening"
            checkpoint()
            doc, design = open_archive(saved)
            case["reopened"] = observe(design)
            ok = compare(case, "reopened", case["reopened"], control["edited"]) and ok
            expressions = sorted((p["owner"] or "", p["expression"]) for p in case["reopened"]["parameters"])
            edited_expressions = sorted((p["owner"] or "", p["expression"]) for p in case["edited"]["parameters"])
            case["checks"]["reopened_parameters_preserved"] = expressions == edited_expressions
            ok = ok and expressions == edited_expressions
            case["reopen_computed"] = design.computeAll()
            case["reopen_recomputed"] = observe(design)
            ok = compare(case, "reopen_recomputed", case["reopen_recomputed"], control["edited"]) and case["reopen_computed"] and ok
            case["saved_sha256"] = hashlib.sha256(saved.read_bytes()).hexdigest()
            close(doc)
            doc = None
            case["status"] = "accepted" if ok else "rejected"
        except Exception:
            case["status"] = "failed"
            case["traceback"] = traceback.format_exc()
        finally:
            for item in list(open_docs):
                close(item)
            for item in list(app.documents):
                if item not in before and item.isValid:
                    case.setdefault("stray_closed", []).append(item.name)
                    item.close(False)
            case["stage"] = "done"
            checkpoint()
    report["status"] = "accepted" if all(c.get("status") == "accepted" for c in report["cases"]) else "rejected"
except Exception:
    report["status"] = "failed"
    report["traceback"] = traceback.format_exc()
finally:
    for item in list(open_docs):
        try:
            close(item)
        except Exception:
            pass
    if original is not None and original.isValid:
        original.activate()
    report["documents_after"] = app.documents.count
    checkpoint()
