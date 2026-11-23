from argparse import ArgumentParser
from contextlib import redirect_stderr, redirect_stdout
from math import isclose
from pathlib import Path
from subprocess import check_output, run
import json
import os
import re
import sys
import time

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent))

from C057PlacementPlan import BUILD, STATES, checked, digest, known_cases, predicted, require, source_case, wire

BASE = "f835b1395a6e0159e2e08ae45d26a3239e0151ed"
ORACLE = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
SCHEMA = "kit.sw2026.disclosed-c057-placement-source.v1"
CONTROLS = {
    "L1": ("ladder/L1_boss.SLDPRT", "55e5a9840cc78a1d4b3ac4b8de3f37540695494e4d7a0edfb3cd3a2a876e2ac6"),
    "Revolve": ("principal-revolve-discovery/PrincipalRevolveTopForward.SLDPRT",
                "4bf2c202be9ae4fc7786e50a92c4f83dc17ea4bc80492b7173075d74f678d3f0"),
}
TOOLS = ("C057PlacementPlan.py", "C057NativeAuthor.py", "C057SourcePacket.py")
COMMON = (
    "AuthorCurves.py", "AuthorAssemblySources.py", "InspectFresh.py", "InspectCircleSketch.py",
    "ObserveAssemblyLoad.py", "OracleIdentity.py", "Swapp.py", "NestedAssemblySourcePlan.py",
    "AuthorNestedAssemblySources.py", "RunSealedNestedSourcePhase.py", "ReferencePlaneSourcePlan.py",
    "ReferencePlaneDimensions.py", "AuthorReferencePlaneSources.py",
)
ACTIONS = ("Metadata", "BeforeL1", "BeforeRevolve", "AuthorC057Box001", "ReopenC057Box001",
           "AuthorSignedRollContrast", "ReopenSignedRollContrast", "AfterL1", "AfterRevolve")
PRIVATE_NAME = re.compile(r"C:\\KitC057PlacementSource[0-9]{2,4}")


def new_bytes(path, content):
    with path.open("xb") as stream:
        stream.write(content)


def new_json(path, value):
    new_bytes(path, wire(value))


def tracked(repo, name):
    return check_output(("git", "-C", str(repo), "show", f"{BASE}:{name}"))


def tool_paths():
    return {f"Tools/{name}" for name in (*TOOLS, *COMMON)}


def members():
    return tool_paths() | {"Cases.json", "Predictions.json"} | {f"Controls/{name}.SLDPRT" for name in CONTROLS}


def expected_predictions(cases):
    return {case["label"]: {state: predicted(case, state) for state in STATES} for case in cases}


def equivalent(actual, expected):
    if isinstance(expected, dict):
        return isinstance(actual, dict) and actual.keys() == expected.keys() and all(
            equivalent(actual[name], value) for name, value in expected.items())
    if isinstance(expected, (tuple, list)):
        return isinstance(actual, (list, tuple)) and len(actual) == len(expected) and all(
            equivalent(a, b) for a, b in zip(actual, expected, strict=True))
    if type(expected) is float:
        return type(actual) is float and isclose(actual, expected, rel_tol=1e-14, abs_tol=1e-15)
    return type(actual) is type(expected) and actual == expected


def same_datum(actual, other):
    if any(actual[key] != other[key] for key in ("constraints", "reference_slots_owned")):
        return False
    for key in ("plane_frame", "sketch_frame"):
        if any(any(abs(x - y) > 2e-9 for x, y in zip(left, right, strict=True))
               for left, right in zip(actual[key], other[key], strict=True)):
            return False
    return isclose(actual["angle_magnitude"], other["angle_magnitude"], rel_tol=0.0, abs_tol=2e-9)


def prepare(output, inventory, guest):
    require(HERE.parent.name == "primitive_stock" and HERE.parents[3].name == "tooling",
            "prepare must run in the task's repository checkout")
    repo = HERE.parents[5]
    require(PRIVATE_NAME.fullmatch(guest), "choose a new numbered C:\\KitC057PlacementSource directory")
    require(not output.exists() and output.parent.is_dir() and not output.is_relative_to(repo),
            "choose an unused packet directory outside the repository")
    cases = known_cases()
    require(cases[0] == source_case(inventory, repo / "re/solidworks/measurements/2026/SdkFreecadPlacedStock01.json"),
            "actual disclosed C057 source did not match the frozen case")
    files = {
        **{f"Tools/{name}": HERE.with_name(name).read_bytes() for name in TOOLS},
        **{f"Tools/{name}": tracked(repo, "re/tooling/sw2026/" + name) for name in COMMON},
        "Cases.json": wire(cases), "Predictions.json": wire(expected_predictions(cases)),
    }
    for name, (path, pin) in CONTROLS.items():
        payload = tracked(repo, "re/solidworks/v2026/corpus/" + path)
        require(digest(payload) == pin, "tracked unchanged control identity differs")
        files[f"Controls/{name}.SLDPRT"] = payload
    require(set(files) == members(), "C057 packet member closure is incomplete")
    output.mkdir(exist_ok=False)
    (output / "Tools").mkdir()
    (output / "Controls").mkdir()
    for name, data in files.items():
        new_bytes(output / name, data)
    manifest = {"schema": SCHEMA, "base": BASE, "build": BUILD, "oracle": ORACLE, "guest_private_base": guest,
                "cohort": "disclosed", "writer_output_count": 0, "heldout_cases": 0,
                "phases": ACTIONS, "files": {name: digest(data) for name, data in files.items()}}
    path = output / "Packet.json"
    new_json(path, manifest)
    pin = digest(wire(manifest))
    run((sys.executable, "-E", "-B", str(output / "Tools" / HERE.name), "verify", str(path), pin),
        capture_output=True, check=True, timeout=30)
    return {"packet": str(path), "sha256": pin, "predictions_sha256": manifest["files"]["Predictions.json"],
            "native_processes": 0, "holdout_inputs_read": 0}


def verify(path, pin):
    spec = json.loads(checked(path, pin))
    root = path.parent
    require(path.name == "Packet.json" and (root / "Tools").resolve() == HERE.parent,
            "use the exact frozen C057 packet tool")
    require(set(spec) == {"schema", "base", "build", "oracle", "guest_private_base", "cohort",
                          "writer_output_count", "heldout_cases", "phases", "files"}
            and (spec["schema"], spec["base"], spec["build"], spec["oracle"], spec["cohort"])
            == (SCHEMA, BASE, BUILD, ORACLE, "disclosed")
            and spec["writer_output_count"] == spec["heldout_cases"] == 0
            and spec["phases"] == list(ACTIONS)
            and PRIVATE_NAME.fullmatch(spec["guest_private_base"])
            and set(spec["files"]) == members(), "unexpected C057 packet scope or provenance")
    require(all(not value.is_symlink() for value in root.rglob("*"))
            and {value.relative_to(root).as_posix() for value in root.rglob("*") if value.is_file()}
            == members() | {"Packet.json"}, "C057 packet has an unbound or linked member")
    payloads = {name: checked(root / name, expected) for name, expected in spec["files"].items()}
    for name, (_, expected) in CONTROLS.items():
        require(digest(payloads[f"Controls/{name}.SLDPRT"]) == expected, "unchanged control pin differs")
    cases = json.loads(payloads["Cases.json"])
    predictions = json.loads(payloads["Predictions.json"])
    require(equivalent(cases, known_cases()) and equivalent(predictions, expected_predictions(cases)),
            "authored signed placement or independent predicted states changed")
    return spec, {case["label"]: case for case in cases}, predictions


def trace(path, payload):
    from AuthorCurves import write_json

    write_json(path, payload)


def load_prior(root, phase, pin):
    result = json.loads((root / phase / "Result.json").read_bytes())
    require(result["phase"] == phase and result["packet_sha256"] == pin and result["passed"] is True,
            "required C057 phase did not complete: " + phase)
    return result


def stamp(identity):
    from RunSealedNestedSourcePhase import opaque_identity

    observed = opaque_identity(identity)
    require(identity["version_matches"] is True, "wrong installed C057 oracle build")
    return observed


def verify_artifacts(native, artifacts):
    expected = {f"{state}.{suffix}" for state in STATES for suffix in ("SLDPRT", "STEP", "x_t")}
    require(set(artifacts) == expected, "authored native and exchange siblings differ")
    for name, row in artifacts.items():
        content = checked(native / name, row["sha256"])
        require(len(content) == row["bytes"] > 0 and row["status"] == [True, 0, 0],
                "authored native source has inconsistent save evidence")


def save_state(controller, author, native, state, artifacts):
    for suffix in ("SLDPRT", "STEP", "x_t"):
        path = native / f"{state}.{suffix}"
        require(not path.exists(), "a C057 source save target already exists")
        status = list(author.rec.call("save exact disclosed source state", controller.save_as, author.model, path))
        require(status == [True, 0, 0] and path.is_file(), "a native disclosed save failed or warned")
        data = path.read_bytes()
        require(bool(data), "native save emitted no bytes")
        artifacts[path.name] = {"status": status, "bytes": len(data), "sha256": digest(data)}
    for name, row in artifacts.items():
        checked(native / name, row["sha256"])


def acquire(case, phase, phase_path, private, api, pin, frozen_predictions):
    import Swapp
    from AuthorCurves import Recorder
    from C057NativeAuthor import PlacedStockAuthor
    from ObserveAssemblyLoad import AssemblyLoadMonitor
    from OracleIdentity import application_identity

    rec = Recorder(phase_path / "Native.json", {"case": case, "phase": phase})
    authored = phase.startswith("Author")
    owner = private / f"Author{case['label']}"
    native = owner / "Native"
    state_path = owner / "AuthorSnapshot.json"
    if authored:
        native.mkdir(exist_ok=False)
    else:
        previous = load_prior(private, f"Author{case['label']}", pin)
        previous_lock = json.loads(checked(state_path, previous["author_snapshot_sha256"]))
        require(previous_lock["packet_sha256"] == pin and previous_lock["case"] == case["label"],
                "authored source snapshot belongs to a different case or input lock")
        artifacts = previous_lock["artifacts"]
        verify_artifacts(native, artifacts)

    result, controller = {}, None
    with AssemblyLoadMonitor() as monitor:
        try:
            rec.call("verify idle native oracle", Swapp.sweep)
            controller = rec.call("launch fresh C057 oracle", Swapp.Sw)
            identity = rec.call("bind exact native build", application_identity, controller.app)
            result["identity"] = stamp(identity)
            author = PlacedStockAuthor(controller.app, rec, Swapp, api)
            author.frozen_predictions = frozen_predictions
            observations = {}
            if authored:
                author.build(case, controller)
                artifacts = {}
                for state in STATES:
                    if state != "Original":
                        author.edit(state, case["edits"][state])
                    observed = author.snapshot(case, state)
                    observations[state] = observed
                    save_state(controller, author, native, state, artifacts)
                    if state != "Original":
                        author.edit(state, case["original"][state])
                        author.snapshot(case, "Original")
            else:
                author.driver_names = previous_lock["drivers"]
                for state in STATES:
                    path = native / f"{state}.SLDPRT"
                    model, errors, warnings = rec.call("fresh read-only source reopening", controller.open, path, read_only=True)
                    require(model is not None and errors == warnings == 0
                            and Path(author.get(model, "GetPathName")).samefile(path), "native source failed fresh exact read-only open")
                    author.model = model
                    try:
                        observed = author.snapshot(case, state)
                        prior_state = previous_lock["observations"][state]
                        require(observed["tree"] == prior_state["tree"] and observed["parents"] == prior_state["parents"],
                                "actual authored feature tree or references changed on fresh open")
                        require(same_datum(observed["datum"], prior_state["datum"]),
                                "actual selected datum or sketch tangent gauge changed on fresh open")
                        observations[state] = observed
                    finally:
                        rec.call("close read-only disclosed source", controller.close_doc, model)
                    verify_artifacts(native, artifacts)
            result["states"] = list(observations)
            result["checks"] = len(rec.data["checks"])
            result["observations_sha256"] = digest(wire(observations))
        except Exception as error:
            rec.failure(error)
            raise
        finally:
            if controller is not None:
                rec.call("close owned C057 native process", controller.close)
                rec.data["controller_diagnostics"] = controller.diagnostics
                rec.flush()
    rec.data["dialogs"] = monitor.log
    rec.flush()
    require(not monitor.log and not controller.diagnostics, "native startup/dialog/exit health failed")
    verify_artifacts(native, artifacts)
    if authored:
        new_json(state_path, {"packet_sha256": pin, "case": case["label"], "artifacts": artifacts,
                              "drivers": author.driver_names, "observations": observations})
    result["author_snapshot_sha256"] = digest(state_path.read_bytes())
    rec.data["passed"] = True
    rec.flush()
    return result


def control(phase, path, source):
    from InspectFresh import healthy, inspect

    expected = CONTROLS[source][1]
    checked(path, expected)
    details = {}
    inspect(path, result=details, checkpoint=lambda: trace(phase / "Native.json", details))
    identity = stamp(details["oracle_identity"])
    require(healthy(details) and details["sha256"] == expected, "unchanged native control failed")
    checked(path, expected)
    return {"identity": identity, "control_sha256": expected,
            "numeric_control_sha256": digest(wire({key: details[key] for key in ("mass", "bodies", "features")}))}


def phase_action(path, pin, phase):
    require(os.name == "nt", "native C057 operations run only inside the Windows oracle")
    spec, cases, predictions = verify(path, pin)
    from C057NativeAuthor import metadata
    from RunSealedNestedSourcePhase import local_trial

    private = local_trial(spec, pin, 0, "T01")
    phase_dir = private / phase
    phase_dir.mkdir(exist_ok=False)
    started = time.time()
    base = {"schema": SCHEMA, "phase": phase, "started_at": started, "packet_sha256": pin, "passed": False}
    trace(phase_dir / "Result.json", base)
    try:
        with (phase_dir / "Console.log").open("x", encoding="utf-8") as out, redirect_stdout(out), redirect_stderr(out):
            if phase == "Metadata":
                observed = metadata()
                new_json(phase_dir / "Bindings.json", observed)
                result = {"bindings_sha256": digest(wire(observed)), "native_processes": 0}
            elif phase.startswith(("Before", "After")):
                source = phase.removeprefix("Before").removeprefix("After")
                result = control(phase_dir, path.parent / "Controls" / f"{source}.SLDPRT", source)
            else:
                for required in ("BeforeL1", "BeforeRevolve"):
                    load_prior(private, required, pin)
                meta = load_prior(private, "Metadata", pin)
                bound = json.loads(checked(private / "Metadata/Bindings.json", meta["bindings_sha256"]))
                require(metadata() == bound, "installed COM bindings changed since metadata qualification")
                label = phase.removeprefix("Author").removeprefix("Reopen")
                result = acquire(cases[label], phase, phase_dir, private, bound, pin, predictions[label])
            verify(path, pin)
        complete = base | result | {"passed": True, "finished_at": time.time()}
        trace(phase_dir / "Result.json", complete)
        return {"phase": phase, "passed": True}
    except Exception as error:
        trace(phase_dir / "Failure.json", {"type": type(error).__name__, "error": repr(error)})
        trace(phase_dir / "Result.json", base | {"finished_at": time.time(), "failure_type": type(error).__name__})
        raise


def summarize(path, pin, output):
    require(os.name == "nt", "C057 native artifact verification runs only inside the Windows oracle")
    spec, cases, _ = verify(path, pin)
    from RunSealedNestedSourcePhase import local_trial

    private = local_trial(spec, pin, 0, "T01")
    rows = [load_prior(private, phase, pin) for phase in ACTIONS]
    actual = rows[1:]
    identities = {row["identity"]["process_creation_filetime"] for row in actual}
    require(len(identities) == 8 and all(a["finished_at"] <= b["started_at"] for a, b in zip(rows, rows[1:])),
            "C057 source batch requires eight distinct serial native lifetimes")
    for name in CONTROLS:
        before = next(row for row in actual if row["phase"] == f"Before{name}")
        after = next(row for row in actual if row["phase"] == f"After{name}")
        require(before["numeric_control_sha256"] == after["numeric_control_sha256"], "native control changed within the source batch")
    locked = {}
    for label in cases:
        owner = private / f"Author{label}"
        before = load_prior(private, f"Author{label}", pin)
        after = load_prior(private, f"Reopen{label}", pin)
        require(before["states"] == after["states"] == list(STATES)
                and before["author_snapshot_sha256"] == after["author_snapshot_sha256"],
                "native disclosed source/edit/reopen lock changed")
        record = json.loads(checked(owner / "AuthorSnapshot.json", before["author_snapshot_sha256"]))
        verify_artifacts(owner / "Native", record["artifacts"])
        locked[label] = {"author_snapshot_sha256": before["author_snapshot_sha256"],
                         "states": len(STATES), "independent_dimension_edits": len(STATES) - 1,
                         "checks": before["checks"] + after["checks"]}
    final = {"schema": SCHEMA, "packet_sha256": pin, "native_build": BUILD, "native_processes": len(identities),
             "healthy_controls": 4, "disclosed": locked, "heldout_cases": 0,
             "writer_output_count": 0, "conversion_credit": 0, "passed": True}
    new_json(output, final)
    return final


def main():
    parser = ArgumentParser()
    actions = parser.add_subparsers(dest="action", required=True)
    worker = actions.add_parser("prepare")
    worker.add_argument("output", type=Path)
    worker.add_argument("--inventory", type=Path, required=True)
    worker.add_argument("--guest-root", required=True)
    for name in ("verify", "run", "summary"):
        child = actions.add_parser(name)
        child.add_argument("packet", type=Path)
        child.add_argument("sha256")
        if name == "run":
            child.add_argument("phase", choices=ACTIONS)
        if name == "summary":
            child.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.action == "prepare":
        result = prepare(args.output.resolve(), args.inventory, args.guest_root)
    elif args.action == "verify":
        verify(args.packet.resolve(strict=True), args.sha256)
        result = {"verified": True, "native_processes": 0}
    elif args.action == "run":
        result = phase_action(args.packet.resolve(strict=True), args.sha256, args.phase)
    else:
        result = summarize(args.packet.resolve(strict=True), args.sha256, args.output)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
