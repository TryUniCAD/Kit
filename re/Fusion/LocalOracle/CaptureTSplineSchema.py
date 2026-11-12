import ctypes
import hashlib
import json
from pathlib import Path
import traceback

import adsk.core
import adsk.fusion

root = Path(__file__).resolve().parent
output = root / "TSplineReflection"
output.mkdir(exist_ok=True)
target = output / "Versions.json"
bridge_path = Path("/tmp/kit-fusion-native-analysis/SchemaVersions.dylib")
evidence = json.loads((root / "VersionsEvidence.json").read_text())
capture = json.loads((root / "TSpline/Capture.json").read_text())
requirements = json.loads((root.parent / "Reconstruction/TSpline/DocumentLinks.json").read_text())
needed = sorted({(entry["class"], entry["version"]) for source in requirements["sources"] for entry in source["unresolved_classes"]})
app = adsk.core.Application.get()
original = app.activeDocument
document = None
form = None
editing = False
report = {"scope": "Owned native Form initialization and exact-version reflection; separate capture without replacing prior schemas", "fusion_version": app.version, "documents_before": app.documents.count, "bridge_sha256": hashlib.sha256(bridge_path.read_bytes()).hexdigest(), "source_sha256": hashlib.sha256((root / "SchemaVersions.cpp").read_bytes()).hexdigest(), "imports": [], "required_classes": [{"name": name, "version": version} for name, version in needed]}


def checkpoint():
    (output / "Capture.json").write_text(json.dumps(report, indent=2) + "\n")


try:
    if target.exists():
        raise RuntimeError("Distinct T-spline reflection destination already exists")
    if report["bridge_sha256"] != evidence["verification"]["compiled_sha256"]:
        raise RuntimeError("Native version bridge digest differs")
    if app.version != evidence["fusion_build"]:
        raise RuntimeError("Native schema bridge build differs")
    contents = Path.home() / "Library/Application Support/Autodesk/webdeploy/production" / evidence["deployment"] / "Autodesk Fusion.app/Contents"
    for name, expected in evidence["native_images"].items():
        if hashlib.sha256((contents / "Libraries/Neutron" / name).read_bytes()).hexdigest() != expected["sha256"]:
            raise RuntimeError("Native schema library digest differs: " + name)
    checkpoint()
    for source in capture["cases"]:
        artifact = source["archive"]
        path = root / "TSpline" / artifact["file"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != artifact["sha256"]:
            raise RuntimeError("Controlled T-spline archive digest differs")
        document = app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(str(path)))
        if document is None:
            raise RuntimeError("Owned T-spline archive did not open")
        design = adsk.fusion.Design.cast(document.products.itemByProductType("DesignProductType"))
        if design is None or design.rootComponent.features.formFeatures.count != 1:
            raise RuntimeError("Controlled document has no unique Form feature")
        form = design.rootComponent.features.formFeatures.item(0)
        if not form.startEdit():
            raise RuntimeError("Owned Form edit did not start")
        editing = True
        bodies = form.tSplineBodies
        counts = [{"faces": body.faces.count, "edges": body.edges.count, "vertices": body.vertices.count} for body in bodies]
        if not form.finishEdit():
            raise RuntimeError("Owned Form edit did not finish")
        editing = False
        if not design.computeAll() or form.healthState != 0:
            raise RuntimeError("Owned Form failed to rebuild")
        report["imports"].append({"file": path.name, "sha256": artifact["sha256"], "cages": counts, "health": int(form.healthState)})
        document.close(False)
        document = None
        form = None
        checkpoint()
    library = ctypes.PyDLL(str(bridge_path))
    library.dump_schema_versions.argtypes = [ctypes.c_char_p]
    library.dump_schema_versions.restype = ctypes.c_int
    report["return_code"] = library.dump_schema_versions(str(target).encode())
    if report["return_code"] != 0:
        raise RuntimeError("Native schema export failed: " + str(report["return_code"]))
    report["schema_sha256"] = hashlib.sha256(target.read_bytes()).hexdigest()
    captured = json.loads(target.read_text())
    by_name = {row["name"]: row for row in captured["metatypes"]}
    results = []
    for name, version in needed:
        row = by_name[name]
        lookup = next((value for value in row["member_set_lookups"] or [] if value["lookup_version"] == version), None)
        own = next((value for value in (lookup or {}).get("member_sets") or [] if value["metatype_identifier"].lower() == row["identifier"].lower()), None)
        results.append({"name": name, "identifier": row["identifier"], "version": version, "initialized": bool(own and own["initialized"]), "members": len((own or {}).get("members") or [])})
    report["required_schema_results"] = results
    report["metatype_count"] = captured["metatype_count"]
    report["status"] = "captured" if all(value["initialized"] for value in results) else "incomplete"
except Exception:
    report["status"] = "failed"
    report["traceback"] = traceback.format_exc()
    raise
finally:
    if editing and form is not None:
        form.finishEdit()
    if document is not None:
        document.close(False)
    if original is not None and original.isValid:
        original.activate()
    report["documents_after"] = app.documents.count
    checkpoint()
