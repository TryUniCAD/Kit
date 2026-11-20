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
        if not stream.endswith("-ResolvedFeatures"):
            continue
        start = data.find(marker)
        while start != -1:
            end = start + len(marker)
            found.append((stream, end))
            if len(found) > 64:
                return []
            start = data.find(marker, end)
    return found


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


def dimension_evidence(root, source, pin, document):
    sets = capture_sets(root)
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
    result = {"training": samples, "absent_training_names": absent, "held_out_recipes": sorted(held),
              "input_sha256": pin, "candidates": sorted(candidates or [])}
    if (len(candidates or []) != 1 or len({s["recipe"] for s in samples}) < 2 or
        len({s["system_value"] for s in samples}) < 2):
        return {**result, "status": "no_unique_rule"}
    fmt, offset = next(iter(candidates))
    streams = SldprtArchive.FromBytes(source.read_bytes()).Streams
    features = {row["id"]: row["name"] for row in document.get("feature_timeline", {}).get("$tuple", [])}
    for row in document.get("parameters", {}).get("$tuple", []):
        requested.setdefault((features.get(row.get("owner_id")), row["name"]), []).append(row)
    measured = {}
    for owner, name, value in checks:
        measured.setdefault((owner, name), []).append(value)
    predictions = []
    for owner, name in sorted(requested, key=str):
        rows = requested[(owner, name)]
        positions = [(key, end + offset) for key, end in name_records(streams, name)
                     if DimensionScalar(streams[key], end, len(streams[key])) == end + offset]
        prediction = {"name": name, "owner": owner, "candidate_count": len(positions)}
        if len(positions) == len(rows) == 1:
            key, pos = positions[0]
            value = struct.unpack_from(fmt, streams[key], pos)[0]
            if math.isfinite(value):
                spans = rows[0].get("provenance", {}).get("spans", {}).get("$tuple", [])
                prediction.update(stream=key, offset=pos, system_value=value,
                                  reader_span_matches=any((s["stream"], s["offset"], s["length"]) ==
                                                          (key, pos, struct.calcsize(fmt)) for s in spans))
                oracle = measured.get((owner, name), [])
                if len(oracle) == 1:
                    prediction["vendor_value_matches"] = math.isclose(value, oracle[0], rel_tol=1e-12, abs_tol=1e-14)
        predictions.append(prediction)
    verified = bool(checks) and len(predictions) == len(checks) and all(
        row.get("vendor_value_matches") and row.get("reader_span_matches") for row in predictions)
    return {**result, "status": "held_out_dimensions_match" if verified else "partial_evidence",
            "measurement_stage": "edited_before_save" if checks else None, "predictions": predictions,
            "measured_count": len(checks), "missing_from_reader": [list(key) for key in measured if key not in requested]}
