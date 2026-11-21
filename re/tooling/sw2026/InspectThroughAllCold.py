from __future__ import annotations

from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path, PureWindowsPath
import time

SCHEMA = "kit.sw2026.generated-through-all-native.v1"
ORACLE = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
PHASES = ("ControlBefore", "Generated", "Reopen", "ControlAfter")


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def checked(root, relative, expected):
    path = (root / relative).resolve(strict=True)
    require(path.is_relative_to(root.resolve()) and path.is_file() and digest(path) == expected, "frozen through-all input or tool changed: " + relative)
    return path


def original_root(root, job):
    binding = job.get("original_native_inputs")
    if binding is None:
        return root
    require(binding["packet_name"] == "GeneratedThroughAll01", "the retry must preserve its declared original native input custody")
    source = root.parent / binding["packet_name"]
    prior = json.loads(checked(source, "Trial.json", binding["packet_sha256"]).read_bytes())
    for relative, expected in prior["files_sha256"].items():
        checked(source, relative, expected)
        require(job["files_sha256"][relative] == expected, "the observer retry changed original input or prediction bytes")
    require(job["control_file"] == prior["control_file"] and job["generated_file"] == prior["generated_file"], "the observer retry changed a selected native input")
    return source


def read_packet(path, expected):
    root = path.parent.resolve(strict=True)
    job = json.loads(checked(root, path.name, expected).read_bytes())
    require(job["schema"] == SCHEMA and job["oracle_sha256"] == ORACLE and job["heldout_payloads_read"] == 0, "expected the exact disclosed through-all native packet")
    require(Path(__file__).resolve().parent == root / "Tools", "use the packet's exact frozen observer")
    require(all(PureWindowsPath(key).as_posix() == key and not PureWindowsPath(key).is_absolute() for key in job["files_sha256"]), "frozen packet keys require relative POSIX spelling on every host")
    require(job["control_file"] in job["files_sha256"] and job["generated_file"] in job["files_sha256"], "native selection must retain the declared packet key")
    for relative, fingerprint in {**job["files_sha256"], **{"Tools/" + key: value for key, value in job["tools_sha256"].items()}}.items():
        checked(root, relative, fingerprint)
    proof = json.loads((root / "BuildProof.json").read_bytes())
    require(proof["passed"] and proof["workers"] == 31 and not proof["native_acceptance"] and not proof["heldout_payloads_read"], "the cold process proof differs")
    case = json.loads((root / "GeneratedCase.json").read_bytes())
    control = json.loads((root / "ControlCase.json").read_bytes())
    requested = PureWindowsPath(case["recipe"]["native_path"])
    require(requested.name == job["generated_file"].split("/")[-1] and requested.parent.name == "GeneratedInput", "the encoded generated file identity differs")
    source = original_root(root, job)
    if job.get("original_native_inputs") is not None:
        require(source.name == requested.parent.parent.name and case["recipe"]["native_path"] == job["original_native_inputs"]["encoded_generated_path"], "the original encoded generated pathname changed")
    return root, job, case, control


def ui_tree(state):
    return [[row["name"], row["type"], row["parent"]] for row in state["tree"]]


def native_case(case):
    recipe = case["recipe"]
    return {"plane": {"x": "right", "y": "top", "z": "front"}[recipe["axis"]], "operation": "cut", "direction": recipe["direction"], "stock_size_m": recipe["stock_size_m"], "stock_center_m": recipe["stock_center_m"], "circle_center_m": recipe["circle_center_m"], "radius_m": recipe["radius_m"], "edit_stock_depth_m": case["prediction"]["edited"]["stock_depth_m"]}


def api_metadata():
    import ThroughAllApiMetadata as api

    api.MEMBERS = {**api.MEMBERS, "IModelDoc2": tuple(dict.fromkeys((*api.MEMBERS["IModelDoc2"], "GetPathName", "GetActiveConfiguration"))), "ISketch": tuple(dict.fromkeys((*api.MEMBERS["ISketch"], "RelationManager"))), "ISketchRelationManager": ("GetRelationsCount", "GetRelations"), "ISketchRelation": ("GetRelationType",)}
    return api.metadata()


def snapshot(author, case, *, edited, rebuild):
    if rebuild:
        require(bool(author.get(author.model, "ForceRebuild3", False)), "generated through-all rebuild failed")
    native = native_case(case)
    target = case["prediction"]["edited" if edited else "source"]
    bodies = author.rec.call("measure initial actual solid body count", author.sw.bodies, author.model)
    require(bodies == target["body_count"] == 1, "through-all part has no actual single solid")
    wrong = int(author.get(author.get(author.model, "Extension"), "GetWhatsWrongCount"))
    require(wrong == 0, "through-all part contains errors or warnings")
    configuration = str(author.get(author.get(author.model, "GetActiveConfiguration"), "Name"))
    require(configuration == case["recipe"]["configuration"], "actual native configuration differs")
    tree = author.feature_tree(required_names=("StockProfile", "StockBoss", "ThroughProfile", "ThroughFeature"))
    require([[row["name"], row["type"], row["parent"]] for row in tree] == case["expected_tree"] and not any(row["suppressed"] for row in tree), "the complete ordered through-all feature tree differs")
    stock, cut = author.definition("StockBoss"), author.definition("ThroughFeature")
    require(stock["fallback_type"] in ("Boss", "Extrusion", "BaseBody") and stock["end_forward"] == 6 and not stock["both_directions"] and not stock["thin"], "stock lost its actual mid-plane boss")
    require(cut["fallback_type"] == "Cut" and cut["type"] == "ICE", "generated operation is not its real ordinary cut")
    both = native["direction"] == "both"
    require(cut["end_forward"] == 1 and cut["end_reverse"] == int(both) and cut["both_directions"] == both and cut["reverse_direction"] == (native["direction"] != "reverse"), "actual through-all termination or direction differs")
    require(cut["depth_forward_m"] == cut["depth_reverse_m"] == 0 and cut["dimensions"] == [], "through-all cut acquired a distance driver")
    require(cut["from_type"] == 0 and not any(cut[key] for key in ("thin", "draft_forward", "draft_reverse", "flip_side_to_cut", "normal_cut")), "through-all cut acquired unsupported end or removal state")
    require("StockBoss" in cut["parents"] and "ThroughProfile" in cut["parents"], "through-all cut lost its actual stock or profile dependency")
    author.rec.close_number("stock total mid-plane driving depth", stock["depth_forward_m"], target["stock_depth_m"])
    parameter = author.get(author.model, "Parameter", "D1@StockBoss")
    require(parameter is not None and str(author.get(parameter, "FullName")).split("@")[1:2] == ["StockBoss"] and not author.get(parameter, "ReadOnly") and int(author.get(parameter, "DrivenState")) == 2, "stock D1 is not its actual editable driver")
    author.rec.close_number("stock driving parameter identity and value", author.get(parameter, "SystemValue"), target["stock_depth_m"])
    profiles = author.profiles(native)
    axis_types = []
    for name, count in (("StockProfile", 4), ("ThroughProfile", 0)):
        sketch = author.get(author.feature(name), "GetSpecificFeature2")
        relations = author.get(sketch, "RelationManager")
        require(int(author.get(relations, "GetRelationsCount", 0)) == count and author.owned_dimensions(name) == [], "sketch acquired missing or unmodeled dimensions or relations")
        values = author.get(relations, "GetRelations", 0) or ()
        observed = [int(author.get(value, "GetRelationType")) for value in values]
        require(len(observed) == count, "actual sketch relation array count differs")
        if name == "StockProfile":
            axis_types = sorted(observed)
    mass = author.rec.call("measure independently predicted through-all mass properties", author.sw.mass, author.model)
    require(mass is not None and "error" not in mass, "native through-all mass is unavailable")
    author.rec.close_number("through-all volume", mass["volume"], target["volume"], absolute=1e-22)
    author.rec.close_number("through-all area", mass["area"], target["area"], absolute=1e-18)
    for index, (actual, expected) in enumerate(zip(mass["com"], target["com"], strict=True)):
        author.rec.close_number("through-all centroid " + str(index), actual, expected, absolute=1e-10)
    return {"configuration": configuration, "tree": tree, "stock": stock, "operation": cut, "profiles": profiles, "stock_axis_relation_types": axis_types, "body_count": bodies, "mass": mass, "whats_wrong": wrong, "edited": edited}


def phase(root, job, case, control, name):
    import Swapp
    from AuthorCurves import Recorder, write_json
    from ObserveAssemblyLoad import AssemblyLoadMonitor
    from OracleIdentity import application_identity
    from ThroughAllAuthor import ThroughAllAuthor

    require(json.loads((root / "ApiMetadata.json").read_bytes()) == json.loads(json.dumps(api_metadata())), "registered native API differs from the prerequisite phase")
    folder = root / "Inspection" / name
    folder.mkdir(parents=True, exist_ok=False)
    recorder = Recorder(folder / "Record.json", {"schema": SCHEMA, "phase": name})
    selected = control if name.startswith("Control") else case
    input_key = job["control_file"] if name.startswith("Control") else job["generated_file"]
    input_file = original_root(root, job) / input_key
    expected = job["files_sha256"][input_key]
    if name == "Reopen":
        preceding = json.loads((root / "Inspection/Generated/Record.json").read_bytes())
        require(preceding.get("passed") is True and preceding.get("result", {}).get("save") == [True, 0, 0], "reopen requires the successful separate generated phase")
        input_file = root / "Inspection/Generated/Saved.SLDPRT"
        expected = preceding["result"]["saved_sha256"]
    result = {"passed": False, "input_sha256": expected, "selected_packet_key": input_key, "original_native_input_custody": name != "Reopen" and job.get("original_native_inputs") is not None}
    controller = model = None
    with AssemblyLoadMonitor() as monitor:
        try:
            require(digest(input_file) == expected, "the immutable through-all input changed")
            recorder.call("require an idle serially owned native oracle", Swapp.sweep)
            controller = recorder.call("start a fresh pinned through-all oracle", Swapp.Sw)
            identity = recorder.call("verify original SOLIDWORKS executable", application_identity, controller.app)
            require(identity["version_matches"] and identity["sha256"] == ORACLE, "native executable differs from the pinned build")
            result["oracle_identity"] = identity
            model, errors, warnings = recorder.call("open immutable through-all native input", controller.open, input_file, read_only=name != "Generated")
            result["open"] = [model is not None, errors, warnings]
            require(result["open"] == [True, 0, 0], "through-all open failed or warned")
            author = ThroughAllAuthor(controller.app, recorder, Swapp)
            author.model = model
            require(Path(author.get(model, "GetPathName")).samefile(input_file), "through-all open selected another file")
            result["initial"] = snapshot(author, selected, edited=name == "Reopen", rebuild=False)
            result["rebuilt"] = snapshot(author, selected, edited=name == "Reopen", rebuild=True)
            require(ui_tree(result["initial"]) == ui_tree(result["rebuilt"]), "native rebuild changed the ordered feature tree")
            if name == "Generated":
                author.edit_stock(native_case(case))
                result["edited"] = snapshot(author, case, edited=True, rebuild=True)
                destination = folder / "Saved.SLDPRT"
                status = recorder.call("save the owned edited generated through-all part", controller.save_as, model, destination)
                result["save"] = list(status)
                require(result["save"] == [True, 0, 0] and destination.is_file() and Path(author.get(model, "GetPathName")).samefile(destination), "edited through-all SaveAs failed or warned")
                result["saved"] = snapshot(author, case, edited=True, rebuild=False)
                result["saved_sha256"] = digest(destination)
                result["saved_bytes"] = destination.stat().st_size
            result["passed"] = True
        except Exception as error:
            recorder.failure(error)
            result["exception"] = repr(error)
        finally:
            if controller is not None:
                try:
                    if model is not None:
                        recorder.call("close the owned through-all native document", controller.close_doc, model)
                except Exception as error:
                    recorder.failure(error, cleanup=True)
                try:
                    controller.close()
                except Exception as error:
                    recorder.failure(error, cleanup=True)
                result["controller_diagnostics"] = controller.diagnostics
    result["input_immutable"] = input_file.is_file() and digest(input_file) == expected
    result["dialogs"] = monitor.log
    result["progress_windows"] = monitor.progress
    result["passed"] = bool(result["passed"] and result["input_immutable"] and not result["dialogs"] and not result.get("controller_diagnostics") and not recorder.data["cleanup_errors"] and recorder.data["first_failure"] is None)
    recorder.data.update(result=result, passed=result["passed"], finished_at=time.time())
    recorder.flush()
    return result["passed"]


def phase_row(root, name):
    path = root / "Inspection" / name / "Record.json"
    if not path.is_file():
        return {"passed": False, "result": {}, "checks": [], "missing_record": True}
    try:
        value = json.loads(path.read_bytes())
    except (ValueError, OSError) as error:
        return {"passed": False, "result": {}, "checks": [], "malformed_record": True, "error": repr(error)}
    if not isinstance(value, dict):
        return {"passed": False, "result": {}, "checks": [], "malformed_record": True}
    result = value.get("result")
    partial = not isinstance(result, dict)
    return {**value, "passed": value.get("passed") is True and not partial and result.get("passed") is True, "result": {} if partial else result, "checks": value.get("checks") if isinstance(value.get("checks"), list) else [], "partial_record": partial}


def summarize(root, job):
    rows = {name: phase_row(root, name) for name in PHASES}
    identities = set()
    for row in rows.values():
        identity = row["result"].get("oracle_identity")
        if isinstance(identity, dict):
            pair = (identity.get("process_id"), identity.get("process_creation_filetime"))
            if all(type(value) is int and value > 0 for value in pair):
                identities.add(pair)
    snapshots = [value for row in rows.values() for key, value in row["result"].items() if key in ("initial", "rebuilt", "edited", "saved")]
    relation_types = [row["stock_axis_relation_types"] for row in snapshots]
    immutable = all(digest(root / relative) == expected for relative, expected in job["files_sha256"].items())
    controls = all(rows[name]["passed"] for name in ("ControlBefore", "ControlAfter"))
    checks = [check for row in rows.values() for check in row["checks"]]
    result = {"schema": SCHEMA, "passed": bool(all(row["passed"] for row in rows.values()) and controls and len(identities) == 4 and all(all(value is not None for value in item) for item in identities) and immutable and checks and all(row["passed"] for row in checks) and relation_types and all(value == relation_types[0] for value in relation_types)), "controls_healthy": controls, "distinct_native_processes": len(identities), "numeric_checks": len(checks), "all_numeric_checks_passed": bool(checks and all(row["passed"] for row in checks)), "numeric_check_status": "recorded" if checks else "not_run", "all_inputs_immutable": immutable, "stock_relations_match_disclosed_control": bool(relation_types and all(value == relation_types[0] for value in relation_types)), "missing_phases": [name for name, row in rows.items() if row.get("missing_record")], "partial_phases": [name for name, row in rows.items() if row.get("partial_record")], "malformed_phases": [name for name, row in rows.items() if row.get("malformed_record")], "native_generated_discovery_only": True, "heldout_payloads_read": 0, "public_writer_qualified": False, "phases": {name: {"passed": row["passed"], "record_sha256": None if row.get("missing_record") else digest(root / "Inspection" / name / "Record.json"), "oracle_identity": row["result"].get("oracle_identity")} for name, row in rows.items()}}
    (root / "Inspection/Result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


def main():
    parser = ArgumentParser()
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--packet-sha256", required=True)
    parser.add_argument("--action", choices=("verify", "metadata", "phase", "summarize"), required=True)
    parser.add_argument("--phase", choices=PHASES)
    args = parser.parse_args()
    root, job, case, control = read_packet(args.packet.resolve(strict=True), args.packet_sha256)
    if args.action == "verify":
        result = {"passed": True, "native_processes_started": 0, "heldout_payloads_read": 0, "tools": len(job["tools_sha256"]), "generated_sha256": job["files_sha256"][job["generated_file"]]}
    elif args.action == "metadata":
        metadata = api_metadata()
        file = root / "ApiMetadata.json"
        require(not file.exists(), "native metadata evidence already exists")
        file.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n")
        result = {"passed": True, "native_processes_started": 0, "metadata_sha256": digest(file)}
    elif args.action == "phase":
        require(args.phase is not None, "a phase identity is required")
        result = {"phase": args.phase, "passed": phase(root, job, case, control, args.phase)}
    else:
        result = summarize(root, job)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
