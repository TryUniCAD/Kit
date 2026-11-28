import argparse
from hashlib import sha256
import json
import os
from pathlib import Path, PureWindowsPath
import shutil
import time

from BlankDrawingPrivate import (
    SLOTS,
    fingerprint,
    read_intent,
    require,
    seal,
    write_new,
)

SCHEMA = "kit.sw2026.blank-drawing-source-slots.v1"
ORACLE = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
CONTROL = "227f12b5834f73e31d1cb64db9e615418852bfba6c30d6c2700be6e26cc4932b"
TEMPLATE = "05eb7612f0921d7f2b5bef7cc5576a54993f38740285d31fb2d7b1a09808ef66"
TEMPLATE_PATH = r"C:\ProgramData\SOLIDWORKS\SOLIDWORKS 2026\templates\Drawing.DRWDOT"
OWNED = (
    "BlankDrawingPrivate.py",
    "BlankDrawingSourceSlots.py",
    "InspectDrawingCache.py",
)
SHARED = (
    "AuthorDrawingSources.py",
    "AuthorCurves.py",
    "DrawingCacheCases.py",
    "OracleIdentity.py",
    "Swapp.py",
)
PHASES = ("before", "author", "edit", "reopen", "after")


def store(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def verify(path, expected):
    root = path.resolve().parent
    require(fingerprint(path) == expected, "source packet identity differs")
    job = json.loads(path.read_bytes())
    require(
        job["schema"] == SCHEMA and job["slots"] == list(SLOTS),
        "source packet scope differs",
    )
    require(
        job["oracle_sha256"] == ORACLE and job["control_sha256"] == CONTROL,
        "oracle/control identity differs",
    )
    require(
        job["template_sha256"] == TEMPLATE and job["writer_output_count"] == 0,
        "source prerequisites differ",
    )
    require(
        job["private_values_on_host"] is False and job["evaluation_enabled"] is False,
        "source-only custody differs",
    )
    require(
        Path(__file__).resolve().parent == root / "Tools",
        "use the frozen source tool directory",
    )
    require(
        set(job["tools_sha256"]) == set(OWNED + SHARED), "source tool closure differs"
    )
    for name, digest in job["tools_sha256"].items():
        require(
            fingerprint(root / "Tools" / name) == digest,
            "source tool identity differs: " + name,
        )
    require(fingerprint(root / "Control.SLDDRW") == CONTROL, "pristine drawing changed")
    if os.name == "nt":
        require(
            fingerprint(Path(job["template_path"])) == TEMPLATE,
            "installed source template changed",
        )
    return root, job


def prepare(args):
    root = args.output.resolve()
    require(
        not root.exists()
        and root.parent.is_dir()
        and not root.is_relative_to(args.source_root.resolve()),
        "use an unused external packet",
    )
    require(fingerprint(args.control) == CONTROL, "use the exact disclosed D00 drawing")
    private = PureWindowsPath(args.private_root)
    guest, python = PureWindowsPath(args.guest_root), PureWindowsPath(args.guest_python)
    require(
        private.drive.upper() == "C:"
        and private.is_absolute()
        and ".." not in private.parts,
        "use guest-local private storage",
    )
    require(
        guest.is_absolute() and python.is_absolute(), "use absolute guest locations"
    )
    root.mkdir()
    (root / "Tools").mkdir()
    shutil.copyfile(args.control, root / "Control.SLDDRW")
    tools = {}
    for name in OWNED + SHARED:
        source = (
            Path(__file__).parent / name
            if name in OWNED
            else args.source_root / "re/tooling/sw2026" / name
        )
        shutil.copyfile(source, root / "Tools" / name)
        tools[name] = fingerprint(root / "Tools" / name)
    constructor = (
        args.source_root
        / "src/convert/adapters/solidworks/Drawing/Construction/Portable/MakeBlankFile.py"
    )
    job = {
        "schema": SCHEMA,
        "slots": list(SLOTS),
        "oracle_sha256": ORACLE,
        "control_sha256": CONTROL,
        "template_sha256": TEMPLATE,
        "template_path": TEMPLATE_PATH,
        "tools_sha256": tools,
        "guest_private_root": str(private),
        "guest_python": str(python),
        "control_expected": {
            "sheet": "Sheet1",
            "sheet_properties": [
                0.0,
                13.0,
                1.0,
                1.0,
                0.0,
                11 * 0.0254,
                8.5 * 0.0254,
                1.0,
            ],
            "whats_wrong": 0,
            "view": None,
        },
        "existing_internal_constructor_sha256": fingerprint(constructor),
        "chronology": "new blind source locks before future public writer promotion; internal MakeBlankFile already exists",
        "private_values_on_host": False,
        "evaluation_enabled": False,
        "writer_output_count": 0,
        "native_acceptance": False,
    }
    write_new(root / "Protocol.json", job)
    digest = fingerprint(root / "Protocol.json")
    command = [str(python), "-B", str(guest / "Tools/BlankDrawingSourceSlots.py")]
    tail = [str(guest / "Protocol.json"), "--packet-sha256", digest]
    commands = [
        {"name": name, "argv": command + [name] + tail}
        for name in ("verify", "metadata")
    ]
    for slot in SLOTS:
        commands.append(
            {
                "name": slot + "/seal",
                "argv": command + ["seal"] + tail + ["--slot", slot],
            }
        )
        for name in (*PHASES, "lock"):
            commands.append(
                {
                    "name": slot + "/" + name,
                    "argv": command
                    + ["phase"]
                    + tail
                    + ["--slot", slot, "--phase", name],
                }
            )
    commands.append({"name": "summary", "argv": command + ["summary"] + tail})
    write_new(
        root / "Recipe.json",
        {
            "schema": SCHEMA,
            "packet_sha256": digest,
            "commands": commands,
            "root_only_serial_native_execution": True,
            "always_run_independent_after_control": True,
            "never_dump_guest_private_files": True,
        },
    )
    return {
        "passed": True,
        "packet_sha256": digest,
        "recipe_sha256": fingerprint(root / "Recipe.json"),
        "private_intents_created": 0,
        "native_launches": 0,
    }


def metadata(root, job):
    require(os.name == "nt", "metadata requires the guest registry")
    import pythoncom

    template = Path(job["template_path"])
    require(
        template.is_file()
        and template.stat().st_size == 15104
        and fingerprint(template) == TEMPLATE,
        "installed drawing template changed",
    )
    pythoncom.CoInitialize()
    try:
        library = pythoncom.LoadRegTypeLib(
            "{83A33D31-27C5-11CE-BFD4-00400513BB57}", 34, 0, 0
        )
        require(
            tuple(library.GetLibAttr()[3:5]) == (34, 0), "type library version differs"
        )
        rows = []
        wanted = {
            "SetName",
            "SetScale",
            "GetName",
            "GetProperties2",
            "GetSheetFormatName",
        }
        for index in range(library.GetTypeInfoCount()):
            info = library.GetTypeInfo(index)
            if info.GetDocumentation(-1)[0] == "ISheet":
                for ordinal in range(info.GetTypeAttr().cFuncs):
                    desc = info.GetFuncDesc(ordinal)
                    names = list(info.GetNames(desc.memid))
                    if names and names[0] in wanted:
                        rows.append(
                            {
                                "names": names,
                                "member_id": desc.memid,
                                "invoke_kind": desc.invkind,
                                "arguments": repr(desc.args),
                                "return_type": repr(desc.rettype),
                                "argument_count": len(desc.args),
                            }
                        )
        require(
            {row["names"][0] for row in rows} == wanted,
            "registered sheet prerequisites differ",
        )
        require(
            all(
                row["argument_count"]
                == {"SetName": 1, "SetScale": 4}.get(row["names"][0], 0)
                for row in rows
            ),
            "registered sheet argument count differs",
        )
        write_new(
            root / "Metadata.json",
            {
                "passed": True,
                "type_library_version": [34, 0],
                "template_sha256": TEMPLATE,
                "members": rows,
                "native_launches": 0,
            },
        )
    finally:
        pythoncom.CoUninitialize()
    return {
        "passed": True,
        "metadata_sha256": fingerprint(root / "Metadata.json"),
        "native_launches": 0,
    }


def prior(root, slot, phase):
    value = json.loads((root / "Progress" / slot / phase / "Record.json").read_bytes())
    require(
        value["passed"]
        and value["phase"] == phase
        and value["slot"] == slot
        and value["packet_sha256"] == fingerprint(root / "Protocol.json"),
        "source phase prerequisite is not healthy",
    )
    return value


def expected(job, intent, edited=False):
    value = {
        **job["control_expected"],
        "sheet": intent["sheet_name"],
        "sheet_properties": list(job["control_expected"]["sheet_properties"]),
    }
    value["sheet_properties"][2:4] = (
        intent["edit_scale_ratio"] if edited else intent["scale_ratio"]
    )
    return value


def author_phase(root, job, private, slot, intent):
    import Swapp
    import AuthorCurves as curves
    from AuthorDrawingSources import make_drawing
    from InspectDrawingCache import check_drawing
    from OracleIdentity import application_identity

    directory = private / "author"
    directory.mkdir(parents=True, exist_ok=False)
    rec = curves.Recorder(directory / "Record.json", {"slot": slot, "phase": "author"})
    controller = author = None
    result = {"passed": False}
    native = private / "Native/Source.SLDDRW"
    native.parent.mkdir(exist_ok=False)
    with Swapp.Dismisser() as dialogs:
        try:
            rec.call("blank source idle guard", Swapp.sweep)
            controller = rec.call(
                "start fresh blank drawing source", Swapp.Sw, visible=True
            )
            identity = rec.call(
                "verify exact drawing oracle", application_identity, controller.app
            )
            result["oracle_identity"] = identity
            require(
                identity["version_matches"]
                and identity["sha256"] == ORACLE
                and controller.revision == "34.5.2",
                "native drawing build differs",
            )
            author = curves.CurveAuthor(controller.app, rec, Swapp)
            drawing = make_drawing(
                author, controller, Path(job["template_path"]), 0, None, None
            )
            sheet = author.typed(author.get(drawing, "GetCurrentSheet"), "Sheet")
            author.get(sheet, "SetName", intent["sheet_name"])
            require(
                str(author.get(sheet, "GetName")) == intent["sheet_name"],
                "actual sheet rename failed",
            )
            require(
                str(author.get(sheet, "GetSheetFormatName")) == "",
                "source is not an unformatted sheet",
            )
            require(
                bool(
                    author.get(sheet, "SetScale", *intent["scale_ratio"], False, False)
                ),
                "source sheet scale failed",
            )
            wanted = expected(job, intent)
            result["initial"], result["tree"] = check_drawing(
                author, drawing, wanted, None
            )
            require(
                len(result["tree"]) == 10,
                "blank source tree is outside the qualified ten-row profile",
            )
            require(
                bool(author.get(author.model, "ForceRebuild3", False)),
                "source rebuild failed",
            )
            result["rebuilt"], _ = check_drawing(
                author, drawing, wanted, result["tree"]
            )
            result["save_status"] = list(
                rec.call(
                    "save native blank source", controller.save_as, author.model, native
                )
            )
            require(
                result["save_status"] == [True, 0, 0]
                and native.is_file()
                and native.stat().st_size > 0,
                "native source save failed or warned",
            )
            result["passed"] = True
        except Exception as error:
            rec.failure(error)
        finally:
            if author is not None and author.model is not None:
                try:
                    controller.close_doc(author.model)
                except Exception as error:
                    rec.failure(error, cleanup=True)
            if controller is not None:
                try:
                    controller.close()
                except Exception as error:
                    rec.failure(error, cleanup=True)
                result["controller_diagnostics"] = controller.diagnostics
    result["passed"] = bool(
        result["passed"]
        and not dialogs.log
        and not result.get("controller_diagnostics")
        and rec.data["first_failure"] is None
        and not rec.data["cleanup_errors"]
    )
    if native.is_file():
        result["native_sha256"] = fingerprint(native)
        result["native_bytes"] = native.stat().st_size
    rec.data.update(result=result, passed=result["passed"], finished_at=time.time())
    rec.flush()
    return {**result, "record_sha256": fingerprint(directory / "Record.json")}


def phase(root, job, packet_sha, slot, name):
    require(os.name == "nt", "native source phases require the guest")
    require(
        json.loads((root / "Metadata.json").read_bytes())["passed"] is True,
        "metadata must qualify before source phases",
    )
    if name == "lock":
        rows = [prior(root, slot, item) for item in PHASES]
        private = Path(job["guest_private_root"]) / slot
        sealed = prior(root, slot, "seal")
        read_intent(private, sealed["intent_sha256"], slot)
        require(
            fingerprint(private / "Native/Source.SLDDRW") == rows[1]["artifact_sha256"]
            and fingerprint(private / "edit/EditedDrawing.SLDDRW")
            == rows[2]["artifact_sha256"],
            "native source artifacts changed before lock",
        )
        identities = [
            row["process_identity"]["process_creation_filetime"] for row in rows
        ]
        require(len(set(identities)) == 5, "source lock needs five fresh processes")
        require(
            all(a["finished_at"] <= b["started_at"] for a, b in zip(rows, rows[1:])),
            "native phases must be serial",
        )
        result = {
            "passed": True,
            "slot": slot,
            "phase": name,
            "packet_sha256": packet_sha,
            "heldout_source_locked": True,
            "native_processes": 5,
            "healthy_controls": 2,
            "writer_output_count": 0,
            "phase_sha256": {
                item: fingerprint(root / "Progress" / slot / item / "Record.json")
                for item in PHASES
            },
            "source_sha256": rows[1]["artifact_sha256"],
            "edited_sha256": rows[2]["artifact_sha256"],
            "intent_sha256": prior(root, slot, "seal")["intent_sha256"],
        }
        write_new(root / "Progress" / slot / "lock/Record.json", result)
        return result
    from InspectDrawingCache import phase as inspect_phase
    import Swapp
    from OracleIdentity import application_identity

    private = Path(job["guest_private_root"]) / slot
    progress = root / "Progress" / slot / name / "Record.json"
    require(not progress.exists(), "phase output is immutable")
    state = {
        "passed": False,
        "slot": slot,
        "phase": name,
        "packet_sha256": packet_sha,
        "stage": "starting",
        "started_at": time.time(),
    }
    store(progress, state)
    result = None
    try:
        if name in ("before", "after"):
            tree = None
            if name == "after":
                try:
                    before = json.loads(
                        (private / "before/Record.json").read_bytes()
                    ).get("result", {})
                    if before.get("passed"):
                        tree = before.get("tree")
                except (OSError, ValueError, TypeError):
                    tree = None
            result = inspect_phase(
                Swapp,
                application_identity,
                directory=private / name,
                native=root / "Control.SLDDRW",
                expected_hash=CONTROL,
                expected=job["control_expected"],
                tree=tree,
                oracle_sha=ORACLE,
                edit=False,
            )
        else:
            prior(root, slot, "before")
            sealed = prior(root, slot, "seal")
            intent = read_intent(private, sealed["intent_sha256"], slot)
            if name == "author":
                result = author_phase(root, job, private, slot, intent)
            else:
                authored = prior(root, slot, "author")
                raw = json.loads((private / "author/Record.json").read_bytes())[
                    "result"
                ]
                edited = name == "reopen"
                previous = prior(root, slot, "edit") if edited else authored
                native = (
                    private / "edit/EditedDrawing.SLDDRW"
                    if edited
                    else private / "Native/Source.SLDDRW"
                )
                result = inspect_phase(
                    Swapp,
                    application_identity,
                    directory=private / name,
                    native=native,
                    expected_hash=previous["artifact_sha256"],
                    expected=expected(job, intent, edited),
                    tree=raw["tree"],
                    oracle_sha=ORACLE,
                    edit=not edited,
                    edited_ratio=intent["edit_scale_ratio"],
                )
                require(
                    fingerprint(private / "Native/Source.SLDDRW")
                    == authored["artifact_sha256"],
                    "original source changed during editing/reopen",
                )
        require(result["passed"], "native source phase failed")
        identity = result["oracle_identity"]
        state.update(
            passed=True,
            stage="passed",
            process_identity={
                key: identity[key]
                for key in (
                    "process_id",
                    "process_creation_filetime",
                    "file_version",
                    "sha256",
                )
            },
            private_record_sha256=result["record_sha256"],
        )
        if name == "author":
            state["artifact_sha256"] = result["native_sha256"]
        elif name == "edit":
            state["artifact_sha256"] = result["derivative_sha256"]
    except Exception as error:
        state.update(stage="failed", error_type=type(error).__name__)
        if result is not None:
            state["private_record_sha256"] = result.get("record_sha256")
            identity = result.get("oracle_identity", {})
            state["process_identity"] = {
                key: identity[key]
                for key in (
                    "process_id",
                    "process_creation_filetime",
                    "file_version",
                    "sha256",
                )
                if key in identity
            }
    state["finished_at"] = time.time()
    store(progress, state)
    return state


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "mode", choices=("prepare", "verify", "metadata", "seal", "phase", "summary")
    )
    parser.add_argument("packet", type=Path, nargs="?")
    parser.add_argument("--packet-sha256")
    parser.add_argument("--slot", choices=SLOTS)
    parser.add_argument("--phase", choices=(*PHASES, "lock"))
    parser.add_argument("--source-root", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--control", type=Path)
    parser.add_argument("--guest-root")
    parser.add_argument("--guest-python")
    parser.add_argument("--private-root")
    args = parser.parse_args()
    try:
        if args.mode == "prepare":
            result = prepare(args)
        else:
            root, job = verify(args.packet, args.packet_sha256)
            if args.mode == "verify":
                result = {
                    "passed": True,
                    "native_launches": 0,
                    "private_intents_read": 0,
                }
            elif args.mode == "metadata":
                result = metadata(root, job)
            elif args.mode == "seal":
                require(os.name == "nt", "private source sealing requires the guest")
                require(
                    json.loads((root / "Metadata.json").read_bytes())["passed"] is True,
                    "metadata must pass before private source sealing",
                )
                result = {
                    "passed": True,
                    "slot": args.slot,
                    "phase": "seal",
                    "packet_sha256": args.packet_sha256,
                    "intent_sha256": seal(
                        Path(job["guest_private_root"]) / args.slot, args.slot
                    ),
                    "writer_output_count": 0,
                }
                write_new(root / "Progress" / args.slot / "seal/Record.json", result)
            elif args.mode == "phase":
                result = phase(root, job, args.packet_sha256, args.slot, args.phase)
            else:
                rows = [prior(root, slot, "lock") for slot in SLOTS]
                identities = [
                    prior(root, slot, name)["process_identity"][
                        "process_creation_filetime"
                    ]
                    for slot in SLOTS
                    for name in PHASES
                ]
                require(
                    len(set(identities)) == 10,
                    "both slots require ten independent native processes",
                )
                result = {
                    "passed": True,
                    "source_slots_locked": 2,
                    "distinct_native_processes": 10,
                    "healthy_controls": 4,
                    "writer_output_count": 0,
                    "evaluation_enabled": False,
                    "slot_lock_sha256": {
                        slot: fingerprint(root / "Progress" / slot / "lock/Record.json")
                        for slot in SLOTS
                    },
                }
                write_new(root / "SourceLock.json", result)
        print(json.dumps(result))
        return 0 if result["passed"] else 3
    except Exception as error:
        print(
            json.dumps(
                {
                    "passed": False,
                    "stage": args.mode,
                    "error_type": type(error).__name__,
                    "private_values_printed": False,
                }
            )
        )
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
