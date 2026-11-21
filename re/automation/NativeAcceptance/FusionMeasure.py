import math
from pathlib import Path

from NativeAcceptance.FusionBrep import MeasureBrep
from NativeAcceptance.FusionSemantics import MeasureSemantics


def MeasureDesign(design):
    import adsk.fusion

    root = design.rootComponent
    if root.allOccurrences.count:
        raise ValueError("assembly verification requires an assembly oracle and is not qualified by part measurements")
    semantics = MeasureSemantics(design)
    bodies = []
    for index, body in enumerate(root.bRepBodies):
        props = body.getPhysicalProperties(adsk.fusion.CalculationAccuracy.VeryHighCalculationAccuracy)
        bodies.append({"name": body.name, "volume_mm3": body.volume * 1000, "center_mm": [value * 10 for value in props.centerOfMass.asArray()], "faces": body.faces.count, "edges": body.edges.count, "vertices": body.vertices.count, "geometry": MeasureBrep(body, semantics["gaps"], f"body:{index}"), "bounds_mm": [[value * 10 for value in point.asArray()] for point in (body.boundingBox.minPoint, body.boundingBox.maxPoint)]})
    features = [{"name": item.name, "type": item.entity.objectType, "suppressed": item.isSuppressed, "health": int(item.healthState), "message": item.errorOrWarningMessage} for item in design.timeline]
    parameters = [{"name": item.name, "value": item.value, "unit": "rad" if item.unit in ("rad", "deg") else "cm" if item.unit in ("mm", "cm", "m", "in", "ft") else item.unit, "display_unit": item.unit, "expression": item.expression} for item in design.allParameters]
    sketches = [{"name": item.name, "entities": item.sketchCurves.count, "constraints": item.geometricConstraints.count, "dimensions": item.sketchDimensions.count} for item in root.sketches]
    return {"bodies": bodies, "features": features, "parameters": parameters, "sketches": sketches, "semantics": semantics}


def FusionMeasure(app, work, request):
    import adsk.core
    import adsk.fusion

    for existing in list(app.documents):
        if not existing.isModified and existing.dataFile is None:
            existing.close(False)
    if app.documents.count:
        raise ValueError("close documents before native verification; an owned fresh session must be empty")
    source = work / request["source"]
    document = None
    result = {"application": "fusion", "build": app.version, "load_errors": [], "edits": []}
    try:
        document = app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(str(source)))
        if document is None:
            raise ValueError("Fusion did not open the candidate")
        design = adsk.fusion.Design.cast(document.products.itemByProductType("DesignProductType"))
        if design is None:
            raise ValueError("candidate did not produce a Fusion design")
        result["opened"] = MeasureDesign(design)
        if not design.computeAll():
            raise ValueError("Fusion computeAll rejected the unchanged candidate")
        result["rebuilt"] = MeasureDesign(design)
        if any(item["health"] != int(adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState) or item["message"] for item in result["rebuilt"]["features"]):
            raise ValueError("Fusion feature tree has a rebuild warning or error")
        if request["role"] == "candidate":
            independent = [item for item in design.allParameters if not item.dependencyParameters.count]
            if any(item.unit not in ("mm", "cm", "m", "in", "ft", "rad", "deg") for item in independent):
                raise ValueError("independent non dimensional parameters require an explicit edit qualification")
            if not independent or len(independent) > 16:
                raise ValueError("candidate needs between one and sixteen independent driving parameters for this verification batch")
            for index, parameter in enumerate(independent):
                original = parameter.expression
                old_value = parameter.value
                value = old_value * 1.1 if abs(old_value) > 1e-12 else 0.1
                internal_unit = "rad" if parameter.unit in ("rad", "deg") else "cm"
                try:
                    parameter.expression = f"{value:.17g} {internal_unit}"
                    if not design.computeAll():
                        raise ValueError("Fusion parameter edit did not rebuild")
                    observed = MeasureDesign(design)
                    if not math.isclose(parameter.value, value, rel_tol=1e-9, abs_tol=1e-12):
                        raise ValueError("Fusion parameter edit was not applied")
                    saved = work / f"edit-{index}.f3d"
                    if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(saved))):
                        raise ValueError("Fusion could not save the edited candidate")
                    if sum(path.stat().st_size for path in work.glob("edit-*.f3d")) > 256 * 1024 * 1024:
                        raise ValueError("edited native output exceeds 256 MiB")
                    result["edits"].append({"parameter": parameter.name, "original_value": old_value, "edited_value": value, "unit": internal_unit, "measured": observed, "saved": saved.name})
                finally:
                    parameter.expression = original
                    if not design.computeAll():
                        raise ValueError("Fusion parameter restore did not rebuild")
                result["edits"][-1]["restored"] = MeasureDesign(design)
        result["status"] = "measured"
    except Exception as error:
        result.update(status="failed", error=f"{type(error).__name__}: {error}"[:2048])
    finally:
        if document is not None:
            document.close(False)
        result["documents_after"] = app.documents.count
    return result
