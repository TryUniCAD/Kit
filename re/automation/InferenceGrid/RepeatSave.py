# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import hashlib
import json
from pathlib import Path
import subprocess

from InferenceInputs import read_file


def scalars(native):
    values = {}
    repeated = set()
    for segment in native["fields"]["Segments"]["tuple"]:
        fields = segment["fields"]
        sid = fields["Metadata"]["fields"]["Header"]["fields"]["SegmentId"]
        for record in fields["Records"]["tuple"]:
            entity = record["fields"]
            for item in entity["Groups"]["tuple"]:
                group = item["fields"]
                for value in group["Fields"]["tuple"]:
                    field = value["fields"]
                    key = (sid, entity["ObjectId"], group["ClassGuid"].upper(), field["FieldName"])
                    if key in values:
                        repeated.add(key)
                    atom = field["Value"]
                    if type(atom) in (float, int, bool):
                        values[key] = (type(atom), atom)
    return {key: item for key, item in values.items() if key not in repeated}


def compare_capture(native, pin, root, scratch, command, env):
    for path in sorted((root / "re/automation/PairedCaptures").glob("P*/fusion-*/receipt.json")):
        receipt = json.loads(read_file(path, 1024 * 1024))
        rows = receipt["native_files"]
        if pin not in {row["sha256"] for row in rows}:
            continue
        measurement = read_file(path.parent / "measurements.json", 16 * 1024 * 1024)
        if hashlib.sha256(measurement).hexdigest() != receipt["measurement_receipt_sha256"]:
            raise ValueError("repeat-save measurements differ from capture receipt")
        measured = json.loads(measurement)
        if receipt["errors"] or measured["errors"] or rows != measured["saves"]:
            raise ValueError("repeat-save controls lack clean measured saves")
        controls = []
        for phase in ("a", "b"):
            name = f"{receipt['recipe_id']}-fusion-baseline-{phase}.f3d"
            matches = [row for row in rows if row["file"] == name]
            if len(matches) != 1 or Path(name).name != name:
                return None
            controls.append(matches[0])
        if len({pin, *(r["sha256"] for r in controls)}) != 3:
            return None
        values = []
        for index, row in enumerate(controls):
            raw = read_file(path.parent / row["file"], 128 * 1024 * 1024)
            if hashlib.sha256(raw).hexdigest() != row["sha256"] or len(raw) != row["size_bytes"]:
                raise ValueError("repeat-save archive differs from capture receipt")
            source = scratch / f"control-{index}.f3d"
            source.write_bytes(raw)
            output = scratch / f"control-{index}.json"
            result = subprocess.run([*command, str(source), "--layer", "native", "-o", str(output)],
                                    cwd=scratch, env=env, capture_output=True, timeout=180)
            if result.returncode:
                return {"status": "control_decode_failed", "control": row["sha256"], "exit_code": result.returncode}
            values.append(scalars(json.loads(read_file(output, 128 * 1024 * 1024))))
        observed = scalars(native)
        first, repeated = values
        common = first.keys() & repeated.keys() & observed.keys()
        stable = [key for key in sorted(common) if first[key] == repeated[key]]
        candidates = [{"segment": key[0], "object": key[1], "class": key[2], "field": key[3],
                       "control": first[key][1], "input": observed[key][1]}
                      for key in stable if first[key][0] is observed[key][0] and first[key] != observed[key]]
        exports = [row["file"] for row in rows if row["sha256"] == pin]
        reopened = [row["reopened"]["feature_tree"] for key in ("variants", "edits")
                    for row in measured["observations"].get(key, []) if row.get("export") in exports
                    and isinstance(row.get("reopened", {}).get("feature_tree"), list)]
        return {"oracle_timeline": reopened[0] if len(reopened) == 1 else None, "status": "compared", "recipe": receipt["recipe_id"], "measurement_sha256": receipt["measurement_receipt_sha256"],
                "controls": [row["sha256"] for row in controls], "input": pin, "shared_scalar_fields": len(common),
                "repeat_stable": len(stable), "changed_after_repeat_filter": candidates}
    return None
