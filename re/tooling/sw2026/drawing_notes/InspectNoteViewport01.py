from argparse import ArgumentParser
from json import dumps, loads
import os
from pathlib import Path

from ObserveNoteDisplayFlags01 import verify
from ObservePlainNotePresentation01 import (
    ORACLE, CurveAuthor, Recorder, capture, digest, publish, require, vector,
)


ROLES = ("ControlBefore", "NativeSource", "Generated", "ControlAfter")


def pose(author):
    view = author.get(author.model, "ActiveView")
    orientation = author.get(author.get(view, "Orientation3"), "ArrayData")
    translation = author.get(author.get(view, "Translation3"), "ArrayData")
    raw_zoom = author.get(view, "Scale2")
    zoom, = vector((raw_zoom,), 1, "drawing viewport zoom")
    require(zoom > 0, "drawing viewport zoom is not positive")
    return {"orientation": vector(orientation, 16, "drawing viewport orientation"),
            "translation": vector(translation, 3, "drawing viewport translation"), "zoom": zoom}


def phase(role, output, source, expected):
    import Swapp
    from OracleIdentity import application_identity

    directory = output / role
    directory.mkdir()
    record = Recorder(directory / "Record.json", {"role": role})
    row = {"passed": False}
    authority = author = None
    with Swapp.Dismisser() as dialogs:
        try:
            require(digest(source) == expected, "viewport input changed")
            Swapp.sweep()
            authority = Swapp.Sw(visible=True)
            row["identity"] = application_identity(authority.app)
            require(row["identity"]["version_matches"] and row["identity"]["sha256"] == ORACLE, "wrong viewport oracle")
            author = CurveAuthor(authority.app, record, Swapp)
            model, errors, warnings = authority.open(source, doctype=3, read_only=True)
            row["open"] = [errors, warnings]
            require(model is not None and errors == warnings == 0, "viewport drawing did not open cleanly")
            author.model = model
            row["initial_pose"] = pose(author)
            row["initial_bitmap"] = capture(author, directory / "Initial.bmp")
            extension = author.typed(author.get(model, "Extension"), "ModelDocExtension")
            author.get(extension, "ViewZoomToSheet")
            row["after_fit_bitmap"] = capture(author, directory / "Fit.bmp")
            row["passed"] = True
        except Exception as error:
            record.failure(error)
        finally:
            if author is not None and author.model is not None:
                try:
                    record.call("close owned model", authority.close_doc, author.model)
                except Exception as error:
                    record.failure(error, cleanup=True)
            if authority is not None:
                try:
                    authority.close()
                except Exception as error:
                    record.failure(error, cleanup=True)
                row["controller_diagnostics"] = authority.diagnostics
    row["immutable_input"] = digest(source) == expected
    row["passed"] = bool(row["passed"] and row["immutable_input"] and not dialogs.log
                         and not row.get("controller_diagnostics") and not record.data["cleanup_errors"])
    record.data.update(result=row, passed=row["passed"])
    record.flush()
    publish(directory / "Result.json", row)
    return row


def main():
    parser = ArgumentParser()
    parser.add_argument("mode", choices=("verify", "run"))
    parser.add_argument("--job", type=Path, required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--tool-sha256", required=True)
    args = parser.parse_args()
    root, job = verify(args.job, args.sha256)
    require(digest(Path(__file__)) == args.tool_sha256, "viewport diagnostic changed")
    if args.mode == "verify":
        print(dumps({"verified": True, "native_processes": 0}))
        return 0
    require(os.name == "nt", "viewport diagnostic requires the reserved Windows guest")
    output = root / "SheetFitDiagnostic02"
    output.mkdir()
    rows = {}
    for role in ROLES:
        if role in ("ControlBefore", "ControlAfter"):
            key = "Control.SLDDRW"
        else:
            controls = ("ControlBefore", "NativeSource") if role == "Generated" else ("ControlBefore",)
            if not all(rows[name]["passed"] for name in controls):
                rows[role] = {"passed": False, "skipped": "preceding control failed"}
                continue
            case = "Source" if role == "NativeSource" else "GridOffBoth"
            key = case + "/Disclosed01.SLDDRW"
        rows[role] = phase(role, output, root / key, job["files"][key])
    births = {row["identity"]["process_creation_filetime"] for row in rows.values() if "identity" in row}
    result = output / "Result.json"
    passed = len(births) == 4 and all(row["passed"] for row in rows.values())
    publish(result, {"schema": "kit.sw2026.disclosed-drawing-note-sheet-fit.v1",
                     "passed": passed, "job_sha256": args.sha256, "tool_sha256": args.tool_sha256,
                     "distinct_processes": len(births), "file_saves": 0, "settings_writes": 0, "phases": rows})
    print(dumps({"passed": passed, "distinct_processes": len(births), "result_sha256": digest(result)}))
    return 0 if passed else 3


if __name__ == "__main__":
    raise SystemExit(main())
