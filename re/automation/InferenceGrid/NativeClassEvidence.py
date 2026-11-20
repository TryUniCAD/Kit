# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import hashlib
import json

from InferenceInputs import read_file


def native_classes(native, root):
    schema_path = "re/Fusion/LocalOracle/Reflection/Schema.json"
    raw = read_file(root / schema_path, 4 * 1024 * 1024)
    schema = json.loads(raw)
    metatypes = {}
    for entry in schema["metatypes"]:
        metatypes.setdefault(entry["identifier"].upper(), set()).add(entry["name"])
    classes = {}
    for segment in native["fields"]["Segments"]["tuple"]:
        fields = segment["fields"]
        segment_id = fields["Metadata"]["fields"]["Header"]["fields"]["SegmentId"]
        for record in fields["Records"]["tuple"]:
            entity = record["fields"]
            for group in entity["Groups"]["tuple"]:
                group = group["fields"]
                guid = group["ClassGuid"].upper()
                if guid not in classes:
                    classes[guid] = {"metatypes": sorted(metatypes.get(guid, ())), "fields": set(),
                                     "occurrences": 0, "first_object": [segment_id, entity["ObjectId"]]}
                row = classes[guid]
                row["occurrences"] += 1
                row["fields"].update(item["fields"]["FieldName"] for item in group["Fields"]["tuple"])
    for row in classes.values():
        row["fields"] = sorted(row["fields"])
    return {"reflection": schema_path, "sha256": hashlib.sha256(raw).hexdigest(),
            "build": schema["expected_fusion_build"], "classes": classes}
