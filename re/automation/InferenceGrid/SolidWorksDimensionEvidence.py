# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import hashlib
import json
import math
import re
from pathlib import Path
import struct

from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import DimensionScalar, KSerializedStringMarker
from InferenceInputs import read_file


def capture_sets(root):
    sets = []
    for path in sorted((root / "re/automation/PairedCaptures").glob("P*/solidworks-*/receipt.json")):
        receipt = json.loads(read_file(path, 1024 * 1024))
        raw = read_file(path.parent / "measurements.json", 16 * 1024 * 1024)
        if hashlib.sha256(raw).hexdigest() != receipt["measurement_receipt_sha256"]:
            continue
        report = json.loads(raw)
        if receipt["errors"] or report["errors"] or receipt["native_files"] != report["saves"]:
            continue
        files = {row["file"]: row for row in receipt["native_files"] if not row["save_errors"] and not row["save_warnings"]}
        sets.append((path.parent, receipt, report, files))
    return sets


def name_records(streams, name):
    raw = name.encode("utf-16le")
    if not raw or len(raw) > 508:
        return []
    marker = KSerializedStringMarker + bytes([len(raw) // 2]) + raw
    found = []
    for stream, data in streams.items():
        if not re.fullmatch(r"Contents/Config-[0-9]+(?:-ResolvedFeatures)?", stream):
            continue
        start = data.find(marker)
        while start != -1:
            end = start + len(marker)
            found.append((stream, end))
            if len(found) > 64:
                return []
            start = data.find(marker, end)
    return found


def observed_records(streams, fmt, displacement):
    records = {}
    count = 0
    for stream, data in streams.items():
        if not re.fullmatch(r"Contents/Config-[0-9]+(?:-ResolvedFeatures)?", stream):
            continue
        start = 0
        while (start := data.find(KSerializedStringMarker, start)) != -1:
            start += len(KSerializedStringMarker)
            if start >= len(data):
                break
            length = data[start]
            end = start + 1 + 2 * length
            if length in (0, 255) or end > len(data) or DimensionScalar(data, end, len(data)) != end + displacement:
                continue
            try:
                name = data[start + 1:end].decode("utf-16le")
            except UnicodeDecodeError:
                continue
            if not name or not name.isprintable():
                continue
            pos = end + displacement
            value = struct.unpack_from(fmt, data, pos)[0]
            if math.isfinite(value):
                if count >= 16384:
                    return records, True
                count += 1
                records.setdefault(name, []).append({"stream": stream, "offset": pos, "system_value": value})
    return records, False


def dimensions(observation):
    return [(feature["name"], dim["name"], dim["system_value"]) for feature in observation.get("feature_tree", [])
            for dim in feature.get("dimensions", []) if isinstance(dim.get("name"), str) and
            type(dim.get("system_value")) in (int, float) and math.isfinite(dim["system_value"])]


def encoding_hits(data, end, value):
    hits = set()
    for fmt in ("<d", ">d", "<f", ">f"):
        try:
            word = struct.pack(fmt, value)
        except OverflowError:
            continue
        for offset in range(97):
            if data.startswith(word, end + offset):
                hits.add((fmt, offset))
    return hits


def dimension_evidence(root, source, pin, document, controls=()):
    from InferenceGrid.SolidWorksFieldDiscovery import discovery_inventory, discover_fields
    sets = capture_sets(root)
    eligible = discovery_inventory(root, sets)
    held = {receipt["recipe_id"] for _, receipt, _, files in sets if any(row["sha256"] == pin for row in files.values())}
    samples, absent, checks, requested = [], [], [], {}
    candidates = None
    for folder, receipt, report, files in sets:
        family = receipt["recipe_id"]
        for edit in report["observations"]["edits"]:
            file = edit["saved_file"]
            row = files.get(file)
            if not row or Path(file).name != file:
                continue
            if family in held:
                if row["sha256"] == pin and row["size_bytes"] == source.stat().st_size:
                    checks = dimensions(edit["edited"])
                continue
            if row["sha256"] not in eligible:
                continue
            raw = read_file(folder / file, 128 * 1024 * 1024)
            if len(raw) != row["size_bytes"] or hashlib.sha256(raw).hexdigest() != row["sha256"]:
                continue
            measured = [d for d in dimensions(edit["edited"]) if d[1] == edit["parameter"]]
            if len(measured) != 1:
                continue
            _, name, value = measured[0]
            streams = SldprtArchive.FromBytes(raw).Streams
            anchors = name_records(streams, name)
            sample = {"recipe": family, "name": name, "system_value": value, "sha256": row["sha256"]}
            if not anchors:
                absent.append(sample)
                continue
            hits = set().union(*(encoding_hits(streams[key], end, value) for key, end in anchors))
            candidates = hits if candidates is None else candidates & hits
            samples.append(sample)
    result = {"discovery_control_count": len(eligible), "input_eligible_for_discovery": pin in eligible,
              "supplied_controls": [{"sha256": path.stem, "eligible_for_discovery": path.stem in eligible} for path in controls],
              "training": samples, "absent_training_names": absent, "held_out_recipes": sorted(held),
              "input_sha256": pin, "candidates": sorted(candidates or [])}
    from InferenceGrid.SolidWorksEquationEvidence import equation_evidence
    streams = SldprtArchive.FromBytes(source.read_bytes()).Streams
    result["discovered_feature_fields"] = discover_fields(root, streams, document, pin, controls, pin in eligible)
    comparisons = (result["discovered_feature_fields"] or {}).get("single_dimension_comparisons", [])
    if comparisons:
        names = {f["attributes"].get("native_object_id"): f["name"] for f in document.get("feature_timeline", {}).get("$tuple", [])}
        witnesses = {}
        for _, receipt, report, files in sets:
            reopened = report["observations"].get("reopened_files", {})
            for filename, row in files.items():
                observation = reopened.get(filename, {})
                if observation.get("open_status") == {"errors": 0, "warnings": 0}:
                    witnesses[row["sha256"]] = (receipt["measurement_receipt_sha256"], dimensions(observation))
        for paired in comparisons:
            for side, digest in (("input", pin), ("control", paired["control_sha256"])):
                if digest not in witnesses:
                    continue
                receipt_sha, values = witnesses[digest]
                matching = [v for f, n, v in values if (f, n) == (names.get(paired["feature_id"]), paired["key"][1])]
                if len(matching) == 1:
                    paired[side + "_reopen"] = {"value": matching[0], "measurement_sha256": receipt_sha,
                                                "matches": math.isclose(matching[0], paired[side + "_value"], rel_tol=1e-12, abs_tol=1e-14)}
    if (len(candidates or []) != 1 or len({s["recipe"] for s in samples}) < 2 or
        len({s["system_value"] for s in samples}) < 2):
        return {**result, "equations": equation_evidence(streams, [], sets, pin, eligible), "status": "no_unique_rule"}
    fmt, offset = next(iter(candidates))
    discovered, truncated = observed_records(streams, fmt, offset)
    if truncated:
        return {**result, "equations": equation_evidence(streams, [], sets, pin, eligible), "status": "dimension_record_limit", "record_limit": 16384}
    features = {row["id"]: row["name"] for row in document.get("feature_timeline", {}).get("$tuple", [])}
    for row in document.get("parameters", {}).get("$tuple", []):
        requested.setdefault((features.get(row.get("owner_id")), row["name"]), []).append(row)
    measured = {}
    for owner, name, value in checks:
        measured.setdefault((owner, name), []).append(value)
    predictions = []
    for owner, name in sorted(requested, key=str):
        rows = requested[(owner, name)]
        matches = discovered.get(name, [])
        prediction = {"name": name, "owner": owner, "candidate_count": len(matches)}
        if len(matches) == len(rows) == 1:
            match = matches[0]
            spans = rows[0].get("provenance", {}).get("spans", {}).get("$tuple", [])
            prediction.update(match, reader_span_matches=any((s["stream"], s["offset"], s["length"]) ==
                                                             (match["stream"], match["offset"], struct.calcsize(fmt)) for s in spans))
            neutral = rows[0].get("value") or {}
            source_unit = rows[0].get("attributes", {}).get("native_unit")
            prediction["system_unit"] = source_unit
            scale = {("m", "mm"): 1000.0, ("rad", "deg"): 180 / math.pi, ("m", "m"): 1.0,
                     ("rad", "rad"): 1.0}.get((source_unit, neutral.get("unit")))
            amount = neutral.get("value")
            prediction["neutral_value_matches"] = scale is not None and type(amount) in (int, float) and math.isclose(
                match["system_value"] * scale, amount, rel_tol=1e-12, abs_tol=1e-12)
            oracle = measured.get((owner, name), [])
            if len(oracle) == 1:
                prediction["vendor_value_matches"] = math.isclose(match["system_value"], oracle[0], rel_tol=1e-12, abs_tol=1e-14)
        predictions.append(prediction)
    verified = bool(checks) and len(predictions) == len(checks) and all(
        row.get("vendor_value_matches") and row.get("reader_span_matches") and row.get("neutral_value_matches") for row in predictions)
    equations = equation_evidence(streams, predictions, sets, pin, eligible)
    from InferenceGrid.SolidWorksKeywordEvidence import keyword_evidence
    keywords = keyword_evidence(streams, discovered, document, root, pin, result["discovered_feature_fields"], controls)
    remaining = {(row["feature_id"], row["name"]): row for row in keywords.get("dimensions", [])
                 if row["status"] in {"ambiguous", "no_matching_record"}}
    requests = []
    for gap in (result["discovered_feature_fields"] or {}).get("unresolved_fields", []):
        for target in gap.get("variation_targets", []):
            row = remaining.get((target["feature_id"], target["field"]))
            if row:
                requests.append({**target, "feature": row["feature"], "key": gap["key"],
                                 "input_sha256": pin, "edit": "vary_one_declared_dimension",
                                 "baseline_display": row["display_text"]})
    result["next_control_edits"] = requests
    return {**result, "keyword_evidence": keywords, "equations": equations, "status": ("same_family_dimensions_match" if pin in eligible else "held_out_dimensions_match") if verified else "partial_evidence",
            "measurement_stage": "edited_before_save" if checks else None, "predictions": predictions,
            "discovered_dimension_records": discovered, "measured_count": len(checks), "missing_from_reader": [list(key) for key in measured if key not in requested]}
