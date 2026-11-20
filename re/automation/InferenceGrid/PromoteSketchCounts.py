# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import difflib
import json
import os
import shutil
import subprocess
import sys

from convert.adapters.solidworks.Core.Native import KSketchCountOffsets
from InferenceInputs import read_file
from InferenceGrid.SolidWorksPatternCounts import count_matches_parameter


def promote_counts(root, source, scratch, env, document, evidence):
    keywords = evidence.get("keyword_evidence", {})
    rows = keywords.get("pattern_counts", [])
    if not rows or not all(row["keyword_count_matches"] for row in rows):
        return None
    rule = keywords["pattern_count_rule"]
    fmt, offset = rule["candidates"][0]
    if fmt != "<d" or any(KSketchCountOffsets.get(row["pattern"], offset) != offset for row in rows):
        return None
    additions = {row["pattern"]: offset for row in rows if row["pattern"] not in KSketchCountOffsets}
    if not additions:
        return None
    path = "src/convert/adapters/solidworks/Core/Native.py"
    original = (root / path).read_text()
    prefix = "KSketchCountOffsets: dict[str, int] = "
    previous = prefix + json.dumps(KSketchCountOffsets, sort_keys=True) + "\n"
    if original.count(previous) != 1:
        return None
    updated = original.replace(previous, prefix + json.dumps(KSketchCountOffsets | additions, sort_keys=True) + "\n")
    stage = scratch / "pattern-candidate"
    shutil.copytree(root / "src", stage / "src", ignore=shutil.ignore_patterns("__pycache__"))
    (stage / path).write_text(updated)
    output = stage / "decoded.json"
    result = subprocess.run([sys.executable, "-m", "KitCli", "decode", str(source), "--from", "solidworks.sldprt",
                             "-o", str(output)], cwd=stage, env={**env, "PYTHONPATH": os.pathsep.join(map(str, (stage / "src", root / "Cli")))},
                            capture_output=True, timeout=180)
    if result.returncode:
        return None
    replay = json.loads(read_file(output, 128 * 1024 * 1024))["document"]
    if replay["source"] != document["source"] or replay["source"]["sha256"] != rule["held_out_sha256"]:
        return None
    before = document["parameters"]["$tuple"]
    after = replay["parameters"]["$tuple"]
    if [p["id"] for p in before] != [p["id"] for p in after]:
        return None
    targets = {(row["feature_id"], row["name"]): row for row in rows}
    owners = {f["id"]: f["attributes"].get("native_object_id") for f in document["feature_timeline"]["$tuple"]}
    checked = []
    for old, new in zip(before, after):
        key = (owners.get(old["owner_id"]), old["name"])
        if key not in targets:
            if old != new:
                return None
            continue
        row = targets[key]
        if not count_matches_parameter(row, new):
            return None
        checked.append(new["id"])
    if len(set(checked)) != len(rows) or len(checked) != len(rows):
        return None
    patch = "".join(difflib.unified_diff(original.splitlines(True), updated.splitlines(True), "a/" + path, "b/" + path))
    return {"patch": patch, "added": additions, "verified_parameters": checked, "input_sha256": rule["held_out_sha256"],
            "base": subprocess.check_output(["git", "-C", root, "rev-parse", "HEAD"], text=True).strip()}
