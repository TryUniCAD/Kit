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

from convert.adapters.solidworks.Core.Native import KFeatureCountCopies, KSketchCountOffsets
from InferenceInputs import read_file
from InferenceGrid.SolidWorksPatternCounts import count_matches_parameter


def promote_counts(root, source, scratch, env, document, evidence, reader_root=None):
    keywords = evidence.get("keyword_evidence", {})
    rows = []
    additions = {}
    path = "src/convert/adapters/solidworks/Core/Native.py"
    reader_root = root if reader_root is None else reader_root
    original = (reader_root / path).read_text()
    updated = original
    sketches = keywords.get("pattern_counts", [])
    if sketches and all(row["keyword_count_matches"] for row in sketches):
        fmt, offset = keywords["pattern_count_rule"]["candidates"][0]
        if fmt == "<d" and all(KSketchCountOffsets.get(row["pattern"], offset) == offset for row in sketches):
            discovered = {row["pattern"]: offset for row in sketches if row["pattern"] not in KSketchCountOffsets}
            prefix = "KSketchCountOffsets: dict[str, int] = "
            previous = prefix + json.dumps(KSketchCountOffsets, sort_keys=True) + "\n"
            if discovered and updated.count(previous) == 1:
                updated = updated.replace(previous, prefix + json.dumps(KSketchCountOffsets | discovered, sort_keys=True) + "\n")
                rows.extend(sketches)
                additions.update(discovered)
    rule = keywords.get("feature_pattern_evidence") or {}
    features = rule.get("counts", [])
    if not KFeatureCountCopies and features and all(row["keyword_count_matches"] for row in features):
        copies = rule["candidates"]
        if len(copies) >= 2 and all(fmt == "<d" for fmt, _ in copies):
            offsets = tuple(offset for _, offset in copies)
            prefix = "KFeatureCountCopies: tuple[int, ...] = "
            if updated.count(prefix + "()\n") == 1:
                updated = updated.replace(prefix + "()\n", prefix + repr(offsets) + "\n")
                rows.extend(features)
                additions["feature_count_copies"] = offsets
    if not rows:
        return None
    stage = scratch / "pattern-candidate"
    shutil.copytree(reader_root / "src", stage / "src", ignore=shutil.ignore_patterns("__pycache__"),
                    copy_function=shutil.copy2 if reader_root == root else os.link)
    (stage / path).unlink()
    (stage / path).write_text(updated)
    output = stage / "decoded.json"
    result = subprocess.run([sys.executable, "-m", "KitCli", "decode", str(source), "--from", "solidworks.sldprt",
                             "-o", str(output)], cwd=stage, env={**env, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": os.pathsep.join(map(str, (stage / "src", root / "Cli")))},
                            capture_output=True, timeout=180)
    if result.returncode:
        if result.returncode == 1 and result.stderr.lstrip().startswith(b"{"):
            error = json.loads(result.stderr)
            if error.get("error") and "message" in error:
                return None
        result.check_returncode()
    replay = json.loads(read_file(output, 128 * 1024 * 1024))["document"]
    if replay["source"] != document["source"] or replay["source"]["sha256"] != evidence["input_sha256"]:
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
    return {"patch": patch, "added": additions, "verified_parameters": checked, "input_sha256": evidence["input_sha256"],
            "base": subprocess.check_output(["git", "-C", root, "rev-parse", "HEAD"], text=True).strip()}
