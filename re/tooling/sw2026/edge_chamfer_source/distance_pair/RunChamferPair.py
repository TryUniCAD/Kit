from argparse import ArgumentParser
from pathlib import Path, PureWindowsPath
import json
from math import isfinite
import os
import re
import secrets
import subprocess
import sys


HERE = Path(__file__).resolve()
TOOL = HERE.parent
RESEARCH = HERE.parents[2]
sys.path[:0] = [str(TOOL), str(TOOL.parent), str(RESEARCH / "edge_fillet_source"), str(RESEARCH)]
from ChamferPacket import TOOLS, valid_hash, write_new
from FilletModel import require
from FilletPacket import BUILD, CONTROL, ORACLE, digest


SCHEMA = "kit.sw2026.chamfer-distance-source-probe.v3"
FAMILY = "re/tooling/sw2026/edge_chamfer_source/distance_pair"
PROBE_TOOLS = TOOLS | {FAMILY: ("PairAuthor.py", HERE.name)}
FILES = {f"Tool/{name}" for values in PROBE_TOOLS.values() for name in values} | {"Control.SLDPRT"}
PHASES = ("author", "reopen-edit-save", "edited-reopen")
STOCK = {"center_mm": [11.25, -8.125], "size_mm": [65.25, 45.5, 18.75],
         "edge_axis": "z", "corner": {"x": "max", "y": "max"}}
CASES = (
    STOCK | {"name": "EqualDistanceEdge", "equal": True, "distances_mm": [4.875, 4.875], "edit_mm": 6.125},
    STOCK | {"name": "UnequalDistanceEdge", "equal": False, "distances_mm": [4.875, 8.375], "edit_mm": 9.625},
)
DISCLOSED_PINS = (
    ("EqualDistanceEdge", "d8ff6c2678c05c88f52a3d10e10e1ccdd84fb52a9b374bf7542be868f4215390"),
    ("UnequalDistanceEdge", "d1892bc383b88c4d0b4a48d2fa768c2274a70f755068e218a28ca6475fb45b51"),
)


def write_bytes(path, data):
    with path.open("xb") as output:
        output.write(data)


def validate_pair(cases):
    require(type(cases) is list and len(cases) == 2, "distance source needs two cases")
    for slot, case in enumerate(cases):
        require(case.keys() == CASES[slot].keys() and case["equal"] is (slot == 0)
                and isinstance(case["name"], str) and re.fullmatch(r"[A-Za-z][A-Za-z0-9]{1,47}", case["name"]),
                "distance source names, domains or equality differ")
        center, size = case["center_mm"], case["size_mm"]
        pair, edit = case["distances_mm"], case["edit_mm"]
        axis, corner = case["edge_axis"], case["corner"]
        require(type(center) is type(size) is type(pair) is list
                and (len(center), len(size), len(pair)) == (2, 3, 2) and axis in ("x", "y", "z")
                and set(corner) == set("xyz") - {axis} and set(corner.values()) <= {"min", "max"}
                and all(type(value) in (int, float) and isfinite(value) for value in (*center, *size, *pair, edit))
                and all(abs(value) < 70 for value in center) and all(10 <= value <= 100 for value in size),
                "distance source stock or edge role differs")
        limit = min(width for direction, width in zip("xyz", size, strict=True) if axis != direction)
        require(min(*pair, edit) >= 0.5 and max(*pair, edit) < limit * 0.45 and edit != pair[1]
                and (pair[0] == pair[1]) is case["equal"] and (case["equal"] or pair[0] != edit),
                "distance source edit and geometric envelope differ")
    require(len({case["name"].casefold() for case in cases}) == 2, "distance source names overlap")


def load_job(path, pin, *, local=False):
    require(path.name == "ProbeJob.json" and valid_hash(pin) and digest(path) == pin,
            "distance chamfer source job digest differs")
    packet = path.parent.resolve()
    spec = json.loads(path.read_bytes())
    require(spec["schema"] == SCHEMA and spec["build"] == BUILD and spec["executable_sha256"] == ORACLE
            and valid_hash(spec["source_revision"], 40) and valid_hash(spec["source_tree"], 40),
            "distance chamfer source job identity differs")
    require(spec["slots"] in ([0], [1], [0, 1]), "distance chamfer case selection differs")
    validate_pair(spec["cases"])
    root = PureWindowsPath(spec["guest_root"])
    require(root.drive.casefold() == "c:" and root.is_absolute() and len(root.parts) == 2,
            "distance chamfer needs a fresh shallow guest-local root")
    if spec["cohort"] == "heldout":
        require(os.name == "nt" and packet == Path(root) / "Packet"
                and spec["slots"] == [0, 1] and valid_hash(spec["method_job_sha256"])
                and spec["disclosed_result_sha256"] == [expected for _, expected in DISCLOSED_PINS],
                "protected distance cases must stay in their guest-local packet")
    else:
        require(spec["cohort"] == "disclosed" and spec["cases"] == list(CASES),
                "disclosed distance case inputs differ")
    if local:
        require(os.name == "nt" and packet == Path(root) / "Packet" and TOOL == packet / "Tool",
                "distance chamfer must use the verified guest-local packet")
    require(spec["files"].keys() == FILES and spec["files"]["Control.SLDPRT"] == CONTROL
            and {item.relative_to(packet).as_posix() for item in packet.rglob("*") if item.is_file()}
            == FILES | {path.name}, "distance chamfer packet inventory differs")
    for relative, sha in spec["files"].items():
        member = packet / relative
        require(member.resolve() == member and digest(member) == sha, f"packet hash differs: {relative}")
    return spec


def make_packet(packet, job, data):
    require(set(data) == FILES, "distance chamfer packet closure differs")
    packet.mkdir(parents=True, exist_ok=False)
    (packet / "Tool").mkdir()
    for name, raw in data.items():
        write_bytes(packet / name, raw)
    job["files"] = {name: digest(packet / name) for name in sorted(FILES)}
    manifest = packet / "ProbeJob.json"
    write_new(manifest, job)
    pin = digest(manifest)
    load_job(manifest, pin)
    return {"probe_job_sha256": pin, "source_revision": job["source_revision"]}


def freeze(args):
    repo = HERE.parents[5]

    def git(*command):
        return subprocess.check_output(("git", "-C", str(repo), *command))

    revision = git("rev-parse", f"{args.revision}^{{commit}}").decode().strip()
    raw = args.control.read_bytes()
    require(digest(args.control) == CONTROL, "wrong known healthy control")
    data = {"Control.SLDPRT": raw}
    for parent, names in PROBE_TOOLS.items():
        for name in names:
            data[f"Tool/{name}"] = git("show", f"{revision}:{parent}/{name}")
    slots = list(range(len(CASES))) if args.slot is None else [args.slot]
    job = {"schema": SCHEMA, "build": BUILD, "executable_sha256": ORACLE, "cases": list(CASES), "slots": slots,
           "source_revision": revision, "source_tree": git("rev-parse", f"{revision}^{{tree}}").decode().strip(),
           "guest_root": args.guest_root, "cohort": "disclosed"}
    return make_packet(args.output.resolve(), job, data)


def private_cases():
    random = secrets.SystemRandom()

    def sample(low, high):
        return random.randint(low, high) / 16

    shared = sample(53, 87)
    return [
        {"name": "Pair" + secrets.token_hex(6), "center_mm": [sample(-491, -406), sample(273, 363)],
         "size_mm": [sample(922, 1057), sample(633, 721), sample(405, 487)],
         "edge_axis": "z", "corner": {"x": "min", "y": "min"}, "equal": True,
         "distances_mm": [shared, shared], "edit_mm": sample(103, 127)},
        {"name": "Pair" + secrets.token_hex(6), "center_mm": [sample(515, 625), sample(-212, -163)],
         "size_mm": [sample(647, 731), sample(1155, 1239), sample(569, 663)],
         "edge_axis": "z", "corner": {"x": "max", "y": "min"}, "equal": False,
         "distances_mm": [sample(57, 81), sample(122, 155)], "edit_mm": sample(170, 191)},
    ]


def seal(args):
    spec = load_job(args.job, args.pin, local=True)
    require(spec["cohort"] == "disclosed", "protected distance method must be a disclosed packet")
    for (case, pin), path in zip(DISCLOSED_PINS, (args.equal_result, args.unequal_result), strict=True):
        raw = path.read_bytes()
        require(path.resolve().drive.casefold() == "c:" and digest(path) == pin,
                "disclosed distance result custody differs")
        result = json.loads(raw)
        (match,) = [row for row in result["cases"] if row["case"] == case]
        require(result["oracle_build"] == BUILD and result["oracle_sha256"] == ORACLE
                and result["control_before"]["passed"] is True and result["control_after"]["passed"] is True
                and match["passed"] is True and match["snapshots"] == 4,
                "disclosed distance lifecycle does not authorize protected authoring")
    root = PureWindowsPath(args.guest_root)
    require(root.drive.casefold() == "c:" and root.is_absolute() and len(root.parts) == 2,
            "protected distance packet requires a fresh shallow guest-local root")
    protected = spec | {"cohort": "heldout", "slots": [0, 1], "cases": private_cases(),
                        "guest_root": str(root), "method_job_sha256": args.pin,
                        "disclosed_result_sha256": [pin for _, pin in DISCLOSED_PINS]}
    data = {name: (args.job.parent / name).read_bytes() for name in FILES}
    return make_packet(Path(root) / "Packet", protected, data)


def stage(path, pin):
    spec = load_job(path, pin)
    require(os.name == "nt" and spec["cohort"] == "disclosed",
            "stage a disclosed method packet on the Windows guest")
    root = Path(spec["guest_root"])
    root.mkdir(exist_ok=False)
    target = root / "Packet"
    (target / "Tool").mkdir(parents=True)
    for name in sorted(FILES | {path.name}):
        write_bytes(target / name, (path.parent / name).read_bytes())
    load_job(target / path.name, pin)
    return {"staged": pin, "packet": str(target)}


def slot_paths(capture, case):
    name = case["name"]
    folder = capture / name
    return folder, folder / (name + ".SLDPRT"), folder / (name + "Edited.SLDPRT")


def run_worker(job, pin, phase, slot, source):
    spec = load_job(job, pin, local=True)
    capture = job.parent.parent / "Capture"
    import Swapp
    from ChamferApi import installed_api
    from FilletSourcePhase import run_control
    from PairAuthor import PairAuthor, pair_plan
    from RunChamferSources import native_phase

    require(not Swapp.application_pids(), "another SOLIDWORKS process is active")
    if phase in ("control-before", "control-after"):
        return run_control(job.parent / "Control.SLDPRT", capture / phase / "Record.json")
    require(phase in PHASES and slot in spec["slots"], "native phase or source slot differs")
    case = spec["cases"][slot]
    folder, before, after = slot_paths(capture, case)
    constants, api = installed_api(Swapp, distance_pair=True)
    require(api == json.loads((capture / "RegisteredApi.json").read_bytes()), "registered distance chamfer API differs")
    return native_phase(case, pair_plan(case), phase, before, after, source,
                        folder / phase / "Record.json", constants, PairAuthor)


def launch(job, pin, folder, phase, identities, slot=None, source=None):
    folder.mkdir(parents=True, exist_ok=False)
    command = [sys.executable, "-E", "-B", str(HERE), "worker", "--job", str(job), "--pin", pin, "--phase", phase]
    if slot is not None:
        command.extend(["--slot", str(slot)])
    if source:
        command.extend(["--source", source])
    try:
        run = subprocess.run(command, capture_output=True, timeout=180, check=False)
        code, out, err = run.returncode, run.stdout, run.stderr
    except subprocess.TimeoutExpired as error:
        code, out, err = None, error.stdout or b"", error.stderr or b""
    write_bytes(folder / "Stdout.txt", out)
    write_bytes(folder / "Stderr.txt", err)
    record_path = folder / "Record.json"
    record = json.loads(record_path.read_bytes()) if record_path.is_file() else {}
    identity = record.get("oracle_identity")
    if identity:
        identities.append((identity["process_id"], identity["process_creation_filetime"]))
        if code is None:
            from AuthorCurves import cleanup_owned_process

            try:
                cleanup = cleanup_owned_process(identity, {"executable_sha256": ORACLE})
            except Exception as error:
                cleanup = {"error": str(error)}
            write_new(folder / "TimeoutCleanup.json", cleanup)
    return record, {"phase": phase, "passed": record.get("passed") is True and code == 0 and not err,
                    "artifact_sha256": record.get("native_sha256"), "return_code": code,
                    "record_sha256": digest(record_path) if record else None,
                    "first_failure": record.get("first_failure")}


def run_batch(job, pin):
    spec = load_job(job, pin, local=True)
    import Swapp
    from ChamferApi import installed_api
    from RunChamferSources import driver_identity, verify_lifecycle

    require(not Swapp.application_pids(), "another SOLIDWORKS process is active")
    _, api = installed_api(Swapp, distance_pair=True)
    capture = job.parent.parent / "Capture"
    capture.mkdir(exist_ok=False)
    write_new(capture / "RegisteredApi.json", api)
    identities = []
    _, before = launch(job, pin, capture / "control-before", "control-before", identities)
    results = []
    if before["passed"]:
        for slot in spec["slots"]:
            case = spec["cases"][slot]
            folder, original, edited = slot_paths(capture, case)
            receipts, rows, source = [], [], None
            result = {"case": case["name"], "phases": rows, "passed": False}
            for phase in PHASES:
                data, row = launch(job, pin, folder / phase, phase, identities, slot, source)
                receipts.append(data)
                rows.append(row)
                if not row["passed"]:
                    break
                source = row["artifact_sha256"]
            else:
                try:
                    result |= verify_lifecycle(original, edited, receipts)
                except ValueError as error:
                    result["lifecycle_failure"] = str(error)
                else:
                    result["native_definition"] = receipts[0]["authored"]["definition"]["fields"]
                    result["drivers"] = driver_identity(receipts[0]["authored"])
                    result["passed"] = True
            results.append(result)
    _, after = launch(job, pin, capture / "control-after", "control-after", identities)
    expected = 2 + len(PHASES) * len(spec["slots"])
    idle = not Swapp.application_pids() and not Swapp.owned_process_ids()
    unchanged = load_job(job, pin, local=True) == spec
    passing = (before["passed"] and after["passed"] and len(results) == len(spec["slots"])
               and all(row["passed"] for row in results) and len(identities) == len(set(identities)) == expected
               and idle and unchanged)
    receipt = {"schema": SCHEMA, "cohort": spec["cohort"], "oracle_build": BUILD, "oracle_sha256": ORACLE, "passed": passing,
               "source_revision": spec["source_revision"], "source_tree": spec["source_tree"], "job_sha256": pin,
               "control_before": before, "control_after": after, "distinct_processes": len(set(identities)),
               "registered_api_sha256": digest(capture / "RegisteredApi.json"), "case_slots": spec["slots"],
               "idle_after": idle, "inputs_unchanged": unchanged, "cases": results}
    target = capture / "Result.json"
    write_new(target, receipt)
    return {"passed": passing, "result_sha256": digest(target), "distinct_processes": len(set(identities))}


def publish(job, pin, result_pin, output):
    spec = load_job(job, pin, local=True)
    result = job.parent.parent / "Capture" / "Result.json"
    require(valid_hash(result_pin) and digest(result) == result_pin, "native probe receipt changed")
    raw = result.read_bytes()
    report = json.loads(raw)
    require(report["job_sha256"] == pin and report["case_slots"] == spec["slots"] and report["control_before"]["passed"]
            and report["control_after"]["passed"], "healthy controls must bracket both measurements")
    if spec["cohort"] == "heldout":
        visible = {key: report[key] for key in ("schema", "cohort", "oracle_build", "oracle_sha256", "passed",
                                                 "source_revision", "source_tree", "job_sha256", "registered_api_sha256",
                                                 "distinct_processes", "case_slots", "idle_after", "inputs_unchanged")}
        visible.update(private_result_sha256=result_pin, method_job_sha256=spec["method_job_sha256"],
                       disclosed_result_sha256=spec["disclosed_result_sha256"], writer_output_count=0,
                       heldout_writer_acceptance=False, control_sha256=CONTROL,
                       controls={side: report["control_" + side]["record_sha256"] for side in ("before", "after")},
                       slots=[{key: row.get(key) for key in
                               ("passed", "snapshots", "tree_rows", "original_sha256", "edited_sha256")}
                              | {"phases": [{key: phase[key] for key in ("phase", "passed", "record_sha256")}
                                            for phase in row["phases"]]}
                              for row in report["cases"]])
        write_new(output, visible)
    else:
        write_bytes(output, raw)
    return {"receipt_sha256": digest(output), "passed": report["passed"]}


def main():
    parser = ArgumentParser()
    commands = parser.add_subparsers(dest="action", required=True)
    create = commands.add_parser("freeze")
    create.add_argument("--output", type=Path, required=True)
    create.add_argument("--control", type=Path, required=True)
    create.add_argument("--guest-root", required=True)
    create.add_argument("--revision", default="HEAD")
    create.add_argument("--slot", type=int, choices=range(len(CASES)))
    for name in ("stage", "seal", "run", "worker", "publish"):
        command = commands.add_parser(name)
        command.add_argument("--job", type=Path, required=True)
        command.add_argument("--pin", required=True)
        if name == "seal":
            command.add_argument("--guest-root", required=True)
            command.add_argument("--equal-result", type=Path, required=True)
            command.add_argument("--unequal-result", type=Path, required=True)
        if name == "worker":
            command.add_argument("--phase", required=True)
            command.add_argument("--slot", type=int)
            command.add_argument("--source")
        if name == "publish":
            command.add_argument("--result-pin", required=True)
            command.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.action == "worker":
        return 0 if run_worker(args.job, args.pin, args.phase, args.slot, args.source) else 1
    if args.action == "freeze":
        result = freeze(args)
    elif args.action == "stage":
        result = stage(args.job, args.pin)
    elif args.action == "seal":
        result = seal(args)
    elif args.action == "run":
        result = run_batch(args.job, args.pin)
    else:
        result = publish(args.job, args.pin, args.result_pin, args.output)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
