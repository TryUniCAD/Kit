# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import math


def near(observed, expected, absolute):
    return (type(observed) in (int, float) and type(expected) in (int, float)
            and math.isfinite(observed) and math.isfinite(expected)
            and math.isclose(observed, expected, abs_tol=absolute, rel_tol=1e-9))


def measure_bodies(document, measured):
    bodies = document["bodies"]["$tuple"]
    expected = measured["bodies"]
    by_name = {body["name"]: body for body in bodies}
    names = [body["name"] for body in expected]
    aligned = len(by_name) == len(bodies) == len(expected) == len(set(names)) and set(names) == set(by_name)
    result = {"count_matches": len(bodies) == measured["body_count"], "unique_names_match": aligned, "bodies": {}}
    if not aligned:
        if len(expected) != 1 or len(bodies) != 1:
            return result
        by_name = {names[0]: bodies[0]}
    for body in expected:
        top = by_name[body["name"]].get("topology") or {}
        box = top.get("bounding_box") or {}
        bounds = body.get("bounding_box_mm")
        checks = {key: type(top.get(key + "_count")) is int and top[key + "_count"] == body.get(label)
                  for key, label in (("face", "faces"), ("edge", "edges"), ("vertex", "vertices"))}
        checks["volume_mm3"] = near(top.get("volume"), body.get("volume_mm3"), 1e-6)
        checks["bounds_mm"] = isinstance(bounds, list) and len(bounds) == 2 and all(
            isinstance(values, list) and len(values) == 3 and all(
                near((box.get(end) or {}).get(axis), value, 1e-6)
                for axis, value in zip("xyz", values))
            for end, values in zip(("minimum", "maximum"), bounds))
        result["bodies"][body["name"]] = checks
    return result
