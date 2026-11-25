from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import runpy
from time import perf_counter_ns
import traceback

import adsk.core


def pinned_control(config_path, expected_sha):
    support_path = Path(__file__).resolve().parents[1] / "EncoderRoundTrip" / "Measure.py"
    settings = json.loads(config_path.read_bytes())
    if sha256(support_path.read_bytes()).hexdigest() != settings["measurement_script_sha256"]:
        raise ValueError("the shared measurement source changed after replay preparation")
    oracle = runpy.run_path(str(support_path))
    require = oracle["require"]
    app = adsk.core.Application.get()
    root = config_path.parent
    receipt = root / "ControlBefore.json"
    archive = root / "VendorControl.f3d"
    require(not receipt.exists(), "ControlBefore receipt already exists")
    started = perf_counter_ns()
    report = {
        "stage": "ControlBefore",
        "case": settings["case"],
        "role": settings["role"],
        "source_sha256": settings["source_sha256"],
        "candidate_sha256": settings["candidate_sha256"],
        "batch_sha256": sha256(config_path.read_bytes()).hexdigest(),
        "measurement_script_sha256": settings["measurement_script_sha256"],
        "control_script_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "fusion_version": app.version,
        "pid": os.getpid(),
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "documents_before": app.documents.count,
        "status": "running",
        "measurements": {},
        "archives": {},
    }
    document = None

    def checkpoint():
        temporary = receipt.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        temporary.replace(receipt)

    try:
        require(report["documents_before"] == 0, "Oracle requires a fresh process with zero unrelated open documents")
        require(oracle["digest"](archive) == expected_sha, "Independent control archive does not match the pinned digest")
        report["archives"][archive.name] = expected_sha
        checkpoint()
        options = app.importManager.createFusionArchiveImportOptions(str(archive))
        document = app.importManager.importToNewDocument(options)
        design = oracle["design_for"](document)
        for label in ("opened", "rebuilt"):
            if label == "rebuilt":
                require(design.computeAll(), "Independent control did not rebuild")
            observed = oracle["observe"](design)
            report["measurements"][label] = observed
            checkpoint()
            oracle["require_shape"](observed, settings["width_mm"], settings["depth_mm"], settings["encoded_height_mm"], False)
        require(document.close(False), "Could not close the independent control")
        document = None
        require(app.documents.count == 0, "A document remains open")
        report["status"] = "passed"
    except Exception:
        report["status"] = "failed"
        report["error"] = traceback.format_exc()
        raise
    finally:
        try:
            if document is not None and not document.close(False):
                raise RuntimeError("Could not close the independent control")
        except Exception:
            report["status"] = "failed"
            report["cleanup_error"] = traceback.format_exc()
        report["documents_after"] = app.documents.count
        report["ended_utc"] = datetime.now(timezone.utc).isoformat()
        report["elapsed_ns"] = perf_counter_ns() - started
        checkpoint()
