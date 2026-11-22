from argparse import ArgumentParser
import json
from math import atan2, degrees, hypot, isclose
import os
from pathlib import Path
import subprocess
import sys

from ColdEllipsePacket import GUEST, TRIAL, candidate_path, stage, verify
from EllipseModel import predict, require
from EllipsePacket import BUILD, CONTROLS, ORACLE, encode, predictions_equal, put, sha, valid_hash
from RunEllipseSources import control, exact


def own_paths(trial):
    packet = Path(GUEST / "Packet")
    require(os.name == "nt" and trial.resolve() == packet / TRIAL
            and Path(__file__).resolve().parent == packet / "Tool", "use the immutable guest-local prototype")
    return packet, Path(GUEST / "Capture")


def record_seam(author, stage_name, plan, api):
    row = author.profile_stage(stage_name, plan, api)
    start, end = (item["point"] for item in row["endpoints"].values() if item["status"] == "observed")
    observed = row["ellipse"]["points_m"]
    require(start == end and start["point_type"] == -1
            and start["id"] not in row["ellipse"]["point_ids"].values()
            and any(any(point == start for point in inventory.get("points", ())) for inventory in row["inventories"].values()),
            "both endpoints must retain one independent scoped seam point")
    relative = [value - center for value, center in zip(start["xyz_m"], observed["Center"], strict=True)]
    cos, sin = (sum(a * b for a, b in zip(relative, axis, strict=True)) / radius
                for axis, radius in zip(plan["unit_axes"], plan["radii_m"], strict=True))
    require(isclose(hypot(cos, sin), 1.0, rel_tol=0.0, abs_tol=1e-10)
            and isclose(relative[2], 0.0, abs_tol=1e-12), "native seam lies outside its actual ellipse")
    value = {"stage": stage_name, "id": start["id"], "phase_degrees": degrees(atan2(sin, cos))}
    entries = author.rec.data.setdefault("seam_positions", [])
    require(not entries or value["id"] == entries[0]["id"], "rebuild changed the scoped seam identity")
    entries.append(value)
    author.rec.flush()


def exact_name(state, source):
    parts = state["driver"]["name"].split("@")
    return len(parts) == 3 and parts[:2] == ["D1", "EllipseBoss"] and parts[2].casefold() == (source.stem + ".Part").casefold()


def candidate_phase(path, derivative, pin, case, phase, api, record):
    import Swapp
    from AuthorCurves import Recorder
    from EllipseSeamAuthor import BOSS, SeamAuthor
    from OracleIdentity import application_identity

    rec = Recorder(record, {"phase": phase, "source_sha256": pin})
    session, complete = None, False
    reopened = phase == "reopen"
    plan = predict(case)
    expected = plan["states"][int(reopened)]
    with Swapp.Dismisser() as monitor:
        try:
            require(not Swapp.application_pids() and sha(path) == pin, "cold input changed or oracle is occupied")
            session = rec.call("launch exact isolated .34 COM", Swapp.Sw)
            identity = rec.call("bind exact build and native lifetime", application_identity, session.app)
            rec.data["oracle_identity"] = identity
            rec.flush()
            require(exact(identity) and session.revision == "34.5.2", "wrong native oracle")
            author = SeamAuthor(session.app, rec, api["enums"])
            author.model, errors, warnings = rec.call("cold native open", session.open, path, read_only=reopened)
            rec.data["open_status"] = {"opened": author.model is not None, "errors": errors, "warnings": warnings}
            rec.flush()
            require(author.model is not None and errors == warnings == 0
                    and Path(str(author.get(author.model, "GetPathName"))).resolve() == path,
                    "cold candidate failed to open cleanly at its actual locator")
            count = rec.call("measure cold SOLIDWORKS solid count", Swapp.bodies, author.model)
            diagnostics = author.get(author.get(author.model, "Extension"), "GetWhatsWrongCount")
            rec.data["cold"] = {"solid_count": count, "diagnostics": diagnostics}
            rec.flush()
            record_seam(author, "cold_before_explicit_rebuild", plan, api)
            require(count == 1 and diagnostics == 0, "cold ellipse has no clean one-solid result")
            boss = author.get(author.model, "FeatureByName", BOSS)
            rec.data["cold"]["body"] = author.measure(boss, plan, expected)
            rec.flush()
            author.snapshot("initial", plan, edited=reopened)
            require(exact_name(rec.data["initial"], path), "native driving D1 has the wrong owning file")
            record_seam(author, "after_explicit_rebuild", plan, api)
            if not reopened:
                author.edit(plan)
                author.snapshot("edited", plan, edited=True)
                require(exact_name(rec.data["edited"], path), "depth edit uses a different native owner")
                record_seam(author, "after_depth_edit", plan, api)
                require(not derivative.exists(), "native derivative destination is occupied")
                status = rec.call("save owned edited native derivative", session.save_as, author.model, derivative)
                rec.data["save_status"] = list(status)
                rec.flush()
                require(status == (True, 0, 0) and derivative.is_file() and derivative.stat().st_size > 0
                        and Path(str(author.get(author.model, "GetPathName"))).resolve() == derivative,
                        "native ellipse derivative did not save cleanly")
                record_seam(author, "after_save", plan, api)
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
    surviving = path if reopened else derivative
    rec.data["artifact_sha256"] = sha(surviving) if surviving.is_file() else None
    rec.data["passed"] = bool(complete and sha(path) == pin and rec.data["artifact_sha256"]
                              and not rec.data["first_failure"] and not rec.data["cleanup_errors"]
                              and not rec.data["dialogs"] and not rec.data.get("controller_diagnostics"))
    rec.flush()
    return rec.data["passed"]


def phase_path(capture, entry):
    suffix = Path(entry["control"]).stem if entry["control"] else f"Slot{entry['slot'] + 1:02d}"
    return capture / f"{entry['phase']}-{suffix}"


def worker(trial, pin, phase_name):
    from EllipseSeamObserve import inspect_api

    job, cases, _ = verify(trial, pin)
    packet, capture = own_paths(trial)
    folder = Path(phase_name)
    require(folder.resolve().parent == capture and folder.resolve() == folder, "native phase is outside its owned capture")
    entry = json.loads((folder / "Phase.json").read_bytes())
    record = folder / "Record.json"
    require(entry["trial_sha256"] == pin and folder == phase_path(capture, entry) and not record.exists(),
            "native phase was not admitted by its locked supervisor")
    name, phase, slot = entry["control"], entry["phase"], entry["slot"]
    if name is not None:
        require(phase in ("before", "after") and name in CONTROLS and slot is entry["source"] is None,
                "incorrect independent control phase")
        return control(packet / name, record, CONTROLS[name])
    source_pin = entry["source"]
    require(phase in ("edit", "reopen") and type(slot) is int and 0 <= slot < len(cases) and valid_hash(source_pin),
            "incorrect native candidate phase")
    case = cases[slot]
    derivative = capture / (case["name"] + "Edited.SLDPRT")
    source = derivative if phase == "reopen" else packet / candidate_path(case)
    require(phase == "reopen" or source_pin == job["files"][candidate_path(case)]["sha256"],
            "edit phase input differs from its guarded generation")
    api = inspect_api()
    require(api == json.loads((capture / "RegisteredApi.json").read_bytes()), "registered ellipse API changed since preflight")
    return candidate_phase(source, derivative, source_pin, case, phase, api, record)


def launch(trial, pin, capture, phase, *, name=None, slot=None, source=None):
    entry = {"phase": phase, "control": name, "slot": slot, "source": source, "trial_sha256": pin}
    folder = phase_path(capture, entry)
    folder.mkdir()
    put(folder / "Phase.json", encode(entry))
    command = [sys.executable, "-E", "-B", str(Path(__file__).resolve()), "--trial", str(trial), "--pin", pin,
               "--phase", str(folder)]
    try:
        completed = subprocess.run(command, capture_output=True, timeout=180, check=False)
        code, stdout, stderr = completed.returncode, completed.stdout, completed.stderr
    except subprocess.TimeoutExpired as error:
        code, stdout, stderr = None, error.stdout or b"", error.stderr or b""
    put(folder / "Stdout.txt", stdout)
    put(folder / "Stderr.txt", stderr)
    record = folder / "Record.json"
    data = json.loads(record.read_bytes()) if record.is_file() else {}
    identity = data.get("oracle_identity", {})
    owned = exact(identity)
    if code is None and owned:
        from AuthorCurves import cleanup_owned_process

        try:
            cleanup = cleanup_owned_process(identity, {"executable_sha256": ORACLE})
        except Exception as error:
            cleanup = {"error": repr(error)}
        put(folder / "TimeoutCleanup.json", encode(cleanup))
    return entry | {"passed": code == 0 and not stderr and owned and data.get("passed") is True,
                    "exit_code": code, "receipt_sha256": sha(record) if record.is_file() else None,
                    "lifetime": [identity["process_id"], identity["process_creation_filetime"]] if owned else None,
                    "checks": len(data.get("checks", ()))}, data


def reconcile(initial, reopened, reference):
    candidates = (initial["initial"], initial["edited"], reopened["initial"])
    require(all({"tree": row["tree"], "configurations": row["configurations"], "parents": row["definition"]["parents"],
                 "children": row["definition"]["children"]} == reference for row in candidates),
            "complete ordered native tree, ordinary configuration or actual parents differ from the disclosed reference")
    require(all(predictions_equal(candidates[0]["profile"], row["profile"]) for row in candidates[1:])
            and initial["artifact_sha256"] == reopened["artifact_sha256"]
            and candidates[0]["body"]["mass"]["volume"] != candidates[2]["body"]["mass"]["volume"]
            and initial["seam_positions"][-1]["id"] == reopened["seam_positions"][0]["id"],
            "native edit and fresh reopen did not preserve actual signed geometry, identity and changed body volume")
    return {"passed": True, "tree_rows": len(reference["tree"]), "source_states": 3,
            "seam_phases": [*initial["seam_positions"], *reopened["seam_positions"]]}


def run(trial, pin):
    import Swapp
    from EllipseSeamObserve import inspect_api

    job, cases, reference = verify(trial, pin)
    packet, capture = own_paths(trial)
    require(not capture.exists() and not Swapp.application_pids() and not Swapp.owned_process_ids(),
            "prototype requires an unused capture and idle native oracle")
    capture.mkdir()
    phases, matched, failure = [], [], None

    def bracket(role):
        for name in CONTROLS:
            try:
                phases.append(launch(trial, pin, capture, role, name=name)[0])
            except Exception as error:
                phases.append({"phase": role, "control": name, "passed": False, "lifetime": None, "error": repr(error)})

    try:
        bracket("before")
        if all(row["passed"] for row in phases):
            put(capture / "RegisteredApi.json", encode(inspect_api()))
            for slot, case in enumerate(cases):
                input_pin = job["files"][candidate_path(case)]["sha256"]
                row, changed = launch(trial, pin, capture, "edit", slot=slot, source=input_pin)
                phases.append(row)
                if not row["passed"]:
                    continue
                row, fresh = launch(trial, pin, capture, "reopen", slot=slot, source=changed["artifact_sha256"])
                phases.append(row)
                if row["passed"]:
                    try:
                        matched.append({"slot": slot} | reconcile(changed, fresh, reference))
                    except ValueError as error:
                        matched.append({"slot": slot, "passed": False, "error": str(error)})
    except Exception as error:
        failure = repr(error)
    finally:
        if not Swapp.application_pids() and not Swapp.owned_process_ids():
            bracket("after")
    lives = [tuple(row["lifetime"]) for row in phases if row["lifetime"]]
    controls = [row for row in phases if row["control"]]
    result = {"trial_sha256": pin, "oracle_build": BUILD, "oracle_sha256": ORACLE, "phases": phases, "comparisons": matched,
              "healthy_controls": len(controls) == 4 and all(row["passed"] for row in controls),
              "fresh_processes": len(set(lives)), "batch_error": failure, "heldout_credit": 0,
              "idle_after": not Swapp.application_pids() and not Swapp.owned_process_ids()}
    result["passed"] = (len(phases) == len(lives) == result["fresh_processes"] == 8 and result["healthy_controls"]
                        and not failure and result["idle_after"] and len(matched) == 2 and all(row["passed"] for row in matched))
    terminal = capture / "Result.json"
    put(terminal, encode(result))
    print(json.dumps({"passed": result["passed"], "receipt_sha256": sha(terminal), "phases": len(phases)}, sort_keys=True))
    return result["passed"]


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--trial", required=True, type=Path)
    parser.add_argument("--pin", required=True)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--verify", action="store_true")
    mode.add_argument("--stage", action="store_true")
    mode.add_argument("--phase")
    args = parser.parse_args()
    if args.verify:
        verify(args.trial, args.pin)
    elif args.stage:
        stage(args.trial, args.pin)
    else:
        own_paths(args.trial)
        passed = worker(args.trial, args.pin, args.phase) if args.phase else run(args.trial, args.pin)
        raise SystemExit(0 if passed else 2)
