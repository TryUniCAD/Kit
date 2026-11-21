from argparse import ArgumentParser
from hashlib import sha256
import json
from math import isclose, isfinite
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
from shutil import copyfileobj
import sys
from time import time


SCHEMA = "kit.sw2026.first-creator-scope-native.v1"
PACKET_NAME = "FirstCreatorScopeNative01"
GUEST_PACKET = PureWindowsPath(r"\\Mac\Home\Documents\UniCAD\Oracle121Takeover") / PACKET_NAME
GUEST_WORK = PureWindowsPath(r"C:\KitWarmFirstCreatorScope")
ORACLE = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
BUILD = "34.5.2.0604"
CONTROL = "c0472f9f42bf473a9073adb997180040b7767dfae93310610f77cff9509bec57"
CASES = {"Single": "SinglePlate", "Translated": "sdk 寸法 beta translated"}
MODES = {"All": 0, "Selected": 1}
TOOLS = ("AuthorCurves.py", "InspectFresh.py", "ObserveFirstCreatorNative.py", "OracleIdentity.py", "Swapp.py")
PHASES = ("Before", *(f"{name}/{mode}/{phase}" for name in CASES for mode in MODES for phase in ("Edit", "Reopen")), "After")
UNAVAILABLE_COM = {0x80020003, 0x80020006, 0x80004001}


def require(value, diagnostic):
    if not value:
        raise ValueError(diagnostic)


def wire(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False, indent=2) + "\n").encode()


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def publish(path, value):
    raw = wire(value)
    with path.open("xb") as output:
        output.write(raw)
    return sha256(raw).hexdigest()


def file_row(root, path):
    return {"path": path.relative_to(root).as_posix(), "bytes": path.stat().st_size, "sha256": digest(path)}


def checked(root, row, expected_path):
    name = PurePosixPath(expected_path)
    path = root.joinpath(*name.parts)
    require(row["path"] == name.as_posix() and not name.is_absolute() and ".." not in name.parts
            and path.is_file() and path.resolve(strict=True) == path and path.stat().st_size == row["bytes"]
            and digest(path) == row["sha256"], f"frozen packet file differs: {name}")
    return path


def predict(vertices, depth):
    (left, bottom), _, (right, top), _ = vertices
    width, height = right - left, top - bottom
    return {
        "volume": width * height * depth,
        "area": 2.0 * (width * height + width * depth + height * depth),
        "com": [(left + right) / 2, (bottom + top) / 2, depth / 2],
        "bounds": [[left, bottom, 0.0], [right, top, depth]],
    }


def verify(packet, expected_sha):
    packet = packet.absolute()
    root = packet.parent.resolve(strict=True)
    require(packet == root / "Packet.json" and packet.resolve(strict=True) == packet and digest(packet) == expected_sha,
            "exact published scope packet digest differs")
    job = json.loads(packet.read_bytes())
    require(job["schema"] == SCHEMA and job["oracle"] == {"sha256": ORACLE, "file_version": BUILD}
            and job["guest_path"] == str(GUEST_PACKET) and job["guest_workspace"] == str(GUEST_WORK)
            and job["phases"] == list(PHASES) and job["heldout_inputs_read"] == job["native_processes_started"] == 0,
            "unexpected scope packet authority")
    require(set(job["tools"]) == set(TOOLS)
            and digest(Path(__file__)) == job["tools"]["ObserveFirstCreatorNative.py"]["sha256"], "incomplete scope observer closure")
    for name in TOOLS:
        checked(root, job["tools"][name], "Tools/" + name)
    require(job["control"]["sha256"] == CONTROL, "control authority differs")
    checked(root, job["control"], "Inputs/Control.SLDPRT")
    require(set(job["cases"]) == set(CASES), "scope experiment does not include both disclosed requests")
    for case_id, model in CASES.items():
        case = job["cases"][case_id]
        name = model + ".SLDPRT"
        require(case["model_name"] == model and case["input_locator"] == str(GUEST_WORK / name)
                and set(case["modes"]) == set(MODES) and len(case["tree"]) == 25
                and any(point[2] != 0.0 for point in case["label_xyz_m"])
                and case["runtime_input_reads"] == 0 and case["scope_byte_values"] == [0, 1],
                "scope experiment lacks its exact modeled identities")
        require(case["expected"] == {label: predict(case["vertices_m"], depth) for label, depth in
                                     (("open", case["dimensions_m"][2]), ("edited", case["edited_depth_m"]))},
                "scope geometry does not follow the independent rectangle invariants")
        request = json.loads(checked(root, case["request"], f"Proof/{case_id}/Request.json").read_bytes())
        proof = json.loads(checked(root, case["proof"], f"Proof/{case_id}/Build.json").read_bytes())
        require(proof["request_sha256"] == case["request"]["sha256"] and proof["modes"] == case["modes"]
                and proof["deterministic_guarded_builds"] == 2 and proof["complete_stream_count"] == 10
                and proof["same_streams"] == 9 and proof["scope_byte_offset"] == case["scope_byte_offset"]
                and request["request"]["label_points"] == case["label_xyz_m"]
                and request["request"]["scope"] == {"first_existing_body_scope": "selected", "prior_body_ids": []},
                "classified geometry build does not bind the exact request and both scope variants")
        for mode, code in MODES.items():
            item = case["modes"][mode]
            require(item["scope_word"] == code and item["derivative_locator"] ==
                    str(GUEST_WORK / "Trials" / case_id / mode / "Edited" / name),
                    "trial mode, edit locator or intended filename changed")
            checked(root, item["input"], f"Inputs/{case_id}/{mode}/{name}")
        require(case["modes"]["All"]["input"]["sha256"] != case["modes"]["Selected"]["input"]["sha256"],
                "isolated scope variable did not change the candidate")
    return root, job


def copy_new(source, target, pin):
    require(digest(source) == pin and not target.exists(), "native transport changed or would overwrite an input")
    with source.open("rb") as first, target.open("xb") as second:
        copyfileobj(first, second)
    require(digest(target) == pin, "native transport copy differs")


def getter(author, definition, name, result_type):
    def query():
        try:
            value = author.sw.cv(definition, name)
        except AttributeError:
            return {"status": "unavailable", "reason": "binding_has_no_member"}
        except author.sw.pythoncom.com_error as error:
            code = error.hresult & 0xFFFFFFFF
            scode = error.excepinfo[-1] & 0xFFFFFFFF if error.excepinfo and type(error.excepinfo[-1]) is int else None
            return {"status": "unavailable" if code in UNAVAILABLE_COM or
                    (code == 0x80020009 and scode in UNAVAILABLE_COM) else "error",
                    "hresult": f"0x{code:08x}", "server_hresult": f"0x{scode:08x}" if scode is not None else None}
        if result_type == "boolean" and (type(value) is bool or (type(value) is int and value in (-1, 0, 1))):
            return {"status": "observed", "value": bool(value)}
        if result_type == "count" and type(value) is int:
            if value == -1:
                return {"status": "unavailable", "reason": "native_count_sentinel", "raw_value": -1}
            return {"status": "observed" if value >= 0 else "error", "value": value}
        return {"status": "error", "reason": "unexpected_getter_result", "result_type": type(value).__name__}

    return author.rec.call("direct scope getter " + name, query)


def assessment(observations, expected):
    flag = observations["feature_scope"]
    applicable = {"feature_scope": expected}
    if expected:
        applicable.update(auto_select=False, body_count=0)
    elif observations["body_count"]["status"] == "observed":
        applicable.update(body_count=0)
    verdicts = {}
    for name, value in applicable.items():
        row = observations[name]
        verdicts[name] = row["status"] if row["status"] != "observed" else "match" if row["value"] == value else "mismatch"
    if not expected and flag == {"status": "observed", "value": False}:
        verdicts["auto_select"] = "not_applicable"
        verdicts.setdefault("body_count", "not_applicable")
    return verdicts


def native_scope(author, boss, mode):
    definition = author.typed(author.get(boss, "GetDefinition"), "ExtrudeFeatureData2")
    result = {
        "feature_scope": getter(author, definition, "FeatureScope", "boolean"),
        "auto_select": getter(author, definition, "AutoSelect", "boolean"),
        "body_count": getter(author, definition, "GetFeatureScopeBodiesCount", "count"),
    }
    result["expected"] = {"feature_scope": mode == "Selected",
                          "auto_select": False if mode == "Selected" else None, "body_count": 0}
    result["assessment"] = assessment(result, mode == "Selected")
    return result, definition


def part_metrics(author, body, expected):
    rec = author.rec
    faces = author.get(body, "GetFaces") or ()
    edges = author.get(body, "GetEdges") or ()
    vertices = author.get(body, "GetVertices") or ()
    require([len(faces), len(edges), len(vertices)] == [6, 12, 8], "native solid is not one complete rectangular prism")
    mass = rec.call("part mass and surface properties", author.sw.mass, author.model)
    rec.close_number("solid volume", mass["volume"], expected["volume"], absolute=1e-20)
    rec.close_number("solid area", mass["area"], expected["area"], absolute=1e-16)
    for index, (actual, wanted) in enumerate(zip(mass["com"], expected["com"], strict=True)):
        rec.close_number(f"solid centre axis {index}", actual, wanted, absolute=1e-10)
    bounds = [[], []]
    for index, sign in enumerate((-1.0, 1.0)):
        for axis in range(3):
            direction = [0.0] * 3
            direction[axis] = sign
            sw = author.sw
            outputs = [sw.VARIANT(sw.pythoncom.VT_BYREF | sw.pythoncom.VT_R8, 0.0) for _ in range(3)]
            answer = author.get(body, "GetExtremePoint", *direction, *outputs)
            if isinstance(answer, tuple):
                require(len(answer) == 4 and bool(answer[0]), "typed extrema unavailable")
                point = answer[1:]
            else:
                require(bool(answer), "native solid extrema unavailable")
                point = [item.value for item in outputs]
            require(len(point) == 3 and all(isfinite(value) for value in point), "incomplete native solid extrema")
            rec.close_number(f"bound side {index} axis {axis}", point[axis], expected["bounds"][index][axis], absolute=1e-10)
            bounds[index].append(point[axis])
    return {"mass": mass, "bounds_m": bounds, "topology": [len(faces), len(edges), len(vertices)]}


def sketch_details(author, sketch, case):
    author.sketch = author.get(sketch, "GetSpecificFeature2")
    require(author.sketch is not None, "native sketch has no actual sketch object")
    geometry = author.geometry()
    expect = case["vertices_m"]
    remaining = list(geometry)
    require(len(remaining) == 4, "native sketch contour is incomplete")
    for first, last in zip(expect, expect[1:] + expect[:1], strict=True):
        candidates = [row for row in remaining if row["kind"] == "line" and not row["construction"]
                      and any(all(isclose(a, b, rel_tol=2e-7, abs_tol=1e-10)
                                  for a, b in zip((*start, *end), (*first, *last), strict=True))
                              for start, end in ((row["start"], row["end"]), (row["end"], row["start"])))]
        require(len(candidates) == 1, "native sketch changed an authored edge")
        remaining.remove(candidates[0])
    manager = author.get(author.sketch, "RelationManager")
    require(int(author.get(manager, "GetRelationsCount", 0)) == 6, "native sketch lost its six actual relations")
    seen = {}
    for relation in author.get(manager, "GetRelations", 0) or ():
        if int(author.get(relation, "GetRelationType")) != 1:
            continue
        display = author.get(relation, "GetDisplayDimension")
        dim = author.get(display, "GetDimension2", 0)
        full = str(author.get(dim, "FullName"))
        short = "@".join(full.split("@")[:2])
        require(short in case["parameter_names"][:2] and short not in seen, "native display is attached to another dimension")
        anno = author.typed(author.get(display, "GetAnnotation"), "Annotation")
        xyz = author.get(anno, "GetPosition")
        require(isinstance(xyz, (list, tuple)) and len(xyz) == 3 and all(isfinite(value) for value in xyz),
                "native relation display did not expose its finite annotation coordinates")
        seen[short] = {"parameter": full, "annotation_get_position_m": [float(value) for value in xyz]}
    require(set(seen) == set(case["parameter_names"][:2]), "native relation displays do not own both sketch dimensions")
    return {"segments": geometry, "annotations": seen,
            "annotation_api_is_stored_xyz": False, "constraint_status": int(author.get(author.sketch, "GetConstrainedStatus"))}


def snapshot(author, case, mode, *, edited, cold_initial=False):
    model = author.model
    profile = author.get(model, "FeatureByName", case["profile"])
    boss = author.get(model, "FeatureByName", case["feature"])
    require(profile is not None and boss is not None, "actual sketch or boss missing")
    state = {"tree": author.feature_tree(required_names=(case["profile"], case["feature"], case["support"]))}
    require([[r["name"], r["type"], r["parent"]] for r in state["tree"]] == case["tree"]
            and not any(row["suppressed"] for row in state["tree"]), "full native feature tree changed")
    configuration = author.get(author.get(model, "GetActiveConfiguration"), "Name")
    require(configuration == case["configuration"], "active configuration changed")
    parents = [[str(author.get(item, "Name")) for item in author.get(node, "GetParents") or ()] for node in (profile, boss)]
    require(parents == [[case["support"]], [case["profile"], case["support"]]], "actual boss lost its sketch or support")
    dimensions = [*case["dimensions_m"]]
    if edited:
        dimensions[2] = case["edited_depth_m"]
    for name, expected in zip(case["parameter_names"], dimensions, strict=True):
        value = author.get(model, "Parameter", name)
        require(value is not None and int(author.get(value, "DrivenState")) == 2 and not author.get(value, "ReadOnly")
                and "@".join(str(author.get(value, "FullName")).split("@")[:2]) == name,
                "live dimension lost its actual editable owner")
        measured = float(author.get(value, "SystemValue"))
        state.setdefault("dimensions_m", {})[name] = measured
        author.rec.close_number(name, measured, expected)
    state["scope"], definition = native_scope(author, boss, mode)
    require(int(author.get(definition, "GetEndCondition", True)) == 0 and not author.get(definition, "ReverseDirection")
            and not author.get(definition, "BothDirections"), "native feature left forward blind first boss")
    author.rec.close_number("native boss definition depth", author.get(definition, "GetDepth", True), dimensions[2])
    state["sketch"] = sketch_details(author, profile, case)
    require(state["sketch"]["constraint_status"] in ((1, 2) if cold_initial else (2,)),
            "unanchored rectangle changed solve classification")
    part = author.typed(model, "PartDoc")
    bodies = author.get(part, "GetBodies2", 0, False) or ()
    require(len(bodies) in ((0, 1) if cold_initial else (1,)), "native part does not have its expected single solid")
    state["body_count"] = len(bodies)
    state["configuration"] = configuration
    state["native_ids"] = [int(author.get(node, "GetID")) for node in (profile, boss)]
    require(len(set(state["native_ids"])) == 2 and all(value >= 0 for value in state["native_ids"])
            and int(author.get(author.get(model, "Extension"), "GetWhatsWrongCount")) == 0,
            "native sketch/boss identities are invalid or rebuild issues were reported")
    if bodies:
        state["solid"] = part_metrics(author, author.typed(bodies[0], "Body2"), case["expected"]["edited" if edited else "open"])
    return state


def phase(root, stage, source, input_sha, *, case=None, mode=None, derivative=None, reopen=False):
    from AuthorCurves import CurveAuthor, Recorder
    from InspectFresh import healthy
    from OracleIdentity import application_identity
    import Swapp

    recorder = Recorder(stage / "Record.json", {"phase": stage.name, "input_sha256": input_sha})
    result = {"passed": False, "input_sha256": input_sha, "states": {}}
    recorder.data["result"] = result
    controller = author = None
    begun = time()
    with Swapp.Dismisser() as dialogs:
        try:
            require(digest(source) == input_sha, "native phase original changed")
            recorder.call("guard the idle native application", Swapp.sweep)
            controller = recorder.call("start a fresh oracle", Swapp.Sw)
            native = recorder.call("verify the installed oracle identity", application_identity, controller.app)
            result["oracle_identity"] = native
            require(native["version_matches"] and native["sha256"] == ORACLE and native["file_version"] == BUILD
                    and controller.revision == "34.5.2", "installed native oracle changed")
            if case is None:
                measured = recorder.call("measure exact immutable control", Swapp.measure, controller, source, read_only=True)
                result["control"] = measured
                require(healthy(measured) and measured["bodies"] == 1, "pristine bracket control failed")
            else:
                author = CurveAuthor(controller.app, recorder, Swapp)
                author.model, errors, warnings = recorder.call("open the exact native path", controller.open, source, read_only=reopen)
                result["open"] = [author.model is not None, errors, warnings]
                require(result["open"] == [True, 0, 0] and Path(author.get(author.model, "GetPathName")).samefile(source),
                        "native open failed, warned or selected a different file")
                result["states"]["Initial"] = snapshot(author, case, mode, edited=reopen, cold_initial=not reopen)
                require(author.get(author.model, "ForceRebuild3", False), "initial native rebuild failed")
                result["states"]["Rebuilt"] = snapshot(author, case, mode, edited=reopen)
                if not reopen:
                    dimension = author.get(author.model, "Parameter", case["parameter_names"][2])
                    result["edit_status"] = author.get(dimension, "SetSystemValue3", case["edited_depth_m"], 1, Swapp.nothing())
                    require(result["edit_status"] == 0 and author.get(author.model, "ForceRebuild3", False), "native depth edit or rebuild failed")
                    result["states"]["Edited"] = snapshot(author, case, mode, edited=True)
                    require(derivative.parent.is_dir() and not derivative.exists(), "native edit destination is not unused")
                    result["save"] = list(recorder.call("save new edited derivative", controller.save_as, author.model, derivative))
                    require(result["save"] == [True, 0, 0] and derivative.is_file()
                            and Path(author.get(author.model, "GetPathName")).samefile(derivative), "native derivative failed to save cleanly")
                    result["derivative_sha256"] = digest(derivative)
                    result["states"]["Saved"] = snapshot(author, case, mode, edited=True)
                require(len({tuple(state["native_ids"]) for state in result["states"].values()}) == 1,
                        "native feature persistent identities changed")
            result["passed"] = True
        except Exception as error:
            recorder.failure(error)
        finally:
            if controller is not None:
                try:
                    if author is not None and author.model is not None:
                        controller.close_doc(author.model)
                    controller.close()
                    Swapp.sweep()
                except Exception as error:
                    recorder.failure(error, cleanup=True)
                result["controller_diagnostics"] = controller.diagnostics
    result.update(input_immutable=source.is_file() and digest(source) == input_sha,
                  dialogs=dialogs.log, progress_windows=dialogs.progress, started_at=begun, finished_at=time())
    result["passed"] = bool(result["passed"] and result["input_immutable"] and not result["dialogs"]
                            and not result.get("controller_diagnostics") and not recorder.data["first_failure"]
                            and not recorder.data["cleanup_errors"] and all(row["passed"] for row in recorder.data["checks"]))
    result["numeric_checks"] = len(recorder.data["checks"])
    recorder.data["passed"] = result["passed"]
    recorder.flush()
    target = root / "Native" / "Records" / stage.relative_to(Path(GUEST_WORK)) / "Record.json"
    target.parent.mkdir(parents=True, exist_ok=False)
    pin = digest(recorder.path)
    copy_new(recorder.path, target, pin)
    return {**result, "record": file_row(root, target)}


def clean_control(result):
    return {key: result["control"][key] for key in ("bodies", "mass", "features", "whats_wrong")}


def paired_state(left, right):
    def numbers(first, second):
        return len(first) == len(second) and all(isclose(a, b, rel_tol=2e-7, abs_tol=1e-10)
                                                 for a, b in zip(first, second, strict=True))

    return all(left[key] == right[key] for key in ("body_count", "configuration", "tree", "native_ids")) and all(
        numbers(left["sketch"]["annotations"][key]["annotation_get_position_m"],
                right["sketch"]["annotations"][key]["annotation_get_position_m"])
        for key in left["sketch"]["annotations"]
    )


def summarize(job, output):
    phases = output["phases"]
    before, after = phases.get("Before", {}), phases.get("After", {})
    controls = bool(before.get("passed") and after.get("passed") and clean_control(before) == clean_control(after))
    output["controls_healthy"] = controls
    actual = [phases[key] for key in PHASES if key in phases and phases[key].get("oracle_identity")]
    identities = {(row["oracle_identity"]["process_id"], row["oracle_identity"]["process_creation_filetime"]) for row in actual}
    output["distinct_native_processes"] = len(identities)
    output["process_bracket_verified"] = (len(actual) == len(identities) == len(PHASES)
                                           and all(a["finished_at"] <= b["started_at"] for a, b in zip(actual, actual[1:])))
    verdicts = {}
    lifecycle = True
    for name in CASES:
        for mode in MODES:
            edit = phases.get(f"{name}/{mode}/Edit", {})
            reopen = phases.get(f"{name}/{mode}/Reopen", {})
            edit_states, reopen_states = edit.get("states", {}), reopen.get("states", {})
            rows = [*edit_states.values(), *reopen_states.values()]
            states = [value for row in rows for value in row["scope"]["assessment"].values()]
            complete = bool(edit.get("passed") and reopen.get("passed") and len(rows) == 6)
            same = complete and paired_state(edit_states["Saved"], reopen_states["Initial"])
            lifecycle &= bool(complete and same and all(row["body_count"] == 1 for row in rows))
            verdicts[f"{name}/{mode}"] = {
                "states_observed": len(rows), "edited_save_to_fresh_reopen_match": same,
                "observed_mode_mismatch": "mismatch" in states, "getter_error": "error" in states,
                "getter_unavailable": "unavailable" in states,
                "feature_scope_and_applicable_auto_select_matched": complete and all(
                    row["scope"]["assessment"].get(name, "unavailable") in ("match", "not_applicable")
                    for row in rows for name in ("feature_scope", "auto_select")
                ),
                "all_applicable_getters_matched": complete and all(v in ("match", "not_applicable") for v in states),
            }
    matched = True
    for name in CASES:
        for phase_name in ("Edit", "Reopen"):
            first, second = (phases.get(f"{name}/{mode}/{phase_name}", {}).get("states", {}) for mode in MODES)
            matched &= bool(first and first.keys() == second.keys() and all(paired_state(first[k], second[k]) for k in first))
    output.update(scope_getters=verdicts, same_geometry_tree_and_api_annotation_positions=matched,
                  all_native_lifecycles_passed=bool(controls and output["process_bracket_verified"] and lifecycle and matched))
    output["passed"] = (not output.get("protocol_error") and output["all_native_lifecycles_passed"]
                        and all(v["all_applicable_getters_matched"] for v in verdicts.values()))
    return output


def run_trials(root, job, local, output):
    for name in CASES:
        case = job["cases"][name]
        source = Path(case["input_locator"])
        for mode in MODES:
            item = case["modes"][mode]
            work = local / "Trials" / name / mode
            stage = work / "Edit"
            edited = Path(item["derivative_locator"])
            stage.mkdir(parents=True, exist_ok=False)
            edited.parent.mkdir(exist_ok=False)
            row = item["input"]
            frozen = checked(root, row, f"Inputs/{name}/{mode}/{source.name}")
            copy_new(frozen, source, row["sha256"])
            code = f"{name}/{mode}"
            initial = phase(root, stage, source, row["sha256"], case=case, mode=mode, derivative=edited)
            output["phases"][code + "/Edit"] = initial
            original = work / source.name
            require(not original.exists(), "native input parking destination is not unused")
            source.rename(original)
            initial["parked_input_immutable"] = original.is_file() and digest(original) == row["sha256"]
            initial["passed"] &= initial["parked_input_immutable"]
            print(json.dumps({"phase": code + "/Edit", "passed": initial["passed"]}), flush=True)
            if initial["passed"]:
                stage = work / "Reopen"
                stage.mkdir(exist_ok=False)
                fresh = phase(root, stage, edited, initial["derivative_sha256"], case=case, mode=mode, reopen=True)
                output["phases"][code + "/Reopen"] = fresh
                print(json.dumps({"phase": code + "/Reopen", "passed": fresh["passed"]}), flush=True)
                if fresh["passed"]:
                    target = root / "Native" / "Derivatives" / name / mode / edited.name
                    target.parent.mkdir(parents=True, exist_ok=False)
                    copy_new(edited, target, initial["derivative_sha256"])
                    output["derivatives"][code] = file_row(root, target)


def bracket(root, local, source, result, label):
    stage = local / label
    stage.mkdir(exist_ok=False)
    observed = result["phases"][label] = phase(root, stage, source, CONTROL)
    print(json.dumps({"phase": label, "passed": observed["passed"]}), flush=True)
    return observed["passed"]


def run(packet, expected_sha):
    require(os.name == "nt" and PureWindowsPath(packet.absolute()) == GUEST_PACKET / "Packet.json",
            "run only at the published guest packet locator")
    root, job = verify(packet, expected_sha)
    require(Path(__file__).resolve().parent == root / "Tools", "guest execution requires its frozen observer")
    sys.path.insert(0, str(root / "Tools"))
    local = Path(GUEST_WORK)
    result_root = root / "Native"
    require(not local.exists() and not result_root.exists(), "exact guest or shared workspace already used")
    local.mkdir(exist_ok=False)
    result_root.mkdir(exist_ok=False)
    output = {"schema": SCHEMA, "packet_sha256": expected_sha, "heldout_inputs_read": 0, "phases": {}, "derivatives": {}}
    seed = local / "Control.SLDPRT"
    copy_new(checked(root, job["control"], "Inputs/Control.SLDPRT"), seed, CONTROL)
    try:
        if bracket(root, local, seed, output, "Before"):
            run_trials(root, job, local, output)
    except Exception as error:
        output["protocol_error"] = repr(error)
    try:
        bracket(root, local, seed, output, "After")
    except Exception as error:
        output["protocol_error"] = [output.get("protocol_error"), repr(error)]
    try:
        verify(packet, expected_sha)
        output["packet_inputs_unchanged"] = True
    except Exception as error:
        output["packet_inputs_unchanged"] = False
        output["protocol_error"] = [output.get("protocol_error"), repr(error)]
    summarize(job, output)
    output["source_transfer_complete"] = output["heldout_acceptance"] = output["public_writer_qualified"] = False
    pin = publish(result_root / "Result.json", output)
    print(json.dumps({key: output[key] for key in ("passed", "all_native_lifecycles_passed", "controls_healthy",
                                                     "distinct_native_processes", "scope_getters")} | {"result_sha256": pin}))
    return int(not output["passed"])


def main():
    parser = ArgumentParser(description="Verify or measure the fixed first-creator scope packet")
    parser.add_argument("command", choices=("verify", "run"))
    parser.add_argument("packet", type=Path)
    parser.add_argument("--packet-sha256", required=True)
    args = parser.parse_args()
    if args.command == "run":
        return run(args.packet, args.packet_sha256)
    _, job = verify(args.packet, args.packet_sha256)
    print(json.dumps({"packet_sha256": args.packet_sha256, "verified": True, "expected_phases": job["phases"],
                      "native_processes_started": 0}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
