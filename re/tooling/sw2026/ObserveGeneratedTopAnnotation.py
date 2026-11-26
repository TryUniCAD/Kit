from argparse import ArgumentParser
import json
from math import ulp
from pathlib import Path
from struct import pack
import subprocess
import sys

from ObserveVendorBossCorpus import demand, digest, observe_part, original, phase, read_json, write_json
from ObserveVendorBossPresentation import (
    OPEN_READ_ONLY_SILENT,
    observe_annotations,
)


OBSERVE_ROLES = (
    "ControlBefore", "EditControl", "PlainBaseline", "CandidateReadOnly",
    "CandidateEdit", "CandidateReopen", "ControlAfter",
)


def observe(base, document):
    return {
        **observe_part(base, document),
        "read_only": bool(base.member(document, "IsOpenedReadOnly")),
        "annotations": observe_annotations(document.Extension, base.member),
    }


def check_depth(state, expected):
    actual = state["depth_m"]
    demand(abs(actual - expected) <= ulp(expected), f"driving depth differs: {actual!r} m vs {expected!r} m")


def inspect(base, app, request, result):
    source = Path(request["path"]).resolve(strict=True)
    sha = request["sha256"]
    demand(digest(source) == sha, "native input does not match its frozen digest")
    read_only = "edit_depth_m" not in request
    errors, warnings = base.statuses()
    options = OPEN_READ_ONLY_SILENT if read_only else 1
    document = app.OpenDoc6(str(source), 1, options, "", errors, warnings)
    result.update(open_errors=errors.value, open_warnings=warnings.value)
    demand(document is not None, f"SOLIDWORKS failed to open the part: {errors.value}")
    try:
        demand(errors.value == warnings.value == 0, "SOLIDWORKS reported load errors or warnings")
        demand(bool(base.member(document, "IsOpenedReadOnly")) == read_only, "native open mode differs")
        result["initial"] = observe(base, document)
        result["rebuild_succeeded"] = bool(document.ForceRebuild3(False))
        demand(result["rebuild_succeeded"], "unchanged part did not rebuild")
        result["rebuilt"] = observe(base, document)
        points = tuple(map(tuple, request["profile_m"]))
        for state in (result["initial"], result["rebuilt"]):
            base.compare_observation(state, points, request["depth_m"])
            check_depth(state, request["depth_m"])
            if request["role"] in ("ControlBefore", "EditControl", "ControlAfter"):
                check_top(state, request["rotation"])
        if not read_only:
            depth = request["edit_depth_m"]
            document.Parameter("D1@Boss-Extrude1").SystemValue = depth
            result["edit_rebuild_succeeded"] = bool(document.ForceRebuild3(False))
            demand(result["edit_rebuild_succeeded"], "edited part did not rebuild")
            result["edited"] = observe(base, document)
            base.compare_observation(result["edited"], points, depth)
            check_depth(result["edited"], depth)
            derivative = Path(request["derivative"])
            result["save_status"] = base.save(document, derivative)
            result["derivative_sha256"] = digest(derivative)
    finally:
        app.QuitDoc(str(base.member(document, "GetTitle")))
    result["source_unchanged"] = digest(source) == sha
    demand(result["source_unchanged"], "native input changed during observation")


def load_plan(plan):
    points = tuple(map(tuple, plan["profile_m"]))
    initial, edited = plan["depth_m"], plan["edit_depth_m"]
    demand(3 <= len(points) <= 64 and initial > 0 and edited > 0 and initial != edited, "invalid prism plan")
    manifest_path = Path(plan["manifest_path"]).resolve(strict=True)
    demand(digest(manifest_path) == plan["manifest_sha256"], "candidate manifest digest differs")
    manifest = read_json(manifest_path)
    demand(
        manifest["schema"] == "kit.sw2026.top-annotation-measurement-input.v1"
        and manifest["stage"] == "awaiting_native_measurement",
        "candidate manifest schema or stage differs",
    )
    request_path = Path(plan["neutral_request_path"]).resolve(strict=True)
    demand(digest(request_path) == manifest["request_sha256"], "neutral request digest differs")
    location = Path(manifest["native_locator"])
    demand(location.is_absolute() and not location.exists(), "encoded archive locator is not absent")
    paths = {}
    for role, spec in plan["inputs"].items():
        source = Path(spec["path"]).resolve(strict=True)
        demand(digest(source) == spec["sha256"], f"{role} source digest differs")
        paths[role] = source
    demand(set(paths) == {"Control", "EditControl", "PlainBaseline", "Candidate"}, "wrong input roster")
    candidate = paths["Candidate"]
    artifact = manifest["archive"]
    demand(
        digest(candidate) == artifact["sha256"] and candidate.stat().st_size == artifact["bytes"]
        and candidate.name == artifact["path"] and manifest_path.parent == candidate.parent,
        "candidate differs from its manifest",
    )
    typed = manifest["typed_readback"]
    matrix = tuple(float.fromhex(value) for value in typed["matrix_binary64"])
    demand(typed["role"] == "top" and len(matrix) == 9, "candidate typed intent differs")
    return points, initial, edited, location, paths, matrix


def check_top(state, rotation):
    annotations = state["annotations"]
    assigned = [row for row in annotations["views"] if not row["unassigned"]]
    demand(annotations["view_count"] == 2 and len(assigned) == 1, "expected one assigned and one unassigned view")
    view, = assigned
    demand(
        len(view["rotation"]) == 9 and pack("<9d", *view["rotation"]) == pack("<9d", *rotation)
        and not view["shown"] and view["annotation_count"] == 0
        and not view["always_2d"] and not view["flat_pattern"] and annotations["total_annotations"] == 0,
        "assigned view differs from the intended hidden Top rotation",
    )


def check_processes(phases, build, executable_sha256):
    start_times = []
    previous_exit = 0
    for row in phases.values():
        if "oracle_identity" not in row or not row.get("exit"):
            continue
        identity, outcome = row["oracle_identity"], row["exit"]
        start = int(identity["started"].split(":", 1)[1])
        demand(
            previous_exit < start < outcome["exit_filetime"] and identity["pid"] == outcome["pid"]
            and identity["started"] == outcome["started"] and identity["build"] == build
            and identity["sha256"] == executable_sha256,
            "native process identity, build or ordering differs",
        )
        start_times.append((identity["pid"], start))
        previous_exit = outcome["exit_filetime"]
    demand(len(start_times) == len(set(start_times)), "native phase reused a process")
    return len(start_times)


def reuse_preflight(base, report, expected_sha, plan_sha, source_hashes, points, initial, edited,
                    rotation, build, executable_sha256):
    demand(digest(report) == expected_sha, "original preflight digest differs")
    result = read_json(report)
    demand(result["plan_sha256"] == plan_sha and result["source_hashes"] == source_hashes
           and result["executable_sha256"] == executable_sha256 and result["controls_healthy"],
           "original preflight used different inputs or an unhealthy control")
    rows = result["phases"]
    leading = ("ControlBefore", "EditControl", "PlainBaseline", "ControlAfter")
    demand(tuple(rows) == leading and check_processes(rows, build, executable_sha256) == 4,
           "original preflight does not have the four expected owned lifetimes")
    demand(result["faults"] == {
        "PlainBaseline": "ValueError: exact driving value differs",
        "CandidateReadOnly": "phase was not run", "CandidateEdit": "phase was not run",
        "CandidateReopen": "phase was not run",
    }, "original stop was not solely the plain baseline binary64 depth comparison")
    for role, row in rows.items():
        folder = report.parent / role
        packet = read_json(folder / "Record.json")
        request = read_json(folder / "Request.json")
        source_role = "Control" if role in ("ControlBefore", "ControlAfter") else role
        demand(all(row[key] == value for key, value in packet.items())
               and digest(folder / "Record.json") == row["record_sha256"]
               and digest(folder / "Request.json") == row["request_sha256"]
               and digest(Path(request["path"])) == row["source_sha256"] == source_hashes[source_role],
               f"{role} original custody differs")
        demand(row["open_errors"] == row["open_warnings"] == row["exit"]["exit_code"] == 0
               and row["rebuild_succeeded"], f"{role} original native process was unhealthy")
        for state_name in ("initial", "rebuilt"):
            state = row[state_name]
            depth = edited if role == "EditControl" else initial
            demand(state["read_only"], f"{role} original open was not read-only")
            base.compare_observation(state, points, depth)
            check_depth(state, depth)
            if role != "PlainBaseline":
                check_top(state, rotation)
    demand(rows["ControlBefore"]["rebuilt"] == rows["ControlAfter"]["rebuilt"],
           "original bracket controls differ")
    return {
        "EditControl": {**rows["EditControl"], "reused_preflight_role": "EditControl"},
        "PlainBaseline": {**rows["PlainBaseline"], "reused_preflight_role": "PlainBaseline",
                          "preflight_depth_adjudicated": True},
        "ControlBefore": {**rows["ControlAfter"], "reused_preflight_role": "ControlAfter"},
    }


def measure(args):
    plan_sha256 = digest(args.plan)
    plan = read_json(args.plan)
    points, initial, edited, locator, paths, rotation = load_plan(plan)
    neutral_request = Path(plan["neutral_request_path"])
    neutral_sha256 = digest(neutral_request)
    binary = args.executable.resolve(strict=True)
    demand(digest(binary) == args.executable_sha256, "licensed oracle executable differs")
    root = args.root.resolve(strict=True)
    base = original(root)
    output = args.output.resolve()
    source_hashes = {role: digest(path) for role, path in paths.items()}
    derivative = output / "CandidateEdit" / "TopEdited.SLDPRT"
    demand(bool(args.preflight) == bool(args.preflight_sha256), "preflight continuation requires a report and digest")
    phases = reuse_preflight(
        base, args.preflight, args.preflight_sha256, plan_sha256, source_hashes, points, initial, edited,
        rotation, plan["oracle_build"], args.executable_sha256,
    ) if args.preflight else {}
    faults = {}
    output.mkdir()

    def run(role, source, expected_sha, depth, **kwargs):
        folder = output / role
        folder.mkdir()
        request, response = folder / "Request.json", folder / "Record.json"
        if role == "CandidateEdit":
            copy = folder / "TopEditable.SLDPRT"
            with copy.open("xb") as stream:
                stream.write(source.read_bytes())
            source = copy
        demand(digest(source) == expected_sha, f"{role} input changed")
        write_json(request, {
            "path": str(source), "sha256": expected_sha, "operation": "measure", "role": role,
            "executable": str(binary), "executable_sha256": args.executable_sha256,
            "profile_m": points, "depth_m": depth, "rotation": rotation, **kwargs,
        })
        command = (sys.executable, "-B", str(Path(__file__).resolve()), "--root", str(root),
                   "phase", str(request), str(response))
        with (folder / "Worker.log").open("xb") as log:
            try:
                worker = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=180, check=False)
            except subprocess.TimeoutExpired:
                phases[role] = {"passed": False, "error": "owned worker exceeded 180 seconds"}
                return False
        if response.is_file():
            item = read_json(response)
            item.update(record_sha256=digest(response), request_sha256=digest(request),
                        worker_exit_code=worker.returncode, source_sha256=expected_sha)
        else:
            item = {"passed": False, "error": "owned worker issued no result", "worker_exit_code": worker.returncode}
        phases[role] = item
        return item["passed"] and worker.returncode == 0

    preflight_ok = bool(phases)
    if not preflight_ok and run("ControlBefore", paths["Control"], source_hashes["Control"], initial):
        edit_ok = run("EditControl", paths["EditControl"], source_hashes["EditControl"], edited)
        plain_ok = run("PlainBaseline", paths["PlainBaseline"], source_hashes["PlainBaseline"], initial)
        preflight_ok = edit_ok and plain_ok
    if preflight_ok and run("CandidateReadOnly", paths["Candidate"], source_hashes["Candidate"], initial):
        if run("CandidateEdit", paths["Candidate"], source_hashes["Candidate"], initial,
               edit_depth_m=edited, derivative=str(derivative)):
            run("CandidateReopen", derivative, phases["CandidateEdit"]["derivative_sha256"], edited)
    run("ControlAfter", paths["Control"], source_hashes["Control"], initial)

    for role in OBSERVE_ROLES:
        row = phases.get(role)
        if row is None:
            faults[role] = "phase was not run"
            continue
        if (not row["passed"] or row["worker_exit_code"] != 0) and not row.get("preflight_depth_adjudicated"):
            faults[role] = row.get("error", "owned worker failed")
            continue
        errors = []
        for state_name in ("initial", "rebuilt", "edited"):
            if state_name not in row:
                continue
            state = row[state_name]
            is_edited = role in ("EditControl", "CandidateReopen") or state_name == "edited"
            expected_depth = edited if is_edited else initial
            reference = phases.get("EditControl" if is_edited else "ControlBefore", {}).get("rebuilt")
            try:
                base.compare_observation(state, points, expected_depth, reference)
                check_depth(state, expected_depth)
            except ValueError as error:
                errors.append(f"{state_name} geometry: {error}")
            try:
                if role == "PlainBaseline":
                    demand(state["annotations"]["view_count"] == 1 and state["annotations"]["views"][0]["unassigned"],
                           "plain baseline differs from one unassigned view")
                else:
                    check_top(state, rotation)
                    demand(reference is not None and state["annotations"] == reference["annotations"],
                           "full API view state differs from the vendor reference")
            except ValueError as error:
                errors.append(f"{state_name} annotation: {error}")
        if errors:
            faults[role] = errors

    if (
        locator.exists() or any(digest(path) != source_hashes[role] for role, path in paths.items())
        or digest(Path(plan["manifest_path"])) != plan["manifest_sha256"]
        or digest(neutral_request) != neutral_sha256 or digest(args.plan) != plan_sha256
    ):
        faults["custody"] = "encoded locator appeared or an original input changed"
    if "CandidateReopen" in phases and phases["CandidateReopen"]["passed"]:
        saved = phases["CandidateEdit"]["edited"]
        reopened = phases["CandidateReopen"]["rebuilt"]
        if saved["tree"] != reopened["tree"] or saved["annotations"] != reopened["annotations"]:
            faults["edit_reopen_continuity"] = "saved edit has different feature tree or view state after fresh rebuild"
    try:
        distinct_processes = check_processes(phases, plan["oracle_build"], args.executable_sha256)
    except ValueError as error:
        distinct_processes = None
        faults["processes"] = str(error)
    controls = ("ControlBefore", "EditControl", "ControlAfter")
    healthy = all(role in phases and role not in faults for role in controls)
    passed = not faults and distinct_processes == len(OBSERVE_ROLES) and healthy
    report = output / "Result.json"
    write_json(report, {
        "schema": "kit.sw2026.generated-top-annotation-native-observation.v1",
        "passed": passed, "controls_healthy": healthy, "distinct_native_processes": distinct_processes,
        "executable_sha256": args.executable_sha256, "plan_sha256": plan_sha256,
        "neutral_request_sha256": neutral_sha256,
        "candidate_manifest_sha256": plan["manifest_sha256"], "candidate_revision": plan["candidate_revision"],
        "original_preflight_sha256": args.preflight_sha256,
        "method_sha256": {path.name: digest(path) for path in (
            Path(__file__), Path(__file__).with_name("ObserveVendorBossCorpus.py"),
            Path(__file__).with_name("ObserveVendorBossPresentation.py"), Path(base.__file__),
        )},
        "source_hashes": source_hashes, "faults": faults, "phases": phases,
    })
    print(json.dumps({"passed": passed, "distinct_native_processes": distinct_processes, "result_sha256": digest(report), "fault_roles": list(faults)}))
    return 0 if passed else 1


if __name__ == "__main__":
    parser = ArgumentParser(description="Measure an isolated generated SOLIDWORKS Top annotation candidate")
    parser.add_argument("--root", type=Path, required=True)
    modes = parser.add_subparsers(dest="mode", required=True)
    batch = modes.add_parser("measure")
    for argument in ("plan", "output", "executable"):
        batch.add_argument(f"--{argument}", type=Path, required=True)
    batch.add_argument("--executable-sha256", required=True)
    batch.add_argument("--preflight", type=Path)
    batch.add_argument("--preflight-sha256")
    worker = modes.add_parser("phase")
    worker.add_argument("request", type=Path)
    worker.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.mode == "phase":
        raise SystemExit(phase(args.root, read_json(args.request), args.output, inspect=inspect))
    raise SystemExit(measure(args))
