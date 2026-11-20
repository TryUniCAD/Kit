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


def file_scope(path, application, scratch, root, control_paths=()):
    data = read_file(path, 128 * 1024 * 1024)
    if not data:
        raise ValueError("input is empty")
    pin = hashlib.sha256(data).hexdigest()
    suffix = ".f3d" if application == "fusion" else ".sldprt"
    if application == "solidworks" and path.suffix.casefold() == ".sldasm":
        suffix = ".sldasm"
    if application == "auto":
        from InferenceGrid.IdentifyFile import identify_file, raw_scope
        application, suffix = identify_file(data)
        if control_paths and suffix != ".sldprt" and application != "unknown":
            raise ValueError("--control requires a SOLIDWORKS part")
        if application in {"asm", "unknown"}:
            return raw_scope(data, path, pin, application, root, scratch, control_paths)
    source = scratch / ("input" + suffix)
    source.write_bytes(data)
    package = None
    if application == "freecad":
        from InferenceGrid.IdentifyFile import inspect_zip
        package = inspect_zip(data)
    del data
    env = {**os.environ, "PYTHONPATH": os.pathsep.join(map(str, (root / "src", root / "Cli")))}
    format_id = {"fusion": "fusion.f3d", "freecad": "freecad.fcstd"}.get(application, "solidworks" + suffix)
    controls = []
    if control_paths:
        from InferenceGrid.SolidWorksFieldDiscovery import snapshot_controls
        controls = snapshot_controls(source, control_paths, scratch)
    command = [sys.executable, "-m", "KitCli", "decode", str(source), "--from", format_id]
    attempts = {}
    reports = {}
    for phase, flags in (("container", ["--layer", "container"]), ("strict", []), ("partial", ["--partial"]), ("native", ["--layer", "native"])):
        if phase == "container" and application == "freecad":
            continue
        if phase == "partial" and "strict" in reports:
            continue
        if phase == "native" and application != "fusion":
            continue
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
    if attempts.get("native", {}).get("message") == "Unsupported Fusion semantic-state value":
        from InferenceGrid.RepairState import repair_state
        repaired = repair_state(root, source, scratch, env)
        if repaired:
            reports["native"], reports["state-repair"] = repaired
    document = reports.get("strict", reports.get("partial", {})).get("document", {})
    if document and document.get("source", {}).get("sha256") != pin:
        raise ValueError("neutral decode refers to a different source")
    features = {}
    unresolved = []
    timeline = document.get("feature_timeline", {}).get("$tuple", [])
    from InferenceGrid.RectangleScope import driving_rectangles
    rectangles = driving_rectangles(document)
    for step in timeline:
        definition = step.get("definition") or {}
        operation = step.get("operation")
        if isinstance(operation, dict):
            operation = operation.get("value")
        kind = step["kind"]
        if isinstance(kind, dict):
            kind = kind["value"]
        termination = definition.get("end_condition")
        if isinstance(termination, dict):
            termination = termination.get("value")
        route = None
        if kind == "extrusion":
            if operation == "cut" and termination == "through_all":
                route = "family:extrude:cut-extrude"
            elif operation in {"create", "join"} and (definition.get("$type") == "DistanceExtrude" or termination == "blind"):
                route = "api:adsk.fusion.ExtrudeFeature" if application == "fusion" else "family:extrude:boss-base-extrude"
        if step.get("sketch_id") in rectangles and kind in ("reference", "sketch"):
            route = "family:sketchdimensions:driving-dimension"
        if route and application in {"fusion", "solidworks"}:
            features[route] = {"plan_id": digest([pin, route]), "route": DescribeRecipe(FeatureRecipes[route])}
        else:
            unresolved.append({"id": step["id"], "kind": kind, "name": step["name"]})
    members = reports.get("container", {}).get("members", [])
    if package:
        reports["raw-structure"] = {"status": "inspected_zip", "package": package}
        members = [{"name": name, "size": row["size"]} for name, row in package.get("members", {}).items()]
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
             "rectangle_driving_parameters": rectangles, "member_count": len(members), "unattributed_stream_ranges": gaps,
             "features_without_experiment": unresolved, "selected_experiments": sorted(features),
             "diagnostics": document.get("diagnostics", {}).get("$tuple", []),
             "whole_file_verified": False}
    if application == "freecad":
        message = attempts.get("strict", {}).get("message", "")
        if not document and message.startswith("FreeCAD inline native controls require unsupported edit reconciliation:"):
            from InferenceGrid.FreeCadDepthEdits import depth_edits
            try:
                changes = depth_edits(read_file(source, 128 * 1024 * 1024))
            except ValueError as error:
                reports["native-edits"] = {"status": "unresolved", "reason": str(error)[:512]}
            else:
                reports["native-edits"] = {"status": "compared", "changes": changes, "source_sha256": pin}
        from runpy import run_path
        cases = run_path(str(root / "re/FreeCad/Verification/Cases.py"))["KCases"]
        for case in cases.values():
            if case["sha256"] != pin:
                continue
            actual = defaultdict(list)
            for parameter in document.get("parameters", {}).get("$tuple", []):
                actual[parameter["id"]].append(parameter)
            checks = []
            for expected in case.get("parameters", []):
                matches = actual[expected["id"]]
                observed = None
                if len(matches) == 1:
                    value = matches[0]
                    observed = {"id": value["id"], "owner": value["owner_id"],
                                "value": value["value"]["value"], "unit": value["value"]["unit"]}
                    if value.get("expression"):
                        expr = value["expression"]
                        observed.update(expression=expr["source"], targets=expr["parameter_ids"]["$tuple"])
                checks.append({"expected": expected, "observed": observed, "matches": observed == expected})
            reports["saved-control"] = {"source_sha256": pin, "expected_mode": case["mode"], "parameters": checks}
            break
    if application == "solidworks" and suffix == ".sldprt" and reports.get("container", {}).get("members"):
        from InferenceGrid.SolidWorksDimensionEvidence import dimension_evidence
        reports["dimension-evidence"] = dimension_evidence(root, source, pin, document, controls)
        if controls:
            audit["supplied_control_sha256"] = [p.stem for p in controls]
        if "strict" in reports:
            from InferenceGrid.ReaderPass import reader_passes
            reports.update(reader_passes(root, source, scratch, env, document, reports["dimension-evidence"], controls))
        from InferenceGrid.RawScalarRule import part_scalars
        measured, scalar_patch = part_scalars(root, source, pin, scratch, controls)
        reports["scalar-streams"] = measured
        if scalar_patch:
            reports["scalar-stream-reader"] = scalar_patch
    if "native" in reports:
        from InferenceGrid.BodyCorrespondence import capture_names
        reports["body-correspondence"] = capture_names(root, pin, source.stat().st_size, reports["native"])
        from InferenceGrid.NativeClassEvidence import native_classes
        from InferenceGrid.TraceRefusal import trace_refusal
        from InferenceGrid.RepeatSave import compare_capture
        audit["native_classes"] = native_classes(reports["native"], root)
        trace = trace_refusal(reports["native"], attempts["strict"].get("message", ""), audit["native_classes"]["classes"])
        comparison = compare_capture(reports["native"], pin, root, scratch, [sys.executable, "-m", "KitCli", "decode"], env)
        if comparison and comparison.get("oracle_geometry") and document:
            from InferenceGrid.MeasureBodies import measure_bodies
            reports["body-measurements"] = measure_bodies(document, comparison["oracle_geometry"])
        if comparison is not None:
            reports["repeat-save"] = comparison
            audit["repeat_save_status"] = comparison["status"]
        from InferenceGrid.ResolveNames import advance_names
        proposal = advance_names(reports["native"], attempts["strict"].get("message", ""), source, root, scratch)
        if proposal is not None:
            reports["design-names"] = proposal
        timeline_env = env.copy()
        if proposal:
            timeline_env["PYTHONPATH"] = os.pathsep.join(map(str, (scratch / "candidate/src", root / "Cli")))
        timeline = subprocess.run([sys.executable, str(Path(__file__).with_name("RecoverTimeline.py")), source],
                                  cwd=scratch, env=timeline_env, capture_output=True, timeout=180)
        if timeline.returncode == 2:
            audit["timeline_refusal"] = json.loads(timeline.stdout)["refusal"]
        else:
            timeline.check_returncode()
            components = json.loads(timeline.stdout)
            from InferenceGrid.InferTimelineNames import infer_names
            label_repair = infer_names(root, source, scratch, timeline_env, components, reports["body-correspondence"]["witnesses"])
            if label_repair:
                components, reports["timeline-names"] = label_repair
            recovered = {"components": components, "oracle_fields_match": None}
            if len(components) == 1:
                names = [row["name"] for row in components[0]["features"]]
                recovered["capture_name_checks"] = [
                    {"capture": witness["capture"], "sha256": witness["sha256"], "case": witness["case"],
                     "expected": witness["timeline_names"], "ordered_names_match": names == witness["timeline_names"]}
                    for witness in reports["body-correspondence"]["witnesses"] if witness["timeline_names"] is not None
                ]
                from InferenceGrid.ParameterWitness import parameter_witness
                recovered["parameter_checks"] = [
                    {"capture": witness["capture"], "sha256": witness["sha256"],
                     **parameter_witness(components[0]["parameters"], witness["parameters"])}
                    for witness in reports["body-correspondence"]["witnesses"]
                    if witness["parameters"] is not None and "parameters" in components[0]
                ]
                from InferenceGrid.ParameterProjection import fit_projection
                projection = fit_projection(root, scratch, timeline_env, components[0], reports["body-correspondence"]["witnesses"], pin)
                if projection:
                    recovered["parameter_projection"] = projection
            oracle = comparison and comparison.get("oracle_timeline")
            if oracle and len(components) == 1:
                actual = components[0]["features"]
                types = {"DcSketch": "Sketch", "DcExtrudeFeature": "ExtrudeFeature"}
                recovered["oracle_fields_match"] = len(actual) == len(oracle) and all(
                    types.get(a["native_class"]) == b["type"] and
                    all(a[k] == b[k] and type(a[k]) is type(b[k]) for k in ("index", "name", "suppressed"))
                    for a, b in zip(actual, oracle))
            if not oracle:
                from InferenceGrid.StudyWitness import study_witness
                recovered["study_measurements"] = study_witness(root, pin, source.stat().st_size, components)
            reports["timeline"] = recovered
        if trace is not None:
            reports["references"] = trace
            audit["refusal_trace"] = {"start": trace["start"], "class": trace["class"], "nodes": len(trace["nodes"]),
                                      "unresolved_targets": len(trace["unresolved_targets"])}
    return {application: {"catalogue_sha256": pin, "features": features}}, (audit, reports)
