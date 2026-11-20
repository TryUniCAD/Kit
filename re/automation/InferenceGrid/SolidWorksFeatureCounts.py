# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections import Counter
import hashlib
import struct

from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import DimensionScalar, KSerializedStringMarker
from convert.adapters.solidworks.Core.Native import ParseKeywords, ParseNames
from InferenceInputs import read_file


def feature_parameters(data, features):
    owners = {f.object_id: f for f in features}
    if len(owners) != len(features):
        return []
    markers = sorted((r.offset, r.object_id) for r in ParseNames(data)
                     if r.object_id in owners and owners[r.object_id].name == r.name)
    counts = Counter(owner for _, owner in markers)
    rows = []
    for index, (start, owner) in enumerate(markers):
        feature = owners[owner]
        if counts[owner] != 1 or feature.kind.casefold() not in ("cirpattern", "circularpattern", "lpattern", "linearpattern"):
            continue
        end = markers[index + 1][0] if index + 1 < len(markers) else len(data)
        dims = [d for d in feature.dimensions if d.name.casefold() == "d1"]
        if len(dims) != 1:
            continue
        name = dims[0].name.encode("utf-16le")
        tag = KSerializedStringMarker + bytes([len(name) // 2]) + name
        pos = data.find(tag, start, end)
        if pos < start + 2 or data.find(tag, pos + len(tag), end) != -1:
            continue
        token = int.from_bytes(data[pos-2:pos], "little")
        scalar = DimensionScalar(data, pos + len(tag), end)
        if not 0x8000 <= token < 0xffff or scalar is None:
            continue
        rows.append((owner, feature.kind, dims[0], scalar, min(end, scalar + 512)))
    return rows


def feature_counts(root, data, features, held_out):
    targets = feature_parameters(data, features)
    if not targets:
        return None
    folder = root / "re/solidworks/examples/Single Turbo Dual Overhead Cam V8 - KDP - 2024"
    streams_seen = {hashlib.sha256(data).hexdigest()}
    samples, candidates = [], None
    for stem in ("CULATA_DERECHO", "RODAMIENTO DE BANDA", "CARRERA DE EMPUJE", "RUEDA DE TURBINA", "TURBINA"):
        path = folder / (stem + ".SLDPRT")
        if not path.exists():
            continue
        raw = read_file(path, 16 * 1024 * 1024)
        digest = hashlib.sha256(raw).hexdigest()
        if digest == held_out:
            continue
        streams = SldprtArchive.FromBytes(raw).Streams
        configs, control_features = ParseKeywords(streams["swXmlContents/KeyWords"])
        if len(configs) != 1:
            continue
        stream = streams["Contents/Config-" + str(configs[0].configuration_id) + "-ResolvedFeatures"]
        stream_digest = hashlib.sha256(stream).hexdigest()
        if stream_digest in streams_seen:
            continue
        streams_seen.add(stream_digest)
        for owner, kind, dim, scalar, end in feature_parameters(stream, control_features):
            text = dim.source_text.strip()
            if not text.isascii() or not text.isdecimal() or len(text) > 9:
                continue
            count = int(text)
            if not count or not any(int.from_bytes(stream[scalar:scalar+w], "little") == count for w in (1, 2, 4, 8)):
                continue
            hits = set()
            for fmt in ("<d", ">d", "<f", ">f"):
                word = struct.pack(fmt, count)
                pos = stream.find(word, scalar + 8, end)
                while pos != -1:
                    hits.add((fmt, pos - scalar))
                    pos = stream.find(word, pos + 1, end)
            candidates = hits if candidates is None else candidates & hits
            samples.append({"sha256": digest, "stream_sha256": stream_digest, "feature_id": owner, "type": kind,
                            "count": count, "parameter_offset": scalar})
    results = []
    copies = sorted(candidates or [])
    if (len({s["sha256"] for s in samples}) >= 2 and len({s["count"] for s in samples}) >= 2 and len(copies) >= 2
            and len({fmt for fmt, _ in copies}) == 1):
        fmt = copies[0][0]
        size = struct.calcsize(fmt)
        offsets = [offset for _, offset in copies]
        if all(b - a >= size for a, b in zip(offsets, offsets[1:])):
            for owner, kind, dim, scalar, end in targets:
                if scalar + offsets[-1] + size > end:
                    continue
                values = {struct.unpack_from(fmt, data, scalar + off)[0] for off in offsets}
                if len(values) != 1:
                    continue
                count = values.pop()
                if not count.is_integer() or not 0 < count < 2**32:
                    continue
                widths = [w for w in (1, 2, 4, 8) if int.from_bytes(data[scalar:scalar+w], "little") == count]
                if widths:
                    results.append({"feature_id": owner, "type": kind, "name": dim.name, "count": int(count),
                                    "parameter_offset": scalar, "possible_integer_widths": widths,
                                    "copy_offsets": [scalar + off for off in offsets],
                                    "keyword_count_matches": dim.source_text.strip() == str(int(count))})
    return {"samples": samples, "held_out_sha256": held_out, "candidates": copies, "counts": results}
