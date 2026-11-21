from argparse import ArgumentParser
from json import dumps, loads
import os
from pathlib import Path
from time import time

from ObservePlainNotePresentation01 import (
    CASES, ORACLE, ROLES, CurveAuthor, Recorder, capture, check_job, digest,
    drawing_state, publish, require,
)


FIELDS = (
    "swGridDisplay", "swGridDisplayDashed", "swGridAutomaticScaling",
    "swDisplayAnnotations", "swDisplayAllAnnotations", "swShowAnnotationInAnnotationViews",
)


def preferences(author, model, extension, api):
    enums = api["enums"]["swUserPreferenceToggle_e"]
    option = api["enums"]["swUserPreferenceOption_e"]["swDetailingNoOptionSpecified"]
    values = {name: bool(author.get(extension, "GetUserPreferenceToggle", enums[name], option)) for name in FIELDS}
    grid = list(author.get(model, "GetGridSettings"))
    require(len(grid) == 9, "unexpected native grid state shape")
    return {"toggles": values, "grid_values": grid}


def phase(directory, path, expected, intent, api):
    import Swapp
    from OracleIdentity import application_identity

    directory.mkdir()
    recorder = Recorder(directory / "Record.json", {"role": directory.name})
    row = {"passed": False}
    authority = author = None
    with Swapp.Dismisser() as dialogs:
        try:
            require(digest(path) == expected, "drawing changed before grid probe")
            Swapp.sweep()
            authority = Swapp.Sw(visible=True)
            row["identity"] = application_identity(authority.app)
            require(row["identity"]["version_matches"] and row["identity"]["sha256"] == ORACLE,
                    "wrong grid probe oracle")
            author = CurveAuthor(authority.app, recorder, Swapp)
            model, errors, warnings = authority.open(path, doctype=3, read_only=True)
            row["open"] = [errors, warnings]
            require(model is not None and errors == warnings == 0, "grid probe failed to open")
            author.model = model
            drawing = author.typed(model, "DrawingDoc")
            extension = author.typed(author.get(model, "Extension"), "ModelDocExtension")
            row["preference_state"] = preferences(author, model, extension, api)
            row["after_redraw_before_rebuild"] = capture(author, directory / "Initial.bmp")
            require(bool(author.get(model, "ForceRebuild3", False)), "grid probe rebuild failed")
            row["drawing"] = drawing_state(author, drawing, intent)
            row["post_rebuild_preference_state"] = preferences(author, model, extension, api)
            require(row["preference_state"] == row["post_rebuild_preference_state"],
                    "drawing preference changed after the observed rebuild")
            row["after_rebuild"] = capture(author, directory / "Rebuilt.bmp")
            row["passed"] = True
        except Exception as error:
            recorder.failure(error)
        finally:
            if author is not None and author.model is not None:
                try:
                    recorder.call("close owned drawing", authority.close_doc, author.model)
                except Exception as error:
                    recorder.failure(error, cleanup=True)
            if authority is not None:
                try:
                    authority.close()
                except Exception as error:
                    recorder.failure(error, cleanup=True)
                row["controller_diagnostics"] = authority.diagnostics
    row["immutable_input"] = digest(path) == expected
    row["passed"] = bool(row["passed"] and row["immutable_input"] and not dialogs.log
                         and not row.get("controller_diagnostics") and not recorder.data["cleanup_errors"])
    recorder.data.update(result=row, passed=row["passed"], finished_at=time())
    recorder.flush()
    publish(directory / "Result.json", row)
    return row


def main():
    parser = ArgumentParser()
    parser.add_argument("mode", choices=("verify", "run"))
    parser.add_argument("--job", type=Path, required=True)
    parser.add_argument("--job-sha256", required=True)
    parser.add_argument("--api-sha256", required=True)
    parser.add_argument("--tool-sha256", required=True)
    args = parser.parse_args()
    root, job = check_job(args.job, args.job_sha256)
    require(digest(Path(__file__)) == args.tool_sha256, "grid probe implementation changed")
    api_file = root / "GridApi01.json"
    require(digest(api_file) == args.api_sha256, "grid probe COM metadata changed")
    api = loads(api_file.read_bytes())
    require(api["version"] == [34, 0] and api["cad_processes_started"] == 0,
            "wrong registered grid preference metadata")
    if args.mode == "verify":
        print(dumps({"native_processes": 0, "passed": True}))
        return 0
    require(os.name == "nt", "grid probe requires the reserved Windows guest")
    output = root / "GridDiagnostic01"
    output.mkdir()
    intent = loads((root / "Intent.json").read_bytes())
    rows = {}
    for role in ROLES:
        control = role in ("ControlBefore", "ControlAfter")
        if not control and not rows["ControlBefore"]["passed"]:
            rows[role] = {"passed": False, "skipped": "leading pristine control failed"}
            continue
        name = "Control.SLDDRW" if control else CASES[role]
        rows[role] = phase(output / role, root / name, job["files"][name], None if control else intent, api)
    check_job(args.job, args.job_sha256)
    births = {row["identity"]["process_creation_filetime"] for row in rows.values() if "identity" in row}
    passed = len(births) == 4 and all(row["passed"] for row in rows.values())
    result = output / "Result.json"
    publish(result, {
        "schema": "kit.sw2026.disclosed-drawing-note-grid.v1",
        "job_sha256": args.job_sha256, "api_sha256": args.api_sha256, "tool_sha256": args.tool_sha256,
        "distinct_processes": len(births), "passed": passed, "settings_writes": 0, "heldout_source_reads": 0,
        "phases": rows,
    })
    print(dumps({"passed": passed, "distinct_processes": len(births), "result_sha256": digest(result)}))
    return 0 if passed else 3


if __name__ == "__main__":
    raise SystemExit(main())
