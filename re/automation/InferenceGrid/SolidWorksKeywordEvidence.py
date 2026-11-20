# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from InferenceGrid.SolidWorksFeatureCounts import feature_counts
from InferenceGrid.SolidWorksPatternCounts import count_matches_parameter, pattern_counts

from bisect import bisect_right
from collections import Counter, defaultdict
import math
import struct

from convert.adapters.solidworks.Core.Native import ParseKeywords, ParseNames
from convert.adapters.solidworks.Core.ParseDisplay import KInformationStream, ParseDisplay


def ownership_hypotheses(rows, features, data, stream):
    by_id = {feature.object_id: feature for feature in features}
    if len(by_id) != len(features):
        return {"status": "duplicate_keyword_ids"}
    markers = [(n.offset, n.object_id) for n in ParseNames(data) if n.object_id in by_id and n.name == by_id[n.object_id].name]
    markers.sort()
    if not markers:
        return {"status": "no_owner_markers"}
    offsets = [m[0] for m in markers]
    if len(offsets) != len(set(offsets)):
        return {"status": "duplicate_marker_offsets"}
    def preceding(location):
        i = bisect_right(offsets, location[1]) - 1
        return markers[i][1] if location[0] == stream and i >= 0 else None
    supports = defaultdict(set)
    failures = defaultdict(set)
    for row in rows:
        if row["status"] != "unique_cross_stream_match" or row["candidate_locations"][0][0] != stream:
            continue
        owner = row["feature_id"]
        group = by_id[owner].kind
        observed = preceding(row["candidate_locations"][0])
        (supports if observed == owner else failures)[group].add(owner)
    counts = Counter()
    proposals = []
    for row in rows:
        if row["status"] != "ambiguous":
            continue
        owner = row["feature_id"]
        group = by_id[owner].kind
        locations = row["candidate_locations"]
        if failures[group] or len(supports[group] - {owner}) < 2:
            counts.update(locations)
            continue
        matches = [location for location in locations if preceding(location) == owner]
        counts.update(matches or locations)
        if len(matches) == 1:
            proposals.append((row, matches[0]))
    for row, location in proposals:
        if counts[location] == 1:
            row["proposed_owner_location"] = location
    return {"status": "compared", "source": stream, "marker_count": len(markers),
            "supporting_owners": {k: sorted(v) for k, v in supports.items() if v},
            "contradicting_owners": {k: sorted(v) for k, v in failures.items() if v},
            "proposed_dimensions": sum(counts[loc] == 1 for _, loc in proposals)}


def keyword_evidence(streams, discovered, document, root, pin):
    data = streams.get("swXmlContents/KeyWords")
    if not data:
        return {"status": "no_keyword_stream"}
    try:
        configs, features = ParseKeywords(data)
    except ValueError as error:
        return {"status": "keyword_refusal", "reason": str(error)[:256]}
    display = ParseDisplay(streams.get(KInformationStream, b""))
    if len(configs) != 1 or not display:
        return {"status": "unresolved_configuration_or_display"}
    base = "Contents/Config-" + str(configs[0].configuration_id)
    owner_ids = {f["id"]: f["attributes"].get("native_object_id") for f in document.get("feature_timeline", {}).get("$tuple", [])}
    projected = {}
    for param in document.get("parameters", {}).get("$tuple", []):
        projected.setdefault((owner_ids.get(param.get("owner_id")), param["name"]), []).append(param)
    rows, uses = [], Counter()
    budget = 2_000_000
    for feature in features:
        for dim in feature.dimensions:
            if dim.value_mm is None or not math.isfinite(dim.value_mm):
                continue
            candidates = discovered.get(dim.name, [])
            budget -= len(candidates) + 1
            if budget < 0:
                return {"status": "comparison_budget_exhausted"}
            if dim.kind == "angle":
                expected, tolerance = math.radians(dim.value_mm), 1e-12
            else:
                unit = {"mm": 0.001, "in": 0.0254}.get(display.UnitName)
                if unit is None:
                    continue
                expected = dim.value_mm * unit
                tolerance = 0.5 * unit * 10 ** -display.Decimals
            matches = [(r["stream"], r["offset"]) for r in candidates
                       if r["stream"] in (base, base + "-ResolvedFeatures") and
                       math.isclose(r["system_value"], expected, rel_tol=1e-12, abs_tol=tolerance)]
            integer_candidates = []
            if not matches and dim.source_text.strip().isascii() and dim.source_text.strip().isdecimal() and 0 < dim.value_mm < 2**32 and dim.value_mm.is_integer():
                for record in candidates:
                    stream, offset = record["stream"], record["offset"]
                    if stream not in (base, base + "-ResolvedFeatures"):
                        continue
                    data = streams[stream]
                    formats = [fmt for fmt in ("<B", "<H", "<I", "<Q", ">H", ">I", ">Q")
                               if struct.unpack_from(fmt, data, offset)[0] == dim.value_mm]
                    if formats:
                        integer_candidates.append({"stream": stream, "offset": offset, "formats": formats})
            uses.update(matches)
            rows.append({"feature_id": feature.object_id, "feature": feature.name, "name": dim.name,
                         "display_text": dim.source_text, "candidate_locations": matches})
            if integer_candidates:
                rows[-1]["integer_encoding_hypotheses"] = integer_candidates
    resolved = base + "-ResolvedFeatures"
    decoded, rule = pattern_counts(streams[resolved], features, root, pin) if resolved in streams else ([], None)
    keyed_rows = defaultdict(list)
    for row in rows:
        keyed_rows[row["feature_id"], row["name"]].append(row)
    keyed_counts = Counter((r["feature_id"], r["name"]) for r in decoded)
    for record in decoded:
        key = record["feature_id"], record["name"]
        matches = keyed_rows[key]
        record["stream"] = resolved
        record["keyword_count_matches"] = len(matches) == 1 and matches[0]["display_text"].strip() == str(record["count"])
        params = projected.get(key, [])
        record["public_reader_matches"] = len(params) == 1 and count_matches_parameter(record, params[0])
        if keyed_counts[key] == 1 and record["keyword_count_matches"]:
            row = matches[0]
            uses.subtract(row["candidate_locations"])
            row["candidate_locations"] = [(resolved, record["handle_value_offset"])]
            row["pattern_count_status"] = "verified_pattern_count" if record["public_reader_matches"] else "pattern_count_reader_mismatch"
            row["reader_span_matches"] = record["public_reader_matches"]
    feature_rule = feature_counts(root, streams[resolved], features, pin) if resolved in streams else None
    for record in (feature_rule or {}).get("counts", []):
        key = record["feature_id"], record["name"]
        matches = keyed_rows[key]
        if len(matches) != 1 or not record["keyword_count_matches"]:
            continue
        row = matches[0]
        uses.subtract(row["candidate_locations"])
        row["candidate_locations"] = [(resolved, offset) for offset in record["copy_offsets"]]
        params = projected.get(key, [])
        record["public_reader_matches"] = False
        if len(params) == 1:
            param = params[0]
            value = param["value"]
            record["public_reader_matches"] = (value["kind"]["value"] == "integer" and type(value["value"]) is int
                and value["value"] == record["count"] and value["unit"] == "" and param["attributes"]["native_unit"] is None
                and any((s["stream"], s["offset"]) in row["candidate_locations"] and s["length"] == 8
                        and s["record_kind"] == "dimension-scalar" for s in param["provenance"]["spans"]["$tuple"]))
        row["pattern_count_status"] = "verified_pattern_count" if record["public_reader_matches"] else "pattern_count_reader_mismatch"
        row["reader_span_matches"] = record["public_reader_matches"]
    counts = Counter()
    for row in rows:
        locations = row["candidate_locations"]
        if "pattern_count_status" in row:
            status = row.pop("pattern_count_status")
        elif not locations:
            status = "no_matching_record"
        elif len(locations) != 1 or uses[locations[0]] != 1:
            status = "ambiguous"
        else:
            status = "unique_cross_stream_match"
            params = projected.get((row["feature_id"], row["name"]), [])
            if len(params) == 1:
                row["reader_span_matches"] = any(
                    (s["stream"], s["offset"]) == locations[0] and s["length"] == 8 and s.get("record_kind") == "dimension-scalar"
                    for s in params[0].get("provenance", {}).get("spans", {}).get("$tuple", []))
        row["status"] = status
        counts[status] += 1
    proposals = ownership_hypotheses(rows, features, streams[resolved], resolved) if resolved in streams else None
    return {"status": "compared", "feature_pattern_evidence": feature_rule, "pattern_count_rule": rule, "pattern_counts": decoded, "ownership_hypotheses": proposals, "configuration_id": configs[0].configuration_id,
            "display_unit": display.UnitName, "counts": counts, "dimensions": rows}
