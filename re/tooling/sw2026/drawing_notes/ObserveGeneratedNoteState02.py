import argparse
from hashlib import sha256
from json import dumps, loads
from math import isclose
import os
from pathlib import Path
import sys


ROLES = ("ControlBefore", "NativeNoteSource", "GeneratedState", "ControlAfter")


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def check(value, reason):
    if not value:
        raise ValueError(reason)


def read_trial(path, expected):
    check(digest(path) == expected, "note observer-only trial identity changed")
    trial = loads(path.read_bytes())
    check(trial["schema"] == "kit.sw2026.generated-note-state-retry.v1"
          and trial["roles"] == list(ROLES)
          and trial["observer_sha256"] == digest(Path(__file__))
          and Path(__file__).resolve().parent == path.resolve().parent,
          "unexpected note state observer method")
    check(trial["source_packet"] in {"NativePacket01", "NativePacket02"}, "unexpected note packet name")
    source_packet = path.resolve().parent.parent / trial["source_packet"]
    prior = source_packet / "Job.json"
    check(trial["prior_job_sha256"] == digest(prior), "original note trial changed")
    prior_job = loads(prior.read_bytes())
    check(
        prior_job["files_sha256"]["Candidate/PlainNativeOrigin.SLDDRW"] == trial["candidate_sha256"],
        "state retry changed the generated note bytes",
    )
    for name, checksum in prior_job["tool_sha256"].items():
        check(digest(source_packet / "Tools" / name) == checksum, "original note observer tool changed")
    sys.path.insert(0, str(source_packet / "Tools"))
    from ObserveGeneratedNote01 import verify
    verify(prior, trial["prior_job_sha256"])
    return trial, source_packet, prior_job


def capture(author, drawing, intent):
    from AuthorPlainDrawingNotes import one_note
    first_view = author.typed(author.get(drawing, "GetFirstView"), "View")
    rows = list(author.get(first_view, "GetAnnotations") or ())
    if intent is None:
        return {"notes": len(rows), "passed": not rows}
    annotation = one_note(author, drawing)
    note = author.typed(author.get(annotation, "GetSpecificAnnotation"), "Note")
    text = str(author.get(note, "GetText"))
    location = list(author.get(annotation, "GetPosition"))
    name = str(author.get(annotation, "GetName") or "")
    try:
        note_text_point = {"value": list(author.get(note, "GetTextPoint2") or ())}
    except Exception as error:
        note_text_point = {"error": {"type": type(error).__name__, "message": str(error)}}
    name_matches = name == "DetailItem1" if intent.get("publish_identity") else bool(name)
    matches = (
        len(location) == 3 and all(isclose(value, target, rel_tol=0.0, abs_tol=2e-9)
                                  for value, target in zip(location, intent["initial_position"], strict=True))
    )
    attachments = len(list(author.get(annotation, "GetAttachedEntities3") or ()))
    dangling = bool(author.get(annotation, "IsDangling"))
    return {
        "text": text, "expected_text": intent["initial_text"],
        "text_matches": text == intent["initial_text"],
        "name": name, "name_nonempty": bool(name), "name_matches": name_matches,
        "position": location, "note_text_point": note_text_point, "expected_position": intent["initial_position"],
        "position_matches": matches, "annotation_count": len(rows),
        "attachments": attachments, "dangling": dangling,
        "passed": text == intent["initial_text"] and name_matches and matches and attachments == 0 and not dangling,
    }


def phase(source, expected, role, intent, out):
    from AuthorCurves import CurveAuthor, Recorder
    from AuthorDrawingSources import snapshot
    from AuthorPlainDrawingNotes import ORACLE
    from OracleIdentity import application_identity
    import Swapp

    report = {"role": role, "observation_complete": False, "passed": False}
    controller = None
    model = None
    recorder = Recorder(out / "Record.json", {"role": role})
    try:
        check(digest(source) == expected, "frozen note comparison input changed")
        Swapp.sweep()
        controller = Swapp.Sw(visible=True)
        identity = application_identity(controller.app)
        check(identity["file_version"] == "34.5.2.0604" and identity["sha256"] == ORACLE
              and identity["version_matches"], "wrong SOLIDWORKS oracle")
        report["identity"] = identity
        author = CurveAuthor(controller.app, recorder, Swapp)
        check(int(author.get(controller.app, "GetDocumentCount")) == 0, "drawing process is not cold")
        model, error, warning = controller.open(source, doctype=3, read_only=True)
        report["open"] = [error, warning]
        check(model is not None and error == warning == 0, "native drawing open failed")
        author.model = model
        drawing = author.typed(model, "DrawingDoc")
        report["before_rebuild"] = capture(author, drawing, intent)
        before = snapshot(author, model, drawing, None, None, 0)
        report["rebuild"] = bool(author.get(model, "ForceRebuild3", False))
        report["after_rebuild"] = capture(author, drawing, intent)
        after = snapshot(author, model, drawing, None, None, 0)
        report["sheet_and_tree_unchanged"] = before == after
        report["source_immutable"] = digest(source) == expected
        report["observation_complete"] = bool(
            report["rebuild"] and report["sheet_and_tree_unchanged"] and report["source_immutable"]
        )
    except Exception as error:
        report["error"] = {"type": type(error).__name__, "message": str(error)}
    finally:
        if controller is not None:
            try:
                if model is not None:
                    controller.close_doc(model)
                controller.close()
                report["owned_cleanup_diagnostics"] = len(controller.diagnostics)
            except Exception as error:
                report["cleanup_error"] = {"type": type(error).__name__, "message": str(error)}
    report["passed"] = bool(
        report["observation_complete"] and report.get("owned_cleanup_diagnostics") == 0
        and report["before_rebuild"]["passed"] and report["after_rebuild"]["passed"]
    )
    return report


def run(trial_path, expected, state, packet, inputs):
    from AuthorPlainDrawingNotes import CONTROL, publish

    check(os.name == "nt", "the root-owned Windows oracle runs native note state")
    output = trial_path.resolve().parent / "Inspection"
    output.mkdir()
    native = "NativeControl/Disclosed01.SLDDRW"
    generated = "Candidate/PlainNativeOrigin.SLDDRW"
    control = packet / "Control.SLDDRW"
    intent = loads((packet / "Intent.json").read_bytes())
    source_intent = loads((packet / "NativeControl/Intent.json").read_bytes())
    check((packet / generated).samefile(intent["locator"]), "same-byte native note moved")
    reference_sha256 = inputs["files_sha256"]
    arguments = {
        "ControlBefore": (control, CONTROL, None),
        "NativeNoteSource": (packet / native, reference_sha256[native], source_intent),
        "GeneratedState": (packet / generated, reference_sha256[generated], intent),
        "ControlAfter": (control, CONTROL, None),
    }
    results = {}
    for role in ROLES:
        if role == "GeneratedState" and not all(results[name]["passed"] for name in ROLES[:2]):
            results[role] = {"skipped": "leading independent controls failed", "observation_complete": False}
            continue
        path = output / role
        path.mkdir()
        source, source_hash, case = arguments[role]
        results[role] = phase(source, source_hash, role, case, path)
        publish(path / "Result.json", results[role])
    identities = {
        row["identity"]["process_creation_filetime"]
        for row in results.values() if "identity" in row
    }
    controls = all(results[role]["passed"] for role in ("ControlBefore", "NativeNoteSource", "ControlAfter"))
    completed = controls and len(identities) == 4 and results["GeneratedState"]["observation_complete"]
    read_trial(trial_path, expected)
    report = {
        "schema": "kit.sw2026.generated-note-state-retry-result.v1",
        "controls_healthy": controls,
        "diagnostic_completed": completed,
        "observations": results,
        "fresh_processes": len(identities),
        "candidate_sha256": state["candidate_sha256"],
        "source_immutable": True,
        "native_acceptance": False,
        "file_saves": 0,
        "parameter_edits": 0,
        "trial_sha256": expected,
    }
    publish(output / "Result.json", report)
    print(dumps({
        "diagnostic_completed": completed, "controls_healthy": controls,
        "fresh_processes": len(identities),
        "raw_result_sha256": digest(output / "Result.json"),
    }, sort_keys=True))
    return 0 if completed else 3


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("verify", "run"))
    parser.add_argument("--trial", required=True, type=Path)
    parser.add_argument("--sha256", required=True)
    args = parser.parse_args()
    state, packet, inputs = read_trial(args.trial, args.sha256)
    if args.command == "verify":
        print(dumps({"verified": True, "native_processes": 0, "input_sha256": state["candidate_sha256"]}))
        return 0
    return run(args.trial, args.sha256, state, packet, inputs)


if __name__ == "__main__":
    raise SystemExit(main())
