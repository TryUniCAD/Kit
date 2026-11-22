from argparse import ArgumentParser
from pathlib import Path, PureWindowsPath
from subprocess import run, TimeoutExpired
import json
import os
import sys

from ChamferModel import predictions, validate_spec
from ChamferPacket import TOOL_FILES, valid_hash, write_new
from FilletModel import require
from FilletPacket import BUILD, CONTROL, ORACLE, digest

PACKET = PureWindowsPath(r"C:\KitGeneratedChamfer01\Packet")
OUTPUT = PACKET.parent / "Run01"
SCHEMA = "kit.sw2026.chamfer-cold-candidate-trial.v1"
ROLES = ("before", "after", "edit", "reopen")
CONTROL_FILE = "Control.SLDPRT"


def verified(path, pin):
    require(path.name == "Trial.json" and not path.is_symlink() and valid_hash(pin) and digest(path) == pin,
            "unbound candidate trial manifest")
    packet = path.parent
    trial = json.loads(path.read_bytes())
    require(trial["schema"] == SCHEMA and trial["oracle_build"] == BUILD and trial["oracle_sha256"] == ORACLE
            and trial["guest_packet"] == str(PACKET) and trial["guest_output"] == str(OUTPUT)
            and valid_hash(trial["construction_revision"], 40) and trial["guarded_generation_processes"] == 4
            and trial["guarded_runtime_reads"] == trial["heldout_inputs_read"] == 0,
            "trial provenance, exact build or destination differs")
    cases = validate_spec(trial["spec"])
    plans = predictions(cases)
    names = {f"Candidates/{case['name']}.SLDPRT" for case in cases}
    files = trial["files"]
    require(set(files) == TOOL_FILES | names | {CONTROL_FILE, "Tool/RunNativeChamferProbe.py"}
            and files[CONTROL_FILE]["sha256"] == CONTROL
            and {node.relative_to(packet).as_posix() for node in packet.rglob("*") if node.is_file()} == set(files) | {"Trial.json"},
            "candidate packet has foreign or missing files")
    for relative, row in files.items():
        candidate = packet / relative
        require(candidate.resolve().is_relative_to(packet.resolve()) and not candidate.is_symlink()
                and candidate.stat().st_size == row["bytes"] and digest(candidate) == row["sha256"],
                "frozen candidate packet file changed " + relative)
    require(len(trial["cases"]) == len(cases), "candidate count and actual author predictions disagree")
    for case, plan, expected in zip(cases, plans, trial["cases"], strict=True):
        filename = f"Candidates/{case['name']}.SLDPRT"
        require(expected["path"] == filename and expected["locator"] == str(PACKET / filename)
                and expected["archive_sha256"] == files[filename]["sha256"]
                and expected["branch"] in [row["branch"] for row in plan["states"]["initial"]],
                "candidate locator or analytic branch is outside its frozen design")
    return trial, cases, plans


def expected_at(plan, branch, edited):
    row, = (item for item in plan["states"]["edited" if edited else "initial"] if item["branch"] == branch)
    return row["geometry"]


def same_drivers(saved, fresh, model_name):
    def actual(state, locator_stem):
        owners = {}
        for role, driver in state["drivers"].items():
            label, feature, file = driver["name"].split("@")
            require(file.casefold() == (locator_stem + ".Part").casefold(),
                    "driver has the wrong qualified file for its native phase")
            owners[role] = (label, feature, driver["value_si"], driver["driven_state"], driver["read_only"])
        return owners

    return actual(saved, model_name) == actual(fresh, model_name + "Edited")


def candidate_phase(case, plan, choice, phase, source, target, source_sha, receipt, metadata):
    import Swapp
    from AuthorCurves import Recorder
    from ChamferApi import installed_api
    from ChamferAuthor import ChamferAuthor
    from FilletSourcePhase import has_exact_identity
    from OracleIdentity import application_identity

    rec = Recorder(receipt, {"phase": phase, "model": case["name"], "original_sha256": source_sha})
    session, passed = None, False
    reopened_edited = phase == "reopen"
    with Swapp.Dismisser() as monitor:
        try:
            require(not Swapp.application_pids() and source.is_file() and digest(source) == source_sha,
                    "native phase has an active app or an unbound input")
            constants, api = installed_api(Swapp)
            require(api == metadata, "installed chamfer API changed after preflight")
            session = rec.call("launch exact SOLIDWORKS oracle", Swapp.Sw)
            identity = rec.call("bind native build and lifetime", application_identity, session.app)
            rec.data["oracle_identity"] = identity
            rec.flush()
            require(has_exact_identity(identity) and session.revision == "34.5.2", "wrong native oracle build")
            author = ChamferAuthor(session.app, rec, constants)
            author.model, errors, warnings = rec.call("open exact candidate or saved derivative", session.open, source,
                                                       read_only=reopened_edited)
            rec.data["open_status"] = {"opened": author.model is not None, "errors": errors, "warnings": warnings}
            rec.flush()
            require(author.model is not None and errors == warnings == 0, "cold native model open failed or warned")
            require(Path(str(author.get(author.model, "GetPathName"))).resolve() == source.resolve(),
                    "native open returned a different model locator")
            count = int(rec.call("count solid bodies before explicit rebuild", Swapp.bodies, author.model))
            diagnostics = int(author.get(author.get(author.model, "Extension"), "GetWhatsWrongCount"))
            mass = rec.call("measure cold volume area and centre", Swapp.mass, author.model) if count == 1 else None
            rec.data["cold"] = {"body_count": count, "diagnostics": diagnostics, "mass": mass}
            rec.flush()
            require(count == 1 and diagnostics == 0 and mass and "error" not in mass,
                    "cold native model lacks its actual solid or clean diagnostics")
            expected = expected_at(plan, choice, reopened_edited)
            for field, zero in (("volume", 1e-21), ("area", 1e-16)):
                author.close_six("before rebuild " + field, mass[field], expected[field], near_zero=zero)
            for axis, (actual, wanted) in enumerate(zip(mass["com"], expected["com"], strict=True)):
                author.close_six(f"before rebuild centre {axis}", actual, wanted, near_zero=1e-10)
            state = author.snapshot(case, plan, "reopened", edited=reopened_edited)
            require(state["branch"] == choice and state["configurations"] == ["Default"],
                    "native rebuild changed independent selected-side geometry or active configuration")
            if not reopened_edited:
                author.edit(case)
                edited = author.snapshot(case, plan, "edited", edited=True)
                require(edited["branch"] == choice and edited["configurations"] == state["configurations"]
                        and edited["tree"] == state["tree"]
                        and edited["definition"]["parents"] == state["definition"]["parents"],
                        "native edit changed the complete feature tree or real stock parent")
                require(not target.exists(), "native derivative destination already exists")
                status = rec.call("save edited owned native derivative", session.save_as, author.model, target)
                rec.data["native_save_status"] = list(status)
                rec.flush()
                require(status == (True, 0, 0) and target.is_file()
                        and Path(str(author.get(author.model, "GetPathName"))).resolve() == target.resolve(),
                        "native derivative save failed or reported diagnostics")
            passed = True
        except Exception as issue:
            rec.failure(issue)
        finally:
            if session is not None:
                try:
                    session.close()
                except Exception as issue:
                    rec.failure(issue, cleanup=True)
                rec.data["controller_diagnostics"] = session.diagnostics
    rec.data["dialogs"] = monitor.log
    produced = source if reopened_edited else target
    rec.data["artifact_sha256"] = digest(produced) if produced.is_file() else None
    rec.data["passed"] = bool(passed and digest(source) == source_sha and rec.data["artifact_sha256"]
                              and not rec.data["first_failure"] and not rec.data["cleanup_errors"]
                              and not rec.data["dialogs"] and not rec.data.get("controller_diagnostics"))
    rec.flush()
    return rec.data["passed"]


def phase_job(manifest, pin, role, slot, source_sha):
    trial, cases, predictions = verified(manifest, pin)
    packet, output = Path(PACKET), Path(OUTPUT)
    child = output / (role if slot is None else f"Slot{slot + 1:02d}-{role}")
    record = child / "Record.json"
    require(child.is_dir() and not record.exists(), "native phase requires an unused owned receipt")
    if role in ("before", "after"):
        from FilletSourcePhase import run_control

        require(slot is None and source_sha is None, "control cannot consume a candidate")
        return run_control(packet / CONTROL_FILE, record)
    require(slot is not None and 0 <= slot < len(cases) and valid_hash(source_sha), "unbound trial phase or source")
    case = cases[slot]
    choice = trial["cases"][slot]
    candidate = packet / choice["path"]
    derivative = output / f"{case['name']}Edited.SLDPRT"
    source = derivative if role == "reopen" else candidate
    require(role == "reopen" or source_sha == choice["archive_sha256"], "pre-edit input differs from its generated seal")
    return candidate_phase(case, predictions[slot], choice["branch"], role, source, derivative, source_sha, record,
                           json.loads((output / "RegisteredApi.json").read_bytes()))


def launch(manifest, pin, role, *, slot=None, source=None):
    folder = Path(OUTPUT) / (role if slot is None else f"Slot{slot + 1:02d}-{role}")
    folder.mkdir()
    command = [sys.executable, "-E", "-B", str(Path(__file__).resolve()),
               "--manifest", str(manifest), "--pin", pin, "--phase", role]
    if slot is not None:
        command.extend(("--slot", str(slot), "--source", source))
    timed_out = False
    try:
        process = run(command, capture_output=True, timeout=175, check=False)
        code, stdout, stderr = process.returncode, process.stdout, process.stderr
    except TimeoutExpired as error:
        timed_out, code, stdout, stderr = True, None, error.stdout or b"", error.stderr or b""
    (folder / "Stdout.txt").write_bytes(stdout)
    (folder / "Stderr.txt").write_bytes(stderr)
    receipt = folder / "Record.json"
    row = json.loads(receipt.read_bytes()) if receipt.is_file() else {}
    owner = row.get("oracle_identity")
    if timed_out and owner is not None:
        from AuthorCurves import cleanup_owned_process

        cleanup_owned_process(owner, {"executable_sha256": ORACLE})
    result = {"role": role, "slot": slot, "exit_code": code, "timed_out": timed_out,
              "receipt_sha256": digest(receipt) if receipt.is_file() else None,
              "phase_passed": code == 0 and not stderr and row.get("passed") is True,
              "lifetime": [owner["process_id"], owner["process_creation_filetime"]] if owner else None}
    return result, row


def run_trial(manifest, pin):
    trial, cases, _ = verified(manifest, pin)
    import Swapp
    from ChamferApi import installed_api

    output = Path(OUTPUT)
    require(not Swapp.application_pids() and not output.exists() and output.parent.resolve() == output.parent,
            "serial oracle must begin idle and at an unused managed output")
    output.mkdir()
    phases, full_lifecycle, failure = [], [], None
    try:
        before, _ = launch(manifest, pin, "before")
        phases.append(before)
        if before["phase_passed"]:
            _, metadata = installed_api(Swapp)
            write_new(output / "RegisteredApi.json", metadata)
            for slot, choice in enumerate(trial["cases"]):
                require(not Swapp.application_pids(), "prior candidate left the serial oracle running")
                primary, after_edit = launch(manifest, pin, "edit", slot=slot, source=choice["archive_sha256"])
                phases.append(primary)
                if not primary["phase_passed"]:
                    continue
                reopened, record = launch(manifest, pin, "reopen", slot=slot, source=after_edit["artifact_sha256"])
                phases.append(reopened)
                if reopened["phase_passed"]:
                    saved, fresh = after_edit["edited"], record["reopened"]
                    if (saved["tree"] == fresh["tree"] and saved["definition"]["parents"] == fresh["definition"]["parents"]
                            and same_drivers(saved, fresh, cases[slot]["name"])):
                        full_lifecycle.append(slot)
    except Exception as issue:
        failure = str(issue)
    finally:
        if phases and not Swapp.application_pids():
            last, _ = launch(manifest, pin, "after")
            phases.append(last)
    lifetimes = [tuple(row["lifetime"]) for row in phases if row["lifetime"]]
    result = {"schema": SCHEMA, "manifest_sha256": pin, "lifecycle_slots": full_lifecycle, "phases": phases,
              "orchestration_failure": failure,
              "healthy_controls": bool(phases) and phases[0]["role"] == "before" and phases[-1]["role"] == "after"
              and phases[0]["phase_passed"] and phases[-1]["phase_passed"],
              "heldout_credit": 0, "proper_distinct_lifetimes": len(lifetimes) == len(set(lifetimes)) == len(phases)}
    result["passed"] = bool(not failure and result["healthy_controls"] and result["proper_distinct_lifetimes"]
                            and len(full_lifecycle) == len(cases) and len(phases) == 6)
    write_new(output / "Result.json", result)
    print(json.dumps({"passed": result["passed"], "receipt_sha256": digest(output / "Result.json"), "phases": len(phases)}))
    return result["passed"]


if __name__ == "__main__":
    options = ArgumentParser()
    options.add_argument("--manifest", type=Path, required=True)
    options.add_argument("--pin", required=True)
    options.add_argument("--verify", action="store_true")
    options.add_argument("--phase", choices=ROLES)
    options.add_argument("--slot", type=int)
    options.add_argument("--source")
    args = options.parse_args()
    if args.verify:
        verified(args.manifest, args.pin)
    else:
        require(os.name == "nt" and args.manifest.resolve() == (Path(PACKET) / "Trial.json").resolve()
                and Path(__file__).resolve().parent == Path(PACKET) / "Tool",
                "native trials require the frozen guest-local packet and runner")
        success = phase_job(args.manifest, args.pin, args.phase, args.slot, args.source) if args.phase else run_trial(args.manifest, args.pin)
        sys.exit(0 if success else 1)
