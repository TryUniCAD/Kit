# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from bisect import bisect_right
from collections import Counter, defaultdict
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import math
import os
import re
import struct
import subprocess

from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.BindMirroredField import MatchesAngle, SelectNamedField
from convert.adapters.solidworks.Core.Native import ParseKeywords, ParseNames, ParseScalars
from convert.adapters.solidworks.Core.ParseDisplay import KInformationStream, ParseDisplay
from InferenceInputs import read_file


def records(streams, wanted):
    xml = streams.get("swXmlContents/KeyWords")
    if not xml:
        return None
    configs, features = ParseKeywords(xml)
    if len(configs) != 1 or not any(f.kind in wanted for f in features):
        return None
    stream = "Contents/Config-" + str(configs[0].configuration_id) + "-ResolvedFeatures"
    data = streams.get(stream)
    if not data:
        return None
    owners = {f.object_id: f for f in features}
    if len(owners) != len(features):
        return None
    names = ParseNames(data)
    markers = sorted((r.offset, r.object_id) for r in names if r.object_id in owners and owners[r.object_id].name == r.name)
    offsets = [offset for offset, _ in markers]
    occurrences = Counter(owner for _, owner in markers)
    scalars = defaultdict(list)
    for s in ParseScalars(data, names):
        i = bisect_right(offsets, s.name_offset) - 1
        if i >= 0:
            scalars[markers[i][1], s.name].append(s)
    display = ParseDisplay(streams.get(KInformationStream, b""))
    rows = []
    for i, (start, owner) in enumerate(markers):
        f = owners[owner]
        if f.kind not in wanted or occurrences[owner] != 1:
            continue
        end = offsets[i+1] if i+1 < len(offsets) else len(data)
        labels = Counter(d.name for d in f.dimensions)
        for d in f.dimensions:
            group = (f.kind, d.name, d.kind)
            if group not in wanted[f.kind] or labels[d.name] != 1 or d.value_mm is None:
                continue
            if d.kind == "angle":
                expected = math.radians(d.value_mm)
            elif display and display.UnitName in ("in", "mm"):
                expected = d.value_mm * (0.0254 if display.UnitName == "in" else 0.001)
            else:
                continue
            scalar = SelectNamedField(scalars[owner, d.name])
            if scalar is not None and scalar.value_offset + 8 <= end:
                rows.append((group, owner, expected, scalar, start, end, d.source_text))
    return stream, data, rows, display


def discover_fields(root, streams, document, pin):
    unresolved = {f["attributes"].get("native_object_id") for f in document.get("feature_timeline", {}).get("$tuple", [])
                  if (f.get("definition") or {}).get("$type") == "NativeFeatureDefinition"}
    xml = streams.get("swXmlContents/KeyWords")
    if not xml:
        return None
    try:
        configs, features = ParseKeywords(xml)
    except ValueError:
        return None
    if len(configs) != 1:
        return None
    known = {f["attributes"].get("native_object_id") for f in document.get("feature_timeline", {}).get("$tuple", [])}
    unresolved.update(f.object_id for f in features if f.object_id not in known)
    wanted = defaultdict(set)
    for f in features:
        wanted[f.kind].update((f.kind, d.name, d.kind) for d in f.dimensions)
    fallback_keys = {(f.kind, d.name, d.kind) for f in features if f.object_id in unresolved for d in f.dimensions}
    target = records(streams, wanted)
    if not target:
        return None
    stream, data, rows, _ = target
    if not rows:
        return {"input_sha256": pin, "input_stream_sha256": hashlib.sha256(data).hexdigest(), "scanned_files": 0,
                "rules": [], "predictions": [], "unresolved_fields": [
                    {"key": key, "reason": "no_unique_named_scalar_in_input", "training_observations": 0}
                    for key in sorted(fallback_keys)]}
    seen = {hashlib.sha256(data).hexdigest()}
    samples = defaultdict(list)
    anchor_samples = defaultdict(list)
    candidates = {}
    folder = "re/solidworks/examples"
    files = subprocess.check_output(["git", "-C", root, "ls-tree", "-rz", "--name-only", "HEAD", "--", folder])
    budget = 64 * 1024 * 1024
    scanned = 0
    for item in files.split(b"\0"):
        if not item.lower().endswith(b".sldprt") or scanned >= 128:
            continue
        p = root / os.fsdecode(item)
        if not p.is_file() or p.stat().st_size > min(4 * 1024 * 1024, budget):
            continue
        raw = read_file(p, min(4 * 1024 * 1024, budget))
        budget -= len(raw)
        scanned += 1
        digest = hashlib.sha256(raw).hexdigest()
        if digest == pin:
            continue
        try:
            sample = records(SldprtArchive.FromBytes(raw).Streams, wanted)
        except ValueError:
            continue
        if not sample:
            continue
        _, blob, training, units = sample
        fingerprint = hashlib.sha256(blob).hexdigest()
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        for key, owner, expected, scalar, start, end, text in training:
            agreement = "exact" if math.isclose(scalar.value, expected, rel_tol=1e-10, abs_tol=1e-14) else "conflict"
            if (agreement == "conflict" and key[2] == "length" and units and units.UnitName == "mm"
                    and type(units.Decimals) is int and 0 <= units.Decimals <= 12 and abs(scalar.value) < 1e9
                    and re.fullmatch(r"[+-]?[0-9]{1,12}(?:[.][0-9]{1,12})?", text.strip())):
                quantum = Decimal(1).scaleb(-units.Decimals)
                measured = Decimal(str(scalar.value)) * 1000
                if measured.quantize(quantum, rounding=ROUND_HALF_UP) == Decimal(text.strip()):
                    agreement = "matches_display_precision"
            anchor_samples[key].append({"file_sha256": digest, "stream_sha256": fingerprint, "feature_id": owner,
                                        "value": scalar.value, "offset": scalar.value_offset, "owner_start": start,
                                        "owner_end": end, "scalar_object_id": scalar.object_id, "expected_value": expected,
                                        "agreement": agreement, "display_text": text})
            if expected == 0 or not math.isclose(scalar.value, expected, rel_tol=1e-10, abs_tol=1e-14):
                continue
            pos = scalar.value_offset
            signature = set()
            for sign in (1, -1):
                word = struct.pack("<d", sign * scalar.value)
                limit = min(end, pos + 2048)
                at = blob.find(word, pos + 8, limit)
                while at != -1:
                    signature.add((at-pos, sign))
                    at = blob.find(word, at+1, limit)
            if key not in candidates:
                candidates[key] = signature
            else:
                candidates[key].intersection_update(signature)
            samples[key].append({"file_sha256": digest, "stream_sha256": fingerprint, "feature_id": owner,
                                 "value": scalar.value, "offset": pos})
    rules, predictions = [], []
    for key, sample_rows in sorted(samples.items()):
        if len({s["file_sha256"] for s in sample_rows}) < 2 or len({s["value"] for s in sample_rows}) < 2:
            continue
        copies = sorted(candidates[key])
        if key not in fallback_keys or not copies or any(b[0]-a[0] < 8 for a,b in zip(copies,copies[1:])):
            continue
        rules.append({"key": key, "copies": copies, "samples": sample_rows})
        for group, owner, expected, scalar, start, end, text in rows:
            if group != key or owner not in unresolved:
                continue
            pos = scalar.value_offset
            if pos+copies[0][0] < start or pos+copies[-1][0]+8 > end:
                continue
            mirrors = [struct.unpack_from("<d", data, pos+off)[0]*sign for off,sign in copies]
            if scalar.value == 0 or any(value != scalar.value for value in mirrors):
                continue
            predictions.append({"key": key, "feature_id": owner, "stream": stream, "scalar_offset": pos,
                                "native_value": scalar.value, "copy_offsets": [pos+off for off,_ in copies],
                                "display_text": text, "keyword_matches": (MatchesAngle(text, math.degrees(expected), math.degrees(scalar.value))
                                if key[2] == "angle" else math.isclose(scalar.value, expected, rel_tol=1e-12, abs_tol=1e-14))})
    anchored = []
    for key, owner, expected, scalar, start, end, text in rows:
        observations = anchor_samples.get(key, [])
        if len({s["stream_sha256"] for s in observations}) < 2 or len({s["value"] for s in observations}) < 2:
            continue
        exact = [s for s in observations if s["agreement"] == "exact"]
        if (any(s["agreement"] == "conflict" for s in observations) or len({s["stream_sha256"] for s in exact}) < 2
                or len({s["value"] for s in exact}) < 2):
            continue
        anchors = {}
        for boundary, offset in (("owner_start", start), ("owner_end", end)):
            differences = {s["offset"] - s[boundary] for s in observations}
            if differences == {scalar.value_offset - offset}:
                anchors[boundary] = scalar.value_offset - offset
        if scalar.object_id is not None and all(s["scalar_object_id"] is not None for s in observations):
            shifts = {s["scalar_object_id"] - s["feature_id"] for s in observations}
            if shifts == {scalar.object_id - owner}:
                anchors["object_id_delta"] = scalar.object_id - owner
        if anchors and scalar.value != 0 and math.isclose(scalar.value, expected, rel_tol=1e-12, abs_tol=1e-14):
            anchored.append({"key": key, "feature_id": owner, "stream": stream, "scalar_offset": scalar.value_offset,
                             "native_value": scalar.value, "anchors": anchors, "display_text": text,
                             "sample_group": list(key)})
    accepted = {r["key"] for r in predictions if r["keyword_matches"]}
    gaps = []
    for key in sorted(fallback_keys - accepted):
        observations = samples.get(key, [])
        if not any(group == key for group, *_ in rows):
            reason = "no_unique_named_scalar_in_input"
        elif len({s["file_sha256"] for s in observations}) < 2:
            reason = "need_another_control_document"
        elif len({s["value"] for s in observations}) < 2:
            reason = "need_a_different_control_value"
        elif not candidates.get(key):
            reason = "no_shared_copy_offset"
        else:
            reason = "no_qualified_held_out_match"
        gaps.append({"key": key, "reason": reason, "training_observations": len(observations)})
    return {"owner_anchor_predictions": anchored, "owner_anchor_controls": [{"key": key, "samples": anchor_samples[key]}
            for key in sorted({r["key"] for r in anchored})], "unresolved_fields": gaps, "input_sha256": pin, "input_stream_sha256": hashlib.sha256(data).hexdigest(), "scanned_files": scanned,
            "rules": rules, "predictions": predictions}


def native_parameter_matches(param, prediction):
    angular = prediction["key"][2] == "angle"
    native = prediction["native_value"]
    value = param["value"]
    span = (prediction["stream"], prediction["scalar_offset"], 8, "dimension-scalar")
    return (value["unit"] == ("deg" if angular else "mm")
            and value["kind"]["value"] == ("angle" if angular else "length")
            and math.isclose(value["value"], math.degrees(native) if angular else native * 1000, rel_tol=1e-12, abs_tol=1e-12)
            and param["attributes"].get("native_value") == native
            and any((s["stream"], s["offset"], s["length"], s["record_kind"]) == span
                    for s in param["provenance"]["spans"]["$tuple"]))
