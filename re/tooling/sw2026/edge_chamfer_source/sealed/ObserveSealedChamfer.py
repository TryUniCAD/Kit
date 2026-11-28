from argparse import ArgumentParser
from pathlib import Path
import json
import os

from ChamferPacket import valid_hash
from FilletModel import require
from FilletPacket import CONTROL, digest
from RunNativeChamferProbe import candidate_phase, expected_at


def source_phase(case, plan, branch, source, pin, record, metadata, *, edited):
    import Swapp
    from AuthorCurves import Recorder
    from ChamferApi import installed_api
    from ChamferAuthor import ChamferAuthor
    from FilletSourcePhase import has_exact_identity
    from OracleIdentity import application_identity

    rec = Recorder(record, {"source_sha256": pin, "state": "edited" if edited else "original"})
    session, complete = None, False
    with Swapp.Dismisser() as monitor:
        try:
            require(not Swapp.application_pids() and source.is_file() and digest(source) == pin,
                    "source observation requires an exact immutable input and idle oracle")
            constants, api = installed_api(Swapp)
            require(api == metadata, "installed source observation API differs from the locked registration")
            session = rec.call("launch exact native oracle for bound source", Swapp.Sw)
            identity = rec.call("bind source build and process lifetime", application_identity, session.app)
            rec.data["oracle_identity"] = identity
            rec.flush()
            require(has_exact_identity(identity) and session.revision == "34.5.2", "wrong source oracle build")
            author = ChamferAuthor(session.app, rec, constants)
            author.model, errors, warnings = rec.call("cold open immutable native source", session.open, source,
                                                       read_only=True)
            rec.data["open_status"] = {"opened": author.model is not None, "errors": errors, "warnings": warnings}
            rec.flush()
            require(author.model is not None and errors == warnings == 0, "immutable source open failed or warned")
            require(Path(str(author.get(author.model, "GetPathName"))).resolve() == source,
                    "source opened an unexpected locator")
            count = int(rec.call("cold source solid count", Swapp.bodies, author.model))
            diagnostics = int(author.get(author.get(author.model, "Extension"), "GetWhatsWrongCount"))
            mass = rec.call("cold source mass and area", Swapp.mass, author.model) if count == 1 else None
            rec.data["cold"] = {"body_count": count, "diagnostics": diagnostics, "mass": mass}
            rec.flush()
            require(count == 1 and diagnostics == 0 and mass and "error" not in mass,
                    "immutable original has no clean cold one-solid result")
            expected = expected_at(plan, branch, edited)
            for key, zero in (("volume", 1e-21), ("area", 1e-16)):
                author.close_six("cold source " + key, mass[key], expected[key], near_zero=zero)
            for index, (a, b) in enumerate(zip(mass["com"], expected["com"], strict=True)):
                author.close_six(f"cold source centre {index}", a, b, near_zero=1e-10)
            state = author.snapshot(case, plan, "reopened", edited=edited)
            require(state["configurations"] == ["Default"] and state["branch"] == branch,
                    "source left the expressly qualified stock or configuration")
            complete = True
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
    rec.data["artifact_sha256"] = digest(source)
    rec.data["passed"] = bool(complete and rec.data["artifact_sha256"] == pin and not rec.data["first_failure"]
                              and not rec.data["cleanup_errors"] and not rec.data["dialogs"]
                              and not rec.data.get("controller_diagnostics"))
    rec.flush()
    return rec.data["passed"]


def worker(spec, pin):
    from RunSealedChamfer import EVAL_ROOT, SIGNED_EVAL_ROOT, SOURCE_ROOT, private_path

    tool = Path(__file__).resolve().parent
    output = tool.parents[1]
    require(os.name == "nt" and valid_hash(pin) and output in (EVAL_ROOT, SIGNED_EVAL_ROOT)
            and tool == output / "Packet/Tool" and private_path(spec, output).is_file() and digest(spec) == pin,
            "native observer must use the frozen guest-local job")
    state = json.loads(spec.read_bytes())
    source = Path(state["source"])
    record = private_path(spec.parent / "Record.json", output)
    role = state["role"]
    require(not record.exists(), "native phase receipt is already occupied")
    if role in ("before", "after"):
        from FilletSourcePhase import run_control

        require(source == output / "Packet/Control.SLDPRT" and digest(source) == CONTROL
                and set(state) == {"role", "source"}, "control is not the independent pinned part")
        return run_control(source, record)
    original = role in ("original", "original-edited")
    require(original or role in ("edit", "reopen"), "native observer received an unknown phase")
    private_path(source, SOURCE_ROOT if original else output)
    target = private_path(Path(state["target"]), output)
    require(valid_hash(state["sha256"]) and digest(source) == state["sha256"], "observer input seal differs")
    metadata = json.loads((output / "RegisteredApi.json").read_bytes())
    args = (state["case"], state["prediction"], state["branch"])
    if original:
        return source_phase(*args, source, state["sha256"], record, metadata, edited=role == "original-edited")
    return candidate_phase(*args, role, source, target, state["sha256"], record, metadata)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("phase", type=Path)
    parser.add_argument("pin")
    args = parser.parse_args()
    raise SystemExit(0 if worker(args.phase, args.pin) else 2)
