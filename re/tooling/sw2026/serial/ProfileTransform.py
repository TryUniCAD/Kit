from __future__ import annotations

import math


def stored_frame(profiles):
    matches = [node for node in profiles if getattr(node, "cls", None) == "moProfileFeature_c"]
    if len(matches) != 1:
        raise ValueError("expected one decoded ordinary sketch profile")
    transform = matches[0]["pd_ff0"]
    if transform["f78"] != 0:
        raise ValueError("principal sketch transform contains unexpected extensions")
    matrix = [transform["f08"][f"m{index}"] for index in range(9)] if transform["has_matrix"] else [float(index in (0, 4, 8)) for index in range(9)]
    values = [*matrix, *(transform[key] for key in ("f58", "f60", "f68", "f70"))]
    if not all(type(value) in (int, float) and math.isfinite(value) for value in values):
        raise ValueError("principal sketch transform contains a nonfinite value")
    return values
