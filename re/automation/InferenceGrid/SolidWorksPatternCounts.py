# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections import defaultdict
import hashlib
import struct

from InferenceGrid.SolidWorksFieldDiscovery import control_parts
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Native import ParseClasses, ParseKeywords, ParseNames
from convert.adapters.solidworks.Core.PatternPairs import PatternPairs


def learn_count_rule(root, held_out, held_stream):
    seen = {held_out}
    stream_digests = {held_stream}
    samples, candidates = [], None
    for raw in control_parts(root, ()):
        digest = hashlib.sha256(raw).hexdigest()
        if digest in seen:
            continue
        seen.add(digest)
        streams = SldprtArchive.FromBytes(raw).Streams
        configs, features = ParseKeywords(streams["swXmlContents/KeyWords"])
        if len(configs) != 1:
            continue
        data = streams["Contents/Config-" + str(configs[0].configuration_id) + "-ResolvedFeatures"]
        stream_digest = hashlib.sha256(data).hexdigest()
        if stream_digest in stream_digests:
            continue
        stream_digests.add(stream_digest)
        labels = defaultdict(list)
        for feature in features:
            for dim in feature.dimensions:
                labels[feature.object_id, dim.name].append(dim.source_text.strip())
        for owner, name, family, _, scalar, _, cursor, end in PatternPairs(data, features, ParseNames(data), ParseClasses(data)):
            texts = labels[owner, name]
            if len(texts) != 1 or not texts[0].isascii() or not texts[0].isdecimal() or len(texts[0]) > 9:
                continue
            count = int(texts[0])
            if count <= 0 or not any(int.from_bytes(data[scalar:scalar+w], "little") == count for w in (1, 2, 4, 8)):
                continue
            hits = set()
            for fmt in ("<d", ">d", "<f", ">f", "<I", ">I", "<H", ">H", "B"):
                try:
                    word = struct.pack(fmt, count)
                except struct.error:
                    continue
                i = data.find(word, cursor, end)
                while i != -1:
                    hits.add((fmt, i - cursor))
                    i = data.find(word, i + 1, end)
            candidates = hits if candidates is None else candidates & hits
            samples.append({"sha256": digest, "stream_sha256": stream_digest, "file": path.name, "pattern": family, "feature_id": owner,
                            "count": count, "handle_payload_offset": cursor, "candidate_count": len(hits)})
    return {"samples": samples, "candidates": sorted(candidates or []),
            "held_out_sha256": held_out, "held_out_stream_sha256": held_stream}


def pattern_counts(data, features, root, held_out):
    pairs = PatternPairs(data, features, ParseNames(data), ParseClasses(data))
    if not pairs:
        return [], None
    rule = learn_count_rule(root, held_out, hashlib.sha256(data).hexdigest())
    samples = rule["samples"]
    if (len(rule["candidates"]) != 1 or len({s["sha256"] for s in samples}) < 2 or
            len({s["count"] for s in samples}) < 2 or len({s["pattern"] for s in samples}) < 2):
        return [], rule
    fmt, offset = rule["candidates"][0]
    results = []
    for owner, name, family, start, scalar, handle, cursor, end in pairs:
        mirror = cursor + offset
        if (mirror + struct.calcsize(fmt) > end or offset < 16 or
                data[mirror-16:mirror] != struct.pack("<4I", 8, 16, 1, 1)):
            continue
        count = struct.unpack_from(fmt, data, mirror)[0]
        if not 0 < count < 2**32 or int(count) != count:
            continue
        widths = [w for w in (1, 2, 4, 8) if int.from_bytes(data[scalar:scalar+w], "little") == count]
        if widths:
            results.append({"feature_id": owner, "name": name, "pattern": family, "count": int(count),
                            "parameter_class_offset": start, "parameter_offset": scalar,
                            "possible_integer_widths": widths, "handle_class_offset": handle, "handle_value_offset": mirror})
    return results, rule



def count_matches_parameter(record, parameter):
    value = parameter.get("value") or {}
    attrs = parameter.get("attributes", {})
    spans = parameter.get("provenance", {}).get("spans", {}).get("$tuple", [])
    offsets = record["copy_offsets"] if "copy_offsets" in record else [record["handle_value_offset"]]
    kind = "instance_count" if "copy_offsets" in record else "sketch_pattern_count"
    return (value.get("kind", {}).get("value") == "integer" and type(value.get("value")) is int
            and value["value"] == record["count"] and value.get("unit") == ""
            and attrs.get("dimension_kind") == kind and "native_unit" in attrs
            and attrs["native_unit"] is None and attrs.get("native_value") == record["count"]
            and any(s["offset"] in offsets and (s["stream"], s["length"], s["record_kind"]) ==
                    (record["stream"], 8, "dimension-scalar") for s in spans))
