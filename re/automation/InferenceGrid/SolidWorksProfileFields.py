# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections import Counter, defaultdict
import math
import struct

from convert.adapters.solidworks.Core.Native import (
    MarkerMetres,
    ParseMarkers,
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
        raw_markers = None
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
            geometry_source = "profile"
            if not matching:
                spans = native[0]["provenance"]["spans"]["$tuple"]
                if len(spans) != 1 or spans[0]["stream"] != stream or spans[0]["record_kind"] != "sketch-native-marker":
                    continue
                if raw_markers is None:
                    raw_markers = ParseMarkers(data, start, end)
                record = next((m for m in raw_markers if m.offset == spans[0]["offset"]), None)
                if (record is None or record.length != spans[0]["length"] or record.length < 86
                        or not record.endpoint_indices or record.endpoint_indices[0] != record.endpoint_indices[1]):
                    continue
                center_index = struct.unpack_from("<H", data, record.offset + 84)[0]
                rim_index = record.endpoint_indices[0]
                if center_index == rim_index or max(center_index, rim_index) >= len(raw_markers):
                    continue
                first, second = raw_markers[center_index], raw_markers[rim_index]
                center, rim = first.coordinates_metres, second.coordinates_metres
                if center is None or rim is None:
                    continue
                radius = math.dist(center, rim)
                if radius <= 0 or not math.isclose(radius * factor, scalar.value, rel_tol=1e-9, abs_tol=1e-12):
                    continue
                matching = [(native[0]["id"], radius, center, rim, first.offset, second.offset)]
                geometry_source = "native_marker_references"
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
                        "geometry_source": geometry_source,
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


def paired_sketch_lengths(data, stream, features, rows, projected):
    ambiguous = [r for r in rows if r["status"] == "ambiguous" and len(r["candidate_locations"]) == 2]
    if not ambiguous:
        return
    owners = {(f.object_id, f.name): f for f in features}
    names = ParseNames(data)
    markers = sorted((n.offset, n.object_id, n.name) for n in names if (n.object_id, n.name) in owners)
    counts = Counter(owner for _, owner, _ in markers)
    bounds = {owner: (start, markers[i+1][0] if i+1 < len(markers) else len(data))
              for i, (start, owner, name) in enumerate(markers)
              if counts[owner] == 1 and owners[owner, name].kind == "Sketch"}
    scalars = {s.value_offset: s for s in ParseScalars(data, names)}
    frequencies = Counter((r["feature_id"], r["name"]) for r in rows)
    for row in ambiguous:
        key = row["feature_id"], row["name"]
        params = projected.get(key, [])
        if key[0] not in bounds or frequencies[key] != 1 or len(params) != 1:
            continue
        start, end = bounds[key[0]]
        pair = [scalars.get(pos) for source, pos in row["candidate_locations"] if source == stream and start <= pos < end - 7]
        if len(pair) != 2 or not all(pair) or {s.role for s in pair} != {"display", "driving"}:
            continue
        copy, driving = pair if pair[0].role == "display" else reversed(pair)
        if (copy.name != row["name"] or driving.name != copy.name or copy.value != driving.value
                or None in {copy.object_id, driving.object_id} or copy.object_id == driving.object_id or not driving.operands
                or [(o.kind_code,o.entity_index) for o in copy.operands] != [(o.kind_code,o.entity_index) for o in driving.operands]):
            continue
        param = params[0]
        if (param["attributes"].get("dimension_kind") != "length" or param["attributes"].get("native_value") != driving.value
                or param["attributes"].get("native_role") != "driving" or param["value"]["unit"] != "mm"
                or not math.isclose(param["value"]["value"], driving.value*1000, rel_tol=1e-12, abs_tol=1e-12)):
            continue
        if any((span["stream"], span["offset"], span["length"], span["record_kind"]) == (stream, driving.value_offset, 8, "dimension-scalar")
               for span in param["provenance"]["spans"]["$tuple"]):
            yield row, {"verified_location": (stream, driving.value_offset), "display_offset": copy.value_offset,
                        "operand_indices": [o.entity_index for o in driving.operands]}
