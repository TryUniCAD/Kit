from argparse import ArgumentParser
from hashlib import sha256
from json import dumps, loads
import os
from pathlib import Path
from struct import unpack_from
from time import time

from InspectNoteGrid01 import preferences
from ObserveNoteDisplayFlags01 import verify as verify_display_matrix
from ObservePlainNotePresentation01 import (
    ORACLE, CurveAuthor, Recorder, capture, digest, drawing_state, note_state, one_note, publish, require,
)


SCHEMA = "kit.sw2026.disclosed-drawing-memory-changes.v1"
ROLES = {
    "ControlBefore": "Control.SLDDRW",
    "NativeSource": "Source/Disclosed01.SLDDRW",
    "Generated": "GridOffBoth/Disclosed01.SLDDRW",
    "ControlAfter": "Control.SLDDRW",
}


def verify(path, expected):
    root = path.resolve().parent
    require(digest(path) == expected, "memory-change trial hash differs")
    job = loads(path.read_bytes())
    require(job["schema"] == SCHEMA and job["roles"] == list(ROLES)
            and job["oracle_sha256"] == ORACLE and job["heldout_inputs_read"] == 0,
            "memory-change trial scope differs")
    require(Path(__file__).resolve().parent == root / "Tools"
            and digest(Path(__file__)) == job["tool_sha256"], "memory-change tool differs")
    _, matrix = verify_display_matrix(root / "Job.json", job["matrix_sha256"])
    require(all(job["files"][name] == matrix["files"][name] for name in ROLES.values())
            and job["files"].keys() == set(ROLES.values()), "memory-change input closure differs")
    source = loads((root / "Source/Intent.json").read_bytes())
    require(job["replace_text"] == source["edited_text"] != source["initial_text"]
            and job["insert_text"] not in (source["initial_text"], job["replace_text"])
            and job["insert_position"] != source["initial_position"], "memory-change requests are not distinct")
    return root, job, source


def insert(author, descriptor):
    author.get(author.model, "ClearSelection2", True)
    note = author.typed(author.get(author.model, "InsertNote", descriptor["initial_text"]), "Note")
    annotation = author.typed(author.get(note, "GetAnnotation"), "Annotation")
    require(bool(author.get(annotation, "SetPosition2", *descriptor["initial_position"])),
            "native insert position rejected")
    return note_state(author, annotation, descriptor, False)[1]


def inventory(author, drawing, descriptors):
    sheet = author.typed(author.get(drawing, "GetFirstView"), "View")
    annotations = list(author.get(sheet, "GetAnnotations") or ())
    require(len(annotations) == len(descriptors), "sheet annotation count differs")
    observations = {}
    for raw in annotations:
        annotation = author.typed(raw, "Annotation")
        note = author.typed(author.get(annotation, "GetSpecificAnnotation"), "Note")
        value = str(author.get(note, "GetText"))
        require(value in descriptors and value not in observations, "unexpected live sheet annotation")
        observations[value] = note_state(author, annotation, descriptors[value], False)[1]
    return observations


def bitmap(author, directory, label):
    author.get(author.model, "ClearSelection2", True)
    path = directory / (label + ".bmp")
    frame = capture(author, path)
    raw = path.read_bytes()
    offset = unpack_from("<I", raw, 10)[0]
    require(54 <= offset < len(raw), "bitmap has no pixel storage")
    return frame | {"pixel_sha256": sha256(raw[offset:]).hexdigest()}


def phase(directory, path, expected, source, job, api):
    import Swapp
    from OracleIdentity import application_identity

    directory.mkdir()
    row = {"passed": False, "input_sha256": expected}
    recorder = Recorder(directory / "Record.json", {"role": directory.name})
    controller = author = None
    new_note = {"initial_text": job["insert_text"], "initial_position": job["insert_position"]}
    with Swapp.Dismisser() as dialogs:
        try:
            require(digest(path) == expected, "drawing changed before open")
            Swapp.sweep()
            controller = Swapp.Sw(visible=True)
            identity = application_identity(controller.app)
            row["identity"] = identity
            require(identity["version_matches"] and identity["sha256"] == ORACLE, "wrong memory-change oracle")
            author = CurveAuthor(controller.app, recorder, Swapp)
            model, errors, warnings = controller.open(path, doctype=3, read_only=True)
            row["open"] = [errors, warnings]
            require(model is not None and errors == warnings == 0, "memory-change drawing did not open cleanly")
            author.model = model
            drawing = author.typed(model, "DrawingDoc")
            extension = author.typed(author.get(model, "Extension"), "ModelDocExtension")
            row["preferences"] = preferences(author, model, extension, api)
            require(bool(author.get(model, "ForceRebuild3", False)), "initial rebuild failed")
            row["initial"] = drawing_state(author, drawing, source)
            row["initial_bitmap"] = bitmap(author, directory, "Initial")
            descriptors = {}
            if source is not None:
                annotation = one_note(author, drawing)
                note, original = note_state(author, annotation, source, False)
                require(bool(author.get(note, "SetText", job["replace_text"])), "native text replacement rejected")
                changed = {"initial_text": job["replace_text"], "initial_position": source["initial_position"]}
                descriptors[job["replace_text"]] = changed
                seen = inventory(author, drawing, descriptors)[job["replace_text"]]
                require(seen["name"] == original["name"], "native text replacement changed note identity")
                row["edited_note"] = seen
                row["edited_bitmap"] = bitmap(author, directory, "Edited")
                require(bool(author.get(model, "ForceRebuild3", False)), "edited rebuild failed")
                require(inventory(author, drawing, descriptors)[job["replace_text"]] == seen,
                        "editor state changed on rebuild")
                row["edited_rebuilt_bitmap"] = bitmap(author, directory, "EditedRebuilt")
            row["inserted_note"] = insert(author, new_note)
            descriptors[job["insert_text"]] = new_note
            row["inserted_annotations"] = inventory(author, drawing, descriptors)
            require(row["inserted_annotations"][job["insert_text"]] == row["inserted_note"],
                    "native inserted note does not belong to the sheet")
            row["inserted_bitmap"] = bitmap(author, directory, "Inserted")
            require(bool(author.get(model, "ForceRebuild3", False)), "inserted rebuild failed")
            require(inventory(author, drawing, descriptors) == row["inserted_annotations"],
                    "inserted sheet annotations changed on rebuild")
            require(preferences(author, model, extension, api) == row["preferences"],
                    "document display preferences changed")
            row["inserted_rebuilt_bitmap"] = bitmap(author, directory, "InsertedRebuilt")
            row["passed"] = True
        except Exception as error:
            recorder.failure(error)
        finally:
            if author is not None and author.model is not None:
                try:
                    recorder.call("close owned drawing", controller.close_doc, author.model)
                except Exception as error:
                    recorder.failure(error, cleanup=True)
            if controller is not None:
                try:
                    controller.close()
                except Exception as error:
                    recorder.failure(error, cleanup=True)
                row["controller_diagnostics"] = controller.diagnostics
    row["immutable_input"] = digest(path) == expected
    row["dialogs"] = dialogs.log
    row["passed"] = bool(row["passed"] and row["immutable_input"] and not row["dialogs"]
                         and not row.get("controller_diagnostics") and not recorder.data["cleanup_errors"])
    recorder.data.update(result=row, passed=row["passed"], finished_at=time())
    recorder.flush()
    publish(directory / "Result.json", row)
    return row


def bitmap_changes(row):
    if not row["passed"]:
        return None
    initial = row["initial_bitmap"]["pixel_sha256"]
    edit = row["edited_rebuilt_bitmap"]["pixel_sha256"] if "edited_rebuilt_bitmap" in row else None
    before_insert = initial if edit is None else edit
    return {
        "edit_changed_pixels_on_redraw": None if edit is None else row["edited_bitmap"]["pixel_sha256"] != initial,
        "edit_changed_pixels_after_rebuild": None if edit is None else edit != initial,
        "insert_changed_pixels_on_redraw": row["inserted_bitmap"]["pixel_sha256"] != before_insert,
        "insert_changed_pixels_after_rebuild": row["inserted_rebuilt_bitmap"]["pixel_sha256"] != before_insert,
    }


def main():
    parser = ArgumentParser()
    parser.add_argument("mode", choices=("verify", "run"))
    parser.add_argument("--job", type=Path, required=True)
    parser.add_argument("--sha256", required=True)
    args = parser.parse_args()
    root, job, source = verify(args.job, args.sha256)
    if args.mode == "verify":
        print(dumps({"verified": True, "native_processes": 0, "heldout_inputs_read": 0}))
        return 0
    require(os.name == "nt", "memory-change trial requires the reserved Windows guest")
    output = root / "MemoryDiagnostic01"
    output.mkdir()
    api = loads((root / "GridApi01.json").read_bytes())
    rows = {}
    for role, name in ROLES.items():
        control = role in ("ControlBefore", "ControlAfter")
        if role == "Generated" and not all(rows[item]["passed"] for item in ("ControlBefore", "NativeSource")):
            rows[role] = {"passed": False, "skipped": "independent leading controls failed"}
            continue
        rows[role] = phase(output / role, root / name, job["files"][name], None if control else source, job, api)
    verify(args.job, args.sha256)
    births = {row["identity"]["process_creation_filetime"] for row in rows.values() if "identity" in row}
    changes = {name: bitmap_changes(row) for name, row in rows.items()}
    before, after = rows["ControlBefore"], rows["ControlAfter"]
    native = changes["NativeSource"]
    controls = bool(before["passed"] and after["passed"] and native and all(
        before[field] == after[field] for field in ("initial", "initial_bitmap", "inserted_rebuilt_bitmap")
    ) and native["edit_changed_pixels_after_rebuild"] and native["insert_changed_pixels_after_rebuild"])
    complete = len(births) == len(ROLES) and all(row["passed"] for row in rows.values())
    result = output / "Result.json"
    aggregate = {"complete": complete, "healthy_controls": controls, "distinct_processes": len(births),
                 "bitmap_changes": changes}
    publish(result, {
        "schema": SCHEMA, "job_sha256": args.sha256, **aggregate, "settings_writes": 0,
        "document_saves": 0, "heldout_source_reads": 0, "phases": rows,
    })
    print(dumps(aggregate | {"result_sha256": digest(result)}))
    return 0 if complete and controls else 3


if __name__ == "__main__":
    raise SystemExit(main())
