import ctypes
import hashlib
import json
from pathlib import Path
import time
import traceback

import adsk.core


root = Path(__file__).resolve().parent
output = root / "Reflection"
repository = root.parents[2]
plan = json.loads((output / "Selection.json").read_text())
state_path = output / "WarmProgress.json"
report = json.loads(state_path.read_text()) if state_path.exists() else {"operation": "load_representative_corpus_for_schema_initialization", "imports": [], "snapshots": []}
app = adsk.core.Application.get()
original = app.activeDocument
started = time.monotonic()
try:
    if app.version != "2706.1.17":
        raise RuntimeError("Unexpected Fusion build")
    initial_count = len(report["imports"])
    batch = plan["selected"][initial_count:initial_count + 1]
    for entry in batch:
        doc = None
        observation = {"path": entry["path"], "sha256": entry["sha256"]}
        try:
            source = repository / entry["path"]
            if hashlib.sha256(source.read_bytes()).hexdigest() != entry["sha256"]:
                raise RuntimeError("Corpus archive digest changed")
            doc = app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(str(source)))
            if doc is None:
                raise RuntimeError("Native archive import returned no document")
            observation["status"] = "opened"
        except Exception:
            observation["status"] = "failed"
            observation["traceback"] = traceback.format_exc()
        finally:
            if doc is not None:
                doc.close(False)
            report["imports"].append(observation)
            state_path.write_text(json.dumps(report, indent=2) + "\n")
        if time.monotonic() - started > 75:
            break
    target = output / ("Schema" + str(len(report["imports"])).zfill(3) + ".json")
    bridge_path = Path("/tmp/kit-fusion-native-analysis/SchemaBridge.dylib")
    initial_capture = json.loads((output / "Capture.json").read_text())
    if hashlib.sha256(bridge_path.read_bytes()).hexdigest() != initial_capture["bridge_sha256"]:
        raise RuntimeError("Native schema bridge digest changed")
    library = ctypes.PyDLL(str(bridge_path))
    library.dump_schema.argtypes = [ctypes.c_char_p]
    library.dump_schema.restype = ctypes.c_int
    code = library.dump_schema(str(target).encode())
    if code:
        raise RuntimeError("Native schema export returned " + str(code))
    captured = json.loads(target.read_text())
    sets = {item["metatype_identifier"]: item for row in captured["metatypes"] for item in row["member_sets"] or []}
    report["snapshots"].append({"file": target.name, "sha256": hashlib.sha256(target.read_bytes()).hexdigest(), "metatype_count": captured["metatype_count"], "initialized_schema_count": sum(item["initialized"] for item in sets.values()), "registered_member_count": sum(len(item["members"] or []) for item in sets.values()), "after_imports": len(report["imports"])})
    if any(item["status"] == "failed" for item in report["imports"][initial_count:]):
        raise RuntimeError("One or more native corpus imports failed; see recorded per-file errors")
    report["status"] = "captured" if len(report["imports"]) == len(plan["selected"]) else "in_progress"
except Exception:
    report["status"] = "failed"
    report["traceback"] = traceback.format_exc()
    raise
finally:
    if original is not None and original.isValid:
        original.activate()
    report["documents_after"] = app.documents.count
    report["fusion_version"] = app.version
    state_path.write_text(json.dumps(report, indent=2) + "\n")
