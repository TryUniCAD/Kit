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

from convert.adapters.solidworks.Core.Native import ParseKeywords, ParseNames
from convert.adapters.solidworks.Core.ParseDisplay import (
    KInformationStream,
    ParseDisplay,
)


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
            elif dim.kind == "length" and scale is not None:
                amount = dim.value_mm * scale
            else:
                continue
            declarations[dim.name].append((feature.object_id, amount))
    if sum(len(declarations[r["name"]]) for r in records) > 2_000_000:
        return {"status": "comparison_limit"}
    markers = []
    if member.endswith("-ResolvedFeatures"):
        for item in ParseNames(archive.Require(member)):
            if item.name == identities.get(item.object_id):
                markers.append((item.offset, item.object_id))
    markers.sort()
    if len({off for off, _ in markers}) != len(markers):
        return {"status": "overlapping_feature_markers"}
    positions = [off for off, _ in markers]
    occurrences = Counter(ident for _, ident in markers)
    rows = []
    local_counts = Counter()
    for record in records:
        label = record["name"]
        possible = [
            ident
            for ident, expected in declarations[label]
            if math.isclose(expected, record["value"], rel_tol=1e-12, abs_tol=1e-14)
        ]
        index = bisect_right(positions, record["offset"]) - 1
        local = None
        if index >= 0:
            start, ident = markers[index]
            if occurrences[ident] == 1 and possible.count(ident) == 1:
                local = {"id": ident, "name": identities[ident], "marker_offset": start}
                local_counts[(ident, label)] += 1
        rows.append(
            {**record, "candidate_feature_ids": possible, "preceding_candidate": local}
        )
    counts = Counter()
    for row in rows:
        possible, local = row["candidate_feature_ids"], row["preceding_candidate"]
        if local and local_counts[local["id"], row["name"]] == 1:
            status = (
                "declaration_and_marker_agree"
                if len(possible) == 1
                else "marker_disambiguation_hypothesis"
            )
        elif not possible:
            status = "no_matching_declaration"
        elif len(possible) == 1:
            status = "declaration_only"
        else:
            status = "ambiguous"
        row["ownership_status"] = status
        counts[status] += 1
    return {
        "status": "compared",
        "configuration_id": configs[0].configuration_id,
        "counts": dict(counts),
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
                    if owner is None or row["ownership_status"] not in {
                        "declaration_and_marker_agree",
                        "marker_disambiguation_hypothesis",
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
