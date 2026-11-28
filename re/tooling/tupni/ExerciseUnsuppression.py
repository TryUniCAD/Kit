from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "sw2026"))

import Swapp


def snapshot(model, target, mark, prefix):
    for name, operation in (
        ("bodies", lambda: Swapp.bodies(model)),
        ("mass", lambda: Swapp.mass(model)),
        ("features", lambda: Swapp.features(model)),
        ("whats_wrong", lambda: Swapp.rebuild_errors(model)),
    ):
        mark(f"{prefix}_{name}_start")
        target[name] = operation()
        mark(f"{prefix}_{name}_return")


def exercise(path, prepared):
    if path is None or not path.is_file() or path.suffix.casefold() != ".sldprt":
        raise ValueError("one copied native part is required")
    if prepared is None:
        raise ValueError("a retained goal-owned controller is required")
    controller = prepared["controller"]
    result = {"kind": "diagnostic-unsuppression", "acceptance": False, "path": str(path), "stages": [], "changes": [], "before": {}, "after": {}}
    prepared["identity"]["suppression_experiment"] = result
    prepared["identity"]["open_mode"] = "silent-writable-no-save"
    model = None

    def mark(stage):
        result["stage"] = stage
        result["stages"].append({"stage": stage, "time": time.time()})
        if prepared.get("trace") is not None:
            try:
                prepared["trace"].markphase(stage)
            except Exception as error:
                result.setdefault("stage_marker_errors", []).append({"stage": stage, "exception": repr(error)})

    try:
        mark("open_start")
        model, errors, warnings = controller.open(path, read_only=False)
        result.update(opened=model is not None, open_errors=errors, open_warnings=warnings)
        mark("open_return")
        if model is None:
            return result
        snapshot(model, result["before"], mark, "before")
        feature = Swapp.cv(model, "FirstFeature")
        while feature is not None:
            feature_type = str(Swapp.cv(feature, "GetTypeName2"))
            if feature_type in ("ProfileFeature", "Extrusion"):
                change = {"name": str(feature.Name), "type": feature_type, "suppressed_before": bool(Swapp.cv(feature, "IsSuppressed"))}
                result["changes"].append(change)
                if change["suppressed_before"]:
                    mark("unsuppress_start")
                    change["returned"] = bool(feature.SetSuppression2(1, 1, Swapp.nothing()))
                    mark("unsuppress_return")
                    change["suppressed_after"] = bool(Swapp.cv(feature, "IsSuppressed"))
            feature = Swapp.cv(feature, "GetNextFeature")
        mark("rebuild_start")
        result["rebuilt"] = bool(model.ForceRebuild3(False))
        mark("rebuild_return")
        snapshot(model, result["after"], mark, "after")
        return result
    except Exception as error:
        result.update(failure_stage=result.get("stage"), exception=repr(error))
        raise
    finally:
        if model is not None:
            mark("close_start")
            controller.close_doc(model)
            mark("close_return")
