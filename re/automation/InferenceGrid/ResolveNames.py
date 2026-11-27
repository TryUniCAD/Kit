# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

from InferenceInputs import read_file

VOCABULARY = "src/convert/adapters/Fusion/Native/Graph/DesignNames.json"
UNKNOWN = re.compile(r"Unknown native Fusion entity class ([A-Fa-f0-9-]{36}) in segment 0, object (\d+)")


def advance_names(native, original_message, source, root, scratch):
    if not UNKNOWN.fullmatch(original_message):
        return None
    evidence = {}
    for path in ("re/Fusion/LocalOracle/Reflection/Schema.json", "re/Fusion/Reconstruction/BinaryClasses.json"):
        raw = read_file(root / path, 4 * 1024 * 1024)
        evidence[path] = hashlib.sha256(raw).hexdigest()
        if path.endswith("Schema.json"):
            reflected = json.loads(raw)
        else:
            labels = json.loads(raw)
    if reflected["expected_fusion_build"] != labels["applicationVersion"]:
        return None
    segments = [s["fields"] for s in native["fields"]["Segments"]["tuple"]
                if s["fields"]["Metadata"]["fields"]["Header"]["fields"]["SegmentId"] == 0]
    if len(segments) != 1:
        return None
    segment = segments[0]
    original = read_file(root / VOCABULARY, 1024 * 1024).decode()
    names = json.loads(original)
    initial = dict(names)
    staging = scratch / "candidate"
    evidence["base"] = subprocess.check_output(["git", "-C", root, "rev-parse", "HEAD"], text=True).strip()
    message = original_message
    for _ in range(32):
        match = UNKNOWN.fullmatch(message)
        if not match:
            break
        guid, obj = match.groups()
        guid = guid.upper()
        if guid in names:
            break
        entries = [c["fields"] for c in segment["Metadata"]["fields"]["Classes"]["tuple"]
                   if c["fields"]["ClassGuid"].upper() == guid and int(obj) in c["fields"]["OwnerIds"]["tuple"]]
        types = [c for c in reflected["metatypes"] if c["identifier"].upper() == guid and c["category"] == "entity"]
        classes = [c["class"].split("::")[-1] for c in labels["classes"] if c["identifier"].upper() == guid]
        if len(entries) != 1 or len(types) != 1 or len(classes) != 1:
            break
        entry, identity, name = entries[0], types[0], classes[0]
        base = entry["BaseGuid"].upper()
        version = entry["SchemaVersion"]
        if (not entry["ClassSpace"] or entry["ClassSpace"] != identity["addin"] or (identity["base_identifier"] or "").upper() != base
            or identity["version"] != version or identity["name"] != name + "MetaType"
            or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,127}", name)
            or sum(c["class"].split("::")[-1] == name for c in labels["classes"]) != 1):
            break
        schemas = [c["fields"] for c in segment["Profile"]["fields"]["Classes"]["tuple"]
                   if c["fields"]["ClassGuid"].upper() == guid and c["fields"]["SchemaVersion"] == version]
        if len(schemas) != 1 or schemas[0]["IsOpaque"] or schemas[0]["IsValue"] or schemas[0]["BaseGuid"].upper() != base:
            break
        if not staging.exists():
            shutil.copytree(root / "src", staging / "src", ignore=shutil.ignore_patterns("__pycache__"))
        names[guid] = [name, version, base, entry["ClassSpace"]]
        candidate = json.dumps(names, sort_keys=True, indent=2) + "\n"
        (staging / VOCABULARY).write_text(candidate, encoding="utf-8")
        env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": os.pathsep.join(map(str, (staging / "src", root / "Cli")))}
        result = subprocess.run([sys.executable, "-m", "KitCli", "decode", source, "--from", "fusion.f3d", "-o", scratch / "candidate-neutral.json"],
                                cwd=staging, env=env, capture_output=True, timeout=180)
        if result.returncode == 0:
            message = "strict reader returned a document; independent verification required"
            break
        if result.returncode != 1:
            raise RuntimeError("candidate reader failed to execute")
        diagnostic = json.loads(result.stderr)
        if diagnostic.get("error") != "ValueError" or diagnostic.get("message") == message:
            del names[guid]
            break
        message = diagnostic["message"]
    if initial == names:
        return None
    candidate = json.dumps(names, sort_keys=True, indent=2) + "\n"
    (staging / VOCABULARY).write_text(candidate, encoding="utf-8")
    patch = "".join(difflib.unified_diff(original.splitlines(True), candidate.splitlines(True), "a/" + VOCABULARY, "b/" + VOCABULARY))
    return {"evidence": evidence, "added": {g: row for g, row in names.items() if g not in initial},
            "next_result": message, "patch": patch, "whole_file_verified": False}
