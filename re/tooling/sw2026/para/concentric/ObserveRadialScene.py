import argparse
import json
import os
from pathlib import Path
import struct
import sys


TOOLS = Path(__file__).resolve().parent
SOURCE = TOOLS.parents[1] if TOOLS.name == "concentric" else TOOLS
sys.path.insert(0, str(SOURCE))

from ConcentricNativeContract import ORACLE, ROLES, checked, digest, require, write_json


SCHEMA = "kit.sw2026.disclosed-radial-scene-native.v1"
KNOWN = {
    "candidate": "6043b1404c1e20027a287a5ba6bda859651080b77091d64463943b8990d1256d",
    "control": "92b83376b42ca55aa3b32a350635585c788ea0f968cc6e54f1730fdeb3c99caa",
    "request": "d25e6b4bdd6631c8c40aeae0335f96cebcbc740af0151dd7154ae08a873a6ca1",
    "build": "4702d138fe9dc3f3373dce99ff62c3791a5eefde42967a46d384e64d23608514",
}
DEPENDENCIES = (
    "AuthorAssemblySources.py", "AuthorCurves.py", "ConcentricNativeContract.py",
    "InspectCircleSketch.py", "InspectFresh.py", "ObserveAssemblyLoad.py", "OracleIdentity.py", "Swapp.py",
)


def freeze(output, candidate, control, request, build, runtime_path):
    from PrepareGeneratedConcentric import input_row, windows_path

    candidate = candidate.resolve(strict=True)
    control = control.resolve(strict=True)
    require(candidate.name == "DisclosedRadialSceneProbe.SLDPRT" and candidate.parent.name == "Build01", "the original final candidate path is mandatory")
    proof = json.loads(checked(build, KNOWN["build"]).read_bytes())
    neutral = json.loads(checked(request, KNOWN["request"]).read_bytes())
    runtime = json.loads(runtime_path.read_bytes())
    require(runtime["version"] == "3.12.7" and runtime["pointer_bits"] == 64, "unexpected guest runtime")
    original = proof["independent_prediction"]["initial"]
    edited = proof["independent_prediction"]["planned_depth_edit"]
    case = {"request": {"document": {
        "plane_axis": "z", "feature_kind": "blind_extrusion", "sketch_name": "CurveSketch", "extrusion_name": "CurveBoss",
        "circle_dimension": {"mode": "radius", "fix_center": True}, "radius_m": original["radius_m"],
        "depth_m": original["depth_m"], "center_m": original["centre_of_mass_m"][:2],
    }}}
    lights = [[row["NameValue"], "AmbientLight" if row["KindValue"] == "ambient" else "DirectionLight",
               neutral["environment_name"]] for row in neutral["lights"]]
    files = {"candidate": input_row(candidate, KNOWN["candidate"]), "control": input_row(control, KNOWN["control"])}
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    closure = output / "Tools"
    closure.mkdir()
    for name in DEPENDENCIES:
        (closure / name).write_bytes((SOURCE / name).read_bytes())
    (closure / Path(__file__).name).write_bytes(Path(__file__).read_bytes())
    packet = output / "Trial.json"
    job = {"schema": SCHEMA, "oracle_sha256": ORACLE, "runtime": runtime, "roles": list(ROLES),
           "heldout_inputs_read": 0, "files": files, "case": case, "lights": lights,
           "predictions": proof["independent_prediction"], "edited_depth_m": edited["depth_m"],
           "tool_sha256": {path.name: digest(path) for path in closure.iterdir()}}
    write_json(packet, job)
    trial_hash = digest(packet)
    guest = [runtime["executable"], "-B", windows_path(closure / Path(__file__).name)]
    guest_trial = windows_path(packet)
    recipe = output / "Recipe.json"
    commands = {"verify_guest": [*guest, "verify", guest_trial, trial_hash],
                **{role: [*guest, "phase", guest_trial, trial_hash, role] for role in ROLES},
                "summary": [*guest, "summary", guest_trial, trial_hash]}
    write_json(recipe, {"ordered_phases": list(ROLES), "always_run_trailing_control": True, "argv": commands})
    return {"trial_sha256": trial_hash, "recipe_sha256": digest(recipe), "native_processes_started": 0}


def verify(packet, expected):
    job = json.loads(checked(packet, expected).read_bytes())
    require(TOOLS == packet.parent / "Tools" and job["schema"] == SCHEMA and job["roles"] == list(ROLES)
            and job["heldout_inputs_read"] == 0 and job["oracle_sha256"] == ORACLE, "wrong disclosed trial or closure")
    for name, wanted in job["tool_sha256"].items():
        checked(TOOLS / name, wanted)
    domain = "guest_path" if os.name == "nt" else "host_path"
    for role, row in job["files"].items():
        require(row["sha256"] == KNOWN[role], "unexpected input identity")
        checked(Path(row[domain]), row["sha256"])
    require(len(job["lights"]) == 4 and len({row[0] for row in job["lights"]}) == 4, "expected four ordered environment lights")
    if os.name == "nt":
        runtime = job["runtime"]
        require(tuple(sys.version_info[:3]) == tuple(map(int, runtime["version"].split(".")))
                and struct.calcsize("P") * 8 == runtime["pointer_bits"]
                and Path(sys.executable).samefile(runtime["executable"]), "unexpected guest runtime")
    return job


def record(root, expected, role):
    path = root / "Inspection" / role / "Record.json"
    if not path.is_file():
        return None
    row = json.loads(path.read_bytes())
    require(row["job"] == {"trial_sha256": expected, "phase": role}, "phase custody differs")
    return row.get("result", {"passed": False, "first_failure": row["first_failure"]})


def capture(author, job, depth_factor):
    import InspectCircleSketch as circle
    from AuthorAssemblySources import feature_tree

    shape = circle.snapshot(author, job["case"], depth_factor=depth_factor)
    tree = feature_tree(author, author.model)
    observed = [[row["name"], row["type"], row["parent"]]
                for row in tree if row["type"] in {"AmbientLight", "DirectionLight"}]
    require(observed == job["lights"] and all(not row["suppressed"] for row in tree), "the four ordered unsuppressed environment lights differ")
    return {"shape": shape, "tree": tree, "ordered_lights": observed}


def phase(packet, expected, role):
    require(os.name == "nt", "only the owned Windows guest can run a native phase")
    job = verify(packet, expected)
    root = packet.parent
    control = role.startswith("Control")
    editing = role == "Generated"
    reopened = role == "Reopen"
    owned = root / "Owned" / Path(job["files"]["candidate"]["guest_path"]).name
    depth = job["case"]["request"]["document"]["depth_m"]
    edit_factor = job["edited_depth_m"] / depth
    saved = None
    if reopened:
        prior = record(root, expected, "Generated")
        require(prior and prior["passed"] is True, "the generated measurement and save must pass first")
        saved = prior["saved_sha256"]
        path = checked(owned, saved)
    else:
        if editing:
            prior = record(root, expected, "ControlBefore")
            require(prior and prior["passed"] is True, "the leading disclosed control must pass first")
        path = Path(job["files"]["control" if control else "candidate"]["guest_path"])

    import InspectCircleSketch as circle
    import Swapp
    from AuthorCurves import CurveAuthor, Recorder
    from OracleIdentity import application_identity

    directory = root / "Inspection" / role
    directory.mkdir(parents=True, exist_ok=False)
    recorder = Recorder(directory / "Record.json", {"trial_sha256": expected, "phase": role})
    result = {"role": role, "passed": False}
    controller = None
    with Swapp.Dismisser() as dialogs:
        try:
            recorder.call("require idle owned solver", Swapp.sweep)
            controller = recorder.call("start exact SOLIDWORKS oracle", Swapp.Sw)
            result["oracle_identity"] = identity = application_identity(controller.app)
            require(identity["sha256"] == ORACLE and identity["version_matches"] and identity["file_version"] == "34.5.2.0604",
                    "unexpected native solver build")
            author = CurveAuthor(controller.app, recorder, Swapp)
            require(int(author.get(controller.app, "GetDocumentCount")) == 0, "the oracle is not cold")
            author.model, errors, warnings = recorder.call("open exact radial child", controller.open, path, read_only=not editing)
            result.update(open_errors=errors, open_warnings=warnings)
            require(author.model is not None and errors == warnings == 0
                    and Path(str(author.get(author.model, "GetPathName"))).samefile(path), "requested native file did not open cleanly")
            result["cold_state"] = circle.initial_state(author, job["case"])
            require(result["cold_state"]["passed"], "cold native part lacks its requested body or active features")
            result["rebuilt"] = capture(author, job, edit_factor if reopened else 1.0)
            if editing:
                parameter = author.get(author.model, "Parameter", "D1@" + job["case"]["request"]["document"]["extrusion_name"])
                result["depth_edit_status"] = int(author.get(parameter, "SetSystemValue3", job["edited_depth_m"], 1, Swapp.nothing()))
                require(result["depth_edit_status"] == 0, "the actual depth edit was rejected")
                result["edited"] = capture(author, job, edit_factor)
                require(result["edited"]["tree"] == result["rebuilt"]["tree"], "the edit changed native feature inventory")
                owned.parent.mkdir(exist_ok=False)
                result["save_status"] = status = recorder.call("save only the owned edited derivative", controller.save_as, author.model, owned)
                require(status == (True, 0, 0) and owned.is_file(), "edited native save failed or warned")
                result["saved_sha256"] = digest(owned)
            if reopened:
                require(result["rebuilt"]["tree"] == prior["edited"]["tree"] and digest(owned) == saved,
                        "fresh reopen changed the feature tree or edited input bytes")
            result["passed"] = True
        except Exception as error:
            recorder.failure(error)
        finally:
            if controller is not None:
                try:
                    controller.close()
                    result["controller_diagnostics"] = controller.diagnostics
                except Exception as error:
                    recorder.failure(error, cleanup=True)
    try:
        verify(packet, expected)
    except Exception as error:
        recorder.failure(error, cleanup=True)
    result.update(dialogs=dialogs.log, numeric_checks=len(recorder.data["checks"]), first_failure=recorder.data["first_failure"])
    result["passed"] = bool(result["passed"] and not result["dialogs"] and not result.get("controller_diagnostics") and not result["first_failure"])
    recorder.data.update(result=result, passed=result["passed"])
    recorder.flush()
    return result["passed"]


def summary(packet, expected):
    verify(packet, expected)
    phases = {role: record(packet.parent, expected, role) for role in ROLES}
    complete = all(row and row["passed"] for row in phases.values())
    births = [row["oracle_identity"]["process_creation_filetime"] for row in phases.values() if row and row.get("oracle_identity")]
    passed = bool(complete and len(births) == 4 and all(a < b for a, b in zip(births, births[1:]))
                  and phases["ControlBefore"]["rebuilt"]["tree"] == phases["ControlAfter"]["rebuilt"]["tree"])
    write_json(packet.parent / "Result.json", {"schema": SCHEMA, "trial_sha256": expected, "passed": passed,
               "distinct_native_processes": len(set(births)), "heldout_credit": 0,
               "numeric_checks": sum(row.get("numeric_checks", 0) for row in phases.values() if row), "phases": phases})
    return passed


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "freeze":
        parser = argparse.ArgumentParser()
        for name in ("output", "candidate", "control", "request", "build", "runtime"):
            parser.add_argument("--" + name, type=Path, required=True)
        args = parser.parse_args(sys.argv[2:])
        print(json.dumps(freeze(args.output, args.candidate, args.control, args.request, args.build, args.runtime)))
        return 0
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("verify", "phase", "summary"))
    parser.add_argument("packet", type=Path)
    parser.add_argument("sha256")
    parser.add_argument("role", choices=ROLES, nargs="?")
    args = parser.parse_args()
    packet = args.packet.resolve(strict=True)
    if args.command == "phase":
        require(args.role is not None, "missing native phase role")
        passed = phase(packet, args.sha256, args.role)
    elif args.command == "summary":
        passed = summary(packet, args.sha256)
    else:
        verify(packet, args.sha256)
        passed = True
    print(json.dumps({"passed": passed, "phase": args.role}))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
