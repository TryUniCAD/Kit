from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "sw2026"))

import Swapp


def exercise(path, prepared):
    if path is None or not path.is_file() or path.suffix.casefold() != ".sldprt":
        raise ValueError("one explicitly selected native part is required")
    if prepared is None:
        raise ValueError("a retained goal-owned controller is required")
    controller = prepared["controller"]
    result = {"kind": "instrumented-native-document", "path": str(path), "revision": controller.revision, "stages": []}
    prepared["identity"]["measurement"] = result

    def progress(stage, partial):
        result.update(partial)
        result["stages"].append({"stage": stage, "time": time.time()})
        if prepared.get("trace") is not None:
            try:
                prepared["trace"].markphase(stage)
            except Exception as error:
                prepared["identity"].setdefault("stage_marker_errors", []).append({"stage": stage, "exception": repr(error)})

    result.update(Swapp.measure(controller, path, progress=progress, read_only=True))
    return result
