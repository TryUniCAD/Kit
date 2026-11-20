# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import re
from collections import deque

LOCAL = "convert.Formats.Fusion.SegmentCodec.Features.Model.LocalRef.LocalRef"
SEGMENT = "convert.Formats.Fusion.EntityCodec.Model.SegmentRef.SegmentRef"


def references(value, path, segment):
    if isinstance(value, dict):
        kind = value.get("record")
        if kind in (LOCAL, SEGMENT):
            fields = value["fields"]
            yield path, (segment if kind == LOCAL else fields["SegmentId"], fields["ObjectId"])
        else:
            for key, child in value.items():
                yield from references(child, (*path, key), segment)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from references(child, (*path, index), segment)


def trace_refusal(native, message, classes):
    match = re.fullmatch(r"Unknown native Fusion entity class ([A-Fa-f0-9-]{36}) in segment (\d+), object (\d+)", message)
    if not match:
        return None
    guid, segment, obj = match.groups()
    start = (int(segment), int(obj))
    entities, primary = {}, {}
    for item in native["fields"]["Segments"]["tuple"]:
        fields = item["fields"]
        sid = fields["Metadata"]["fields"]["Header"]["fields"]["SegmentId"]
        for record in fields["Records"]["tuple"]:
            entity = record["fields"]
            key = (sid, entity["ObjectId"])
            groups = [group["fields"] for group in entity["Groups"]["tuple"]]
            if entity["IsPrimary"]:
                if key in primary or not groups:
                    raise ValueError("ambiguous primary native entity")
                primary[key] = groups[0]["ClassGuid"].upper()
            entities.setdefault(key, []).extend(groups)
    if primary.get(start) != guid.upper():
        raise ValueError("strict refusal differs from the native record")
    seen = {start}
    pending = deque([start])
    nodes = []
    unresolved = set()
    while pending:
        key = pending.popleft()
        links = []
        for group in entities[key]:
            for field in group["Fields"]["tuple"]:
                attr = field["fields"]
                for path, target in references(attr["Value"], (), key[0]):
                    links.append({"group": group["ClassGuid"].upper(), "field": attr["FieldName"],
                                  "path": path, "target": target})
                    if target not in primary:
                        unresolved.add(target)
                    elif target not in seen:
                        seen.add(target)
                        pending.append(target)
        owner = primary[key]
        nodes.append({"id": key, "class": owner, "metatypes": classes[owner]["metatypes"], "links": links})
    return {"start": start, "class": guid.upper(), "nodes": nodes, "unresolved_targets": sorted(unresolved)}
