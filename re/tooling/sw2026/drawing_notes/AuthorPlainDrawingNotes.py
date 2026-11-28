from argparse import ArgumentParser
from hashlib import sha256
from json import dumps, loads
from math import isclose
from pathlib import Path
from secrets import randbelow, token_hex
import os


ORACLE = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
CONTROL = "227f12b5834f73e31d1cb64db9e615418852bfba6c30d6c2700be6e26cc4932b"
TEMPLATE = "05eb7612f0921d7f2b5bef7cc5576a54993f38740285d31fb2d7b1a09808ef66"
SCHEMA = "kit.sw2026.drawing-plain-note-source.v1"
TOOLS = {"AuthorPlainDrawingNotes.py", "AuthorCurves.py", "AuthorDrawingSources.py",
         "OracleIdentity.py", "Swapp.py"}
PAPER = [0.0, 13.0, 1.0, 1.0, 0.0, 11 * 0.0254, 8.5 * 0.0254, 1.0]
CASES = ("Disclosed01", "Disclosed02", "Slot01", "Slot02")


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def publish(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as output:
        output.write(dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n")


def read_job(path, expected):
    require(digest(path) == expected, "plain-note job changed")
    value = loads(path.read_bytes())
    root = path.resolve().parent
    require(value["schema"] == SCHEMA and value["cases"] == list(CASES),
            "plain-note case scope differs")
    require(value["oracle_sha256"] == ORACLE and value["template_sha256"] == TEMPLATE,
            "plain-note oracle or template identity differs")
    require(value["control_sha256"] == CONTROL and digest(root / "Control.SLDDRW") == CONTROL,
            "pristine drawing control changed")
    require(set(value["tools_sha256"]) == TOOLS and Path(__file__).resolve().parent == root / "Tools",
            "frozen plain-note tool closure differs")
    for name, known in value["tools_sha256"].items():
        require(digest(root / "Tools" / name) == known, "plain-note source program changed")
    return value


def note_state(author, annotation, intent, edited):
    note = author.typed(author.get(annotation, "GetSpecificAnnotation"), "Note")
    stem = "edited" if edited else "initial"
    text = str(author.get(note, "GetText"))
    position = list(author.get(annotation, "GetPosition"))
    name = str(author.get(annotation, "GetName"))
    require(text == intent[stem + "_text"] and bool(name), "ordinary note text or name differs")
    require(not list(author.get(annotation, "GetAttachedEntities3") or ())
            and not bool(author.get(annotation, "IsDangling")), "expected a free non-dangling note")
    require(len(position) == 3 and all(
        isclose(actual, target, rel_tol=0.0, abs_tol=2e-9)
        for actual, target in zip(position, intent[stem + "_position"], strict=True)
    ), "ordinary note coordinate differs")
    return note, {"name": name, "text": text, "position": position, "attachment_count": 0}


def one_note(author, drawing):
    sheet = author.typed(author.get(drawing, "GetFirstView"), "View")
    notes = list(author.get(sheet, "GetAnnotations") or ())
    require(len(notes) == 1, "expected exactly one unlinked sheet annotation")
    return author.typed(notes[0], "Annotation")


def native_phase(control, template, directory, label, intent, incoming, expected, outgoing):
    import Swapp
    from AuthorCurves import CurveAuthor, Recorder
    from AuthorDrawingSources import snapshot
    from OracleIdentity import application_identity

    row = {"phase": label, "passed": False}
    controller = model = None
    directory.mkdir()
    recorder = Recorder(directory / "Record.json", {"phase": label})
    try:
        Swapp.sweep()
        controller = Swapp.Sw(visible=True)
        identity = application_identity(controller.app)
        require(identity["version_matches"] and identity["sha256"] == ORACLE, "wrong SOLIDWORKS oracle")
        row["identity"] = identity
        author = CurveAuthor(controller.app, recorder, Swapp)
        source = control if intent is None else incoming
        if source is None:
            model = author.get(controller.app, "NewDocument", str(template), 0, 0.0, 0.0)
            require(model is not None, "native drawing template returned no document")
        else:
            require(digest(source) == expected, "native source identity differs before open")
            model, errors, warnings = controller.open(source, doctype=3, read_only=outgoing is None)
            row["open"] = [errors, warnings]
            require(model is not None and errors == warnings == 0, "native source open failed or warned")
        author.model = model
        drawing = author.typed(model, "DrawingDoc")
        sheet = snapshot(author, model, drawing, None, None, 0)
        require(all(isclose(actual, target, rel_tol=0.0, abs_tol=1e-12)
                    for actual, target in zip(sheet["sheet_properties"], PAPER, strict=True)),
                "native note source changed its unformatted ANSI A sheet")
        if intent is not None:
            if source is None:
                author.get(model, "ClearSelection2", True)
                note = author.typed(author.get(model, "InsertNote", intent["initial_text"]), "Note")
                annotation = author.typed(author.get(note, "GetAnnotation"), "Annotation")
                require(bool(author.get(annotation, "SetPosition2", *intent["initial_position"])),
                        "native note position was rejected")
            else:
                annotation = one_note(author, drawing)
            if label == "edit":
                note, _ = note_state(author, annotation, intent, False)
                require(bool(author.get(note, "SetText", intent["edited_text"])),
                        "native note text edit failed")
                require(bool(author.get(annotation, "SetPosition2", *intent["edited_position"])),
                        "native note position edit failed")
            edited = label in ("edit", "reopen")
            _, row["initial_note"] = note_state(author, annotation, intent, edited)
        require(bool(author.get(model, "ForceRebuild3", False)), "native drawing rebuild failed")
        row["sheet"] = snapshot(author, model, drawing, None, None, 0)
        require(row["sheet"] == sheet, "native sheet changed during note lifecycle")
        if intent is None:
            view = author.typed(author.get(drawing, "GetFirstView"), "View")
            require(not list(author.get(view, "GetAnnotations") or ()), "pristine control has an annotation")
        else:
            _, row["rebuilt_note"] = note_state(author, one_note(author, drawing), intent, edited)
            require(row["initial_note"]["name"] == row["rebuilt_note"]["name"], "note identity changed during rebuild")
        if outgoing is not None:
            require(not outgoing.exists(), "native source destination already exists")
            row["save"] = list(controller.save_as(model, outgoing))
            require(row["save"] == [True, 0, 0] and outgoing.is_file(), "native source save failed")
            row["output_sha256"] = digest(outgoing)
        if source is not None:
            require(digest(source) == expected, "native phase edited its immutable input")
        row["passed"] = True
    finally:
        if controller is not None:
            if model is not None:
                controller.close_doc(model)
            controller.close()
            row["diagnostic_count"] = len(controller.diagnostics)
            row["passed"] = row["passed"] and row["diagnostic_count"] == 0
        publish(directory / "PrivateResult.json", row)
    require(row["passed"], "native note phase or owned cleanup failed")
    return row


def make_private_intent(case):
    region = 0.055 if case == "Slot01" else 0.135
    x, y = region + randbelow(200) / 10000, 0.058 + randbelow(650) / 10000
    token = token_hex(8)
    prefix = "inspection " if case == "Slot01" else "drawing Ω "
    return {"initial_text": prefix + token, "edited_text": prefix + "revised " + token,
            "initial_position": [x, y, 0.0], "edited_position": [x + 0.0113, y - 0.0041, 0.0]}


def run(path, job, receipt):
    root = path.parent
    template = Path(job["template"])
    private = Path(job["private_root"])
    require(os.name == "nt" and private.is_absolute() and private.drive.upper() == "C:"
            and not private.exists() and digest(template) == TEMPLATE, "guest-local source custody differs")
    require(not receipt.exists(), "source report already exists")
    private.mkdir()
    control = root / "Control.SLDDRW"
    rows, controls, failures = {}, {}, []
    for case in ("ControlBefore", *CASES, "ControlAfter"):
        try:
            if case in ("ControlBefore", "ControlAfter"):
                expected = native_phase(control, template, private / case, case, None, None, CONTROL, None)
                controls[case] = expected["identity"]["process_creation_filetime"]
                continue
            require("ControlBefore" in controls, "leading source control failed")
            is_private = case.startswith("Slot")
            directory = (private if is_private else root) / case
            directory.mkdir()
            intent = make_private_intent(case) if is_private else job["disclosed_intent"][case]
            publish(directory / "Intent.json", intent)
            original = directory / (case + ".SLDDRW")
            edited = directory / (case + "Edit.SLDDRW")
            author = native_phase(control, template, directory / "author", "author", intent, None, None, original)
            edit = native_phase(control, template, directory / "edit", "edit", intent, original,
                                author["output_sha256"], edited)
            reopen = native_phase(control, template, directory / "reopen", "reopen", intent, edited,
                                  edit["output_sha256"], None)
            require(edit["rebuilt_note"]["name"] == reopen["rebuilt_note"]["name"],
                    "edited note identity changed on fresh reopen")
            rows[case] = {
                "original_sha256": author["output_sha256"], "edited_sha256": edit["output_sha256"],
                "intent_sha256": digest(directory / "Intent.json"), "private": is_private,
                "process_births": [item["identity"]["process_creation_filetime"] for item in (author, edit, reopen)],
            }
        except Exception as error:
            if case.startswith("Slot"):
                failures.append({"case": case, "failure_kind": type(error).__name__})
            else:
                failures.append({"case": case, "failure_kind": type(error).__name__, "failure": str(error)})
    births = {*controls.values(), *(birth for row in rows.values() for birth in row["process_births"])}
    passed = not failures and len(births) == 14 and len(rows) == 4 and len(controls) == 2
    result = {"schema": SCHEMA, "oracle_build": "34.5.2.0604", "job_sha256": digest(path),
              "prewriter_revision": job["prewriter_revision"], "source_cases": rows, "controls": controls,
              "distinct_passing_processes": len(births), "failure": failures, "passed": passed,
              "private_source_values_disclosed": False, "writer_generated_cases": 0}
    publish(receipt, result)
    return 0 if passed else 1


def main():
    parser = ArgumentParser()
    parser.add_argument("mode", choices=("verify", "run"))
    parser.add_argument("job", type=Path)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()
    job = read_job(args.job, args.sha256)
    if args.mode == "verify":
        print(dumps({"passed": True, "native_launches": 0, "cases": len(CASES)}))
        return 0
    require(args.receipt is not None and args.receipt.parent == args.job.parent,
            "use an unused receipt inside the shared packet directory")
    return run(args.job, job, args.receipt)


if __name__ == "__main__":
    raise SystemExit(main())
