# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import difflib
import json
from pathlib import Path
import subprocess
import sys

REGISTRY = "re/automation/InferenceGrid/TimelineNames.json"


def infer_names(root, source, scratch, env, components, witnesses):
    if len(components) != 1:
        return None
    features = components[0]["features"]
    evidence = [w for w in witnesses if w["timeline_names"] is not None]
    if not evidence:
        return None
    expected = evidence[0]["timeline_names"]
    if len(features) != len(expected) or any(w["timeline_names"] != expected for w in evidence):
        return None
    original = (root / REGISTRY).read_text()
    registry = json.loads(original)
    candidates = {}
    for feature, measured in zip(features, expected):
        kind = feature["native_class"]
        if kind in registry or feature["name"] == measured:
            continue
        paths = {(v["field"], v["class"]) for v in feature.get("name_candidates", []) if v["name"] == measured}
        candidates[kind] = candidates.get(kind, paths) & paths
    additions = {k: list(next(iter(v))) for k, v in candidates.items() if len(v) == 1}
    if not additions:
        return None
    candidate = "{\n" + ",\n".join("  " + json.dumps(k) + ": " + json.dumps(v)
                                      for k, v in sorted((registry | additions).items())) + "\n}\n"
    path = scratch / "TimelineNames.json"
    path.write_text(candidate)
    replay = subprocess.run([sys.executable, str(Path(__file__).with_name("RecoverTimeline.py")), source, path],
                            cwd=scratch, env=env, capture_output=True, timeout=180)
    if replay.returncode:
        return None
    revised = json.loads(replay.stdout)
    if len(revised) != 1:
        return None
    actual = revised[0]["features"]
    if [f["id"] for f in actual] != [f["id"] for f in features] or any(
        new["name"] != (label if old["native_class"] in additions else old["name"])
        for old, new, label in zip(features, actual, expected)
    ):
        return None
    patch = "".join(difflib.unified_diff(original.splitlines(True), candidate.splitlines(True), "a/" + REGISTRY, "b/" + REGISTRY))
    return revised, {"added": additions, "patch": patch, "capture_sha256": sorted({w["sha256"] for w in evidence}),
                     "base": subprocess.check_output(["git", "-C", root, "rev-parse", "HEAD"], text=True).strip()}
