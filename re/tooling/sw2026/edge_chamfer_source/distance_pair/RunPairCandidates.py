from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path, PureWindowsPath
import json
import os
import subprocess
import sys


HERE = Path(__file__).resolve()
METHOD = PureWindowsPath(r"C:\KitChamferPairMethod04\Packet\ProbeJob.json")
METHOD_PIN = "7a0b036c39e5aaa82283e1f1dffa67549965dc3f2916c7b06f5baccbe17eb726"
DESTINATION = PureWindowsPath(r"C:\KitChamferPairGenerated05\Packet\Candidates")
PHASES = ("reopen-edit-save", "edited-reopen")


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(data):
    return sha256(data).hexdigest()


def write_new(path, payload):
    with path.open("xb") as target:
        target.write(payload)


def pinned(path, pin):
    raw = path.read_bytes()
    require(digest(raw) == pin, "distance pair candidate or manifest digest differs")
    return raw


def load_manifest(path, pin, local):
    raw = pinned(path, pin)
    manifest = json.loads(raw)
    require(os.name == "nt" and manifest["schema"] == "kit.sw2026.distance-pair-neutral-build.v1"
            and PureWindowsPath(manifest["destination"]) == DESTINATION,
            "distance pair evaluation requires its exact guest-local candidate layout")
    if local:
        require(path.resolve() == Path(DESTINATION.parent / "Generated.json")
                and HERE.parent == path.parent, "distance pair evaluation must use its guest-local packet")
    rows = manifest["candidates"]
    require([(row["name"], row["mode_word"]) for row in rows] ==
            [("EqualDistanceEdge.SLDPRT", 18), ("UnequalDistanceEdge.SLDPRT", 2)],
            "distance pair writer manifest does not cover both modes")
    require(all(row["guarded_processes"] == 2 and row["runtime_external_reads"] == 0 for row in rows),
            "distance pair candidates lack independent no-read generation")
    return manifest, raw


def stage(args):
    manifest, raw = load_manifest(args.job, args.pin, False)
    target = Path(DESTINATION.parent)
    require(not target.exists(), "distance pair candidate packet already exists")
    source = args.job.parent / "Candidates"
    files = {row["name"]: pinned(source / row["name"], row["archive_sha256"]) for row in manifest["candidates"]}
    target.mkdir(parents=True, exist_ok=False)
    (target / "Candidates").mkdir()
    for name, data in files.items():
        write_new(target / "Candidates" / name, data)
    write_new(target / args.job.name, raw)
    write_new(target / HERE.name, HERE.read_bytes())
    return {"staged": args.pin, "files": len(files), "runner_sha256": digest(HERE.read_bytes())}


def method():
    path = Path(METHOD)
    sys.path.insert(0, str(path.parent / "Tool"))
    from RunChamferPair import load_job

    return load_job(path, METHOD_PIN, local=True), path.parent


def phase(args):
    manifest, _ = load_manifest(args.job, args.pin, True)
    spec, packet = method()
    import Swapp
    from ChamferApi import installed_api
    from FilletSourcePhase import run_control
    from PairAuthor import PairAuthor, pair_plan
    from RunChamferSources import native_phase

    require(not Swapp.application_pids(), "distance pair requires a fresh SOLIDWORKS process")
    capture = args.job.parent.parent / "Capture"
    if args.phase in ("control-before", "control-after"):
        return run_control(packet / "Control.SLDPRT", capture / args.phase / "Record.json")
    require(args.slot in (0, 1) and args.phase in PHASES, "distance candidate phase is unbound")
    row = manifest["candidates"][args.slot]
    case = spec["cases"][args.slot]
    original = args.job.parent / "Candidates" / row["name"]
    folder = capture / str(args.slot)
    edited = folder / ("Edited-" + row["name"])
    constants, _ = installed_api(Swapp, distance_pair=True)
    pin = row["archive_sha256"] if args.phase == PHASES[0] else args.source
    return native_phase(case, pair_plan(case), args.phase, original, edited, pin,
                        folder / args.phase / "Record.json", constants, PairAuthor)


def launch(args, folder, name, lifetimes, slot=None, source=None):
    folder.mkdir(parents=True, exist_ok=False)
    command = [sys.executable, "-E", "-B", str(HERE), "worker", "--job", str(args.job),
               "--pin", args.pin, "--phase", name]
    if slot is not None:
        command.extend(("--slot", str(slot)))
    if source is not None:
        command.extend(("--source", source))
    try:
        result = subprocess.run(command, capture_output=True, timeout=180, check=False)
        status, stdout, stderr = result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired as error:
        status, stdout, stderr = None, error.stdout or b"", error.stderr or b""
    write_new(folder / "Stdout.txt", stdout)
    write_new(folder / "Stderr.txt", stderr)
    record_path = folder / "Record.json"
    data = record_path.read_bytes() if record_path.exists() else b""
    record = json.loads(data) if data else {}
    identity = record.get("oracle_identity")
    if identity:
        lifetimes.append((identity["process_id"], identity["process_creation_filetime"]))
        if status is None:
            from AuthorCurves import cleanup_owned_process
            from FilletPacket import ORACLE

            cleanup = cleanup_owned_process(identity, {"executable_sha256": ORACLE})
            write_new(folder / "TimeoutCleanup.json", json.dumps(cleanup, sort_keys=True).encode())
    row = {"phase": name, "passed": record.get("passed") is True and status == 0 and not stderr,
           "record_sha256": digest(data) if data else None, "native_sha256": record.get("native_sha256"),
           "first_failure": record.get("first_failure"), "checks": len(record.get("checks", ()))}
    return row, record


def evaluate(args):
    manifest, _ = load_manifest(args.job, args.pin, True)
    method()
    import Swapp
    from FilletPacket import BUILD, ORACLE
    from RunChamferSources import driver_identity

    require(not Swapp.application_pids(), "another SOLIDWORKS process is active")
    capture = args.job.parent.parent / "Capture"
    capture.mkdir(exist_ok=False)
    lifetimes, rows = [], []
    before, _ = launch(args, capture / "control-before", "control-before", lifetimes)
    if before["passed"]:
        for slot, candidate in enumerate(manifest["candidates"]):
            source = candidate["archive_sha256"]
            accepted = {"slot": slot, "candidate_sha256": source, "phases": [], "passed": False}
            records = []
            for name in PHASES:
                row, record = launch(args, capture / str(slot) / name, name, lifetimes, slot, source)
                accepted["phases"].append(row)
                if not row["passed"]:
                    break
                records.append(record)
                source = row["native_sha256"]
            else:
                states = (records[0]["reopened"], records[0]["edited"], records[1]["reopened"])
                if all(state["branch"] == [slot] and state["tree"] == states[0]["tree"]
                       and driver_identity(state) == driver_identity(states[0]) for state in states):
                    accepted.update(passed=True, tree_rows=len(states[0]["tree"]),
                                    drivers=driver_identity(states[0]), edited_sha256=source)
                else:
                    accepted["lifecycle_failure"] = "edit changed the tree, orientation or driver ownership"
            rows.append(accepted)
    after, _ = launch(args, capture / "control-after", "control-after", lifetimes)
    idle = not Swapp.application_pids() and not Swapp.owned_process_ids()
    passed = before["passed"] and after["passed"] and len(rows) == 2 and all(row["passed"] for row in rows)
    passed = passed and len(lifetimes) == len(set(lifetimes)) == 6 and idle
    report = {"schema":"kit.sw2026.distance-pair-generated-native.v1", "build": BUILD, "oracle_sha256": ORACLE,
              "runner_sha256": digest(HERE.read_bytes()), "generation_sha256": args.pin, "method_sha256": METHOD_PIN,
              "controls": [before, after], "candidates": rows, "heldout_writer_acceptance": False,
              "passed": passed, "distinct_processes": len(set(lifetimes)), "idle_after": idle}
    raw = (json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    write_new(capture / "Result.json", raw)
    return {"passed": passed, "result_sha256": digest(raw), "distinct_processes": len(set(lifetimes))}


def main():
    parser = ArgumentParser()
    parser.add_argument("action", choices=("stage", "run", "worker"))
    parser.add_argument("--job", type=Path, required=True)
    parser.add_argument("--pin", required=True)
    parser.add_argument("--phase")
    parser.add_argument("--slot", type=int)
    parser.add_argument("--source")
    args = parser.parse_args()
    if args.action == "worker":
        return 0 if phase(args) else 1
    print(json.dumps(stage(args) if args.action == "stage" else evaluate(args), sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
