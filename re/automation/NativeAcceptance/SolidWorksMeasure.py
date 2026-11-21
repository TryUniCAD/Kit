import math
import os
from pathlib import Path
import sys

sys.path[:0] = [str(Path(__file__).resolve().parents[1]), str(Path(__file__).resolve().parents[1] / "ApplicationWorkers")]

from NativeAcceptance.Records import FileHash, ReadJson, WriteJson
from NativeAcceptance.SolidWorksBrep import MeasureBrep
from NativeAcceptance.SolidWorksSemantics import MeasureSemantics
from SolidWorksAvailability import HoldMutex, IsSolidWorksRunning, OracleMutex


def ComValue(owner, name):
    value = getattr(owner, name)
    return value() if callable(value) else value


def MeasurePart(document, app):
    import pythoncom
    from win32com.client import VARIANT

    features, parameters, sketches, native_features = [], [], [], []
    feature = ComValue(document, "FirstFeature")
    while feature is not None:
        if len(features) >= 4096:
            raise ValueError("native feature inventory exceeds 4096 nodes")
        name = str(feature.Name)
        native_features.append(feature)
        warning = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_BOOL, False)
        error = feature.GetErrorCode2(warning)
        features.append({"name": name, "type": feature.GetTypeName2(), "suppressed": bool(ComValue(feature, "IsSuppressed")), "health": int(error), "message": "warning" if error and warning.value else "error" if error else ""})
        display = ComValue(feature, "GetFirstDisplayDimension")
        count = 0
        while display is not None:
            count += 1
            if count > 256:
                raise ValueError("native feature dimensions exceed 256 entries")
            dimension = display.GetDimension2(0)
            kind = int(display.Type2)
            unit = "rad" if kind in (3, 16) else "m"
            if str(dimension.FullName).split("@")[1:2] == [name]:
                parameters.append({"name": "@".join(str(dimension.FullName).split("@")[:2]), "value": float(dimension.SystemValue), "unit": unit, "driving": int(dimension.DrivenState) == 2, "dimension_type": kind})
            display = feature.GetNextDisplayDimension(display)
        if feature.GetTypeName2() in ("ProfileFeature", "3DProfileFeature"):
            sketch = feature.GetSpecificFeature2()
            segments = sketch.GetSketchSegments() or ()
            relations = sketch.RelationManager.GetRelations(0) or ()
            sketches.append({"name": name, "entities": len(segments), "constraints": len(relations), "dimensions": count})
        feature = ComValue(feature, "GetNextFeature")
    semantics = MeasureSemantics(app, document, native_features)
    bodies = []
    for index, body in enumerate(document.GetBodies2(0, False) or ()):
        props = body.GetMassProperties(1.0)
        if props is None or len(props) < 6:
            raise ValueError("native body has no measured mass properties")
        bodies.append({"name": body.Name, "volume_mm3": float(props[3]) * 1e9, "center_mm": [float(item) * 1000 for item in props[:3]], "faces": int(body.GetFaceCount()), "edges": int(body.GetEdgeCount()), "vertices": len(body.GetVertices() or ()), "geometry": MeasureBrep(body, f"body:{index}", semantics["gaps"])})
    return {"bodies": bodies, "features": features, "parameters": parameters, "sketches": sketches, "semantics": semantics, "configuration": str(document.ConfigurationManager.ActiveConfiguration.Name)}


def MeasureSource(app, work, request):
    import pythoncom
    from win32com.client import VARIANT

    errors = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
    warnings = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
    document = app.OpenDoc6(str(work / request["source"]), 1, 3, request.get("configuration") or "", errors, warnings)
    result = {"application": "solidworks", "build": str(ComValue(app, "RevisionNumber")), "load_errors": [int(errors.value)] if errors.value else [], "load_warnings": [int(warnings.value)] if warnings.value else [], "edits": []}
    if document is None:
        raise ValueError(f"SOLIDWORKS could not open the candidate: {errors.value}")
    try:
        result["opened"] = MeasurePart(document, app)
        if errors.value or warnings.value & ~2 or not document.ForceRebuild3(False):
            raise ValueError("SOLIDWORKS reported a load or rebuild problem")
        result["rebuilt"] = MeasurePart(document, app)
        if any(item["health"] for item in result["rebuilt"]["features"]):
            raise ValueError("SOLIDWORKS feature tree contains a rebuild error or warning")
        if request["role"] == "candidate":
            parameters = {item["name"]: item for item in result["rebuilt"]["parameters"]}
            driving = {item["name"] for item in result["rebuilt"]["semantics"]["parameters"] if item["role"] == "driving"}
            independent = [item for item in parameters.values() if item["driving"] and item["name"] in driving]
            if not independent or len(independent) > 16:
                raise ValueError("candidate needs between one and sixteen independent driving parameters for this verification batch")
            for index, parameter in enumerate(independent):
                handle = document.Parameter(parameter["name"])
                original = float(handle.SystemValue)
                value = original * 1.1 if abs(original) > 1e-12 else (0.1 if parameter["unit"] == "rad" else 0.001)
                try:
                    handle.SystemValue = value
                    if not document.ForceRebuild3(False) or not math.isclose(float(handle.SystemValue), value, rel_tol=1e-9, abs_tol=1e-12):
                        raise ValueError("SOLIDWORKS driving edit was not applied or did not rebuild")
                    measured = MeasurePart(document, app)
                    saved = work / f"edit-{index}.SLDPRT"
                    if not document.Extension.SaveAs(str(saved), 0, 1, None, errors, warnings) or errors.value or warnings.value:
                        raise ValueError("SOLIDWORKS could not save the edited candidate without warnings")
                    if sum(path.stat().st_size for path in work.glob("edit-*.SLDPRT")) > 256 * 1024 * 1024:
                        raise ValueError("edited native output exceeds 256 MiB")
                    result["edits"].append({"parameter": parameter["name"], "original_value": original, "edited_value": value, "unit": parameter["unit"], "measured": measured, "saved": saved.name})
                finally:
                    handle.SystemValue = original
                    if not document.ForceRebuild3(False):
                        raise ValueError("SOLIDWORKS driving parameter restore did not rebuild")
                result["edits"][-1]["restored"] = MeasurePart(document, app)
        return {**result, "status": "measured"}
    finally:
        app.QuitDoc(str(ComValue(document, "GetTitle")))


def MainMeasure():
    import pythoncom
    import win32api
    import win32event
    from win32com.client import DispatchEx

    work = Path(sys.argv[1]).resolve(strict=True)
    request = ReadJson(work / "request.json")
    result = {"status": "unavailable", "nonce": request["nonce"], "source_sha256": request["source_sha256"]}
    app, handle = None, None
    with HoldMutex(OracleMutex) as held:
        if not held or IsSolidWorksRunning():
            WriteJson(work / "response.json", {**result, "error": "close SOLIDWORKS before verification so Kit can start a fresh owned session"})
            return 4
        pythoncom.CoInitialize()
        try:
            if FileHash(work / request["source"]) != request["source_sha256"]:
                raise ValueError("native candidate changed before measurement")
            app = DispatchEx("SldWorks.Application")
            pid = int(ComValue(app, "GetProcessID"))
            handle = win32api.OpenProcess(0x100000, False, pid)
            if ComValue(app, "GetDocumentCount"):
                app = None
                raise ValueError("new SOLIDWORKS process unexpectedly contains documents")
            app.UserControlBackground = True
            app.Visible = False
            result.update(MeasureSource(app, work, request), pid=pid)
            if ComValue(app, "GetDocumentCount"):
                raise ValueError("SOLIDWORKS retained a document after candidate cleanup")
            result["documents_after"] = 0
        except Exception as error:
            result.update(status="failed", error=f"{type(error).__name__}: {error}"[:2048])
        finally:
            if app is not None:
                if not ComValue(app, "GetDocumentCount"):
                    app.ExitApp()
                    app = None
                    if win32event.WaitForSingleObject(handle, 30000) != win32event.WAIT_OBJECT_0:
                        result.update(status="failed", error="owned SOLIDWORKS process did not exit")
                else:
                    result.update(status="failed", error="SOLIDWORKS retained documents; session left open for recovery")
            if handle is not None:
                handle.Close()
            pythoncom.CoUninitialize()
    WriteJson(work / "response.json", result)
    return 0 if result["status"] == "measured" else 4


if __name__ == "__main__":
    sys.exit(MainMeasure())
