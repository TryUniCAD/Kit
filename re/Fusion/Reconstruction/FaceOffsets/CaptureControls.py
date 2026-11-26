import hashlib
import json
import traceback

import adsk.core
import adsk.fusion


report = {"scope": "native planar face offset controls for deterministic decoding research, not conversion acceptance", "version": app.version, "controls": []}
cases = [
    ("HealthyBefore", (0, 0, 4, 3), 20, None, None),
    ("TopPositive", (0, 0, 4, 3), 20, (0, 0, 1), 5),
    ("TopNegative", (0, 0, 4, 3), 20, (0, 0, 1), -3),
    ("SidePositive", (0, 0, 4, 3), 20, (1, 0, 0), 4),
    ("SideNegative", (0, 0, 4, 3), 20, (1, 0, 0), -2),
    ("HeldOutTop", (-1.3, -0.7, 2.8, 3.9), 31, (0, 0, 1), 7.3),
    ("HeldOutSide", (-1.3, -0.7, 2.8, 3.9), 31, (0, -1, 0), 2.7),
    ("HealthyAfter", (0, 0, 4, 3), 20, None, None),
]


def rectangle(comp, bounds, height, operation, name):
    sk = comp.sketches.add(comp.xYConstructionPlane)
    sk.name = name + " sketch"
    sk.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(bounds[0], bounds[1], 0),
        adsk.core.Point3D.create(bounds[2], bounds[3], 0),
    )
    ext = comp.features.extrudeFeatures.addSimple(
        sk.profiles.item(0),
        adsk.core.ValueInput.createByString(str(height) + " mm"),
        operation,
    )
    ext.name = name
    return ext


def observe(design):
    comp = design.rootComponent
    bodies = []
    for body in comp.bRepBodies:
        box = body.boundingBox
        bodies.append({
            "centroid_cm": body.physicalProperties.centerOfMass.asArray(),
            "solid": body.isSolid,
            "volume_cm3": body.volume,
            "area_cm2": body.area,
            "min_cm": box.minPoint.asArray(),
            "max_cm": box.maxPoint.asArray(),
            "faces": body.faces.count,
            "edges": body.edges.count,
            "vertices": body.vertices.count,
            "face_types": [face.geometry.surfaceType for face in body.faces],
            "vertex_cm": [vertex.geometry.asArray() for vertex in body.vertices],
        })
    parameters = []
    for param in design.allParameters:
        model = adsk.fusion.ModelParameter.cast(param)
        parameters.append({"name": param.name, "expression": param.expression, "value": param.value, "unit": param.unit, "role": model.role if model else None})
    return {
        "bodies": bodies,
        "parameters": parameters,
        "timeline": [{"name": item.name, "health": item.healthState, "message": item.errorOrWarningMessage} for item in design.timeline],
        "extrusions": [{"name": item.name, "operation": item.operation, "start_extent": item.startExtent.objectType, "extent": item.extentOne.objectType, "profile_sketch": item.profile.parentSketch.name} for item in comp.features.extrudeFeatures],
    }


def select_face(body, normal):
    faces = []
    for face in body.faces:
        if face.geometry.surfaceType != adsk.core.SurfaceTypes.PlaneSurfaceType:
            continue
        valid, direction = face.evaluator.getNormalAtPoint(face.pointOnFace)
        if valid and sum(a * b for a, b in zip(direction.asArray(), normal)) > 0.999:
            faces.append(face)
    if len(faces) != 1:
        raise RuntimeError("Offset source face is not unique")
    return faces[0]


for name, bounds, height, normal, distance in cases:
    entry = {"name": name, "inputs": {"base_cm": bounds, "height_mm": height, "face_normal": normal, "offset_mm": distance}, "split": "held_out" if name.startswith("HeldOut") else "derivation"}
    report["controls"].append(entry)
    doc = None
    try:
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        comp = design.rootComponent
        stock = rectangle(comp, bounds, height, adsk.fusion.FeatureOperations.NewBodyFeatureOperation, "Base")
        offset = None
        if normal:
            face = select_face(stock.bodies.item(0), normal)
            offsets = comp.features.offsetFacesFeatures
            offset = offsets.add(offsets.createInput([face], adsk.core.ValueInput.createByString(str(distance) + " mm")))
            offset.name = "Measured face offset"
        if not design.computeAll():
            raise RuntimeError("Source did not recompute")
        entry["observed"] = observe(design)
        output = work / (name + ".f3d")
        if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(output))):
            raise RuntimeError("Native archive export failed")
        entry["file"] = output.name
        entry["sha256"] = hashlib.sha256(output.read_bytes()).hexdigest()
        if offset:
            parameter = next(p for p in design.allParameters if adsk.fusion.ModelParameter.cast(p) and adsk.fusion.ModelParameter.cast(p).createdBy == offset and p.unit in ("mm", "cm"))
            original = parameter.expression
            parameter.expression = str(distance / 2) + " mm"
            if not design.computeAll():
                raise RuntimeError("Offset dimension did not recompute")
            entry["half_offset_edit"] = observe(design)
            parameter.expression = original
            if not design.computeAll():
                raise RuntimeError("Restored offset did not recompute")
            entry["restored"] = observe(design)
        entry["status"] = "captured"
    except Exception:
        entry["status"] = "failed"
        entry["traceback"] = traceback.format_exc()
    finally:
        if doc is not None:
            doc.close(False)
        (work / "OffsetCorpus.json").write_text(json.dumps(report, indent=2))
result = report
