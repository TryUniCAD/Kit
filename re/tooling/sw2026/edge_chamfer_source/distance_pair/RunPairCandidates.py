from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path, PureWindowsPath
import json
import os
import subprocess
import sys


HERE = Path(__file__).resolve()
METHODS = {
    "disclosed": (r"C:\KitChamferPairMethod04\Packet\ProbeJob.json",
                  "7a0b036c39e5aaa82283e1f1dffa67549965dc3f2916c7b06f5baccbe17eb726",
                  r"C:\KitChamferPairGenerated05\Packet\Candidates"),
    "heldout": (r"C:\KitChamferPairHeldout04\Packet\ProbeJob.json",
                "31473099e2efb94820f4580e59648e47c783775e5210276edc728fe134692982",
                r"C:\KitChamferPairHeldoutGenerated06\Packet\Candidates"),
}
PROTECTED_SOURCE = "42a343efb48020971424d5dac0e11a3c54297fd833329dd46c9a50955ad31846"
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
    cohort = manifest.get("cohort", "disclosed")
    _, _, destination = METHODS[cohort]
    destination = PureWindowsPath(destination)
    require(os.name == "nt" and manifest["schema"] == "kit.sw2026.distance-pair-neutral-build.v1"
            and PureWindowsPath(manifest["destination"]) == destination,
            "distance pair evaluation requires its exact guest-local candidate layout")
    if local:
        require(path.resolve() == Path(destination.parent / "Generated.json")
                and HERE.parent == path.parent, "distance pair evaluation must use its guest-local packet")
    rows = manifest["candidates"]
    spec, _ = method(cohort)
    require([row["name"] for row in rows] == [case["name"] + ".SLDPRT" for case in spec["cases"]]
            and [row["mode_word"] for row in rows] == [18, 2],
            "distance pair writer manifest does not cover both exact models")
    if cohort == "heldout":
        require(manifest["private_source_sha256"] == PROTECTED_SOURCE
                and manifest["writer_revision"] == "9e939d42ca5eaa9e71c1c253c255010c9ef9c99e" and local,
                "heldout generation must bind the earlier native source and exact prepared writer")
    require(all(row["guarded_processes"] == 2 and row["runtime_external_reads"] == 0 for row in rows),
            "distance pair candidates lack independent no-read generation")
    return manifest, raw


def stage(args):
    manifest, raw = load_manifest(args.job, args.pin, False)
    target = Path(PureWindowsPath(manifest["destination"]).parent)
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


def method(cohort):
    job, pin, _ = METHODS[cohort]
    path = Path(job)
    sys.path.insert(0, str(path.parent / "Tool"))
    from RunChamferPair import load_job

    return load_job(path, pin, local=True), path.parent


def phase(args):
    manifest, _ = load_manifest(args.job, args.pin, True)
    spec, packet = method(manifest.get("cohort", "disclosed"))
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
    edited = folder / (case["name"] + "Edited.SLDPRT")
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
    cohort = manifest.get("cohort", "disclosed")
    spec, method_packet = method(cohort)
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
                if all(state["tree"] == states[0]["tree"] and state["branch"] == states[0]["branch"]
                       and driver_identity(state) == driver_identity(states[0]) for state in states):
                    accepted.update(passed=True, tree_rows=len(states[0]["tree"]),
                                    drivers=driver_identity(states[0]), edited_sha256=source)
                    if cohort == "heldout":
                        from CompareLockedPair import compare_source

                        try:
                            accepted["native_source_comparisons"] = compare_source(
                                method_packet.parent / "Capture", spec["cases"][slot], states, PROTECTED_SOURCE,
                            )
                        except (ValueError, TypeError, KeyError) as error:
                            accepted.update(passed=False, lifecycle_failure=str(error))
                    elif states[0]["branch"] != [slot]:
                        accepted.update(passed=False, lifecycle_failure="disclosed orientation differs")
                else:
                    accepted["lifecycle_failure"] = "edit changed the tree, orientation or driver ownership"
            rows.append(accepted)
    after, _ = launch(args, capture / "control-after", "control-after", lifetimes)
    idle = not Swapp.application_pids() and not Swapp.owned_process_ids()
    passed = before["passed"] and after["passed"] and len(rows) == 2 and all(row["passed"] for row in rows)
    passed = passed and len(lifetimes) == len(set(lifetimes)) == 6 and idle
    report = {"schema":"kit.sw2026.distance-pair-generated-native.v1", "build": BUILD, "oracle_sha256": ORACLE,
              "runner_sha256": digest(HERE.read_bytes()), "generation_sha256": args.pin, "method_sha256": METHODS[cohort][1],
              "controls": [before, after], "candidates": rows, "heldout_writer_acceptance": cohort == "heldout" and passed,
              "passed": passed, "distinct_processes": len(set(lifetimes)), "idle_after": idle}
    raw = (json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    write_new(capture / "Result.json", raw)
    return {"passed": passed, "result_sha256": digest(raw), "distinct_processes": len(set(lifetimes))}


def publish(args):
    manifest, _ = load_manifest(args.job, args.pin, True)
    raw = pinned(args.job.parent.parent / "Capture" / "Result.json", args.result_pin)
    report = json.loads(raw)
    require(report["generation_sha256"] == args.pin and all(row["passed"] for row in report["controls"]),
            "distance pair report lacks passing bracket controls")
    if manifest.get("cohort", "disclosed") == "heldout":
        report["private_result_sha256"] = args.result_pin
        report["private_source_sha256"] = PROTECTED_SOURCE
        report["writer_revision"] = manifest["writer_revision"]
        for row in report["candidates"]:
            row.pop("drivers", None)
            row.pop("lifecycle_failure", None)
            for phase_result in row["phases"]:
                phase_result.pop("first_failure", None)
        raw = (json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    write_new(args.output, raw)
    return {"published_sha256": digest(raw), "passed": report["passed"]}


def main():
    parser = ArgumentParser()
    parser.add_argument("action", choices=("stage", "run", "worker", "publish"))
    parser.add_argument("--job", type=Path, required=True)
    parser.add_argument("--pin", required=True)
    parser.add_argument("--phase")
    parser.add_argument("--slot", type=int)
    parser.add_argument("--source")
    parser.add_argument("--result-pin")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.action == "worker":
        return 0 if phase(args) else 1
    actions = {"stage": stage, "run": evaluate, "publish": publish}
    print(json.dumps(actions[args.action](args), sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
