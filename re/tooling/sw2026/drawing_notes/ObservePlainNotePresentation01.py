from argparse import ArgumentParser
from hashlib import sha256
from json import dumps, loads
from math import isclose, isfinite
import os
from pathlib import Path
from struct import unpack_from
from time import time

from AuthorCurves import CurveAuthor, Recorder
from AuthorDrawingSources import snapshot
from AuthorPlainDrawingNotes import CONTROL, ORACLE, note_state, one_note, publish, require
from InspectDrawingCache import drawing_tree


SCHEMA = "kit.sw2026.disclosed-plain-note-presentation.v1"
ROLES = ("ControlBefore", "NativeSource", "SdkCandidate", "ControlAfter")
CASES = {
    "NativeSource": "NativeSource/Disclosed01.SLDDRW",
    "SdkCandidate": "SdkCandidate/Disclosed01.SLDDRW",
}
TOOLS = {
    "AuthorCurves.py", "AuthorDrawingSources.py", "AuthorPlainDrawingNotes.py",
    "DrawingCacheCases.py", "InspectDrawingCache.py", "ObservePlainNotePresentation01.py",
    "OracleIdentity.py", "Swapp.py",
}


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def check_job(path, expected):
    root = path.resolve().parent
    require(digest(path) == expected, "presentation request hash differs")
    row = loads(path.read_bytes())
    require(row["schema"] == SCHEMA and row["roles"] == list(ROLES)
            and row["oracle_sha256"] == ORACLE and row["heldout_inputs_read"] == 0,
            "unexpected disclosed presentation scope")
    require(Path(__file__).resolve().parent == root / "Tools" and row["tools"].keys() == TOOLS,
            "presentation tool closure differs")
    for name, value in row["tools"].items():
        require(digest(root / "Tools" / name) == value, "presentation tool hash differs")
    require(row["files"].keys() == {"Control.SLDDRW", *CASES.values(), "Intent.json"}
            and row["files"]["Control.SLDDRW"] == CONTROL, "presentation archive closure differs")
    for name, value in row["files"].items():
        require(digest(root / name) == value, "presentation file hash differs")
    return root, row


def vector(raw, count, label):
    value = [float(item) for item in raw]
    require(len(value) == count and all(isfinite(item) for item in value), "invalid native " + label)
    return value


def note_geometry(author, drawing, intent):
    annotation = one_note(author, drawing)
    note, state = note_state(author, annotation, intent, False)
    text_point = vector(author.get(note, "GetTextPoint2"), 3, "text reference point")
    require(all(isclose(x, y, abs_tol=2e-9, rel_tol=0.0)
                for x, y in zip(text_point, state["position"], strict=True)),
            "native annotation point and text point differ")
    visible = int(author.get(annotation, "Visible"))
    require(visible == 1, "native note visibility differs")
    extent = vector(author.get(note, "GetExtent"), 6, "sheet-coordinate note extent")
    require(extent[0] < extent[3] and extent[1] < extent[4], "empty native note extent")
    display = author.typed(author.get(annotation, "GetDisplayData"), "DisplayData")
    count = int(author.get(display, "GetTextCount"))
    require(0 < count <= 512, "native annotation exposes no displayed text")
    pieces = []
    for index in range(count):
        piece = {
            "text": str(author.get(display, "GetTextAtIndex", index)),
            "font": str(author.get(display, "GetTextFontAtIndex", index)),
            "position": vector(author.get(display, "GetTextPositionAtIndex", index), 3, "display text offset"),
            "height": float(author.get(display, "GetTextHeightAtIndex", index)),
            "angle": float(author.get(display, "GetTextAngleAtIndex", index)),
        }
        require(isfinite(piece["height"]) and piece["height"] > 0 and isfinite(piece["angle"]),
                "incomplete native displayed text geometry")
        pieces.append(piece)
    require("".join(piece["text"] for piece in pieces) == state["text"], "displayed and live note text differ")
    note_name = str(author.get(note, "GetName"))
    require(note_name == state["name"], "native note and annotation names differ")
    return {
        **state, "note_name": note_name, "note_text_point": text_point, "visible": visible,
        "extent": extent, "display_pieces": pieces, "dangling": False,
    }


def drawing_state(author, drawing, intent):
    layout = snapshot(author, author.model, drawing, None, None, 0)
    tree = drawing_tree(author)
    require(any(row[0] == layout["sheet"] for row in tree), "native feature tree lacks the actual active sheet")
    extension = author.typed(author.get(author.model, "Extension"), "ModelDocExtension")
    references = list(author.get(extension, "GetDependencies", True, False, False, True, True) or ())
    require(not references, "drawing contains unexpected external references")
    sheet_view = author.typed(author.get(drawing, "GetFirstView"), "View")
    count = len(author.get(sheet_view, "GetAnnotations") or ())
    require(count == int(intent is not None), "drawing annotation count differs")
    return {
        "sheet_view": layout, "ordered_feature_tree": tree, "model_dependencies": references,
        "annotation_count": count, "note": None if intent is None else note_geometry(author, drawing, intent),
    }


def capture(author, path):
    require(not path.exists(), "native drawing viewport output already exists")
    author.get(author.model, "GraphicsRedraw2")
    require(bool(author.get(author.model, "SaveBMP", str(path), 960, 720)),
            "native drawing viewport did not produce a bitmap")
    raw = path.read_bytes()
    require(len(raw) > 54 and raw[:2] == b"BM", "native drawing did not produce a valid bitmap header")
    width, height = unpack_from("<ii", raw, 18)
    require(width > 0 and height != 0, "native drawing viewport bitmap is empty")
    return {"sha256": sha256(raw).hexdigest(), "bytes": len(raw), "width": width, "height": abs(height)}


def phase(directory, source, expected, intent):
    import Swapp
    from OracleIdentity import application_identity

    directory.mkdir()
    row = {"passed": False, "input_sha256": expected}
    record = Recorder(directory / "Record.json", {"role": directory.name})
    controller = author = None
    with Swapp.Dismisser() as dialogs:
        try:
            require(digest(source) == expected, "drawing changed before presentation open")
            Swapp.sweep()
            controller = Swapp.Sw(visible=True)
            identity = application_identity(controller.app)
            row["identity"] = identity
            require(identity["version_matches"] and identity["sha256"] == ORACLE, "wrong presentation oracle")
            author = CurveAuthor(controller.app, record, Swapp)
            model, errors, warnings = controller.open(source, doctype=3, read_only=True)
            row["open"] = [errors, warnings]
            require(model is not None and errors == warnings == 0, "presentation drawing did not open cleanly")
            author.model = model
            drawing = author.typed(model, "DrawingDoc")
            author.get(model, "GraphicsRedraw2")
            row["initial"] = drawing_state(author, drawing, intent)
            row["rebuild"] = bool(author.get(model, "ForceRebuild3", False))
            require(row["rebuild"], "presentation drawing rebuild failed")
            author.get(model, "GraphicsRedraw2")
            row["rebuilt"] = drawing_state(author, drawing, intent)
            require(row["initial"] == row["rebuilt"], "note presentation changed on rebuild")
            row["bitmap"] = capture(author, directory / "Viewport.bmp")
            row["passed"] = True
        except Exception as error:
            record.failure(error)
        finally:
            if author is not None and author.model is not None:
                try:
                    record.call("close owned drawing", controller.close_doc, author.model)
                except Exception as error:
                    record.failure(error, cleanup=True)
            if controller is not None:
                try:
                    controller.close()
                except Exception as error:
                    record.failure(error, cleanup=True)
                row["controller_diagnostics"] = controller.diagnostics
    row["immutable_input"] = digest(source) == expected
    row["dialogs"] = dialogs.log
    row["passed"] = bool(row["passed"] and row["immutable_input"] and not row["dialogs"]
                         and not row.get("controller_diagnostics") and not record.data["cleanup_errors"])
    record.data.update(result=row, passed=row["passed"], finished_at=time())
    record.flush()
    publish(directory / "Result.json", row)
    return row


def run(path, expected):
    require(os.name == "nt", "presentation observation requires the reserved Windows guest")
    root, job = check_job(path, expected)
    output = root / "Inspection"
    output.mkdir()
    intent = loads((root / "Intent.json").read_bytes())
    require((root / CASES["SdkCandidate"]).samefile(intent["locator"]), "candidate locator differs from the native file")
    rows = {}
    for role in ROLES:
        is_control = role in ("ControlBefore", "ControlAfter")
        if not is_control and not rows["ControlBefore"]["passed"]:
            rows[role] = {"passed": False, "skipped": "leading control failed"}
            continue
        name = "Control.SLDDRW" if is_control else CASES[role]
        rows[role] = phase(output / role, root / name, job["files"][name], None if is_control else intent)
    check_job(path, expected)
    births = {
        row["identity"]["process_creation_filetime"]
        for row in rows.values() if "identity" in row
    }
    ready = len(births) == len(ROLES) and all(row["passed"] for row in rows.values())
    controls_healthy = all(rows[role]["passed"] for role in ("ControlBefore", "ControlAfter"))
    controls_healthy = controls_healthy and rows["ControlBefore"]["initial"] == rows["ControlAfter"]["initial"]
    source, candidate = rows["NativeSource"], rows["SdkCandidate"]
    report = {
        "schema": SCHEMA, "job_sha256": expected, "measurements_complete": ready,
        "healthy_pristine_controls": controls_healthy, "distinct_processes": len(births),
        "sheet_and_tree_match": bool(ready and all(
            candidate["initial"][field] == source["initial"][field]
            for field in ("sheet_view", "ordered_feature_tree", "model_dependencies")
        )),
        "note_presentation_exact_match": bool(ready and candidate["initial"]["note"] == source["initial"]["note"]),
        "bitmap_bytes_match": bool(ready and candidate["bitmap"]["sha256"] == source["bitmap"]["sha256"]),
        "heldout_source_credit": False, "public_writer_qualified": False, "phases": rows,
    }
    result = output / "Result.json"
    publish(result, report)
    print(dumps({k: v for k, v in report.items() if k not in {"phases", "schema"}} | {"result_sha256": digest(result)}))
    return 0 if ready and controls_healthy else 3


def main():
    parser = ArgumentParser()
    parser.add_argument("mode", choices=("verify", "run"))
    parser.add_argument("--job", type=Path, required=True)
    parser.add_argument("--sha256", required=True)
    args = parser.parse_args()
    if args.mode == "run":
        return run(args.job, args.sha256)
    check_job(args.job, args.sha256)
    print(dumps({"verified": True, "native_processes": 0, "heldout_inputs_read": 0}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
