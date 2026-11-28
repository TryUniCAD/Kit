from __future__ import annotations

import argparse
import json
import math
from pathlib import Path, PureWindowsPath
from shutil import copyfile
import sys
import time

from AuthorCurves import Recorder, digest, require, write_json
from AuthorNestedAssemblySources import exact_file, force_rebuild, match_geometry, save_current
from NestedAssemblySourcePlan import ORACLE, TOOL_FILES, checked, matches_transform
from ReplayNestedAssemblyReopen import AUTHORED, SOURCE, inspect_case, source_cases
from SdkNestedExpectations import verify_prediction


SCHEMA = "kit.sw2026.sdk-nested-assembly-native-trial.v1"
SOURCE_LOCK = "01d38c3a89af115cf41134701888fb987513e86506f6559401ee323d9bcdc202"
PHASES = ("before", "generated", "reopen", "after")
TOOLS = (*TOOL_FILES, "ReplayIndexedAssemblyProgress.py", "ReplayNestedAssemblyReopen.py", "PredictSdkNestedAssembly.py",
         "PrepareSdkAssemblyNative.py", "SdkNestedExpectations.py", Path(__file__).name)


def load_json(path, sha, root):
    return json.loads(checked(path, sha, root).read_bytes())


def verify(path, sha):
    root = path.parent
    packet = load_json(path, sha, root)
    require(path.name == "Packet.json" and packet["schema"] == SCHEMA and packet["oracle_sha256"] == ORACLE
            and packet["source_lock_sha256"] == SOURCE_LOCK and packet["heldout_inputs_read"] == 0
            and packet["native_acceptance"] is False, "unexpected SDK nested native packet provenance")
    tools = (root / "Tools").resolve(strict=True)
    require(tools == Path(__file__).resolve().parent and set(packet["tools_sha256"]) == set(TOOLS), "run the exact frozen SDK nested observer")
    for name, wanted in packet["tools_sha256"].items():
        checked(tools / name, wanted, tools)
    checked(root / "SourceLock.json", SOURCE_LOCK, root)
    fixture = load_json(root / "Fixture.json", packet["fixture_sha256"], root)
    request = load_json(root / "NeutralRequest.json", fixture["request_sha256"], root)
    prediction = load_json(root / "Prediction.json", fixture["prediction_sha256"], root)
    work = verify_prediction(request, prediction)
    checked(root / "SourceManifest.json", fixture["source_manifest_sha256"], root)
    proof = load_json(root / "SourceProcessResult.json", fixture["source_process_result_sha256"], root)
    require(proof["passed"] and proof["source_manifest_sha256"] == fixture["source_manifest_sha256"]
            and proof["runtime_input_file_reads"] == proof["heldout_inputs_read"] == proof["native_processes_started"] == 0
            and proof["native_acceptance"] is False and fixture["native_acceptance"] is False, "unqualified SDK constructor proof")
    builds = [load_json(root / (name + ".stdout"), fixture["build_sha256"][name], root) for name in ("BuildA", "BuildB")]
    first, second = (dict(row) for row in builds)
    require(first.pop("worker_pid") != second.pop("worker_pid") and first == second and first["passed"]
            and first["runtime_input_file_reads"] == first["sdk_runtime_research_imports"] == 0, "fresh SDK nested builds differ or cross their input boundary")
    require(set(fixture["files"]) == set(prediction["definitions"]) == set(first["documents"]), "incomplete generated native dependency closure")
    for key, row in fixture["files"].items():
        target = prediction["definitions"][key]
        require(row["file"] == target["file"] and PureWindowsPath(row["encoded_path"]) == work / row["file"]
                and row["sha256"] == first["documents"][key]["sha256"] and row["bytes"] == first["documents"][key]["bytes"],
                "the native artifact identity differs from its authored target or guarded SDK proof")
        require(checked(root / "FrozenGenerated" / row["file"], row["sha256"], root).stat().st_size == row["bytes"], "generated native artifact size differs")
    require(packet["control"] in AUTHORED and packet["control_author_sha256"] == AUTHORED[packet["control"]], "unqualified nested bracket profile")
    sources = source_cases((root.parent / SOURCE).resolve(strict=True))
    return packet, fixture, request, prediction, sources[packet["control"]]


def active_configuration(author, model, expected):
    manager = author.get(model, "ConfigurationManager")
    active = author.get(manager, "ActiveConfiguration")
    require(list(author.get(model, "GetConfigurationNames") or ()) == [expected] and author.get(active, "Name") == expected,
            "the generated definition changed its independently authored active configuration")
    return active


def observe_document(author, model, path, target, tree, edited):
    import Swapp
    from AuthorAssemblySources import feature_tree

    require(exact_file(author.get(model, "GetPathName"), path), "generated definition resolves outside its owned physical file")
    active_configuration(author, model, target["configuration"])
    extension = author.get(model, "Extension")
    require(int(author.get(extension, "GetWhatsWrongCount")) == 0, "generated definition has native errors or warnings")
    expected = target["edited" if edited else "initial"]
    mass = author.rec.call("measure generated SDK definition geometry", Swapp.mass, model)
    match_geometry(mass, expected)
    native_tree = feature_tree(author, model)
    require([[row["name"], row["type"], row["parent"]] for row in native_tree] == tree
            and not any(row["suppressed"] for row in native_tree), "generated native feature tree differs from the complete authored role expansion")
    result = {"file": path.name, "sha256": digest(path), "configuration": target["configuration"], "tree": native_tree,
              "mass_properties": mass, "update_stamp": int(author.get(model, "GetUpdateStamp")), "whats_wrong": 0,
              "needs_rebuild": int(author.get(extension, "NeedsRebuild2"))}
    if target["kind"] == "part":
        dimensions = {}
        for name, value in expected["parameters_m"].items():
            parameter = author.get(model, "Parameter", name)
            if value is None:
                require(parameter is None, "the plain SDK child acquired an unauthored sketch dimension")
                dimensions[name] = None
            else:
                require(parameter is not None and author.get(parameter, "DrivenState") == 2 and not author.get(parameter, "ReadOnly"), "the authored depth lost its driving editable state")
                dimensions[name] = float(author.get(parameter, "SystemValue"))
                author.rec.close_number(name, dimensions[name], value)
        part = author.typed(model, "PartDoc")
        bodies = len(author.get(part, "GetBodies2", 0, True) or ())
        require(bodies == expected["body_count"] == 1, "generated plain child must contain one visible solid body")
        result.update(parameters_m=dimensions, body_count=bodies)
    return result


def observe_scene(author, model, paths, prediction, edited):
    scope = prediction["edited" if edited else "initial"]
    definitions = {prediction["root"]: model}
    targets = prediction["definitions"]

    def visit(native, parent_path):
        wanted = [row for row in scope["occurrences"] if row["path"][:-1] == parent_path]
        children = author.get(native, "GetChildren") or ()
        require(len(children) == len(wanted), "generated direct child count differs from the complete neutral hierarchy")
        observed = {}
        for value in children:
            component = author.typed(value, "Component2")
            path = author.get(component, "GetPathName")
            transform = author.typed(author.get(component, "Transform2"), "MathTransform")
            world = [float(number) for number in author.get(transform, "ArrayData")]
            matches = [row for row in wanted if row["path"][-1] not in observed and exact_file(path, paths[row["definition"]])
                       and matches_transform(world, row["transform"])]
            require(len(matches) == 1, "native occurrence does not match a unique authored target and independent root-context transform")
            row, = matches
            key, name = row["definition"], str(author.get(component, "Name2"))
            require(name.rsplit("/", 1)[-1] == row["path"][-1] and author.get(component, "ReferencedConfiguration") == row["configuration"]
                    and not author.get(component, "IsSuppressed") and not author.get(component, "IsHidden", False)
                    and bool(author.get(component, "IsFixed")) == row["fixed"], "generated occurrence changed its name configuration activation or fixed state")
            child = author.get(component, "GetModelDoc2")
            require(child is not None and exact_file(author.get(child, "GetPathName"), paths[key]), "generated occurrence binds the wrong physical dependency")
            definitions.setdefault(key, child)
            descendants = visit(component, row["path"])
            if row["kind"] == "part":
                bodies = len(author.get(author.typed(child, "PartDoc"), "GetBodies2", 0, True) or ())
                require(bodies == 1 and not descendants, "generated part occurrence must have one solid and no child occurrences")
            else:
                bodies = sum(item["body_count"] for item in descendants)
            observed[row["path"][-1]] = {"name": name, "target": key, "world": world, "configuration": row["configuration"],
                                         "fixed": bool(author.get(component, "IsFixed")), "children": descendants, "body_count": bodies}
        return [observed[row["path"][-1]] for row in wanted]

    active = active_configuration(author, model, scope["configuration"])
    root = author.typed(author.get(active, "GetRootComponent3", True), "Component2")
    occurrences = visit(root, [])
    assembly = author.typed(model, "AssemblyDoc")
    direct = int(author.get(assembly, "GetComponentCount", True))
    expanded = int(author.get(assembly, "GetComponentCount", False))
    require(direct == scope["direct_occurrences"] and expanded == scope["expanded_occurrences"] and set(definitions) == set(paths)
            and sum(row["body_count"] for row in occurrences) == scope["body_count"], "generated expanded hierarchy body count or dependency closure differs")
    result = {"occurrences": occurrences, "direct_occurrences": direct, "expanded_occurrences": expanded, "body_count": scope["body_count"],
              "definitions": {key: observe_document(author, native, paths[key], targets[key], prediction["trees"][key], edited) for key, native in definitions.items()}}
    return result, definitions


def generated_phase(phase, path, packet, fixture, prediction, output):
    import Swapp
    from AuthorCurves import CurveAuthor
    from ObserveAssemblyLoad import AssemblyLoadMonitor
    from OracleIdentity import application_identity

    root = path.parent
    working = root / "GeneratedInput"
    require(PureWindowsPath(str(working)) == verify_prediction(load_json(root / "NeutralRequest.json", fixture["request_sha256"], root), prediction),
            "run the SDK nested measurement at its exact encoded UNC working path")
    paths = {key: working / row["file"] for key, row in fixture["files"].items()}
    recorder = Recorder(output / "Record.json", {"phase": phase, "packet_sha256": digest(path)})
    result, controller = {"passed": False, "mode": phase}, None
    with AssemblyLoadMonitor() as monitor:
        try:
            recorder.call("verify idle oracle", Swapp.sweep)
            if phase == "generated":
                working.mkdir(exist_ok=False)
                for row in fixture["files"].values():
                    copyfile(root / "FrozenGenerated" / row["file"], working / row["file"])
                require(all(digest(paths[key]) == row["sha256"] for key, row in fixture["files"].items()), "working SDK inputs differ before native open")
            else:
                previous = json.loads((root / "Inspection/generated/Record.json").read_bytes())
                require(previous["passed"] and previous["job"]["packet_sha256"] == digest(path), "fresh reopen requires the passed synchronized save phase")
                saved = previous["result"]["saved_files"]
                require(set(saved) == set(paths) and all(digest(paths[key]) == row["sha256"] for key, row in saved.items()), "saved SDK dependencies changed before fresh reopen")
            controller = recorder.call("launch fresh owned oracle", Swapp.Sw)
            identity = recorder.call("verify executable version and hash", application_identity, controller.app)
            result["oracle_identity"] = identity
            require(identity["version_matches"] and identity["sha256"] == ORACLE and controller.revision == "34.5.2", "unexpected native oracle build")
            author = CurveAuthor(controller.app, recorder, Swapp)
            model, errors, warnings = recorder.call("open exact SDK nested root", controller.open, paths[prediction["root"]], read_only=phase == "reopen")
            result.update(open_errors=errors, open_warnings=warnings)
            require(model is not None and errors == warnings == 0, "SDK nested root failed or warned on open")
            edited = phase == "reopen"
            result["initial"], loaded = observe_scene(author, model, paths, prediction, edited)
            for key in prediction["save_order"]:
                force_rebuild(author, loaded[key])
            result["rebuilt"], loaded = observe_scene(author, model, paths, prediction, edited)
            if phase == "generated":
                edit = prediction["edit"]
                parameter = author.get(loaded[edit["part"]], "Parameter", edit["parameter"])
                require(parameter is not None, "generated leaf has no exact authored driving depth")
                author.set(parameter, "SystemValue", edit["depth_m"])
                for key in prediction["save_order"]:
                    force_rebuild(author, loaded[key])
                result["edited"], loaded = observe_scene(author, model, paths, prediction, True)
                require(result["initial"]["definitions"][prediction["root"]]["mass_properties"]["volume"] != result["edited"]["definitions"][prediction["root"]]["mass_properties"]["volume"],
                        "the driving leaf edit left the measured root unchanged")
                saved = result["saved_files"] = {}
                for key in prediction["save_order"]:
                    saved[key] = save_current(author, loaded[key], paths[key], working)
                    require(all(digest(paths[prior]) == row["sha256"] and int(author.get(loaded[prior], "GetUpdateStamp")) == row["update_stamp"] for prior, row in saved.items()),
                            "parent save changed an already synchronized dependency")
            else:
                require(all(result["initial"]["definitions"][key]["update_stamp"] == row["update_stamp"] for key, row in saved.items()), "fresh reopen bound a different persisted update stamp")
            require(all(digest(paths[key]) == row["sha256"] for key, row in saved.items()), "measured SDK derivative changed after its save")
            result["passed"] = True
        except Exception as error:
            recorder.failure(error)
            result["exception"] = repr(error)
        finally:
            if controller is not None:
                controller.close()
                result["controller_diagnostics"] = controller.diagnostics
    result["dialogs"], result["progress_windows"] = monitor.log, monitor.progress
    result["passed"] = bool(result["passed"] and not result["dialogs"] and not result.get("controller_diagnostics") and not recorder.data["cleanup_errors"])
    recorder.data.update(result=result, passed=result["passed"], finished_at=time.time())
    recorder.flush()
    return result


def run_phase(path, sha, phase):
    require(sys.platform == "win32", "native SDK nested phases run only in the Windows guest")
    packet, fixture, _, prediction, source = verify(path, sha)
    output = path.parent / "Inspection" / phase
    output.mkdir(parents=True, exist_ok=False)
    if phase in ("before", "after"):
        started = time.time()
        record = output / "Record.json"
        write_json(record, {"passed": False, "job": {"phase": phase, "packet_sha256": sha}, "started_at": started})
        result = inspect_case(*source, output)
        result["mode"] = phase
        write_json(record, {"passed": result["passed"], "job": {"phase": phase, "packet_sha256": sha}, "result": result,
                            "started_at": started, "finished_at": time.time()})
    else:
        before = json.loads((path.parent / "Inspection/before/Record.json").read_bytes())
        require(before["passed"] and before["job"]["packet_sha256"] == sha, "generated measurement requires its healthy exact before control")
        result = generated_phase(phase, path, packet, fixture, prediction, output)
    return {"phase": phase, "passed": result["passed"], "open_errors": result.get("open_errors"), "open_warnings": result.get("open_warnings")}


def summarize(path, sha):
    _, fixture, _, prediction, _ = verify(path, sha)
    rows = []
    for phase in PHASES:
        record = path.parent / "Inspection" / phase / "Record.json"
        if not record.is_file():
            rows.append({"mode": phase, "passed": False, "record_missing": True})
            continue
        value = json.loads(record.read_bytes())
        require(value["job"]["packet_sha256"] == sha, "SDK nested native result belongs to a different frozen packet")
        rows.append(value.get("result", {"mode": phase, "passed": False, "record_incomplete": True})
                    | {"record_sha256": digest(record), "started_at": value.get("started_at"), "finished_at": value.get("finished_at")})
    births = {row.get("oracle_identity", {}).get("process_creation_filetime") for row in rows}
    count = sum(type(value) is int and value > 0 for value in births)
    controls = [row["passed"] for row in rows if row["mode"] in ("before", "after")] == [True, True]
    ordered = all(type(a.get("finished_at")) in (int, float) and type(b.get("started_at")) in (int, float)
                  and a["finished_at"] <= b["started_at"] for a, b in zip(rows, rows[1:]))
    saved = rows[1].get("saved_files", {})
    match = set(saved) == set(fixture["files"]) and all((file := path.parent / "GeneratedInput" / fixture["files"][key]["file"]).is_file()
                                                       and digest(file) == row["sha256"] for key, row in saved.items())
    result = {"schema": SCHEMA, "packet_sha256": sha, "fixture_sha256": digest(path.parent / "Fixture.json"), "oracle_sha256": ORACLE,
              "source_lock_sha256": SOURCE_LOCK, "source_manifest_sha256": fixture["source_manifest_sha256"], "prediction_sha256": fixture["prediction_sha256"],
              "root": prediction["root"], "controls_healthy": controls, "distinct_processes": count, "bracket_order_verified": ordered,
              "frozen_inputs_unchanged": True, "synchronized_derivative_files_match": match, "heldout_inputs_read": 0, "phases": rows,
              "passed": bool(controls and count == 4 and ordered and match and all(row["passed"] for row in rows))}
    write_json(path.parent / "Inspection/Result.json", result)
    return {key: result[key] for key in ("passed", "controls_healthy", "distinct_processes")}


def main():
    parser = argparse.ArgumentParser(description="Measure complete SDK nested hierarchies with independent geometry, live leaf editing and synchronized persistence")
    parser.add_argument("command", choices=("verify", "run", "summarize"))
    parser.add_argument("packet", type=Path)
    parser.add_argument("phase", choices=PHASES, nargs="?")
    parser.add_argument("--packet-sha256", required=True)
    args = parser.parse_args()
    path = args.packet.resolve(strict=True)
    if args.command == "verify":
        verify(path, args.packet_sha256)
        print('{"passed": true, "native_processes_started": 0}')
        return 0
    require(args.command != "run" or args.phase is not None, "a native run requires one explicit independent phase")
    result = run_phase(path, args.packet_sha256, args.phase) if args.command == "run" else summarize(path, args.packet_sha256)
    print(json.dumps(result, sort_keys=True))
    return int(not result["passed"])


if __name__ == "__main__":
    raise SystemExit(main())
