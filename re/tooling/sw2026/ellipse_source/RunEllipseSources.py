import argparse
import json
import os
import secrets
import subprocess
import sys
import time
from pathlib import Path, PureWindowsPath

from EllipseModel import require
from EllipsePacket import (
    BUILD, CONTROLS, FILES, LOCK, ORACLE, SHARE, create, encode, guest_paths, local_paths,
    model_files, pinned_json, predictions_equal, put, sha, stage, valid_hash, verify,
)


PHASES = ("author", "reopen-edit-save", "edited-reopen")


def exact(identity):
    return (identity.get("file_version"), identity.get("sha256"), identity.get("pe_machine"),
            identity.get("version_matches")) == (BUILD, ORACLE, "0x8664", True)


def control(path, record, pin):
    from AuthorCurves import write_json
    from InspectFresh import healthy, inspect

    require(sha(path) == pin, "control source was changed")
    data = {}
    try:
        inspect(path, result=data, checkpoint=lambda: write_json(record, data))
    except Exception as error:
        data["exception"] = repr(error)
    data["passed"] = bool(healthy(data) and exact(data.get("oracle_identity", {})) and sha(path) == pin)
    write_json(record, data)
    return data["passed"]


def paths(capture, slot, case):
    folder = capture / f"Slot{slot + 1:02d}"
    return folder, folder / f"{case['name']}.SLDPRT", folder / f"{case['name']}Edited.SLDPRT"


def native_phase(phase, record, initial, edited, pin, plan, constants):
    import Swapp
    from AuthorCurves import Recorder
    from EllipseAuthor import EllipseAuthor
    from OracleIdentity import application_identity

    rec = Recorder(record, {"phase": phase, "source_sha256": pin})
    rec.data.update(schema="kit.sw2026.full-ellipse-blind-boss-source-phase.v1", writer_output_count=0)
    session, complete = None, False
    source = edited if phase == "edited-reopen" else initial
    target = initial if phase == "author" else edited
    with Swapp.Dismisser() as monitor:
        try:
            if phase == "author":
                require(not initial.exists() and not edited.exists(), "authoring requires absent native destinations")
            else:
                require(source.is_file() and sha(source) == pin, "native source changed before open")
            session = rec.call("launch exact isolated .34 COM", Swapp.Sw)
            identity = rec.call("measure native process identity", application_identity, session.app)
            rec.data["oracle_identity"] = identity
            rec.flush()
            require(exact(identity) and session.revision == "34.5.2", "wrong native oracle or build")
            author = EllipseAuthor(session.app, rec, constants)
            if phase == "author":
                author.author(session, plan)
                author.snapshot("authored", plan)
            else:
                author.model, errors, warnings = rec.call("open immutable native component", session.open, source,
                                                           read_only=phase == "edited-reopen")
                rec.data["open_status"] = {"opened": author.model is not None, "errors": errors, "warnings": warnings}
                rec.flush()
                require(author.model is not None and errors == warnings == 0, "native open failed or issued a diagnostic")
                require(Path(str(author.get(author.model, "GetPathName"))).resolve() == source,
                        "native open returned the wrong document")
                cold = {"solids": rec.call("cold solid count", Swapp.bodies, author.model),
                        "diagnostics": int(author.get(author.get(author.model, "Extension"), "GetWhatsWrongCount"))}
                rec.data["cold"] = cold
                rec.flush()
                require(cold == {"solids": 1, "diagnostics": 0}, "fresh native open has no solid or issued a diagnostic")
                author.snapshot("reopened", plan, edited=phase == "edited-reopen")
                owner = rec.data["reopened"]["driver"]["name"].split("@")
                require(len(owner) == 3 and owner[2].casefold() == f"{source.stem}.Part".casefold(),
                        "actual D1 document qualifier does not match this saved source")
                if phase == "reopen-edit-save":
                    author.edit(plan)
                    author.snapshot("edited", plan, edited=True)
            if phase != "edited-reopen":
                require(not target.exists(), "native save destination is occupied")
                status = rec.call("save owned native source", session.save_as, author.model, target)
                rec.data["save_status"] = list(status)
                rec.flush()
                require(status == (True, 0, 0) and target.is_file() and target.stat().st_size > 0
                        and Path(str(author.get(author.model, "GetPathName"))).resolve() == target,
                        "native save warned, failed or changed locator")
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
    rec.data["dialogs"] = monitor.log
    rec.data["source_immutable"] = phase == "author" or (source.is_file() and sha(source) == pin)
    artifact = source if phase == "edited-reopen" else target
    if artifact.is_file():
        rec.data["artifact_sha256"] = sha(artifact)
    rec.data["passed"] = bool(complete and not rec.data["first_failure"] and not rec.data["cleanup_errors"]
                              and not rec.data["dialogs"] and not rec.data.get("controller_diagnostics")
                              and rec.data["source_immutable"] and rec.data.get("artifact_sha256"))
    rec.flush()
    return rec.data["passed"]


def worker(job_path, pin, phase, slot, source_pin, control_name):
    job, cases, plans = verify(job_path, pin, permit_private=True)
    packet, capture = local_paths(job_path, job)
    if phase.startswith("control-"):
        require(phase in ("control-before", "control-after") and control_name in CONTROLS
                and slot is source_pin is None, "unexpected control request")
        folder = capture / f"{phase}-{Path(control_name).stem}"
    else:
        require(phase in PHASES and slot in range(len(cases)) and control_name is None
                and (source_pin is None if phase == "author" else valid_hash(source_pin)), "unexpected source phase request")
        root, initial, edited = paths(capture, slot, cases[slot])
        folder = root / phase
    record = folder / "Record.json"
    phase_data = {"phase": phase, "slot": slot, "source_sha256": source_pin, "job_sha256": pin, "control": control_name}
    require(folder.is_dir() and folder.resolve() == folder and not record.exists()
            and json.loads((folder / "Phase.json").read_bytes()) == phase_data, "phase was not admitted by the locked supervisor")
    if control_name:
        return control(packet / control_name, record, CONTROLS[control_name])
    from EllipseAuthor import installed_api

    api = installed_api()
    require(api == json.loads((capture / "RegisteredApi.json").read_bytes()), "registered API changed since exact preflight")
    return native_phase(phase, record, initial, edited, source_pin, plans[slot], api["enums"])


def launch(job, pin, folder, phase, processes, *, slot=None, source=None, control_name=None):
    folder.mkdir(parents=True, exist_ok=False)
    entry = {"phase": phase, "slot": slot, "source_sha256": source, "job_sha256": pin, "control": control_name}
    put(folder / "Phase.json", encode(entry))
    command = [sys.executable, "-E", "-B", str(Path(__file__).resolve()), "--job", str(job), "--pin", pin, "--phase", phase]
    if control_name:
        command.extend(("--control", control_name))
    else:
        command.extend(("--slot", str(slot)))
        if source:
            command.extend(("--source", source))
    try:
        result = subprocess.run(command, capture_output=True, timeout=180, check=False)
        code, stdout, stderr = result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired as error:
        code, stdout, stderr = None, error.stdout or b"", error.stderr or b""
    put(folder / "Stdout.txt", stdout)
    put(folder / "Stderr.txt", stderr)
    record = folder / "Record.json"
    data = json.loads(record.read_bytes()) if record.is_file() else {}
    identity = data.get("oracle_identity")
    if identity:
        processes.append((identity["process_id"], identity["process_creation_filetime"]))
    if code is None and identity:
        from AuthorCurves import cleanup_owned_process

        try:
            recovered = cleanup_owned_process(identity, {"executable_sha256": ORACLE})
        except Exception as error:
            recovered = {"error": repr(error)}
        put(folder / "TimeoutCleanup.json", encode(recovered))
    return entry | {"passed": code == 0 and not stderr and data.get("passed") is True,
                    "phase_sha256": sha(record) if record.is_file() else None, "exit_code": code,
                    "artifact_sha256": data.get("artifact_sha256"), "checks": len(data.get("checks", ()))}, data


def reconcile(initial, edited, records):
    authored, changed, fresh = records
    states = (authored["authored"], changed["reopened"], changed["edited"], fresh["reopened"])
    reference = states[0]
    require(sha(initial) == authored["artifact_sha256"] and sha(edited) == changed["artifact_sha256"] == fresh["artifact_sha256"]
            and sha(initial) != sha(edited), "original or edited artifact does not match its measured immutable phase")
    require(all(row["tree"] == reference["tree"] and row["configurations"] == reference["configurations"]
                and row["definition"]["parents"] == reference["definition"]["parents"]
                and row["definition"]["children"] == reference["definition"]["children"]
                and predictions_equal(row["profile"], reference["profile"]) for row in states),
            "full tree, support, segment/point ownership, signed sketch points or configuration drifted")
    first = authored["first_draw"]
    require(all(predictions_equal(first[key], reference["profile"][key]) for key in first)
            and predictions_equal(authored["before_boss"], reference["profile"]), "first-draw segment or point owners drifted")
    require(all(row["driver"]["name"].split("@")[:2] == reference["driver"]["name"].split("@")[:2]
                for row in states) and states[0]["body"]["mass"]["volume"] != states[3]["body"]["mass"]["volume"],
            "live driving depth did not retain its owner and change physical geometry")
    return {"original_sha256": sha(initial), "edited_sha256": sha(edited), "tree_rows": len(reference["tree"]), "snapshots": len(states)}


def source(job_path, pin, capture, slot, case, processes):
    folder, initial, edited = paths(capture, slot, case)
    rows, records, current = [], [], None
    for phase in PHASES:
        row, data = launch(job_path, pin, folder / phase, phase, processes, slot=slot, source=current)
        rows.append(row)
        if not row["passed"]:
            return {"slot": slot, "passed": False, "phases": rows}
        records.append(data)
        current = row["artifact_sha256"]
    try:
        lifecycle = reconcile(initial, edited, records)
    except ValueError as error:
        put(folder / "LifecycleFailure.json", encode({"error": str(error)}))
        return {"slot": slot, "passed": False, "phases": rows, "lifecycle_failed": True}
    return {"slot": slot, "passed": True, "phases": rows} | lifecycle


def run(job_path, pin):
    job, cases, _ = verify(job_path, pin, permit_private=True)
    _, capture = local_paths(job_path, job)
    import Swapp
    from EllipseAuthor import installed_api

    require(not capture.exists() and not Swapp.application_pids(), "native capture is occupied or another CAD process is active")
    capture.mkdir(exist_ok=False)
    lock = {"schema": LOCK, "job_sha256": pin, "cohort": job["cohort"], "revision": job["revision"],
            "tree": job["tree"], "oracle_build": BUILD, "oracle_sha256": ORACLE,
            "spec_sha256": job["files"]["Spec.json"]["sha256"], "prediction_sha256": job["files"]["Predictions.json"]["sha256"],
            "controls": {}, "sources": [], "started_at": time.time(), "writer_output_count": 0, "heldout_writer_acceptance": False}
    processes = []

    def bracket(position):
        for name in CONTROLS:
            phase = f"control-{position}"
            key = f"{phase}-{Path(name).stem}"
            try:
                lock["controls"][key] = launch(job_path, pin, capture / key, phase, processes, control_name=name)[0]
            except Exception as error:
                lock["controls"][key] = {"passed": False, "error": repr(error)}

    try:
        bracket("before")
        if all(row["passed"] for row in lock["controls"].values()):
            metadata = capture / "RegisteredApi.json"
            put(metadata, encode(installed_api()))
            lock["registered_api_sha256"] = sha(metadata)
            for slot, case in enumerate(cases):
                row = source(job_path, pin, capture, slot, case, processes)
                lock["sources"].append(row)
                if not row["passed"]:
                    break
    except Exception as error:
        put(capture / "BatchFailure.json", encode({"exception": repr(error)}))
        lock["batch_failed"] = True
    finally:
        bracket("after")
    lock["idle_after"] = not Swapp.application_pids() and not Swapp.owned_process_ids()
    try:
        lock["inputs_unchanged"] = verify(job_path, pin, permit_private=True)[0] == job
    except Exception as error:
        put(capture / "InputCustodyFailure.json", encode({"exception": repr(error)}))
        lock["inputs_unchanged"] = False
    lock["fresh_processes"], lock["distinct_processes"] = len(processes), len(set(processes))
    lock["passed"] = bool(not lock.get("batch_failed") and lock["idle_after"] and lock["inputs_unchanged"]
                          and lock["fresh_processes"] == lock["distinct_processes"] == 10
                          and len(lock["controls"]) == 4 and all(row["passed"] for row in lock["controls"].values())
                          and len(lock["sources"]) == len(cases) == 2 and all(row["passed"] for row in lock["sources"]))
    lock["finished_at"] = time.time()
    receipt = capture / "SourceLock.json"
    put(receipt, encode(lock))
    return {"source_lock_sha256": sha(receipt), "passed": lock["passed"], "distinct_processes": lock["distinct_processes"],
            "completed_slots": sum(row["passed"] for row in lock["sources"]), "writer_output_count": 0}


def checked_lock(job, packet_pin, capture, pin):
    lock = pinned_json(capture / "SourceLock.json", pin)
    require(lock["schema"] == LOCK and lock["job_sha256"] == packet_pin and lock["passed"] is True
            and all(lock[key] == job[key] for key in ("cohort", "revision", "tree", "oracle_build", "oracle_sha256"))
            and lock["spec_sha256"] == job["files"]["Spec.json"]["sha256"]
            and lock["prediction_sha256"] == job["files"]["Predictions.json"]["sha256"]
            and lock["writer_output_count"] == 0 and lock["heldout_writer_acceptance"] is False
            and lock["inputs_unchanged"] and lock["idle_after"] and valid_hash(lock["registered_api_sha256"])
            and lock["fresh_processes"] == lock["distinct_processes"] == 10
            and len(lock["controls"]) == 4 and all(row["passed"] and valid_hash(row["phase_sha256"]) for row in lock["controls"].values())
            and [row["slot"] for row in lock["sources"]] == [0, 1], "existing source lock is not a complete native lifecycle")
    for row in lock["sources"]:
        require(row["passed"] and row["snapshots"] == 4 and [phase["phase"] for phase in row["phases"]] == list(PHASES)
                and all(phase["passed"] and valid_hash(phase["phase_sha256"]) for phase in row["phases"])
                and valid_hash(row["original_sha256"]) and valid_hash(row["edited_sha256"]), "source lock lacks its original or derivative")
    return lock


def prepare_private(job_path, pin, disclosed_pin, root):
    job, _, _ = verify(job_path, pin)
    packet, capture = local_paths(job_path, job)
    checked_lock(job, pin, capture, disclosed_pin)
    require(root != packet.parent and not root.exists(), "private episode requires unoccupied local custody")
    target, _ = guest_paths(str(root))
    random = secrets.SystemRandom()

    def val(start, end):
        return random.randint(start, end) / 16

    first = {"name": "Ellipse" + secrets.token_hex(8), "center_mm": [val(400, 460), val(266, 293)],
             "radii_mm": [val(448, 490), val(255, 283)], "angle_deg": val(732, 774),
             "depth_mm": val(127, 145), "edited_depth_mm": val(243, 251)}
    second = {"name": "Ellipse" + secrets.token_hex(8), "center_mm": [val(-514, -487), val(-417, -391)],
              "radii_mm": [val(393, 421), val(162, 179)], "angle_deg": val(-343, -301),
              "depth_mm": val(459, 494), "edited_depth_mm": val(359, 383)}
    data = {name: (packet / name).read_bytes() for name in FILES - {"Spec.json", "Predictions.json"}}
    data.update(model_files("heldout", [first, second]))
    hidden = job | {"cohort": "heldout", "guest_root": str(root), "disclosed_job_sha256": pin, "disclosed_lock_sha256": disclosed_pin}
    private_pin = create(Path(target), hidden, data)
    return {"job_sha256": private_pin, "spec_sha256": sha(Path(target) / "Spec.json"),
            "prediction_sha256": sha(Path(target) / "Predictions.json"), "native_processes": 0, "slots": 2}


def redact(job_path, pin, lock_pin, output):
    job, cases, _ = verify(job_path, pin, permit_private=True)
    _, capture = local_paths(job_path, job)
    require(job["cohort"] == "heldout" and output.is_absolute() and output.parent.is_dir() and not output.exists()
            and PureWindowsPath(output.resolve()).is_relative_to(SHARE), "publish only new redacted evidence to the managed share")
    lock = checked_lock(job, pin, capture, lock_pin)
    for row, case in zip(lock["sources"], cases, strict=True):
        folder, initial, edited = paths(capture, row["slot"], case)
        require(sha(initial) == row["original_sha256"] and sha(edited) == row["edited_sha256"]
                and all(sha(folder / phase["phase"] / "Record.json") == phase["phase_sha256"] for phase in row["phases"]),
                "private native sources or phase receipts have changed")
    require(all(sha(capture / key / "Record.json") == row["phase_sha256"] for key, row in lock["controls"].items())
            and sha(capture / "RegisteredApi.json") == lock["registered_api_sha256"], "native control or registered API receipts changed")
    summary = {key: lock[key] for key in ("revision", "tree", "oracle_build", "oracle_sha256", "spec_sha256",
               "prediction_sha256", "registered_api_sha256", "distinct_processes", "writer_output_count",
               "heldout_writer_acceptance", "finished_at")}
    summary.update(schema="kit.sw2026.full-ellipse-blind-boss-prewriter-lock.v1", source_lock_sha256=lock_pin,
                   source_job_sha256=pin, disclosed_job_sha256=job["disclosed_job_sha256"],
                   disclosed_lock_sha256=job["disclosed_lock_sha256"],
                   controls={key: row["phase_sha256"] for key, row in lock["controls"].items()},
                   slots=[{"slot": f"Slot{row['slot'] + 1:02d}", "original_sha256": row["original_sha256"],
                           "edited_sha256": row["edited_sha256"], "phases": [item["phase_sha256"] for item in row["phases"]]}
                          for row in lock["sources"]])
    put(output, encode(summary))
    return {"redacted_lock_sha256": sha(output), "source_lock_sha256": lock_pin, "native_processes": 0, "slots": 2}


def main():
    parser = argparse.ArgumentParser(description="Verify, transfer, or run a full-ellipse source-only oracle packet")
    parser.add_argument("--job", type=Path, required=True)
    parser.add_argument("--pin", required=True)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--verify", action="store_true")
    modes.add_argument("--stage", action="store_true")
    modes.add_argument("--phase")
    modes.add_argument("--prepare-private", type=Path)
    modes.add_argument("--redact", type=Path)
    parser.add_argument("--slot", type=int)
    parser.add_argument("--source")
    parser.add_argument("--control", choices=tuple(CONTROLS))
    parser.add_argument("--lock-pin")
    args = parser.parse_args()
    if args.verify:
        job, _, _ = verify(args.job, args.pin)
        result = {"job_sha256": args.pin, "bound_files": len(job["files"]), "native_processes": 0}
    elif args.stage:
        result = stage(args.job, args.pin)
    else:
        require(os.name == "nt", "native source and protected method execution are guest-only")
        if args.phase:
            return int(not worker(args.job, args.pin, args.phase, args.slot, args.source, args.control))
        if args.prepare_private:
            result = prepare_private(args.job, args.pin, args.lock_pin, args.prepare_private)
        elif args.redact:
            result = redact(args.job, args.pin, args.lock_pin, args.redact)
        else:
            result = run(args.job, args.pin)
    print(json.dumps(result, allow_nan=False))
    return int(not result.get("passed", True))


if __name__ == "__main__":
    raise SystemExit(main())
