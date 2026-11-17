from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
import sys
import time
from pathlib import Path, PureWindowsPath
from shutil import copyfile

from AuthorCurves import Recorder, digest, require, write_json
from AuthorNestedAssemblySources import active_configuration, edit_depth, exact_file, force_rebuild, match_geometry, save_current
from NestedAssemblySourcePlan import ORACLE, TOOL_FILES, checked, matches_transform
from PredictNestedAssembly import predict
from ReplayNestedAssemblyReopen import AUTHORED, inspect_case, source_cases


SCRIPT = Path(__file__).resolve()
CHECKOUT = SCRIPT.parents[3]
PHASES = ("before", "generated", "reopen", "after")
TOOLS = (*TOOL_FILES, "ReplayIndexedAssemblyProgress.py", "ReplayNestedAssemblyReopen.py", "PredictNestedAssembly.py", SCRIPT.name)
SCHEMA = "kit.sw2026.generated-nested-assembly-native-trial.v1"
SOURCE_LOCK = "01d38c3a89af115cf41134701888fb987513e86506f6559401ee323d9bcdc202"
WRITER_EVIDENCE = "2539defed11f4fffd6c84d4caf0297895b5f24d1fb1cb6f123b83dd1b5840560"
SOURCE = Path("NestedAssemblySource01") / "Results"
WORK_DIRECTORY = PureWindowsPath(r"\\Mac\Home\Documents\UniCAD\Oracle121Takeover\GeneratedNestedAssembly01\GeneratedInput")


def json_file(path, expected, owner):
    return json.loads(checked(path, expected, owner).read_bytes())


def definition_order(bundle):
    definitions = {row["id"]: row for row in bundle["definitions"]}
    result = []
    visiting = set()

    def visit(key):
        if key in result:
            return
        require(key in definitions and key not in visiting, "invalid native trial dependency graph")
        visiting.add(key)
        row = definitions[key]
        if row["kind"] == "assembly":
            for item in row["occurrences"]:
                visit(item["target"])
        result.append(key)
        visiting.remove(key)

    visit(bundle["root"])
    require(len(result) == len(definitions), "native trial contains an unreachable definition")
    return result


def validate_prediction(bundle, prediction):
    request = {"bundle": bundle, "edit": prediction["edit"]}
    require(json.loads(json.dumps(predict(request), allow_nan=False)) == prediction, "native geometry prediction does not follow from the neutral bundle")
    definitions = prediction["definitions"]
    require(prediction["schema"] == "kit.sw2026.generated-nested-prism-prediction.v1" and
            all(row["configuration"] == "Default" for row in definitions.values()), "the first native trial requires independent Default configurations")
    by_id = {row["id"]: row for row in bundle["definitions"]}
    for key in definition_order(bundle):
        spec = by_id[key]
        file = prediction["definitions"][key]["file"]
        require(PureWindowsPath(spec["request"]["output"]["path_name"]) == WORK_DIRECTORY / file and Path(file).name == file,
                "generated native references must point into their exact owned working directory")
        if spec["kind"] == "part":
            require("rectangle_dimensions" in spec["request"]["document"], "native leaf proof requires both authored driving sketch dimensions")
    root = definitions[prediction["root"]]
    require(root["initial"]["total_occurrences"] >= 2 and root["initial"]["body_count"] > 0 and
            root["initial"]["volume"] != root["edited"]["volume"], "the native leaf edit must change the expanded root geometry")


def prepare(args):
    output = args.output.resolve()
    require(output.name == "GeneratedNestedAssembly01" and output.parent.is_dir() and not output.exists() and
            not output.is_relative_to(CHECKOUT), "choose the unused private GeneratedNestedAssembly01 packet")
    source = args.source.resolve(strict=True)
    require(source == output.parent / SOURCE, "keep the disclosed source at its exact original path")
    source_cases(source)
    build = args.build.resolve(strict=True)
    require(not build.is_relative_to(CHECKOUT) and build != output, "keep the generated build private and independent")
    request = json.loads((build / "Request.json").read_bytes())
    prediction = json.loads((build / "Expected.json").read_bytes())
    report = json.loads((build / "SanitizedBuild.json").read_bytes())
    evidence_path = CHECKOUT / "re/solidworks/measurements/2026/GeneratedNestedAssemblyBundle01.json"
    evidence = json_file(evidence_path, WRITER_EVIDENCE, CHECKOUT)
    lock_path = CHECKOUT / "re/solidworks/v2026/heldout/NestedAssemblySourceLock01.json"
    checked(lock_path, SOURCE_LOCK, CHECKOUT)
    require(re.fullmatch(r"[0-9a-f]{40}", args.writer_revision) and report["source_lock_sha256"] == SOURCE_LOCK and report["native_acceptance"] is False and
            report["input_runtime_file_access_attempts"] == report["heldout_inputs_tested"] == 0 and
            set(report["documents"]) == set(prediction["definitions"]) == set(evidence["documents"]), "generated native trial evidence differs")
    require(digest(build / "Request.json") == evidence["request_sha256"] and digest(build / "Expected.json") == evidence["prediction_sha256"],
            "native trial request or independent prediction changed")
    for name, sha in evidence["writer_tool_sha256"].items():
        checked(SCRIPT.parent / name, sha, SCRIPT.parent)
    validate_prediction(request, prediction)
    files = {}
    for key, row in report["documents"].items():
        spec = evidence["documents"][key]
        require((row["sha256"], row["bytes"]) == (spec["sha256"], spec["bytes"]), "generated report differs from its scoped proof")
        path = checked(build / "Generated" / prediction["definitions"][key]["file"], row["sha256"], build)
        require(path.stat().st_size == row["bytes"], "generated native input length changed")
        files[key] = {"file": path.name, "bytes": row["bytes"], "sha256": row["sha256"]}
    output.mkdir()
    tools = output / "Tools"
    tools.mkdir()
    frozen = output / "FrozenGenerated"
    frozen.mkdir()
    for row in files.values():
        copyfile(build / "Generated" / row["file"], frozen / row["file"])
    for source_path, target in ((build / "Request.json", "Request.json"), (build / "Expected.json", "Expected.json"),
                                (build / "SanitizedBuild.json", "GeneratorReport.json"), (evidence_path, "WriterEvidence.json"), (lock_path, "SourceLock.json")):
        copyfile(source_path, output / target)
    tool_hashes = {}
    for name in TOOLS:
        copyfile(SCRIPT.parent / name, tools / name)
        tool_hashes[name] = digest(tools / name)
    packet = output / "Trial.json"
    write_json(packet, {"schema": SCHEMA, "oracle_sha256": ORACLE, "source_lock_sha256": SOURCE_LOCK,
                        "writer_revision": args.writer_revision, "writer_evidence_sha256": WRITER_EVIDENCE,
                        "writer_tool_sha256": evidence["writer_tool_sha256"], "tool_sha256": tool_hashes, "files": files,
                        "request_sha256": digest(output / "Request.json"), "prediction_sha256": digest(output / "Expected.json"),
                        "generator_report_sha256": digest(output / "GeneratorReport.json"), "control_author_sha256": AUTHORED["N01NestedSingle"],
                        "heldout_inputs_read": 0, "native_acceptance": False})
    sha = digest(packet)
    subprocess.run([sys.executable, "-B", str(tools / SCRIPT.name), "verify", str(packet), "--packet-sha256", sha], check=True, capture_output=True, timeout=25)
    return {"packet": str(packet), "packet_sha256": sha, "observer_sha256": tool_hashes[SCRIPT.name]}


def verify(path, sha):
    root = path.parent
    require(path.name == "Trial.json" and checked(path, sha, root) == path, "native nested trial manifest is not pinned")
    packet = json.loads(path.read_bytes())
    require(packet["schema"] == SCHEMA and packet["oracle_sha256"] == ORACLE and packet["source_lock_sha256"] == SOURCE_LOCK and
            packet["writer_evidence_sha256"] == WRITER_EVIDENCE and packet["heldout_inputs_read"] == 0 and packet["native_acceptance"] is False and
            re.fullmatch(r"[0-9a-f]{40}", packet["writer_revision"]), "unexpected native nested trial provenance")
    tools = (root / "Tools").resolve(strict=True)
    require(tools == SCRIPT.parent and tools.is_relative_to(root) and set(packet["tool_sha256"]) == set(TOOLS), "run the exact frozen native nested tooling")
    for name, wanted in packet["tool_sha256"].items():
        checked(tools / name, wanted, tools)
    checked(root / "SourceLock.json", SOURCE_LOCK, root)
    evidence = json_file(root / "WriterEvidence.json", WRITER_EVIDENCE, root)
    require(packet["writer_tool_sha256"] == evidence["writer_tool_sha256"] and packet["control_author_sha256"] == AUTHORED["N01NestedSingle"],
            "native nested writer or disclosed control identity differs")
    bundle = json_file(root / "Request.json", packet["request_sha256"], root)
    prediction = json_file(root / "Expected.json", packet["prediction_sha256"], root)
    json_file(root / "GeneratorReport.json", packet["generator_report_sha256"], root)
    validate_prediction(bundle, prediction)
    require(set(packet["files"]) == set(prediction["definitions"]), "native trial has an incomplete file closure")
    for key, row in packet["files"].items():
        require(row["file"] == prediction["definitions"][key]["file"] and row["sha256"] == evidence["documents"][key]["sha256"] and
                row["bytes"] == evidence["documents"][key]["bytes"], "native trial file does not match its writer proof")
        checked(root / "FrozenGenerated" / row["file"], row["sha256"], root)
    return packet, bundle, prediction, source_cases(root.parent / SOURCE)


def observe_document(author, model, path, prediction):
    import Swapp
    from AuthorAssemblySources import feature_tree

    require(exact_file(author.get(model, "GetPathName"), path), "generated definition resolves outside its owned native file")
    active_configuration(author, model)
    extension = author.get(model, "Extension")
    require(int(author.get(extension, "GetWhatsWrongCount")) == 0, "generated definition has native warnings or errors")
    properties = author.rec.call("measure generated native definition", Swapp.mass, model)
    match_geometry(properties, prediction)
    result = {"file": path.name, "sha256": digest(path), "update_stamp": int(author.get(model, "GetUpdateStamp")),
              "mass_properties": properties, "tree": feature_tree(author, model), "whats_wrong": 0,
              "needs_rebuild": int(author.get(extension, "NeedsRebuild2"))}
    if "dimensions_m" in prediction:
        for name in prediction["dimensions_m"]:
            require(author.get(model, "Parameter", name) is not None, "generated leaf has no authored driving parameter")
        dimensions = author.rec.call("read generated prism driving dimensions", Swapp.parameters, model, tuple(prediction["dimensions_m"]))
        require(all(type(dimensions.get(name)) in (float, int) and math.isclose(dimensions[name], wanted, rel_tol=0, abs_tol=1e-12)
                    for name, wanted in prediction["dimensions_m"].items()), "generated prism driving dimensions differ from their authored values")
        part = author.typed(model, "PartDoc")
        bodies = len(author.get(part, "GetBodies2", 0, True) or ())
        require(bodies == 1, "generated leaf must contain one visible solid body")
        result["dimensions_m"] = dimensions
        result["body_count"] = bodies
    return result


def observe_scene(author, model, paths, prediction, edited):
    root_key = prediction["root"]
    shapes = {key: row["edited" if edited else "initial"] for key, row in prediction["definitions"].items()}
    definitions = {root_key: model}

    def visit(native, predicted):
        values = author.get(native, "GetChildren") or ()
        require(len(values) == len(predicted), "generated hierarchy has an unexpected direct child count")
        rows = {}
        for value in values:
            component = author.typed(value, "Component2")
            path = author.get(component, "GetPathName")
            transform = author.typed(author.get(component, "Transform2"), "MathTransform")
            world = [float(number) for number in author.get(transform, "ArrayData")]
            candidates = [row for row in predicted if row["ordinal"] not in rows and exact_file(path, paths[row["target"]]) and matches_transform(world, row["world"])]
            require(len(candidates) == 1, "generated occurrence does not match one independent target and root-context transform")
            wanted, = candidates
            name = str(author.get(component, "Name2"))
            target = wanted["target"]
            require(name.rsplit("/", 1)[-1] == wanted["name"] and author.get(component, "ReferencedConfiguration") == "Default" and
                    not author.get(component, "IsSuppressed") and not author.get(component, "IsHidden", False), "generated occurrence has an unexpected identity or activation state")
            child = author.get(component, "GetModelDoc2")
            require(child is not None and exact_file(author.get(child, "GetPathName"), paths[target]), "generated occurrence binds the wrong physical model")
            definitions.setdefault(target, child)
            children = visit(component, wanted["children"])
            if prediction["definitions"][target]["kind"] == "part":
                native_part = author.typed(child, "PartDoc")
                bodies = len(author.get(native_part, "GetBodies2", 0, True) or ())
                require(bodies == 1, "generated part occurrence must contain one solid body")
            else:
                bodies = sum(row["body_count"] for row in children)
            rows[wanted["ordinal"]] = {"name": name, "target": target, "world": world, "fixed": bool(author.get(component, "IsFixed")),
                                       "children": children, "body_count": bodies}
        return [rows[index] for index in range(len(predicted))]

    active = active_configuration(author, model)
    root = author.typed(author.get(active, "GetRootComponent3", True), "Component2")
    occurrences = visit(root, shapes[root_key]["children"])
    assembly = author.typed(model, "AssemblyDoc")
    require(int(author.get(assembly, "GetComponentCount", True)) == len(occurrences) and
            int(author.get(assembly, "GetComponentCount", False)) == shapes[root_key]["total_occurrences"] and
            set(definitions) == set(paths) and sum(row["body_count"] for row in occurrences) == shapes[root_key]["body_count"],
            "generated expanded hierarchy or dependency closure differs")
    result = {"occurrences": occurrences, "definitions": {key: observe_document(author, native, paths[key], shapes[key]) for key, native in definitions.items()},
              "total_occurrences": int(author.get(assembly, "GetComponentCount", False)), "body_count": sum(row["body_count"] for row in occurrences)}
    return result, definitions


def generated_phase(phase, packet_path, packet, bundle, prediction, output):
    import Swapp
    from AuthorCurves import CurveAuthor
    from ObserveAssemblyLoad import AssemblyLoadMonitor
    from OracleIdentity import application_identity

    root = packet_path.parent
    working = root / "GeneratedInput"
    paths = {key: working / row["file"] for key, row in packet["files"].items()}
    require(PureWindowsPath(str(working)) == WORK_DIRECTORY, "run the generated trial at its exact encoded UNC path")
    recorder = Recorder(output / "Record.json", {"phase": phase, "packet_sha256": digest(packet_path)})
    result = {"passed": False, "mode": phase}
    controller = None
    with AssemblyLoadMonitor() as monitor:
        try:
            recorder.call("verify idle oracle", Swapp.sweep)
            if phase == "generated":
                working.mkdir(exist_ok=False)
                for row in packet["files"].values():
                    copyfile(root / "FrozenGenerated" / row["file"], working / row["file"])
                require(all(digest(paths[key]) == row["sha256"] for key, row in packet["files"].items()), "working files differ from the generated source")
            else:
                previous = json.loads((root / "Inspection/generated/Record.json").read_bytes())
                require(previous["passed"] and previous["job"]["packet_sha256"] == digest(packet_path), "generated save phase did not pass")
                saved = previous["result"]["saved_files"]
                require(set(saved) == set(paths) and all(digest(paths[key]) == row["sha256"] for key, row in saved.items()), "saved generated dependencies changed before fresh reopen")
            controller = recorder.call("launch fresh owned oracle", Swapp.Sw)
            identity = recorder.call("verify executable version and SHA-256", application_identity, controller.app)
            require(identity["version_matches"] and identity["sha256"] == ORACLE and controller.revision == "34.5.2", "unexpected native build")
            result["oracle_identity"] = identity
            author = CurveAuthor(controller.app, recorder, Swapp)
            model, errors, warnings = recorder.call("open exact generated nested root", controller.open, paths[prediction["root"]], read_only=phase == "reopen")
            result.update(open_errors=errors, open_warnings=warnings)
            require(model is not None and errors == warnings == 0, "generated native root failed or warned on open")
            edited = phase == "reopen"
            result["initial"], loaded = observe_scene(author, model, paths, prediction, edited)
            order = definition_order(bundle)
            for key in order:
                force_rebuild(author, loaded[key])
            result["rebuilt"], loaded = observe_scene(author, model, paths, prediction, edited)
            if phase == "generated":
                edit = prediction["edit"]
                edit_depth(author, loaded[edit["part"]], edit["depth_m"])
                for key in order:
                    force_rebuild(author, loaded[key])
                result["edited"], loaded = observe_scene(author, model, paths, prediction, True)
                require(result["initial"]["definitions"][prediction["root"]]["mass_properties"]["volume"] !=
                        result["edited"]["definitions"][prediction["root"]]["mass_properties"]["volume"], "driving depth edit left the measured root unchanged")
                saved = result["saved_files"] = {}
                for key in order:
                    saved[key] = save_current(author, loaded[key], paths[key], working)
                    require(all(digest(paths[prior]) == row["sha256"] and int(author.get(loaded[prior], "GetUpdateStamp")) == row["update_stamp"]
                                for prior, row in saved.items()), "parent save changed an already synchronized dependency")
                write_json(root / "Inspection/generated/SavedState.json", {"files": saved, "edited_depth_m": edit["depth_m"]})
            else:
                require(all(result["initial"]["definitions"][key]["update_stamp"] == row["update_stamp"] for key, row in saved.items()), "fresh reopen bound a different persisted update stamp")
            require(all(digest(paths[key]) == row["sha256"] for key, row in saved.items()), "generated native file state changed after its measurement")
            result["passed"] = True
        except Exception as error:
            recorder.failure(error)
            result["exception"] = repr(error)
        finally:
            if controller is not None:
                controller.close()
                result["controller_diagnostics"] = controller.diagnostics
    result["dialogs"] = monitor.log
    result["progress_windows"] = monitor.progress
    result["passed"] = bool(result["passed"] and not result["dialogs"] and not result.get("controller_diagnostics") and not recorder.data["cleanup_errors"])
    recorder.data.update(result=result, passed=result["passed"], finished_at=time.time())
    recorder.flush()
    return result


def run_phase(path, sha, phase):
    require(sys.platform == "win32", "native nested phases run only in the Windows guest")
    packet, bundle, prediction, sources = verify(path, sha)
    output = path.parent / "Inspection" / phase
    output.mkdir(parents=True, exist_ok=False)
    if phase in ("before", "after"):
        record = output / "Record.json"
        started = time.time()
        write_json(record, {"stage": "native_control", "passed": False, "job": {"phase": phase, "packet_sha256": sha}, "started_at": started})
        case, paths, prior = sources["N01NestedSingle"]
        result = inspect_case(case, paths, prior, output)
        result["mode"] = phase
        write_json(record, {"stage": "complete", "passed": result["passed"], "job": {"phase": phase, "packet_sha256": sha},
                            "result": result, "started_at": started, "finished_at": time.time()})
    else:
        if phase == "generated":
            before = json.loads((path.parent / "Inspection/before/Record.json").read_bytes())
            require(before["passed"] and before["job"]["packet_sha256"] == sha, "generated phase requires its healthy before control")
        result = generated_phase(phase, path, packet, bundle, prediction, output)
    return {"phase": phase, "passed": result["passed"], "open_errors": result.get("open_errors"), "open_warnings": result.get("open_warnings")}


def summarize(path, sha):
    packet, _, prediction, _ = verify(path, sha)
    results = []
    for phase in PHASES:
        record = path.parent / "Inspection" / phase / "Record.json"
        if not record.is_file():
            results.append({"mode": phase, "passed": False, "record_missing": True})
            continue
        observed = json.loads(record.read_bytes())
        require(observed["job"]["packet_sha256"] == sha, "native result belongs to another packet")
        if "result" not in observed:
            results.append({"mode": phase, "passed": False, "record_incomplete": True, "record_sha256": digest(record)})
            continue
        results.append(observed["result"] | {"record_sha256": digest(record), "started_at": observed["started_at"], "finished_at": observed["finished_at"]})
    identifiers = {row.get("oracle_identity", {}).get("process_creation_filetime") for row in results}
    distinct = sum(type(value) is int and value > 0 for value in identifiers)
    controls = [row["passed"] for row in results if row["mode"] in ("before", "after")] == [True, True]
    saved = results[1].get("saved_files", {})
    edited_files_match = set(saved) == set(packet["files"]) and all((native := path.parent / "GeneratedInput" / packet["files"][key]["file"]).is_file() and
                                                                       digest(native) == row["sha256"] for key, row in saved.items())
    bracket_order = all(first.get("finished_at", float("inf")) <= second.get("started_at", float("-inf")) for first, second in zip(results, results[1:]))
    result = {"schema": SCHEMA, "packet_sha256": sha, "writer_revision": packet["writer_revision"], "writer_tool_sha256": packet["writer_tool_sha256"],
              "source_lock_sha256": SOURCE_LOCK, "prediction_sha256": packet["prediction_sha256"], "oracle_sha256": ORACLE,
              "heldout_inputs_read": 0, "generated_input_files_immutable": True, "synchronized_derivative_files_match": edited_files_match,
              "controls_healthy": controls, "distinct_processes": distinct, "phases": results, "bracket_order_verified": bracket_order,
              "passed": controls and distinct == 4 and bracket_order and edited_files_match and all(row["passed"] for row in results),
              "root": prediction["root"]}
    write_json(path.parent / "Inspection/NestedAssemblyResults.json", result)
    return {key: result[key] for key in ("passed", "controls_healthy", "distinct_processes")}


def main():
    parser = argparse.ArgumentParser(description="Freeze and measure the first generated ordinary nested prism bundle")
    modes = parser.add_subparsers(dest="mode", required=True)
    freezer = modes.add_parser("prepare")
    for name in ("source", "build", "output"):
        freezer.add_argument(name, type=Path)
    freezer.add_argument("--writer-revision", required=True)
    for mode in ("verify", "run", "summarize"):
        command = modes.add_parser(mode)
        command.add_argument("manifest", type=Path)
        command.add_argument("--packet-sha256", required=True)
        if mode == "run":
            command.add_argument("phase", choices=PHASES)
    args = parser.parse_args()
    if args.mode == "prepare":
        print(json.dumps(prepare(args), sort_keys=True))
        return 0
    path = args.manifest.resolve(strict=True)
    if args.mode == "verify":
        verify(path, args.packet_sha256)
        print(json.dumps({"verified_packet": args.packet_sha256}))
        return 0
    result = run_phase(path, args.packet_sha256, args.phase) if args.mode == "run" else summarize(path, args.packet_sha256)
    print(json.dumps(result, sort_keys=True))
    return int(not result["passed"])


if __name__ == "__main__":
    raise SystemExit(main())
