import argparse
import json
import subprocess
import sys

from pathlib import Path

from FilletModel import require
from FilletPacket import BUILD, CONTROL, ORACLE, digest

from ChamferPacket import local_roots, stage_guest, valid_hash, verify, write_new

PHASES = ("author", "reopen-edit-save", "edited-reopen")
CONTROLS = ("control-before", "control-after")


def case_paths(capture, slot, case):
    folder = capture / f"Slot{slot + 1:02d}"
    return folder, folder / (case["name"] + ".SLDPRT"), folder / (case["name"] + "Edited.SLDPRT")


def native_phase(case, plan, phase, initial, edited, source_hash, record, constants, author_type=None):
    import Swapp
    from AuthorCurves import Recorder
    from FilletSourcePhase import has_exact_identity, save_part
    from OracleIdentity import application_identity
    from ChamferAuthor import ChamferAuthor

    rec = Recorder(record, {"phase": phase, "case": case})
    rec.data.update(schema="kit.sw2026.edge-chamfer-source-phase.v1", writer_output_count=0)
    session, complete = None, False
    source = edited if phase == "edited-reopen" else initial
    target = initial if phase == "author" else edited
    with Swapp.Dismisser() as monitor:
        try:
            if phase == "author":
                require(not initial.exists() and not edited.exists(), "fresh native capture destination already exists")
            else:
                require(source.is_file() and digest(source) == source_hash, "immutable native phase input differs")
            session = rec.call("launch isolated SOLIDWORKS .34 COM", Swapp.Sw)
            identity = rec.call("exact native executable identity", application_identity, session.app)
            rec.data["oracle_identity"] = identity
            rec.flush()
            require(has_exact_identity(identity) and session.revision == "34.5.2", "incorrect native executable or build")
            author = (author_type or ChamferAuthor)(session.app, rec, constants)
            if phase == "author":
                author.author(case, session, plan["stock"])
                author.snapshot(case, plan, "authored")
            else:
                author.model, errors, warnings = rec.call("open exact native source", session.open, source,
                                                           read_only=phase == "edited-reopen")
                rec.data["open_status"] = {"opened": author.model is not None, "errors": errors, "warnings": warnings}
                rec.flush()
                require(author.model is not None and errors == warnings == 0, "native open failed or warned")
                require(Path(str(author.get(author.model, "GetPathName"))).resolve() == source.resolve(),
                        "native open returned a different source document")
                cold = {"solid_bodies": int(rec.call("cold solid body count", Swapp.bodies, author.model)),
                        "diagnostics": int(author.get(author.get(author.model, "Extension"), "GetWhatsWrongCount"))}
                rec.data["before_explicit_rebuild"] = cold
                rec.flush()
                require(cold == {"solid_bodies": 1, "diagnostics": 0}, "cold open lost its solid or had diagnostics")
                author.snapshot(case, plan, "reopened", edited=phase == "edited-reopen")
                if phase == "reopen-edit-save":
                    author.edit(case)
                    author.snapshot(case, plan, "edited", edited=True)
            if phase != "edited-reopen":
                save_part(session, rec, author, target)
            complete = True
        except Exception as error:
            rec.failure(error)
        finally:
            if session is not None:
                try:
                    session.close()
                except Exception as error:
                    rec.failure(error, cleanup=True)
                rec.data["controller_diagnostics"] = session.diagnostics
    artifact = source if phase == "edited-reopen" else target
    rec.data["dialogs"] = monitor.log
    rec.data["source_immutable"] = phase == "author" or (source.is_file() and digest(source) == source_hash)
    if artifact.is_file():
        rec.data.update(native_sha256=digest(artifact), native_bytes=artifact.stat().st_size)
    rec.data["passed"] = bool(complete and rec.data["source_immutable"] and rec.data.get("native_sha256")
                              and not rec.data["first_failure"] and not rec.data["cleanup_errors"]
                              and not rec.data["dialogs"] and not rec.data.get("controller_diagnostics"))
    rec.flush()
    return rec.data["passed"]


def phase_worker(job_path, pin, phase, slot, source_hash):
    job, cases, plans = verify(job_path, pin, private=True)
    packet, capture = local_roots(job_path, job)
    if phase in CONTROLS:
        require(slot is None and source_hash is None, "control request unexpectedly has a source")
        folder = capture / phase
    else:
        require(phase in PHASES and slot is not None and 0 <= slot < len(cases), "invalid source phase or slot")
        require(source_hash is None if phase == "author" else valid_hash(source_hash), "phase source pin differs")
        base, initial, edited = case_paths(capture, slot, cases[slot])
        folder = base / phase
    require(folder.is_dir() and folder.resolve() == folder and not (folder / "Record.json").exists(),
            "phase receipt destination is unowned or already exists")
    if phase in CONTROLS:
        from FilletSourcePhase import run_control

        return run_control(packet / "Control.SLDPRT", folder / "Record.json")
    import Swapp
    from ChamferApi import installed_api

    constants, api = installed_api(Swapp)
    require(api == json.loads((capture / "RegisteredApi.json").read_bytes()), "registered API changed after preflight")
    return native_phase(cases[slot], plans[slot], phase, initial, edited, source_hash, folder / "Record.json", constants)


def launch(job, pin, folder, phase, processes, slot=None, source=None):
    folder.mkdir(parents=True, exist_ok=False)
    entry = {"phase": phase, "slot": slot, "source_sha256": source, "job_sha256": pin}
    write_new(folder / "Phase.json", entry)
    command = [sys.executable, "-E", "-B", str(Path(__file__).resolve()), "--job", str(job), "--pin", pin, "--phase", phase]
    if slot is not None:
        command.extend(("--slot", str(slot)))
    if source is not None:
        command.extend(("--source", source))
    try:
        result = subprocess.run(command, capture_output=True, timeout=180, check=False)
        code, stdout, stderr = result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired as error:
        code, stdout, stderr = None, error.stdout or b"", error.stderr or b""
    with (folder / "Stdout.txt").open("xb") as stream:
        stream.write(stdout)
    with (folder / "Stderr.txt").open("xb") as stream:
        stream.write(stderr)
    record = folder / "Record.json"
    data = json.loads(record.read_bytes()) if record.is_file() else {}
    identity = data.get("oracle_identity")
    if identity:
        processes.append((identity["process_id"], identity["process_creation_filetime"]))
    if code is None and identity:
        from AuthorCurves import cleanup_owned_process

        try:
            recovery = cleanup_owned_process(identity, {"executable_sha256": ORACLE})
        except Exception as error:
            recovery = {"error": repr(error)}
        write_new(folder / "TimeoutCleanup.json", recovery)
    summary = entry | {"passed": code == 0 and not stderr and data.get("passed") is True,
                       "worker_exit_code": code, "timed_out": code is None,
                       "receipt_sha256": digest(record) if record.is_file() else None,
                       "artifact_sha256": data.get("native_sha256"), "artifact_bytes": data.get("native_bytes"),
                       "checks": len(data.get("checks", ())),
                       "checks_passed": sum(row["passed"] for row in data.get("checks", ()))}
    return summary, data


def driver_identity(state):
    return {role: [row["name"].split("@")[0], row["name"].split("@")[1], row["display_kind"], row["index"]]
            for role, row in state["drivers"].items()}


def verify_lifecycle(initial, edited, receipts):
    first, second, third = receipts
    states = (first["authored"], second["reopened"], second["edited"], third["reopened"])
    baseline = states[0]
    require(digest(initial) == first["native_sha256"] and digest(edited) == second["native_sha256"] == third["native_sha256"]
            and first["native_sha256"] != second["native_sha256"], "original or derivative changed outside its owned phase")
    require(all(row["tree"] == baseline["tree"] and row["configurations"] == baseline["configurations"]
                and row["branch"] == baseline["branch"] and driver_identity(row) == driver_identity(baseline)
                and row["definition"]["parents"] == baseline["definition"]["parents"] for row in states),
            "native lifecycle changed full tree, owner, analytic orientation or driver identity")
    require(states[0]["body"]["native"]["volume"] != states[3]["body"]["native"]["volume"],
            "the one persisted driving edit did not change the actual solid volume")
    return {"tree_rows": len(baseline["tree"]), "orientation": baseline["branch"], "snapshots": len(states),
            "original_sha256": first["native_sha256"], "edited_sha256": third["native_sha256"]}


def run_case(job, pin, capture, slot, case, processes):
    folder, initial, edited = case_paths(capture, slot, case)
    rows, receipts, source = [], [], None
    for phase in PHASES:
        row, data = launch(job, pin, folder / phase, phase, processes, slot, source)
        rows.append(row)
        receipts.append(data)
        if not row["passed"]:
            return {"slot": slot, "phases": rows, "passed": False}
        source = row["artifact_sha256"]
    try:
        lifecycle = verify_lifecycle(initial, edited, receipts)
    except ValueError as error:
        write_new(folder / "LifecycleFailure.json", {"error": str(error)})
        return {"slot": slot, "phases": rows, "passed": False, "lifecycle_failed": True}
    return {"slot": slot, "phases": rows, "passed": True} | lifecycle


def execute(job_path, pin):
    job, cases, _ = verify(job_path, pin, private=True)
    _, capture = local_roots(job_path, job)
    import Swapp
    from ChamferApi import installed_api

    require(not capture.exists() and not Swapp.application_pids(), "capture already exists or native application is active")
    capture.mkdir(parents=True, exist_ok=False)
    lock = {"schema": "kit.sw2026.edge-chamfer-source-lock.v1", "cohort": job["cohort"], "job_sha256": pin,
            "source_revision": job["source_revision"], "source_tree": job["source_tree"], "oracle_build": BUILD,
            "oracle_sha256": ORACLE, "control_sha256": CONTROL, "spec_sha256": job["files"]["Spec.json"]["sha256"],
            "prediction_sha256": job["files"]["Predictions.json"]["sha256"], "controls": {}, "sources": [],
            "api_sha256": None, "writer_output_count": 0, "heldout_writer_acceptance": False}
    processes = []
    try:
        before, _ = launch(job_path, pin, capture / CONTROLS[0], CONTROLS[0], processes)
        lock["controls"]["before"] = before
        if before["passed"]:
            _, api = installed_api(Swapp)
            api_path = capture / "RegisteredApi.json"
            write_new(api_path, api)
            lock["api_sha256"] = digest(api_path)
            for slot, case in enumerate(cases):
                result = run_case(job_path, pin, capture, slot, case, processes)
                lock["sources"].append(result)
                if not result["passed"]:
                    break
    except Exception as error:
        write_new(capture / "BatchFailure.json", {"error": repr(error)})
        lock["batch_failure"] = True
    finally:
        try:
            after, _ = launch(job_path, pin, capture / CONTROLS[1], CONTROLS[1], processes)
            lock["controls"]["after"] = after
        except Exception as error:
            write_new(capture / "ControlFailure.json", {"error": repr(error)})
            lock["controls"]["after"] = {"passed": False}
    lock["idle_after"] = not Swapp.application_pids() and not Swapp.owned_process_ids()
    try:
        lock["inputs_unchanged"] = verify(job_path, pin, private=True)[0] == job
    except Exception as error:
        write_new(capture / "InputCustodyFailure.json", {"error": repr(error)})
        lock["inputs_unchanged"] = False
    lock["fresh_processes"], lock["distinct_processes"] = len(processes), len(set(processes))
    lock["passed"] = bool(not lock.get("batch_failure") and lock["idle_after"] and lock["inputs_unchanged"]
                          and lock["fresh_processes"] == lock["distinct_processes"] == 8
                          and all(lock["controls"].get(key, {}).get("passed") for key in ("before", "after"))
                          and len(lock["sources"]) == len(cases) and all(row["passed"] for row in lock["sources"]))
    report = capture / "SourceLock.json"
    write_new(report, lock)
    return {"source_lock_sha256": digest(report), "passed": lock["passed"], "distinct_processes": lock["distinct_processes"],
            "sources": len(lock["sources"]), "writer_output_count": 0}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--job", type=Path, required=True)
    parser.add_argument("--pin", required=True)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--verify-packet", action="store_true")
    modes.add_argument("--stage-guest", action="store_true")
    modes.add_argument("--phase", choices=(*PHASES, *CONTROLS))
    parser.add_argument("--slot", type=int)
    parser.add_argument("--source")
    args = parser.parse_args()
    if args.verify_packet:
        job, _, _ = verify(args.job, args.pin)
        result = {"job_sha256": args.pin, "bound_files": len(job["files"]), "native_processes": 0}
    elif args.stage_guest:
        result = stage_guest(args.job, args.pin)
    elif args.phase:
        return int(not phase_worker(args.job, args.pin, args.phase, args.slot, args.source))
    else:
        result = execute(args.job, args.pin)
    print(json.dumps(result, allow_nan=False))
    return int(not result.get("passed", True))


if __name__ == "__main__":
    raise SystemExit(main())
