# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from bisect import bisect_right
from collections import defaultdict
import hashlib
import struct

from InferenceInputs import read_file
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import DimensionScalar, KSerializedStringMarker
from convert.adapters.solidworks.Core.Native import ParseClasses, ParseKeywords, ParseNames


def pattern_pairs(data, features):
    owners = {f.object_id: f.name for f in features}
    if len(owners) != len(features):
        return []
    markers = sorted((n.offset, n.object_id) for n in ParseNames(data)
                     if n.object_id in owners and owners[n.object_id] == n.name)
    offsets = [offset for offset, _ in markers]
    if len(set(offsets)) != len(offsets):
        return []
    classes = ParseClasses(data)
    parameters, handles = defaultdict(list), defaultdict(list)
    for index, record in enumerate(classes):
        marker = bisect_right(offsets, record.offset) - 1
        if marker < 0:
            continue
        key = (marker, record.name)
        end = offsets[marker + 1] if marker + 1 < len(offsets) else len(data)
        cursor = record.offset + 6 + len(record.name)
        if record.name in ("moSkDimHandleCircularPattCnt_c", "moSkDimHandleLinearPattCnt_c"):
            end = min(end, classes[index + 1].offset if index + 1 < len(classes) else end)
            handles[key].append((record.offset, cursor, min(end, cursor + 1024)))
            continue
        if record.name not in ("sgCircularPattCntDim", "sgLinearPattCntDim") or data[cursor:cursor+4] != bytes(4):
            continue
        cursor += 4
        nested = classes[index + 1] if index + 1 < len(classes) else None
        if nested and nested.offset == cursor and nested.name == "moIntegerParameter_c":
            cursor += 6 + len(nested.name)
        elif cursor + 2 <= end and 0x8000 <= int.from_bytes(data[cursor:cursor+2], "little") < 0xffff:
            cursor += 2
        else:
            continue
        if cursor + 6 > end or not int.from_bytes(data[cursor:cursor+2], "little") & 0x8000:
            continue
        cursor += 2
        if data[cursor:cursor+3] != KSerializedStringMarker:
            continue
        size = data[cursor+3]
        if not 0 < size < 255:
            continue
        text_end = cursor + 4 + 2 * size
        scalar = DimensionScalar(data, text_end, end)
        if scalar is None:
            continue
        try:
            name = data[cursor+4:text_end].decode("utf-16le")
        except UnicodeDecodeError:
            continue
        parameters[key].append((record.offset, name, scalar))
    results = []
    for (marker, kind), items in parameters.items():
        family = "Circular" if kind == "sgCircularPattCntDim" else "Linear"
        copies = handles.get((marker, "moSkDimHandle" + family + "PattCnt_c"), [])
        if len(items) != 1 or len(copies) != 1:
            continue
        start, name, scalar = items[0]
        handle, cursor, end = copies[0]
        if scalar + 8 <= handle:
            results.append((markers[marker][1], name, family.lower(), start, scalar, handle, cursor, end))
    return results


def learn_count_rule(root, held_out, held_stream):
    directory = root / "re/solidworks/examples/Single Turbo Dual Overhead Cam V8 - KDP - 2024"
    controls = ("CARTER", "CULATA_DERECHO", "RODAMIENTO DE BANDA", "SOPORTE DE RODAMIENTO PARA LA BANDA")
    seen = {held_out}
    stream_digests = {held_stream}
    samples, candidates = [], None
    for control in controls:
        path = directory / (control + ".SLDPRT")
        if not path.exists():
            continue
        raw = read_file(path, 16 * 1024 * 1024)
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
        for owner, name, family, _, scalar, _, cursor, end in pattern_pairs(data, features):
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
    pairs = pattern_pairs(data, features)
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
