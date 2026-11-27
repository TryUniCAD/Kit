import hashlib
import json
import traceback

import adsk.core
import adsk.fusion


report = {"scope": "native source controls for strict multi-feature decoding research, not conversion acceptance", "version": app.version, "controls": []}
cases = [
    ("HealthyBefore", (0, 0, 4, 3), None, 20, 20),
    ("CornerOriginal", (0, 0, 4, 3), (3, 2, 5, 4), 20, 20),
    ("CornerHeldOut", (-2, -1, 3.2, 2.7), (2.3, 1.9, 4, 4), 31, 31),
    ("CornerOpposite", (-2, -1, 3.2, 2.7), (-3, -2, -0.8, -0.3), 31, 31),
    ("CornerPocket", (0, 0, 4, 3), (3, 2, 5, 4), 20, 9),
    ("HealthyAfter", (0, 0, 4, 3), None, 20, 20),
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


for name, bounds, tool, height, depth in cases:
    entry = {"name": name, "inputs": {"base_cm": bounds, "tool_cm": tool, "height_mm": height, "depth_mm": depth}}
    report["controls"].append(entry)
    doc = None
    try:
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        comp = design.rootComponent
        rectangle(comp, bounds, height, adsk.fusion.FeatureOperations.NewBodyFeatureOperation, "Base")
        cut = rectangle(comp, tool, depth, adsk.fusion.FeatureOperations.CutFeatureOperation, "Corner") if tool else None
        if not design.computeAll():
            raise RuntimeError("Source did not recompute")
        entry["observed"] = observe(design)
        output = work / (name + ".f3d")
        if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(output))):
            raise RuntimeError("Native archive export failed")
        entry["file"] = output.name
        entry["sha256"] = hashlib.sha256(output.read_bytes()).hexdigest()
        if cut:
            parameter = adsk.fusion.DistanceExtentDefinition.cast(cut.extentOne).distance
            original = parameter.expression
            parameter.expression = str(depth / 2) + " mm"
            if not design.computeAll():
                raise RuntimeError("Cut dimension did not recompute")
            entry["half_depth_edit"] = observe(design)
            parameter.expression = original
            if not design.computeAll():
                raise RuntimeError("Restored cut did not recompute")
            entry["restored"] = observe(design)
        entry["status"] = "captured"
    except Exception:
        entry["status"] = "failed"
        entry["traceback"] = traceback.format_exc()
    finally:
        if doc is not None:
            doc.close(False)
        (work / "CutCorpus.json").write_text(json.dumps(report, indent=2))
result = report
