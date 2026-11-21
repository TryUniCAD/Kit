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
from pathlib import Path
import shutil
import subprocess
import sys

from InferenceInputs import read_file


def repair_state(root, source, scratch, env):
    inspect = [sys.executable, str(Path(__file__).with_name("InspectState.py")), str(source)]
    probe = subprocess.run([*inspect, str(root / "src")], env=env, capture_output=True, timeout=180)
    if probe.returncode:
        return None
    records = json.loads(probe.stdout)
    if not records or len(records) > 64 or len({name for _, name in records}) != len(records):
        return None
    registry = "src/convert/adapters/Fusion/State/Types/BrepTypes.py"
    original = (root / registry).read_text()
    imports = []
    for module, name in records:
        if name in original.splitlines() or f"    {name}," in original.splitlines():
            return None
        line = f"from {module} import {name}"
        imports.append(line if len(line) <= 88 else f"from {module} import (\n    {name},\n)")
    header, marker, entries = original.partition("KBrepTypes: tuple[type[object], ...] = (\n")
    if not marker:
        return None
    candidate = "\n".join(imports) + "\n" + header + marker + "".join(f"    {name},\n" for _, name in records) + entries
    stage = scratch / "state-candidate"
    shutil.copytree(root / "src", stage / "src", ignore=shutil.ignore_patterns("__pycache__"))
    (stage / registry).write_text(candidate)
    candidate_env = {**env, "PYTHONPATH": os.pathsep.join(map(str, (stage / "src", root / "Cli")))}
    replay = subprocess.run(inspect, cwd=stage, env=candidate_env, capture_output=True, timeout=180)
    if replay.returncode:
        return None
    output = stage / "native.json"
    cli = subprocess.run([sys.executable, "-m", "KitCli", "decode", str(source), "--from", "fusion.f3d",
                          "--layer", "native", "-o", str(output)], cwd=stage, env=candidate_env, capture_output=True, timeout=180)
    if cli.returncode:
        return None
    report = json.loads(read_file(output, 128 * 1024 * 1024))
    patch = "".join(difflib.unified_diff(original.splitlines(True), candidate.splitlines(True), "a/" + registry, "b/" + registry))
    return report, {"records": records, "state_round_trip": True, "patch": patch,
                    "base": subprocess.check_output(["git", "-C", root, "rev-parse", "HEAD"], text=True).strip()}
