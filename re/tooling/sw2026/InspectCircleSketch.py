from __future__ import annotations

import hashlib
import json
import math
import sys
import time
from pathlib import Path

import AuthorCurves
import Swapp
from InspectFresh import healthy, inspect
from OracleIdentity import application_identity


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def frame_basis(axis):
    bases = {
        "z": ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        "x": ((0.0, 0.0, -1.0), (0.0, 1.0, 0.0)),
        "y": ((1.0, 0.0, 0.0), (0.0, 0.0, -1.0)),
    }
    return bases[axis]


def check_frame(author, document):
    utility = author.get(author.app, "GetMathUtility")
    inverse = author.get(author.get(author.sketch, "ModelToSketchTransform"), "Inverse")
    u, v = frame_basis(document["plane_axis"])
    observations = {}
    for label, point, expected in (("origin", [0.0, 0.0, 0.0], (0.0, 0.0, 0.0)), ("u", [1.0, 0.0, 0.0], u), ("v", [0.0, 1.0, 0.0], v)):
        native = author.get(utility, "CreatePoint", Swapp.VARIANT(Swapp.pythoncom.VT_ARRAY | Swapp.pythoncom.VT_R8, point))
        world = [float(value) for value in author.get(author.get(native, "MultiplyTransform", inverse), "ArrayData")]
        AuthorCurves.require(len(world) == 3, "native frame point has wrong cardinality")
        for axis, value in enumerate(expected):
            author.rec.close_number(f"frame {label} {axis}", world[axis], value)
        observations[label] = world
    return observations


def driving_dimension(author, case, feature, factor):
    document = case["request"]["document"]
    request = document["circle_dimension"]
    name = "D1@" + document["sketch_name"]
    parameter = author.get(author.model, "Parameter", name)
    AuthorCurves.require(parameter is not None, "generated radial parameter is missing")
    AuthorCurves.require(int(author.get(parameter, "DrivenState")) == 2 and not bool(author.get(parameter, "ReadOnly")), "generated radial dimension is not editable and driving")
    expected = document["radius_m"] * factor * (2 if request["mode"] == "diameter" else 1)
    author.rec.close_number("driving radial value", author.get(parameter, "SystemValue"), expected)
    displays = []
    display = author.get(feature, "GetFirstDisplayDimension")
    while display is not None:
        AuthorCurves.require(len(displays) < 4, "unexpected radial display cycle or cardinality")
        dimension = author.get(display, "GetDimension2", 0)
        AuthorCurves.require(dimension is not None, "radial display has no dimension")
        full = str(author.get(dimension, "FullName"))
        AuthorCurves.require(full.split("@")[:2] == name.split("@"), "radial display targets a different parameter")
        displays.append({"name": full, "value": float(author.get(dimension, "SystemValue"))})
        display = author.get(feature, "GetNextDisplayDimension", display)
    AuthorCurves.require(len(displays) == 1, "generated sketch must contain exactly one radial display")
    return {"name": name, "mode": request["mode"], "value": float(author.get(parameter, "SystemValue")), "driving": True, "editable": True, "displays": displays}


def center_fixation(author, geometry):
    manager = author.get(author.sketch, "RelationManager")
    observed = []
    for relation in author.get(manager, "GetRelations", 0) or []:
        if int(author.get(relation, "GetRelationType")) == 17:
            observed.append(author.observe_relation(relation, {}))
    AuthorCurves.require(len(observed) == 1, "generated circle must have exactly one fixed-point relation")
    fixed = observed[0]
    AuthorCurves.require(fixed["entities"] == 1 and fixed["returned_entities"] == 1 and not fixed["suppressed"], "center fixation has wrong cardinality or is suppressed")
    expected = AuthorCurves.binding_key(geometry[0]["point_bindings"]["center"])
    AuthorCurves.require(AuthorCurves.binding_key(fixed["bindings"][0]) == expected, "fixed-point relation targets another point")
    for selector in (1, 2, 6):
        AuthorCurves.require(not (author.get(manager, "GetRelations", selector) or []), f"generated fixed sketch has invalid relation filter {selector}")
    return fixed


def body_snapshot(author, document, radius_factor, depth_factor):
    require = AuthorCurves.require
    u, v = frame_basis(document["plane_axis"])
    normal = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
    feature = author.get(author.model, "FeatureByName", document["extrusion_name"])
    require(feature is not None and str(author.get(feature, "GetTypeName2")) == "Extrusion", "generated circle boss is missing or has another feature type")
    definition = author.get(feature, "GetDefinition")
    require(definition is not None, "circle boss has no native feature definition")
    end = int(author.get(definition, "GetEndCondition", True))
    require(end == 0 and not bool(author.get(definition, "BothDirections")) and not bool(author.get(definition, "ReverseDirection")), "circle boss is not the requested forward single-ended blind feature")
    radius = document["radius_m"] * radius_factor
    depth = document["depth_m"] * depth_factor
    author.rec.close_number("blind definition depth", author.get(definition, "GetDepth", True), depth)
    name = "D1@" + document["extrusion_name"]
    parameter = author.get(author.model, "Parameter", name)
    require(parameter is not None and int(author.get(parameter, "DrivenState")) == 2 and not bool(author.get(parameter, "ReadOnly")), "circle boss depth is not an editable driving parameter")
    author.rec.close_number("driving blind depth", author.get(parameter, "SystemValue"), depth)
    properties = author.get(author.get(author.model, "Extension"), "CreateMassProperty")
    require(properties is not None, "generated circle boss has no mass properties")
    author.set(properties, "UseSystemUnits", True)
    measured = {"volume": float(author.get(properties, "Volume")), "area": float(author.get(properties, "SurfaceArea")), "com": [float(value) for value in author.get(properties, "CenterOfMass")]}
    center_x, center_y = document["center_m"]
    expected = {"volume": math.pi * radius * radius * depth, "area": 2.0 * math.pi * radius * radius + 2.0 * math.pi * radius * depth, "com": [center_x * u[index] + center_y * v[index] + normal[index] * depth / 2.0 for index in range(3)]}
    author.rec.close_number("solid volume", measured["volume"], expected["volume"], absolute=1e-22)
    author.rec.close_number("solid area", measured["area"], expected["area"], absolute=1e-18)
    require(len(measured["com"]) == 3, "solid mass center has wrong cardinality")
    for axis in range(3):
        author.rec.close_number(f"solid center of mass {axis}", measured["com"][axis], expected["com"][axis])
    return {"feature_type": "Extrusion", "end_condition": end, "depth_parameter": name, "depth": depth, "radius": radius, "mass": measured, "expected_mass": expected}


def initial_state(author, case):
    document = case["request"]["document"]
    body_count = len(author.get(author.model, "GetBodies2", 0, False) or [])
    wrong = int(author.get(author.get(author.model, "Extension"), "GetWhatsWrongCount"))
    features = author.rec.call("native feature tree before explicit rebuild", Swapp.features, author.model)
    has_body = document.get("feature_kind") == "blind_extrusion"
    requested = [(document["sketch_name"], "ProfileFeature")]
    if has_body:
        requested.append((document["extrusion_name"], "Extrusion"))
    targets = []
    for name, kind in requested:
        rows = [row for row in features if row.get("name") == name]
        targets.append({"name": name, "type": kind, "matches": len(rows), "active": len(rows) == 1 and rows[0].get("type") == kind and rows[0].get("suppressed") is False and not rows[0].get("suppression_query_error")})
    tree_healthy = bool(features) and all(row.get("error") == 0 and row.get("warning") is False and not row.get("error_query_error") for row in features)
    return {"before_explicit_rebuild": True, "body_count": body_count, "expected_body_count": int(has_body), "rebuild_problem_count": wrong, "features": features, "requested_features": targets, "passed": body_count == int(has_body) and wrong == 0 and tree_healthy and all(row["active"] for row in targets)}


def snapshot(author, case, factor=1.0, depth_factor=1.0):
    require = AuthorCurves.require
    require(bool(author.get(author.model, "ForceRebuild3", False)), "circle sketch rebuild returned failure")
    wrong = int(author.get(author.get(author.model, "Extension"), "GetWhatsWrongCount"))
    require(wrong == 0, f"circle sketch has {wrong} rebuild problems")
    document = case["request"]["document"]
    feature = author.get(author.model, "FeatureByName", document["sketch_name"])
    require(feature is not None, "generated circle sketch feature is missing")
    require(str(author.get(feature, "GetTypeName2")) == "ProfileFeature", "generated circle is not an ordinary native profile")
    author.sketch = author.get(feature, "GetSpecificFeature2")
    constrained_status = int(author.get(author.sketch, "GetConstrainedStatus"))
    require(constrained_status not in (4, 5, 6, 7), f"generated circle has unacceptable constraint state {constrained_status}")
    geometry = author.geometry()
    expected_circles = document["circles_m"] if document.get("profile_kind") == "circle_set" else [{"center_m": document["center_m"], "radius_m": document["radius_m"]}]
    require(len(geometry) == len(expected_circles) and all(row["kind"] == "circle" and not row["construction"] for row in geometry), "generated sketch does not contain the requested ordinary circles")
    for circle_index, (actual, expected_circle) in enumerate(zip(geometry, expected_circles)):
        prefix = "" if len(expected_circles) == 1 else f"circle {circle_index} "
        for index, expected in enumerate(expected_circle["center_m"]):
            author.rec.close_number(f"{prefix}center {index}", actual["center"][index], expected)
        author.rec.close_number(prefix + "radius", actual["radius"], expected_circle["radius_m"] * factor)
    body_objects = author.get(author.model, "GetBodies2", 0, False) or []
    has_body = document.get("feature_kind") == "blind_extrusion"
    require(len(body_objects) == int(has_body), "generated candidate has an unexpected solid body count")
    features = author.rec.call("native feature tree", Swapp.features, author.model)
    require(features and all(row.get("error") == 0 and row.get("warning") is False and not row.get("error_query_error") for row in features), "native feature tree has errors or warnings")
    if not has_body:
        require(not any(row["type"] == "Extrusion" for row in features), "sketch rung must not contain an extrusion")
    transform = author.get(author.sketch, "ModelToSketchTransform")
    result = {"geometry": geometry, "bodies": len(body_objects), "whats_wrong": wrong, "features": features, "constraint_status": constrained_status, "model_to_sketch_transform": list(author.get(transform, "ArrayData")), "frame": check_frame(author, document)}
    if "circle_dimension" in document:
        result["radial"] = driving_dimension(author, case, feature, factor)
        if document["circle_dimension"].get("fix_center", False):
            require(constrained_status == 3, f"center-fixed radial sketch is not fully constrained: {constrained_status}")
            result["center_fixation"] = center_fixation(author, geometry)
    if has_body:
        result["extrusion"] = body_snapshot(author, document, factor, depth_factor)
    return result


def run_phase(case, phase, source, output, expected_oracle, checkpoint, factor=1.0, depth_factor=1.0):
    directory = output / case["name"] / phase
    directory.mkdir(parents=True, exist_ok=False)
    rec = AuthorCurves.Recorder(directory / "Record.json", {"case": case, "phase": phase})
    controller = None
    author = None
    result = {"phase": phase, "source": str(source), "source_sha256": digest(source), "passed": False}
    with Swapp.Dismisser() as dialogs:
        try:
            rec.call("fresh oracle idle guard", Swapp.sweep)
            controller = rec.call("start owned oracle", Swapp.Sw)
            identity = rec.call("oracle executable identity", application_identity, controller.app)
            AuthorCurves.require(identity["version_matches"] and identity["sha256"] == expected_oracle and controller.revision == "34.5.2", "circle sketch oracle identity differs")
            result["oracle_identity"] = identity
            author = AuthorCurves.CurveAuthor(controller.app, rec, Swapp)
            author.model, errors, warnings = rec.call("open generated circle sketch", controller.open, source)
            AuthorCurves.require(author.model is not None and errors == warnings == 0, f"circle sketch load failed or warned: {errors}, {warnings}")
            result.update(open_errors=errors, open_warnings=warnings, initial_state=initial_state(author, case))
            result["snapshot"] = snapshot(author, case, factor, depth_factor)
            AuthorCurves.require(result["initial_state"]["passed"], "generated candidate failed native body/feature checks before explicit rebuild")
            if phase == "fresh-reopen" and "circle_dimension" in case["request"]["document"]:
                edited_factor = case["edit_factor"]
                AuthorCurves.require(type(edited_factor) in (float, int) and math.isfinite(edited_factor) and edited_factor > 0 and edited_factor != 1, "radial edit factor must be an explicit finite positive change")
                name = result["snapshot"]["radial"]["name"]
                parameter = author.get(author.model, "Parameter", name)
                target = result["snapshot"]["radial"]["value"] * edited_factor
                status = int(author.get(parameter, "SetSystemValue3", target, 1, Swapp.nothing()))
                AuthorCurves.require(status == 0, f"radial driving edit returned status {status}")
                result["edit"] = {"name": name, "before": result["snapshot"]["radial"]["value"], "after": target, "factor": edited_factor, "setter_status": status}
                result["edited_snapshot"] = snapshot(author, case, edited_factor)
                factor = edited_factor
                if case["request"]["document"].get("feature_kind") == "blind_extrusion":
                    depth_factor = case["depth_edit_factor"]
                    AuthorCurves.require(type(depth_factor) in (float, int) and math.isfinite(depth_factor) and depth_factor > 0 and depth_factor != 1, "blind-depth edit factor must be an explicit finite positive change")
                    document = case["request"]["document"]
                    name = "D1@" + document["extrusion_name"]
                    parameter = author.get(author.model, "Parameter", name)
                    target = document["depth_m"] * depth_factor
                    status = int(author.get(parameter, "SetSystemValue3", target, 1, Swapp.nothing()))
                    AuthorCurves.require(status == 0, f"circle boss depth edit returned status {status}")
                    result["depth_edit"] = {"name": name, "before": document["depth_m"], "after": target, "factor": depth_factor, "setter_status": status}
                    result["edited_body_snapshot"] = snapshot(author, case, factor, depth_factor)
            saved = directory / (case["name"] + "Saved.SLDPRT")
            save_result = rec.call("save circle sketch copy", controller.save_as, author.model, saved)
            AuthorCurves.require(save_result == (True, 0, 0), f"circle sketch save failed or warned: {save_result}")
            result.update(saved_path=str(saved), saved_sha256=digest(saved), saved_bytes=saved.stat().st_size, saved_factor=factor, saved_depth_factor=depth_factor)
            result["passed"] = True
        except Exception as error:
            rec.failure(error)
            result["exception"] = repr(error)
        finally:
            try:
                if author is not None and author.model is not None:
                    rec.call("close owned circle sketch", controller.close_doc, author.model)
                    author.model = None
            except Exception as error:
                rec.failure(error, cleanup=True)
            finally:
                if controller is not None:
                    try:
                        controller.close()
                    except Exception as error:
                        rec.failure(error, cleanup=True)
                    result["controller_diagnostics"] = controller.diagnostics
    result.update(dialogs=dialogs.log, progress_windows=dialogs.progress)
    result["source_immutable"] = digest(source) == result["source_sha256"]
    result["passed"] = result["passed"] and result["source_immutable"] and rec.data["first_failure"] is None and not rec.data["cleanup_errors"] and not result.get("controller_diagnostics") and not result["dialogs"]
    rec.data.update(passed=result["passed"], sketch_result=result, finished_at=time.time())
    rec.flush()
    checkpoint()
    return result


def main():
    source = Path(sys.argv[1])
    job = json.loads(source.read_bytes())
    output = Path(job["output"])
    root = Path(job["checkout_root"]).resolve()
    AuthorCurves.require(not output.resolve().is_relative_to(root), "oracle output must be outside the checkout")
    output.mkdir(parents=True, exist_ok=False)
    control = Path(job["control"])
    AuthorCurves.require(digest(control) == job["control_sha256"], "native control identity changed")
    result = {"schema": "kit.sw2026.circle-sketch-inspection.v5", "scope": "independent circle sketches and single-circle blind boss research rungs only", "started_at": time.time(), "generator": job["generator"], "job_sha256": digest(source), "tool_sha256": digest(Path(__file__)), "cases": [], "controls": [], "native_acceptance": False, "heldout_acceptance": False, "radial_dimension_acceptance": False, "circle_extrusion_acceptance": False, "passed": False}
    def checkpoint():
        (output / "Inspection.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    checkpoint()
    before = {"kind": "control_before"}
    result["controls"].append(before)
    inspect(control, result=before, checkpoint=checkpoint)
    before["healthy"] = healthy(before) and before["oracle_identity"]["sha256"] == job["oracle_sha256"]
    try:
        if before["healthy"]:
            for case in job["cases"]:
                path = Path(case["path"])
                AuthorCurves.require(digest(path) == case["sha256"], "generated source identity changed")
                record = {"name": case["name"], "phases": []}
                result["cases"].append(record)
                first = run_phase(case, "open-save", path, output, job["oracle_sha256"], checkpoint)
                record["phases"].append(first)
                if first["passed"]:
                    second = run_phase(case, "fresh-reopen", Path(first["saved_path"]), output, job["oracle_sha256"], checkpoint)
                    record["phases"].append(second)
                    if second["passed"] and "circle_dimension" in case["request"]["document"]:
                        third = run_phase(case, "edited-fresh-reopen", Path(second["saved_path"]), output, job["oracle_sha256"], checkpoint, second["saved_factor"], second["saved_depth_factor"])
                        record["phases"].append(third)
                    identities = [row["oracle_identity"] for row in record["phases"]]
                    record["fresh_process"] = len({row["process_id"] for row in identities}) == len(identities) and len({row["process_creation_filetime"] for row in identities}) == len(identities)
                expected_phases = 3 if "circle_dimension" in case["request"]["document"] else 2
                record["passed"] = len(record["phases"]) == expected_phases and record.get("fresh_process") is True and all(row["passed"] for row in record["phases"])
                checkpoint()
    except Exception as error:
        result["exception"] = repr(error)
    finally:
        after = {"kind": "control_after"}
        result["controls"].append(after)
        inspect(control, result=after, checkpoint=checkpoint)
        after["healthy"] = healthy(after) and after["oracle_identity"]["sha256"] == job["oracle_sha256"]
        result["controls_healthy"] = len(result["controls"]) == 2 and all(row.get("healthy") for row in result["controls"])
        result["control_immutable"] = digest(control) == job["control_sha256"]
        result["passed"] = result["controls_healthy"] and result["control_immutable"] and bool(job["cases"]) and len(result["cases"]) == len(job["cases"]) and all(row.get("passed") is True for row in result["cases"]) and not result.get("exception")
        result["finished_at"] = time.time()
        checkpoint()
    print(json.dumps({"passed": result["passed"], "cases": len(result["cases"]), "native_acceptance": False}))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
