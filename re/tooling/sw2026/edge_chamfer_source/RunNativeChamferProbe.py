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
SIGNED_PACKET = PureWindowsPath(r"C:\KitGeneratedChamferSigned01\Packet")
SIGNED_SOURCE_LOCK = "2bce5961120ea7d8ea95ceaa5c10f7cbdbe6338152833357304647f432b86ff8"
SIGNED_COMPARISON = {"Reference.json", "Tool/ChamferComparison.py"}
SCHEMA = "kit.sw2026.chamfer-cold-candidate-trial.v1"
ROLES = ("before", "after", "edit", "reopen")
CONTROL_FILE = "Control.SLDPRT"


def verified(path, pin):
    require(path.name == "Trial.json" and not path.is_symlink() and valid_hash(pin) and digest(path) == pin,
            "unbound candidate trial manifest")
    packet = path.parent
    trial = json.loads(path.read_bytes())
    guest = PureWindowsPath(trial["guest_packet"])
    signed = guest == SIGNED_PACKET
    require(trial["schema"] == SCHEMA and trial["oracle_build"] == BUILD and trial["oracle_sha256"] == ORACLE
            and trial["guest_packet"] in (str(PACKET), str(SIGNED_PACKET))
            and trial["guest_output"] == str(guest.parent / OUTPUT.name)
            and valid_hash(trial["construction_revision"], 40) and trial["guarded_generation_processes"] == 4
            and trial["guarded_runtime_reads"] == trial["heldout_inputs_read"] == 0,
            "trial provenance, exact build or destination differs")
    cases = validate_spec(trial["spec"])
    plans = predictions(cases)
    names = {f"Candidates/{case['name']}.SLDPRT" for case in cases}
    files = trial["files"]
    comparison = SIGNED_COMPARISON if signed else set()
    require(set(files) == TOOL_FILES | names | {CONTROL_FILE, "Tool/RunNativeChamferProbe.py"} | comparison
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
        require(expected["path"] == filename and expected["locator"] == str(guest / filename)
                and expected["archive_sha256"] == files[filename]["sha256"]
                and expected["branch"] in [row["branch"] for row in plan["states"]["initial"]],
                "candidate locator or analytic branch is outside its frozen design")
    if signed:
        reference = json.loads((packet / "Reference.json").read_bytes())
        require(trial["disclosed_source_lock_sha256"] == reference["source_lock_sha256"] == SIGNED_SOURCE_LOCK
                and len(reference["cases"]) == len(cases) and trial["heldout_credit"] == 0
                and all(has_signed_reference(row, case, expected) for row, case, expected in
                        zip(reference["cases"], cases, trial["cases"], strict=True)),
                "signed trial must bind both independent measured source lifecycles")
    return trial, cases, plans


def has_signed_reference(row, case, expected):
    return (row["name"] == case["name"] and len(row["source_artifacts"]) == 2 and len(row["source_phases"]) == 3
            and all(valid_hash(pin) for pin in row["source_artifacts"] + row["source_phases"])
            and all(row[role]["branch"] == expected["branch"] and len(row[role]["tree"]) == 26
                    and row[role]["configurations"] == ["Default"] for role in ("initial", "edited")))


def stage_signed_guest(manifest, pin):
    require(os.name == "nt", "native candidate transfer is Windows-only")
    trial, _, _ = verified(manifest, pin)
    require(trial["guest_packet"] == str(SIGNED_PACKET), "transfer requires a fresh signed disclosure")
    destination = Path(SIGNED_PACKET)
    require(not destination.parent.exists(), "guest signed trial root already exists")
    destination.mkdir(parents=True)
    for name in sorted((*trial["files"], "Trial.json")):
        target = destination / name
        target.parent.mkdir(exist_ok=True)
        with target.open("xb") as stream:
            stream.write((manifest.parent / name).read_bytes())
    verified(destination / "Trial.json", pin)


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
    packet, output = (Path(trial[key]) for key in ("guest_packet", "guest_output"))
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


def launch(manifest, pin, role, output, *, slot=None, source=None):
    folder = output / (role if slot is None else f"Slot{slot + 1:02d}-{role}")
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

    reference = (json.loads((manifest.parent / "Reference.json").read_bytes())["cases"]
                 if trial["guest_packet"] == str(SIGNED_PACKET) else None)
    output = Path(trial["guest_output"])
    require(not Swapp.application_pids() and not output.exists() and output.parent.resolve() == output.parent,
            "serial oracle must begin idle and at an unused managed output")
    output.mkdir()
    phases, full_lifecycle, failure = [], [], None
    matched = []
    try:
        before, _ = launch(manifest, pin, "before", output)
        phases.append(before)
        if before["phase_passed"]:
            _, metadata = installed_api(Swapp)
            write_new(output / "RegisteredApi.json", metadata)
            for slot, choice in enumerate(trial["cases"]):
                require(not Swapp.application_pids(), "prior candidate left the serial oracle running")
                primary, after_edit = launch(manifest, pin, "edit", output, slot=slot, source=choice["archive_sha256"])
                phases.append(primary)
                if not primary["phase_passed"]:
                    continue
                reopened, record = launch(manifest, pin, "reopen", output, slot=slot, source=after_edit["artifact_sha256"])
                phases.append(reopened)
                if reopened["phase_passed"]:
                    saved, fresh = after_edit["edited"], record["reopened"]
                    if (saved["tree"] == fresh["tree"] and saved["definition"]["parents"] == fresh["definition"]["parents"]
                            and same_drivers(saved, fresh, cases[slot]["name"])):
                        full_lifecycle.append(slot)
                        if reference is not None:
                            matched.append(compare_disclosed_source(slot, cases[slot], reference[slot], after_edit, record))
    except Exception as issue:
        failure = str(issue)
    finally:
        if phases and not Swapp.application_pids():
            last, _ = launch(manifest, pin, "after", output)
            phases.append(last)
    lifetimes = [tuple(row["lifetime"]) for row in phases if row["lifetime"]]
    result = {"schema": SCHEMA, "manifest_sha256": pin, "lifecycle_slots": full_lifecycle, "phases": phases,
              "orchestration_failure": failure,
              "healthy_controls": bool(phases) and phases[0]["role"] == "before" and phases[-1]["role"] == "after"
              and phases[0]["phase_passed"] and phases[-1]["phase_passed"],
              "heldout_credit": 0, "proper_distinct_lifetimes": len(lifetimes) == len(set(lifetimes)) == len(phases)}
    result["passed"] = bool(not failure and result["healthy_controls"] and result["proper_distinct_lifetimes"]
                            and len(full_lifecycle) == len(cases) and len(phases) == 6)
    if reference is not None:
        result["disclosed_source_comparisons"] = matched
        result["passed"] = result["passed"] and len(matched) == len(cases) and all(row["passed"] for row in matched)
    write_new(output / "Result.json", result)
    print(json.dumps({"passed": result["passed"], "receipt_sha256": digest(output / "Result.json"), "phases": len(phases)}))
    return result["passed"]


def compare_disclosed_source(slot, case, reference, live, fresh):
    from ChamferComparison import compare_state

    rows = []
    for label, state, edited, saved in (
        ("open", live["reopened"], False, False),
        ("edited", live["edited"], True, False),
        ("reopen", fresh["reopened"], True, True),
    ):
        try:
            count = compare_state(state, reference["edited" if edited else "initial"], case,
                                  edited=edited, actual_saved=saved)
            rows.append({"phase": label, "numeric_checks": count, "passed": True})
        except ValueError as issue:
            rows.append({"phase": label, "failure": str(issue), "passed": False})
    return {"slot": slot, "passed": all(row["passed"] for row in rows), "phases": rows}


if __name__ == "__main__":
    options = ArgumentParser()
    options.add_argument("--manifest", type=Path, required=True)
    options.add_argument("--pin", required=True)
    mode = options.add_mutually_exclusive_group()
    mode.add_argument("--verify", action="store_true")
    mode.add_argument("--stage-signed", action="store_true")
    options.add_argument("--phase", choices=ROLES)
    options.add_argument("--slot", type=int)
    options.add_argument("--source")
    args = options.parse_args()
    if args.verify:
        verified(args.manifest, args.pin)
    elif args.stage_signed:
        stage_signed_guest(args.manifest, args.pin)
    else:
        trial, _, _ = verified(args.manifest, args.pin)
        guest = Path(trial["guest_packet"])
        require(os.name == "nt" and args.manifest.resolve() == (guest / "Trial.json").resolve()
                and Path(__file__).resolve().parent == guest / "Tool",
                "native trials require the frozen guest-local packet and runner")
        success = phase_job(args.manifest, args.pin, args.phase, args.slot, args.source) if args.phase else run_trial(args.manifest, args.pin)
        sys.exit(0 if success else 1)
