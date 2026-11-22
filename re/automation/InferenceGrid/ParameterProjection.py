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


def listed_cases(root, family, revision):
    base = "re/Fusion/LocalOracle/FeatureAuthoring/Controls"
    index = subprocess.check_output(["git", "-C", root, "ls-tree", "-r", "--name-only", revision, "--", base],
                                    text=True).splitlines()
    for path in index:
        if not re.fullmatch(r"Capture[A-Za-z]*\.json", Path(path).name):
            continue
        raw = blob(root, revision + ":" + path, 16 * 1024 * 1024)
        report = json.loads(raw) if raw else {}
        if report.get("status") != "captured":
            continue
        for case in report.get("controls", []):
            name = case.get("file", "")
            if isinstance(name, str) and name.startswith(family) and re.fullmatch(r"[A-Za-z0-9_-]+\.f3d", name):
                member = str(Path(path).with_name(name))
                if member in index and case.get("status") == "captured":
                    yield path, member, case.get("sha256"), case.get("bytes"), case.get("observed", {}).get("parameters")
    kind = "adsk::fusion::" + family + "Feature"
    matches = subprocess.run(["git", "-C", root, "grep", "-l", "-F", "-e", kind, revision, "--",
                              "re/Fusion/Study/*/ground_truth.json"], text=True, capture_output=True, timeout=60)
    if matches.returncode not in (0, 1):
        matches.check_returncode()
    for ref in matches.stdout.splitlines():
        path = ref.split(":", 1)[1]
        raw = blob(root, ref, 16 * 1024 * 1024)
        report = json.loads(raw) if raw else {}
        if str(report.get("terminal_status")).lower() != "complete" or report.get("errors") != []:
            continue
        for case in report.get("samples", []):
            feature = case.get("feature_at_timeline_end") or {}
            export = case.get("export") or {}
            rows = case.get("model_parameters_after")
            name = case.get("file")
            if (case.get("phase") != "export_complete" or case.get("getter_errors") != [] or
                export.get("returned_success") is not True or feature.get("isValid") is not True or
                feature.get("healthState") != 0 or feature.get("objectType") != kind or not isinstance(rows, list) or
                not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9_-]+\.f3d", name)):
                continue
            if all(isinstance(r, dict) and r.get("isValid") is True and r.get("getter_errors") == [] and
                   (r.get("createdBy") or {}).get("objectType") == kind for r in rows):
                yield path, str(Path(path).with_name(name)), export.get("sha256"), export.get("size_bytes"), rows


def fit_projection(root, scratch, env, component, witnesses, pin):
    target = inventory(component)
    if not target:
        return None
    feature, roles = target
    observed = [w["parameters"] for w in witnesses if w["parameters"] is not None]
    if observed and all(len(rows) == len(roles) for rows in observed):
        return None
    family = feature["native_class"].removeprefix("Dc").removesuffix("Feature")
    revision = subprocess.check_output(["git", "-C", root, "rev-parse", "HEAD"], text=True).strip()
    seen = {pin}
    trained = []
    rejected = []
    source = scratch / "projection-control.f3d"
    for path, member, checksum, size, measurements in listed_cases(root, family, revision):
        if not isinstance(checksum, str) or not re.fullmatch("[a-f0-9]{64}", checksum) or type(size) is not int:
            continue
        if checksum in seen and checksum != pin:
            continue
        if len(seen) >= 9 and checksum != pin:
            return {"status": "control_budget_exhausted", "training": trained}
        try:
            data = blob(root, revision + ":" + member, 32 * 1024 * 1024)
        except subprocess.CalledProcessError:
            continue
        if not data or len(data) != size or hashlib.sha256(data).hexdigest() != checksum:
            rejected.append({"capture": path, "member": member, "reason": "export size or sha256 mismatch"})
            continue
        if checksum == pin:
            if measurements not in observed:
                observed.append(measurements)
            continue
        seen.add(checksum)
        source.write_bytes(data)
        replay = subprocess.run([sys.executable, str(Path(__file__).with_name("RecoverTimeline.py")), source],
                                cwd=scratch, env=env, capture_output=True, timeout=180)
        if replay.returncode:
            continue
        components = json.loads(replay.stdout)
        sample = inventory(components[0]) if len(components) == 1 else None
        if not sample or sample[0]["parameter_context"] != feature["parameter_context"] or sample[1].keys() != roles.keys():
            continue
        visible = visible_roles(sample[1], measurements)
        if visible is None:
            return {"status": "unverified_control", "source_sha256": checksum, "training": trained}
        trained.append({"source_sha256": checksum, "capture": path, "roles": visible})
    result = {"training": trained, "held_out_sha256": pin, "context": feature["parameter_context"], "rejected": rejected, "revision": revision}
    if len(trained) < 2:
        return {**result, "status": "needs_independent_controls"}
    prediction = trained[0]["roles"]
    if any(row["roles"] != prediction for row in trained):
        return {**result, "status": "conflicting_training_controls"}
    matched = bool(observed) and all(visible_roles(roles, measured) == prediction for measured in observed)
    return {**result, "status": "held_out_match" if matched else "held_out_refutation" if observed else "prediction_without_input_measurement",
            "predicted_visible_roles": prediction, "other_saved_roles": sorted(roles.keys() - set(prediction))}
