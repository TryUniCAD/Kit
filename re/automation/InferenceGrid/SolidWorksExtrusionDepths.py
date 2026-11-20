# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections import Counter, defaultdict
import hashlib
import math
import struct

from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Native import ParseKeywords, ParseNames, ParseScalars
from convert.adapters.solidworks.Core.ParseDisplay import KInformationStream, ParseDisplay
from InferenceGrid.SolidWorksFieldDiscovery import control_parts


def extrusion_records(data, features):
    names = ParseNames(data)
    owners = {f.object_id: f for f in features}
    if len(owners) != len(features):
        return [], []
    markers = sorted((n.offset, n.object_id) for n in names if n.object_id in owners and owners[n.object_id].name == n.name)
    occurrences = Counter(owner for _, owner in markers)
    intervals = [(owners[owner], start, markers[i+1][0] if i+1 < len(markers) else len(data))
                 for i, (start, owner) in enumerate(markers)
                 if owners[owner].kind == "Extrusion" and occurrences[owner] == 1]
    return intervals, ParseScalars(data, names)


def extrusion_depths(root, data, features, pin, dimensions, projected, stream, controls=()):
    candidates = {(r["feature_id"], r["name"]): r for r in dimensions
                  if r["status"] in {"ambiguous", "unique_cross_stream_match"}}
    if not any(f.kind == "Extrusion" for f in features):
        return None
    seen = {hashlib.sha256(data).hexdigest()}
    groups = defaultdict(list)
    for raw in control_parts(root, controls):
        digest = hashlib.sha256(raw).hexdigest()
        if digest == pin:
            continue
        try:
            streams = SldprtArchive.FromBytes(raw).Streams
            configs, fs = ParseKeywords(streams.get("swXmlContents/KeyWords", b""))
        except ValueError:
            continue
        display = ParseDisplay(streams.get(KInformationStream, b""))
        if len(configs) != 1 or not display or display.UnitName != "mm":
            continue
        control = streams.get("Contents/Config-" + str(configs[0].configuration_id) + "-ResolvedFeatures")
        if not control:
            continue
        fingerprint = hashlib.sha256(control).hexdigest()
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        intervals, scalars = extrusion_records(control, fs)
        by_name = defaultdict(list)
        for scalar in scalars:
            by_name[scalar.name].append(scalar)
        for f, start, end in intervals:
            if len(f.dimensions) != 1:
                continue
            d = f.dimensions[0]
            if d.kind != "length" or d.value_mm is None or d.value_mm <= 0:
                continue
            matches = [s for s in by_name[d.name] if math.isclose(s.value, d.value_mm * 0.001, rel_tol=1e-12)]
            if len(matches) != 1:
                continue
            s = matches[0]
            if not (start <= s.value_offset < end and 16 <= end - s.value_offset <= 2048):
                continue
            mirrors = set()
            for sign in (1, -1):
                word = struct.pack("<d", sign*s.value)
                pos = control.find(word, s.value_offset + 8, end)
                while pos != -1:
                    mirrors.add((pos - s.value_offset, sign))
                    pos = control.find(word, pos + 1, end)
            groups[end == len(control), end-s.value_offset].append({"file_sha256": digest, "stream_sha256": fingerprint, "feature_id": f.object_id,
                                               "value_m": s.value, "mirrors": sorted(mirrors)})
    rules = []
    for (terminal, distance), samples in sorted(groups.items()):
        if len({s["file_sha256"] for s in samples}) < 2 or len({s["value_m"] for s in samples}) < 2:
            continue
        offsets = sorted(set.intersection(*(set(s["mirrors"]) for s in samples)))
        if offsets:
            rules.append({"boundary": "stream_end" if terminal else "next_feature", "bytes_before_boundary": distance, "mirror_offsets": offsets, "samples": samples})
    intervals, scalars = extrusion_records(data, features)
    by_offset = {s.value_offset: s for s in scalars}
    results = []
    for f, start, end in intervals:
        if len(f.dimensions) != 1:
            continue
        dim = f.dimensions[0]
        row = candidates.get((f.object_id, dim.name))
        if not row or dim.kind != "length":
            continue
        predictions = []
        for rule in rules:
            if (rule["boundary"] == "stream_end") != (end == len(data)):
                continue
            pos = end - rule["bytes_before_boundary"]
            s = by_offset.get(pos)
            if pos < start or s is None or s.name != dim.name or s.value <= 0:
                continue
            mirrors = [pos + off for off, _ in rule["mirror_offsets"]]
            if all(m + 8 <= end and struct.unpack_from("<d", data, m)[0] == sign * s.value
                   for m, (_, sign) in zip(mirrors, rule["mirror_offsets"])):
                predictions.append((pos, s.value, mirrors))
        if len(predictions) != 1:
            continue
        pos, value, mirrors = predictions[0]
        if (stream, pos) not in row["candidate_locations"]:
            continue
        params = projected.get((f.object_id, dim.name), [])
        matches = len(params) == 1 and any((s["stream"], s["offset"], s["length"], s["record_kind"]) ==
                 (stream, pos, 8, "dimension-scalar") for s in params[0]["provenance"]["spans"]["$tuple"])
        results.append({"feature_id": f.object_id, "name": dim.name, "stream": stream, "offset": pos, "value_m": value,
                        "mirror_offsets": mirrors, "reader_span_matches": matches})
    return {"held_out_sha256": pin, "rules": rules, "predictions": results}
