from argparse import ArgumentParser
import json
from pathlib import Path
import subprocess
import sys

from EllipseModel import require
from EllipsePacket import BUILD, CONTROLS, ORACLE, encode, predictions_equal, put, sha, valid_hash
from EllipseSeamObserve import inspect_api
from EllipseSeamPacket import DESTINATIONS, RESULT, TEMPLATE_SHA256, local_paths, stage, verify
from RunEllipseSources import control, exact

PHASES = ("author-sketch", "reopen-sketch", "author-boss", "reopen-boss")
SCHEMA = "kit.sw2026.ellipse-seam-discriminator-result.v1"
PHASE_SCHEMA = "kit.sw2026.ellipse-seam-discriminator-phase.v1"


def native_phase(entry, record, path, plan, api, close_updates):
    import Swapp
    from AuthorCurves import Recorder
    from EllipseSeamAuthor import SeamAuthor
    from OracleIdentity import application_identity

    operation, role = entry["phase"].split("-")
    before = entry["input_sha256"]
    rec = Recorder(record, entry)
    rec.data.update(schema=PHASE_SCHEMA, seam_stages=[], writer_output_count=0, close_updates=close_updates)
    session, success = None, False
    with Swapp.Dismisser() as monitor:
        try:
            require(not Swapp.application_pids(), "ellipse seam phase needs a fresh native process")
            if operation == "author":
                require(not path.exists(), "native seam output already exists")
            else:
                require(path.is_file() and not path.is_symlink() and sha(path) == before,
                        "open-only seam input differs from the author save")
            session = rec.call("launch exact isolated .34 COM", Swapp.Sw)
            identity = rec.call("measure native process identity", application_identity, session.app)
            rec.data["oracle_identity"] = identity
            rec.flush()
            require(exact(identity) and session.revision == "34.5.2", "wrong native oracle or build")
            author = SeamAuthor(session.app, rec, api["enums"])
            if operation == "author":
                profile = author.draw_profile(session, plan, api, close_updates=close_updates)
                if role == "boss":
                    author.create_boss(profile, plan, api)
                author.check_shape(role, "before_save", plan, api)
                status = rec.call("save new native ellipse seam snapshot", session.save_as, author.model, path)
                rec.data["save_status"] = list(status)
                rec.flush()
                require(status == (True, 0, 0) and path.is_file() and path.stat().st_size > 0
                        and Path(str(author.get(author.model, "GetPathName"))).resolve() == path,
                        "native seam save warned, failed or changed locator")
                author.profile_stage("after_save", plan, api)
            else:
                author.model, errors, warnings = rec.call("open immutable native seam snapshot", session.open, path, read_only=True)
                rec.data["open_status"] = {"opened": author.model is not None, "errors": errors, "warnings": warnings}
                rec.flush()
                require(author.model is not None and not errors and not warnings
                        and Path(str(author.get(author.model, "GetPathName"))).resolve() == path,
                        "fresh native seam reopen failed or returned a different document")
                expected = int(role == "boss")
                require(rec.call("check cold native seam solid count", Swapp.bodies, author.model) == expected
                        and not author.get(author.get(author.model, "Extension"), "GetWhatsWrongCount"),
                        "saved native seam snapshot has incorrect cold geometry or diagnostics")
                author.profile_stage("reopened_cold", plan, api)
                author.check_shape(role, "reopened_rebuilt", plan, api)
            if operation == "reopen" and role == "boss":
                qualifier = rec.data["shape"]["driver"]["name"].split("@")
                require(len(qualifier) == 3 and qualifier[2].casefold() == f"{path.stem}.Part".casefold(),
                        "reopened D1 belongs to a different native document")
            success = True
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
    digest = sha(path) if path.is_file() else None
    rec.data.update(artifact_sha256=digest, immutable=operation == "author" or digest == before)
    rec.data["passed"] = bool(success and digest and rec.data["immutable"] and not rec.data["first_failure"]
                              and not rec.data["cleanup_errors"] and not rec.data["dialogs"]
                              and not rec.data.get("controller_diagnostics"))
    rec.flush()
    return rec.data["passed"]


def request(phase, pin, control_name, incoming):
    return {"phase": phase, "job_sha256": pin, "control": control_name, "input_sha256": incoming}


def work(job_path, pin, phase, control_name, incoming):
    job, plan = verify(job_path, pin)
    packet, capture = local_paths(job_path, job)
    if control_name is None:
        require(phase in PHASES and (valid_hash(incoming) if phase.startswith("reopen-") else incoming is None),
                "unsupported ellipse seam phase")
        folder = capture / phase
    else:
        require(phase in ("control-before", "control-after") and control_name in CONTROLS and incoming is None,
                "unexpected ellipse seam control")
        folder = capture / f"{phase}-{Path(control_name).stem}"
    entry = request(phase, pin, control_name, incoming)
    record = folder / "Record.json"
    require(folder.is_dir() and folder.resolve() == folder and not record.exists()
            and json.loads((folder / "Phase.json").read_bytes()) == entry,
            "ellipse seam phase must be prepared by the locked supervisor")
    if control_name is not None:
        return control(packet / control_name, record, CONTROLS[control_name])
    api = inspect_api()
    require(api == json.loads((capture / "RegisteredApi.json").read_bytes()),
            "registered ellipse seam interfaces changed")
    return native_phase(entry, record, capture / DESTINATIONS[phase.split("-")[1]], plan, api,
                        job.get("close_updates", True))


def launch(job_path, pin, capture, phase, processes, *, control_name=None, incoming=None):
    entry = request(phase, pin, control_name, incoming)
    key = phase if control_name is None else f"{phase}-{Path(control_name).stem}"
    folder = capture / key
    folder.mkdir(exist_ok=False)
    put(folder / "Phase.json", encode(entry))
    command = [sys.executable, "-E", "-B", str(Path(__file__).resolve()),
               "--job", str(job_path), "--pin", pin, "--phase", phase]
    if control_name:
        command.extend(("--control", control_name))
    if incoming:
        command.extend(("--input-sha256", incoming))
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
    if identity and exact(identity):
        processes.append((identity["process_id"], identity["process_creation_filetime"]))
    if code is None and identity and exact(identity):
        from AuthorCurves import cleanup_owned_process

        try:
            cleanup = cleanup_owned_process(identity, {"executable_sha256": ORACLE})
        except Exception as error:
            cleanup = {"error": repr(error)}
        put(folder / "TimeoutCleanup.json", encode(cleanup))
    return entry | {"record_sha256": sha(record) if record.is_file() else None, "exit_code": code,
                    "passed": bool(code == 0 and not stderr and data.get("passed") and identity and exact(identity)),
                    "artifact_sha256": data.get("artifact_sha256"), "checks": len(data.get("checks", ()))}, data


def reconcile(capture, phases, observed):
    drafts = [observed[phase] for phase in ("author-sketch", "author-boss")]
    require(drafts[0]["template_sha256"] == drafts[1]["template_sha256"] == TEMPLATE_SHA256,
            "the two independent ellipse authors did not share the exact template")
    profile = drafts[0]["shape"]["profile"]
    require(all(predictions_equal(row["shape"]["profile"], profile)
                and row["shape"]["configurations"] == drafts[0]["shape"]["configurations"]
                for row in observed.values()), "source roles changed the signed ellipse or active configuration")
    for row in drafts:
        expected = row["seam_stages"][0]["ellipse"]
        require(all(predictions_equal(expected[key], profile[key]) for key in expected),
                "active draw differs from the saved axis and membership identities")
    for role, name in DESTINATIONS.items():
        first, reopened = (observed[f"{op}-{role}"] for op in ("author", "reopen"))
        require(first["shape"]["tree"] == reopened["shape"]["tree"]
                and phases[f"author-{role}"]["artifact_sha256"] == phases[f"reopen-{role}"]["input_sha256"]
                == reopened["artifact_sha256"] == sha(capture / name),
                "fresh reopen changed the complete native tree or exact artifact identity")
    return {role: sha(capture / name) for role, name in DESTINATIONS.items()}


def run(job_path, pin):
    import Swapp

    job, _ = verify(job_path, pin)
    _, capture = local_paths(job_path, job)
    require(not capture.exists() and not Swapp.application_pids() and not Swapp.owned_process_ids(),
            "ellipse seam capture is occupied or another CAD process is active")
    capture.mkdir(exist_ok=False)
    controls, phases, observed, processes = {}, {}, {}, []
    outcome = {"schema": SCHEMA, "job_sha256": pin, "revision": job["revision"], "tree": job["tree"],
               "oracle_build": BUILD, "oracle_sha256": ORACLE, "controls": controls, "phases": phases,
               "close_updates": job.get("close_updates", True),
               "writer_output_count": 0, "native_writer_acceptance": False}

    def bracket(side):
        for name in CONTROLS:
            phase = f"control-{side}"
            key = f"{phase}-{Path(name).stem}"
            try:
                controls[key] = launch(job_path, pin, capture, phase, processes, control_name=name)[0]
            except Exception as error:
                controls[key] = {"passed": False, "error": repr(error)}

    try:
        bracket("before")
        if len(controls) == 2 and all(row["passed"] for row in controls.values()):
            registration = capture / "RegisteredApi.json"
            put(registration, encode(inspect_api()))
            outcome["registered_api_sha256"] = sha(registration)
            for phase in PHASES:
                operation, role = phase.split("-")
                incoming = phases[f"author-{role}"]["artifact_sha256"] if operation == "reopen" else None
                phases[phase], observed[phase] = launch(job_path, pin, capture, phase, processes, incoming=incoming)
                if not phases[phase]["passed"]:
                    break
            if len(phases) == len(PHASES) and all(row["passed"] for row in phases.values()):
                outcome["native_artifacts"] = reconcile(capture, phases, observed)
    except Exception as error:
        outcome["batch_error"] = repr(error)
    finally:
        bracket("after")
    outcome["fresh_processes"], outcome["distinct_processes"] = len(processes), len(set(processes))
    outcome["idle_after"] = not Swapp.application_pids() and not Swapp.owned_process_ids()
    try:
        outcome["inputs_unchanged"] = verify(job_path, pin)[0] == job
    except Exception as error:
        outcome.update(inputs_unchanged=False, custody_error=repr(error))
    outcome["passed"] = bool(outcome["idle_after"] and outcome["inputs_unchanged"]
                             and outcome.get("native_artifacts") and len(controls) == 4
                             and all(row["passed"] for row in controls.values())
                             and outcome["fresh_processes"] == outcome["distinct_processes"] == 8)
    receipt = capture / RESULT
    put(receipt, encode(outcome))
    return {"result_sha256": sha(receipt), "passed": outcome["passed"], "distinct_processes": outcome["distinct_processes"]}


if __name__ == "__main__":
    parser = ArgumentParser(description="Run one disclosed full-ellipse seam source discriminator")
    parser.add_argument("--job", required=True, type=Path)
    parser.add_argument("--pin", required=True)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--stage", action="store_true")
    mode.add_argument("--verify-only", action="store_true")
    mode.add_argument("--phase")
    parser.add_argument("--control")
    parser.add_argument("--input-sha256")
    arg = parser.parse_args()
    require(arg.phase or (arg.control is None and arg.input_sha256 is None), "worker flags require a declared phase")
    if arg.phase:
        raise SystemExit(0 if work(arg.job, arg.pin, arg.phase, arg.control, arg.input_sha256) else 3)
    if arg.stage:
        answer = stage(arg.job, arg.pin)
    elif arg.verify_only:
        job, _ = verify(arg.job, arg.pin)
        answer = {"job_sha256": arg.pin, "verified": True, "bound_files": len(job["files"]), "native_processes": 0}
    else:
        answer = run(arg.job, arg.pin)
    print(json.dumps(answer, sort_keys=True))
    raise SystemExit(0 if answer.get("passed", True) else 3)
