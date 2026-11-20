# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections import defaultdict
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from InferenceGrid.FeatureRoutes import DescribeRecipe, FeatureRecipes
from InferenceInputs import read_file
from Records import digest


def file_scope(path, application, scratch, root):
    data = read_file(path, 128 * 1024 * 1024)
    if not data:
        raise ValueError("input is empty")
    pin = hashlib.sha256(data).hexdigest()
    suffix = ".f3d" if application == "fusion" else ".sldprt"
    if application == "solidworks" and path.suffix.casefold() == ".sldasm":
        suffix = ".sldasm"
    source = scratch / ("input" + suffix)
    source.write_bytes(data)
    del data
    env = {**os.environ, "PYTHONPATH": os.pathsep.join(map(str, (root / "src", root / "Cli")))}
    format_id = "fusion.f3d" if application == "fusion" else "solidworks" + suffix
    command = [sys.executable, "-m", "KitCli", "decode", str(source), "--from", format_id]
    attempts = {}
    reports = {}
    for phase, flags in (("container", ["--layer", "container"]), ("strict", []), ("partial", ["--partial"])):
        if phase == "partial" and "strict" in reports:
            break
        target = scratch / (phase + ".json")
        result = subprocess.run([*command, *flags, "-o", str(target)], cwd=scratch, env=env,
                                stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=180)
        if result.returncode:
            if result.returncode != 1:
                raise RuntimeError("reader process exited unexpectedly")
            failure = json.loads(result.stderr)
            attempts[phase] = {"error": failure["error"], "message": str(failure["message"])[:1024]}
        else:
            reports[phase] = json.loads(read_file(target, 128 * 1024 * 1024))
            attempts[phase] = {"status": "decoded"}
    document = reports.get("strict", reports.get("partial", {})).get("document", {})
    if document and document.get("source", {}).get("sha256") != pin:
        raise ValueError("neutral decode refers to a different source")
    features = {}
    unresolved = []
    timeline = document.get("feature_timeline", {}).get("$tuple", [])
    for step in timeline:
        definition = step.get("definition") or {}
        operation = (step.get("operation") or {}).get("value")
        termination = (definition.get("end_condition") or {}).get("value")
        route = None
        if step["kind"]["value"] == "extrusion":
            if operation == "cut" and termination == "through_all":
                route = "family:extrude:cut-extrude"
            elif operation in {"create", "join"} and (definition.get("$type") == "DistanceExtrude" or termination == "blind"):
                route = "api:adsk.fusion.ExtrudeFeature" if application == "fusion" else "family:extrude:boss-base-extrude"
        if route:
            features[route] = {"plan_id": digest([pin, route]), "route": DescribeRecipe(FeatureRecipes[route])}
        else:
            unresolved.append({"id": step["id"], "kind": step["kind"]["value"], "name": step["name"]})
    members = reports.get("container", {}).get("members", [])
    intervals = defaultdict(list)
    pending = [document]
    while pending:
        item = pending.pop()
        if isinstance(item, list):
            pending.extend(item)
        elif isinstance(item, dict):
            if item.get("$type") == "ProvenanceSpan":
                start, size = item.get("offset"), item.get("length")
                if type(start) is int and type(size) is int and start >= 0 and size > 0:
                    intervals[item.get("stream")].append((start, start + size))
            else:
                pending.extend(item.values())
    gaps = []
    for member in members:
        name, size = member["name"], member["size"]
        cursor = 0
        for start, end in sorted(intervals.get(name, ())):
            if end > size:
                continue
            if start > cursor:
                gaps.append([name, cursor, start])
            cursor = max(cursor, end)
        if cursor < size:
            gaps.append([name, cursor, size])
    audit = {"source_sha256": pin, "source_name": path.name, "format": format_id, "reader_attempts": attempts,
             "member_count": len(members), "unattributed_stream_ranges": gaps,
             "features_without_experiment": unresolved, "selected_experiments": sorted(features),
             "diagnostics": document.get("diagnostics", {}).get("$tuple", []),
             "whole_file_verified": False}
    return {application: {"catalogue_sha256": pin, "features": features}}, (audit, reports)
