# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from bisect import bisect_right
from collections import defaultdict
import struct

from convert.adapters.solidworks.Container.Format import DimensionScalar, KSerializedStringMarker
from convert.adapters.solidworks.Core.Native import ParseClasses, ParseNames


def pattern_counts(data, features):
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
            scalar = cursor + 401
            if scalar + 8 > end or data[scalar-16:scalar] != struct.pack("<4I", 8, 16, 1, 1):
                continue
            value = struct.unpack_from("<d", data, scalar)[0]
            if value.is_integer() and 0 < value < 2**32:
                handles[key].append((record.offset, scalar, int(value)))
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
        handle, mirror, count = copies[0]
        widths = [width for width in (1, 2, 4, 8) if int.from_bytes(data[scalar:scalar+width], "little") == count]
        if scalar + 8 > handle or not widths:
            continue
        results.append({"feature_id": markers[marker][1], "name": name, "pattern": family.lower(),
                        "count": count, "parameter_class_offset": start, "parameter_offset": scalar,
                        "possible_integer_widths": widths, "handle_class_offset": handle, "handle_value_offset": mirror})
    return results
