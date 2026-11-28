from __future__ import annotations

from ExerciseSolidworks import exercise as measure


def exercise(path, prepared):
    if prepared is None:
        raise ValueError("a retained goal-owned controller is required")
    prepared["read_only"] = False
    prepared["identity"]["open_mode"] = "silent-writable-no-save"
    return measure(path, prepared)
