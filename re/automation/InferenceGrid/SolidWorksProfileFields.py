# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections import Counter, defaultdict
import math

from convert.adapters.solidworks.Core.Native import (
    MarkerMetres,
    ParseNames,
    ParseScalars,
)


def profile_fields(data, stream, features, rows, projected, sketches):
    frequencies = Counter((row["feature_id"], row["name"]) for row in rows)
    targets = defaultdict(list)
    for row in rows:
        if (
            frequencies[row["feature_id"], row["name"]] == 1
            and row["status"] == "ambiguous"
            and (
                "<MOD-DIAM>" in row["display_text"]
                or row["display_text"].lstrip().startswith("R")
            )
        ):
            targets[row["feature_id"]].append(row)
    if not targets:
        return []
    owners = {f.object_id: f.name for f in features}
    if len(owners) != len(features):
        return []
    names = ParseNames(data)
    markers = sorted(
        (n.offset, n.object_id)
        for n in names
        if n.object_id in owners and owners[n.object_id] == n.name
    )
    occurrences = Counter(owner for _, owner in markers)
    scalars = {s.value_offset: s for s in ParseScalars(data, names)}
    results = []
    for index, (start, owner) in enumerate(markers):
        if occurrences[owner] != 1 or owner not in targets or owner not in sketches:
            continue
        end = markers[index + 1][0] if index + 1 < len(markers) else len(data)
        sketch = sketches[owner]
        circles = []
        native_circles = []
        for entity in sketch["entities"]["$tuple"]:
            geom = entity["geometry"]
            if geom["$type"] != "CircleGeometry":
                continue
            if entity["attributes"].get("semantic") == "circle":
                native_circles.append(entity)
            spans = entity.get("provenance", {}).get("spans", {}).get("$tuple", [])
            if len(spans) != 2 or not all(
                s["stream"] == stream
                and s["record_kind"] == "sketch-circle-marker"
                and start <= s["offset"] < s["offset"] + s["length"] <= end
                for s in spans
            ):
                continue
            first, second = spans
            if first["offset"] + first["length"] > second["offset"]:
                continue
            center, rim = [
                MarkerMetres(data, s["offset"], s["offset"] + s["length"])
                for s in spans
            ]
            if center is None or rim is None:
                continue
            radius = math.dist(center, rim)
            if radius <= 0 or not math.isclose(
                radius * 1000, geom["radius"], rel_tol=1e-9, abs_tol=1e-9
            ):
                continue
            if not all(
                math.isclose(
                    coord * 1000, geom["center"][axis], rel_tol=1e-9, abs_tol=1e-9
                )
                for coord, axis in zip(center, ("x", "y"))
            ):
                continue
            circles.append(
                (entity["id"], radius, center, rim, first["offset"], second["offset"])
            )
        constraints = defaultdict(list)
        for rule in sketch["constraints"]["$tuple"]:
            constraints[rule.get("parameter_id")].append(rule)
        for row in targets[owner]:
            params = projected.get((owner, row["name"]), [])
            if len(params) != 1:
                continue
            candidates = [
                scalars.get(pos)
                for source, pos in row["candidate_locations"]
                if source == stream and start <= pos < end
            ]
            driving = [
                s
                for s in candidates
                if s and s.name == row["name"] and s.role == "driving"
            ]
            if len(driving) != 1:
                continue
            scalar = driving[0]
            kind = "diameter" if "<MOD-DIAM>" in row["display_text"] else "radius"
            factor = 2 if kind == "diameter" else 1
            if len(scalar.operands) != 1:
                continue
            native = [
                e
                for e in native_circles
                if e["attributes"].get("object_index")
                == scalar.operands[0].entity_index + 1
            ]
            if len(native) != 1:
                continue
            matching = [
                c
                for c in circles
                if math.isclose(
                    c[1] * factor, scalar.value, rel_tol=1e-9, abs_tol=1e-12
                )
            ]
            rules = constraints[params[0]["id"]]
            if (
                len(matching) != 1
                or len(rules) != 1
                or rules[0]["kind"] != kind
                or not rules[0]["driving"]
            ):
                continue
            entity, radius, center, rim, center_offset, rim_offset = matching[0]
            geom = native[0]["geometry"]
            if not math.isclose(
                geom["radius"], radius * 1000, rel_tol=1e-9, abs_tol=1e-9
            ) or not all(
                math.isclose(
                    coord * 1000, geom["center"][axis], rel_tol=1e-9, abs_tol=1e-9
                )
                for coord, axis in zip(center, ("x", "y"))
            ):
                continue
            refs = rules[0]["references"]["$tuple"]
            if len(refs) != 1 or refs[0]["entity_id"] != entity:
                continue
            if not any(
                (s["stream"], s["offset"], s["length"], s["record_kind"])
                == (stream, scalar.value_offset, 8, "dimension-scalar")
                for s in params[0]["provenance"]["spans"]["$tuple"]
            ):
                continue
            results.append(
                (
                    row,
                    {
                        "verified_location": (stream, scalar.value_offset),
                        "entity_id": entity,
                        "native_entity_id": native[0]["id"],
                        "center_offset": center_offset,
                        "rim_offset": rim_offset,
                        "center_m": center,
                        "rim_m": rim,
                        "radius_m": radius,
                        "native_dimension_m": scalar.value,
                    },
                )
            )
    return results
