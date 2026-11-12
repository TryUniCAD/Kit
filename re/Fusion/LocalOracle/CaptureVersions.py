import ctypes
import hashlib
import json
from pathlib import Path
import traceback

import adsk.core


root = Path(__file__).resolve().parent
output = root / "Reflection"
output.mkdir(exist_ok=True)
target = output / "Versions.json"
bridge_path = Path("/tmp/kit-fusion-native-analysis/SchemaVersions.dylib")
evidence = json.loads((root / "VersionsEvidence.json").read_text())
app = adsk.core.Application.get()
report = {"fusion_version": app.version, "documents_before": app.documents.count, "bridge_sha256": hashlib.sha256(bridge_path.read_bytes()).hexdigest(), "source_sha256": hashlib.sha256((root / "SchemaVersions.cpp").read_bytes()).hexdigest()}
try:
    if report["bridge_sha256"] != evidence["verification"]["compiled_sha256"]:
        raise RuntimeError("Native version bridge digest differs")
    if app.version != evidence["fusion_build"]:
        raise RuntimeError("Native schema bridge build differs from the running application")
    if target.exists():
        raise RuntimeError("Schema capture destination already exists")
    contents = Path.home() / "Library/Application Support/Autodesk/webdeploy/production" / evidence["deployment"] / "Autodesk Fusion.app/Contents"
    for name, expected in evidence["native_images"].items():
        path = contents / "Libraries/Neutron" / name
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected["sha256"]:
            raise RuntimeError("Native library digest differs: " + name)
    library = ctypes.PyDLL(str(bridge_path))
    library.dump_schema_versions.argtypes = [ctypes.c_char_p]
    library.dump_schema_versions.restype = ctypes.c_int
    report["return_code"] = library.dump_schema_versions(str(target).encode())
    if target.exists():
        report["schema_sha256"] = hashlib.sha256(target.read_bytes()).hexdigest()
    if report["return_code"] != 0:
        raise RuntimeError("Native schema export returned " + str(report["return_code"]))
    captured = json.loads(target.read_text())
    report["metatype_count"] = captured["metatype_count"]
    report["status"] = "captured"
except Exception:
    report["status"] = "failed"
    report["traceback"] = traceback.format_exc()
    raise
finally:
    report["documents_after"] = app.documents.count
    (output / "VersionsCapture.json").write_text(json.dumps(report, indent=2) + "\n")
