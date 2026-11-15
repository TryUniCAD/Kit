from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "sw2026"))

import Swapp


def exercise(path, prepared):
    if path is None or not path.is_file() or path.suffix.casefold() != ".sldprt":
        raise ValueError("one explicitly selected native part is required")
    if prepared is None:
        raise ValueError("a retained goal-owned controller is required")
    app = prepared["controller"].app
    model = None
    try:
        errors, warnings = Swapp.byref_long(), Swapp.byref_long()
        model = app.OpenDoc6(str(path), 1, Swapp.OPEN_SILENT | Swapp.OPEN_READONLY, "", errors, warnings)
        result = {
            "kind": "instrumented-native-document",
            "path": str(path), "revision": str(Swapp.cv(app, "RevisionNumber")),
            "opened": model is not None, "open_errors": int(errors.value), "open_warnings": int(warnings.value),
        }
        if model is not None:
            result.update(rebuilt=bool(model.ForceRebuild3(False)), bodies=Swapp.bodies(model), mass=Swapp.mass(model), features=Swapp.features(model), whats_wrong=Swapp.rebuild_errors(model))
        return result
    finally:
        if app is not None and model is not None:
            app.CloseDoc(str(Swapp.cv(model, "GetTitle")))
