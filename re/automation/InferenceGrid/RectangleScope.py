# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import math


def driving_rectangles(document):
    result = {}
    params = {p["id"]: p for p in document.get("parameters", {}).get("$tuple", [])}
    for sketch in document.get("sketches", {}).get("$tuple", []):
        profiles = sketch.get("closed_profile_entity_ids", {}).get("$tuple", [])
        if len(profiles) != 1:
            continue
        ids = profiles[0].get("$tuple", [])
        entities = {e["id"]: e for e in sketch.get("entities", {}).get("$tuple", []) if e.get("construction") is False}
        if len(ids) != 4 or len(set(ids)) != 4 or set(ids) != entities.keys():
            continue
        edges = set()
        for entity in entities.values():
            line = entity.get("geometry") or {}
            if line.get("$type") != "LineGeometry":
                break
            points = [tuple(line[end].get(axis) for axis in ("x", "y")) for end in ("start", "end")]
            if not all(type(x) in (int, float) and math.isfinite(x) for point in points for x in point):
                break
            a, b = points
            if (a[0] == b[0]) == (a[1] == b[1]):
                break
            edges.add(tuple(sorted(points)))
        if len(edges) != 4:
            continue
        vertices = {v for edge in edges for v in edge}
        if len(vertices) != 4 or any(sum(v in edge for edge in edges) != 2 for v in vertices):
            continue
        owned = set(sketch.get("parameter_ids", {}).get("$tuple", []))
        drivers = {c["parameter_id"] for c in sketch.get("constraints", {}).get("$tuple", []) if
                   c.get("driving") is True and c.get("kind") in ("distance", "distance_x", "distance_y") and
                   c.get("parameter_id") in owned and c["parameter_id"] in params and
                   params[c["parameter_id"]].get("value", {}).get("kind", {}).get("value") == "length"}
        if len(drivers) >= 2:
            result[sketch["id"]] = sorted(drivers)
    return result
