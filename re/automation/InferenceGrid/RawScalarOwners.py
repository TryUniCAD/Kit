# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from bisect import bisect_right
from collections import Counter, defaultdict
import math
import struct

from convert.adapters.solidworks.Core.BindMirrorField import IsAngleMatch
from convert.adapters.solidworks.Core.Dimensions.PickNamedScalar import PickNamedScalar
from convert.adapters.solidworks.Core.Dimensions.CountFields import CountFields
from convert.adapters.solidworks.Core.Native import ParseKeywords, ParseNames, ParseScalars
from convert.adapters.solidworks.Core.ParseDisplay import (
    KInformationStream,
    ParseDisplay,
)


def count_interpretations(blob, features, names):
    alternatives = {}
    for owner, family, dim, offset, end in CountFields(blob, features, names):
        text = dim.source_text.strip()
        if not text.isascii() or not text.isdecimal() or len(text) > 10:
            continue
        count = int(text)
        if not 0 < count < 2**32:
            continue
        formats = [fmt for fmt in ("B", "<H", ">H", "<I", ">I", "<Q", ">Q")
                   if struct.unpack_from(fmt, blob, offset)[0] == count]
        if not formats:
            continue
        mirrors = []
        for fmt in ("<d", ">d", "<f", ">f"):
            word = struct.pack(fmt, count)
            if struct.unpack(fmt, word)[0] != count:
                continue
            start = offset + 8
            while (found := blob.find(word, start, end)) >= 0:
                mirrors.append({"format": fmt, "offset": found})
                start = found + len(word)
        alternatives[offset] = {"feature_id": owner, "family": family, "parameter": dim.name,
                                "count": count, "integer_formats": formats, "matching_copies": mirrors}
    return alternatives


def associate(archive, member, records):
    keywords = archive.GetAction("swXmlContents/KeyWords")
    if not keywords:
        return {"status": "missing_feature_declarations"}
    try:
        configs, features = ParseKeywords(keywords)
    except ValueError:
        return {"status": "unreadable_feature_declarations"}
    if len(configs) != 1 or len({f.object_id for f in features}) != len(features):
        return {"status": "ambiguous_configuration_or_feature_ids"}
    prefix = "Contents/Config-" + str(configs[0].configuration_id)
    if member not in (prefix, prefix + "-ResolvedFeatures"):
        return {"status": "different_configuration"}
    units = ParseDisplay(archive.GetAction(KInformationStream) or b"")
    scale = {"mm": 0.001, "in": 0.0254}.get(units.UnitName) if units else None
    declarations = defaultdict(list)
    identities = {}
    for feature in features:
        identities[feature.object_id] = feature.name
        for dim in feature.dimensions:
            if dim.value_mm is None or not math.isfinite(dim.value_mm):
                continue
            if dim.kind == "angle":
                amount = math.radians(dim.value_mm)
            elif dim.kind in {"length", "diameter", "radius"} and scale is not None:
                amount = dim.value_mm * scale
            else:
                continue
            tolerance = 0.0
            if dim.kind != "angle" and type(units.Decimals) is int and 0 <= units.Decimals <= 12:
                tolerance = 0.5 * scale * 10 ** -units.Decimals
            declarations[dim.name].append((feature.object_id, amount, tolerance, dim.kind, dim.source_text))
    if sum(len(declarations[r["name"]]) for r in records) > 2_000_000:
        return {"status": "comparison_limit"}
    blob = archive.Require(member)
    names = ParseNames(blob) if records else ()
    scalars = {s.value_offset: s for s in ParseScalars(blob, names)}
    markers = []
    if member.endswith("-ResolvedFeatures"):
        for item in names:
            if item.name == identities.get(item.object_id):
                markers.append((item.offset, item.object_id))
    markers.sort()
    if len({off for off, _ in markers}) != len(markers):
        return {"status": "overlapping_feature_markers"}
    count_fields = count_interpretations(blob, features, names) if markers else {}
    positions = [off for off, _ in markers]
    occurrences = Counter(ident for _, ident in markers)
    rows = []
    local_counts = Counter()
    groups = defaultdict(list)
    for record in records:
        label = record["name"]
        matches = []
        for ident, expected, tolerance, kind, display in declarations[label]:
            exact = math.isclose(expected, record["value"], rel_tol=1e-12, abs_tol=1e-14)
            rounded_angle = kind == "angle" and IsAngleMatch(display, math.degrees(expected), math.degrees(record["value"]))
            if exact or rounded_angle or abs(expected - record["value"]) <= tolerance:
                matches.append({"id": ident, "kind": kind, "display": display,
                                "agreement": "exact" if exact else "display_precision"})
        possible = [match["id"] for match in matches]
        index = bisect_right(positions, record["offset"]) - 1
        local = None
        if index >= 0:
            start, ident = markers[index]
            if occurrences[ident] == 1 and possible.count(ident) == 1:
                local = {"id": ident, "name": identities[ident], "marker_offset": start}
                local_counts[(ident, label)] += 1
        scalar = scalars.get(record["offset"])
        trailer = None
        if scalar and scalar.name == label and scalar.value == record["value"]:
            trailer = {"role": scalar.role, "object_id": scalar.object_id,
                       "operands": [{"offset": operand.offset, "kind_code": operand.kind_code,
                                     "entity_index": operand.entity_index} for operand in scalar.operands]}
        if index >= 0:
            groups[(markers[index][1], label)].append(scalar if trailer else None)
        alternative = count_fields.get(record["offset"])
        rows.append(
            {**record, "count_hypothesis": alternative, "native_trailer": trailer, "candidate_feature_ids": possible, "declaration_matches": matches, "preceding_candidate": local}
        )
    driving = set()
    for group in groups.values():
        if len(group) > 1 and all(item is not None for item in group):
            selected = PickNamedScalar(group)
            if selected is not None:
                driving.add(selected.value_offset)
    counts = Counter()
    roles = defaultdict(Counter)
    for row in rows:
        possible, local = row["candidate_feature_ids"], row["preceding_candidate"]
        rounded = any(m["agreement"] == "display_precision" for m in row["declaration_matches"])
        row["selected_among_display_copies"] = bool(local and row["offset"] in driving)
        if row["count_hypothesis"]:
            status = "pattern_count_hypothesis"
            row["selected_among_display_copies"] = False
        elif local and (local_counts[local["id"], row["name"]] == 1 or row["selected_among_display_copies"]):
            status = (
                "rounded_declaration_and_marker_agree" if rounded and len(possible) == 1
                else "declaration_and_marker_agree"
                if len(possible) == 1
                else "marker_disambiguation_hypothesis"
            )
        elif not possible:
            status = "no_matching_declaration"
        elif len(possible) == 1:
            status = "rounded_declaration_only" if rounded else "declaration_only"
        else:
            status = "ambiguous"
        row["ownership_status"] = status
        counts[status] += 1
        roles[(row["native_trailer"] or {}).get("role", "unparsed")][status] += 1
    return {
        "status": "compared",
        "configuration_id": configs[0].configuration_id,
        "counts": dict(counts),
        "role_counts": {role: dict(group) for role, group in roles.items()},
        "records": rows,
    }


def native_comparisons(root, pin, members):
    from InferenceGrid.SolidWorksDimensionEvidence import capture_sets, dimensions

    comparisons = []
    for _, receipt, report, files in capture_sets(root):
        for name, item in files.items():
            if item["sha256"] != pin:
                continue
            opened = report["observations"].get("reopened_files", {}).get(name, {})
            if opened.get("open_status") != {"errors": 0, "warnings": 0}:
                continue
            observed = defaultdict(list)
            for feature, parameter, value in dimensions(opened):
                observed[feature, parameter].append(value)
            for member, details in members.items():
                for row in details.get("ownership", {}).get("records", []):
                    owner = row["preceding_candidate"]
                    if (row.get("native_trailer") or {}).get("role") == "display":
                        continue
                    if owner is None or row["ownership_status"] not in {
                        "declaration_and_marker_agree",
                        "marker_disambiguation_hypothesis",
                        "rounded_declaration_and_marker_agree",
                    }:
                        continue
                    expected = observed[owner["name"], row["name"]]
                    status = "native_measurement_unavailable"
                    if len(expected) == 1:
                        status = (
                            "native_name_and_value_match"
                            if math.isclose(
                                row["value"], expected[0], rel_tol=1e-12, abs_tol=1e-14
                            )
                            else "native_value_conflict"
                        )
                    comparisons.append(
                        {
                            "member": member,
                            "offset": row["offset"],
                            "feature_id": owner["id"],
                            "feature": owner["name"],
                            "parameter": row["name"],
                            "native_values": expected,
                            "status": status,
                            "measurement_sha256": receipt["measurement_receipt_sha256"],
                        }
                    )
    return comparisons


def changed_owner(before, after):
    rows = before.get("ownership", {}).get("records", [])
    controls = after.get("ownership", {}).get("records", [])
    if not rows or [r["name"] for r in rows] != [r["name"] for r in controls]:
        return {"status": "different_record_layout"}
    changed = [(a, b) for a, b in zip(rows, controls) if a["value"] != b["value"]]
    if len(changed) != 1:
        return {"status": "requires_single_changed_record", "changed_records": len(changed)}
    a, b = changed[0]
    first, second = a.get("count_hypothesis"), b.get("count_hypothesis")
    if first or second:
        if not first or not second or any(first[k] != second[k] for k in ("feature_id", "family", "parameter")):
            return {"status": "inconsistent_pattern_count_evidence"}
        if first["count"] == second["count"]:
            return {"status": "unchanged_declared_count_with_different_record_bytes"}
        formats = sorted(set(first["integer_formats"]) & set(second["integer_formats"]))
        mirrors = {(m["format"], m["offset"] - a["offset"]) for m in first["matching_copies"]} & {
            (m["format"], m["offset"] - b["offset"]) for m in second["matching_copies"]}
        return {"status": "changed_pattern_count_hypothesis", "parameter": a["name"],
                "candidate_feature_ids": [first["feature_id"]], "input_offset": a["offset"],
                "control_offset": b["offset"], "input_value": first["count"], "control_value": second["count"],
                "shared_integer_formats": formats, "shared_copy_displacements": sorted(mirrors)}
    owners = sorted(set(a["candidate_feature_ids"]) & set(b["candidate_feature_ids"]))
    return {
        "status": "single_shared_candidate" if len(owners) == 1 else "unresolved",
        "parameter": a["name"],
        "input_offset": a["offset"],
        "control_offset": b["offset"],
        "input_value": a["value"],
        "control_value": b["value"],
        "candidate_feature_ids": owners,
    }
