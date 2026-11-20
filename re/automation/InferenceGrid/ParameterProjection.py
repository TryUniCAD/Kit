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
import re
import subprocess
import sys

from InferenceGrid.ParameterWitness import parameter_witness


def inventory(component):
    rows = component.get("parameters", [])
    if not rows or any("refusal" in row for row in rows):
        return None
    owners = {row["owner"] for row in rows}
    features = [row for row in component["features"] if row["id"] in owners]
    if len(owners) != 1 or len(features) != 1 or not features[0].get("parameter_context"):
        return None
    if any(not isinstance(row.get("role"), str) or not row["role"] for row in rows):
        return None
    roles = {row["role"]: row for row in rows}
    if len(roles) != len(rows) or len({row["name"] for row in rows}) != len(rows):
        return None
    return features[0], roles


def visible_roles(roles, measured):
    if not isinstance(measured, list) or not measured or any(not isinstance(row, dict) for row in measured):
        return None
    names = {m.get("name") for m in measured}
    visible = [row for row in roles.values() if row["name"] in names]
    proof = parameter_witness(visible, measured)
    if not proof["all_names_match"] or any(set(checks) != {"expression", "role", "unit", "value"} or
                                           not all(checks.values()) for checks in proof["fields"].values()):
        return None
    return sorted(row["role"] for row in visible)


def blob(root, ref, limit):
    size = int(subprocess.check_output(["git", "-C", root, "cat-file", "-s", ref]))
    if size > limit:
        return None
    return subprocess.check_output(["git", "-C", root, "cat-file", "blob", ref])


def fit_projection(root, scratch, env, component, witnesses, pin):
    target = inventory(component)
    if not target:
        return None
    feature, roles = target
    observed = [w["parameters"] for w in witnesses if w["parameters"] is not None]
    if not observed or all(len(rows) == len(roles) for rows in observed):
        return None
    family = feature["native_class"].removeprefix("Dc").removesuffix("Feature")
    index = subprocess.check_output(["git", "-C", root, "ls-tree", "-r", "--name-only", "HEAD", "--",
                                     "re/Fusion/LocalOracle/FeatureAuthoring/Controls"], text=True).splitlines()
    paths = set(index)
    seen = {pin}
    trained = []
    source = scratch / "projection-control.f3d"
    for path in sorted(paths):
        if not re.fullmatch(r"Capture[A-Za-z]*\.json", Path(path).name):
            continue
        raw = blob(root, "HEAD:" + path, 16 * 1024 * 1024)
        report = json.loads(raw) if raw else {}
        if report.get("status") != "captured":
            continue
        for case in report.get("controls", []):
            name = case.get("file", "")
            if not isinstance(name, str) or not name.startswith(family) or not re.fullmatch(r"[A-Za-z0-9_-]+\.f3d", name):
                continue
            member = str(Path(path).with_name(name))
            checksum = case.get("sha256")
            if member not in paths or checksum in seen or case.get("status") != "captured":
                continue
            if len(seen) >= 9:
                return {"status": "control_budget_exhausted", "training": trained}
            seen.add(checksum)
            data = blob(root, "HEAD:" + member, 32 * 1024 * 1024)
            if not data or len(data) != case.get("bytes") or hashlib.sha256(data).hexdigest() != checksum:
                continue
            source.write_bytes(data)
            replay = subprocess.run([sys.executable, str(Path(__file__).with_name("RecoverTimeline.py")), source],
                                    cwd=scratch, env=env, capture_output=True, timeout=180)
            if replay.returncode:
                continue
            components = json.loads(replay.stdout)
            sample = inventory(components[0]) if len(components) == 1 else None
            if not sample or sample[0]["parameter_context"] != feature["parameter_context"] or sample[1].keys() != roles.keys():
                continue
            visible = visible_roles(sample[1], case.get("observed", {}).get("parameters"))
            if visible is None:
                return {"status": "unverified_control", "source_sha256": checksum, "training": trained}
            trained.append({"source_sha256": checksum, "capture": path, "roles": visible})
    result = {"training": trained, "held_out_sha256": pin, "context": feature["parameter_context"]}
    if len(trained) < 2:
        return {**result, "status": "needs_independent_controls"}
    prediction = trained[0]["roles"]
    if any(row["roles"] != prediction for row in trained):
        return {**result, "status": "conflicting_training_controls"}
    matched = all(visible_roles(roles, measured) == prediction for measured in observed)
    return {**result, "status": "held_out_match" if matched else "held_out_refutation",
            "predicted_visible_roles": prediction, "other_saved_roles": sorted(roles.keys() - set(prediction))}
