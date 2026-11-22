from argparse import ArgumentParser
from pathlib import Path, PureWindowsPath
import json
import os
import subprocess
import sys


HERE = Path(__file__).resolve()
TOOL = HERE.parent
RESEARCH = HERE.parents[2]
sys.path[:0] = [str(TOOL), str(TOOL.parent), str(RESEARCH / "edge_fillet_source"), str(RESEARCH)]
from ChamferPacket import TOOLS, valid_hash, write_new
from FilletModel import require
from FilletPacket import BUILD, CONTROL, ORACLE, digest


SCHEMA = "kit.sw2026.chamfer-distance-source-probe.v1"
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


def write_bytes(path, data):
    with path.open("xb") as output:
        output.write(data)


def load_job(path, pin, *, local=False):
    require(path.name == "ProbeJob.json" and valid_hash(pin) and digest(path) == pin,
            "distance chamfer source job digest differs")
    packet = path.parent.resolve()
    spec = json.loads(path.read_bytes())
    require(spec["schema"] == SCHEMA and spec["build"] == BUILD and spec["executable_sha256"] == ORACLE
            and spec["cases"] == list(CASES) and valid_hash(spec["source_revision"], 40),
            "distance chamfer source job identity differs")
    root = PureWindowsPath(spec["guest_root"])
    require(root.drive.casefold() == "c:" and root.is_absolute() and len(root.parts) == 2,
            "distance chamfer needs a fresh shallow guest-local root")
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


def freeze(args):
    repo = HERE.parents[5]

    def git(*command):
        return subprocess.check_output(("git", "-C", str(repo), *command))

    revision = git("rev-parse", f"{args.revision}^{{commit}}").decode().strip()
    raw = args.control.read_bytes()
    require(digest(args.control) == CONTROL, "wrong known healthy control")
    packet = args.output.resolve()
    packet.mkdir(parents=True, exist_ok=False)
    (packet / "Tool").mkdir()
    for parent, names in PROBE_TOOLS.items():
        for name in names:
            write_bytes(packet / "Tool" / name, git("show", f"{revision}:{parent}/{name}"))
    write_bytes(packet / "Control.SLDPRT", raw)
    job = {"schema": SCHEMA, "build": BUILD, "executable_sha256": ORACLE, "cases": CASES,
           "source_revision": revision, "guest_root": args.guest_root,
           "files": {name: digest(packet / name) for name in sorted(FILES)}}
    manifest = packet / "ProbeJob.json"
    write_new(manifest, job)
    pin = digest(manifest)
    load_job(manifest, pin)
    return {"probe_job_sha256": pin, "source_revision": revision}


def stage(path, pin):
    spec = load_job(path, pin)
    require(os.name == "nt", "stage the native probe on the Windows guest")
    root = Path(spec["guest_root"])
    root.mkdir(exist_ok=False)
    target = root / "Packet"
    (target / "Tool").mkdir(parents=True)
    for name in sorted(FILES | {path.name}):
        write_bytes(target / name, (path.parent / name).read_bytes())
    load_job(target / path.name, pin)
    return {"staged": pin, "packet": str(target)}


def slot_paths(capture, slot):
    case = CASES[slot]
    name = case["name"]
    folder = capture / name
    return folder, folder / (name + ".SLDPRT"), folder / (name + "Edited.SLDPRT")


def run_worker(job, pin, phase, slot, source):
    load_job(job, pin, local=True)
    capture = job.parent.parent / "Capture"
    import Swapp
    from ChamferApi import installed_api
    from FilletSourcePhase import run_control
    from PairAuthor import PairAuthor, pair_plan
    from RunChamferSources import native_phase

    require(not Swapp.application_pids(), "another SOLIDWORKS process is active")
    if phase in ("control-before", "control-after"):
        return run_control(job.parent / "Control.SLDPRT", capture / phase / "Record.json")
    require(phase in PHASES and slot in range(len(CASES)), "native phase or source slot differs")
    case = CASES[slot]
    folder, before, after = slot_paths(capture, slot)
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
        for slot, case in enumerate(CASES):
            folder, original, edited = slot_paths(capture, slot)
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
    passing = (before["passed"] and after["passed"] and len(results) == len(CASES)
               and all(row["passed"] for row in results) and len(identities) == len(set(identities)) == 8)
    receipt = {"schema": SCHEMA, "oracle_build": BUILD, "oracle_sha256": ORACLE, "passed": passing,
               "source_revision": spec["source_revision"], "job_sha256": pin,
               "control_before": before, "control_after": after, "distinct_processes": len(set(identities)),
               "registered_api_sha256": digest(capture / "RegisteredApi.json"), "cases": results}
    target = capture / "Result.json"
    write_new(target, receipt)
    return {"passed": passing, "result_sha256": digest(target), "distinct_processes": len(set(identities))}


def publish(job, pin, result_pin, output):
    load_job(job, pin, local=True)
    result = job.parent.parent / "Capture" / "Result.json"
    require(valid_hash(result_pin) and digest(result) == result_pin, "native probe receipt changed")
    raw = result.read_bytes()
    report = json.loads(raw)
    require(report["job_sha256"] == pin and report["control_before"]["passed"]
            and report["control_after"]["passed"], "healthy controls must bracket both measurements")
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
    for name in ("stage", "run", "worker", "publish"):
        command = commands.add_parser(name)
        command.add_argument("--job", type=Path, required=True)
        command.add_argument("--pin", required=True)
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
    elif args.action == "run":
        result = run_batch(args.job, args.pin)
    else:
        result = publish(args.job, args.pin, args.result_pin, args.output)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
