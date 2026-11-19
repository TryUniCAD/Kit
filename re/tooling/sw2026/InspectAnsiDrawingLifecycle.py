from __future__ import annotations

import sys
from pathlib import Path, PureWindowsPath

TOOLS = Path(__file__).resolve().parent
sys.path[:] = [value for value in sys.path if Path(value or ".").resolve() != TOOLS]
sys.path.append(str(TOOLS))

import argparse
import json
import os
from math import isclose
from shutil import copyfileobj
import time

from AuthorCurves import Recorder, digest, require, write_json
from AuthorDrawingSources import set_view_position
from AuthorRectangleAnchors import RectangleAuthor
from SpatialTextNativeObserve import child_state, observe

SCHEMA = "kit.sw2026.ansi-pair-native-lifecycle-packet.v1"
ORACLE = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
CONTROL = "c0472f9f42bf473a9073adb997180040b7767dfae93310610f77cff9509bec57"
PHASES = ("open-save", "reopen", "edit-move-save", "reopen-edited")
NAMES = {
    "InspectAnsiDrawingLifecycle.py",
    "SpatialTextNativeObserve.py",
    "OriginNativeObserve.py",
    "OriginNativePredict.py",
    "AuthorCurves.py",
    "AuthorDrawingSources.py",
    "AuthorRectangleAnchors.py",
    "InspectFresh.py",
    "OracleIdentity.py",
    "Swapp.py",
}


def checked(root, row):
    name = Path(row["path"])
    require(
        not name.is_absolute() and ".." not in name.parts,
        "packet input path must be contained",
    )
    raw = root / name
    path = raw.resolve(strict=True)
    require(
        not raw.is_symlink()
        and path.is_relative_to(root.resolve())
        and path.is_file()
        and path.stat().st_size == row["bytes"]
        and digest(path) == row["sha256"],
        "frozen origin trial input changed",
    )
    return path


def verify(packet, expected):
    require(
        packet.is_file() and digest(packet) == expected,
        "origin trial packet digest differs",
    )
    root = packet.parent.resolve(strict=True)
    job = json.loads(packet.read_bytes())
    require(
        job["schema"] == SCHEMA
        and job["oracle_sha256"] == ORACLE
        and job["hidden_inputs_read"] == 0
        and job["native_acceptance"] is False
        and job["heldout_acceptance"] is False,
        "origin trial scope differs",
    )
    require(
        Path(__file__).resolve().parent == root / "Tools"
        and set(job["tools"]) == NAMES,
        "origin trial requires its exact complete observer tools",
    )
    for name, row in job["tools"].items():
        require(row["path"] == "Tools/" + name, "observer tool path differs")
        checked(root, row)
    centreline = job.get("experiment") == "drawing-centreline-initialization"
    expected_cases = 2 if centreline else 4
    require(
        job["control"]["sha256"] == CONTROL
        and len(job["cases"]) == expected_cases
        and job.get("expected_native_processes", 18) == 2 + expected_cases * len(PHASES)
        and job["source_original_admission"] is False
        and job["expected_text_depths_m"] == [0.0, 0.0, 0.0, 0.0],
        "spatial text trial control or case scope differs",
    )
    if centreline:
        require(
            {(case["style_mode"], case["kind"]) for case in job["cases"]}
            == {("ansi", "corner"), ("ansi", "center")}
            and job["complete_style_retention_required"] is True
            and job["ansi_drawing_f20_exemption"] is False,
            "centreline trial requires both measured ANSI profiles and full style retention",
        )
    checked(root, job["control"])
    for row in job["custody"]:
        checked(root, row)
    targets = set()
    for case in job["cases"]:
        require(
            case["kind"] in ("corner", "center")
            and len(case["part_tree"]) == 25
            and len(case["drawing_tree"]) == 16,
            "origin trial lacks its complete independently predicted trees",
        )
        for kind, suffix in (("drawing", ".SLDDRW"), ("child", ".SLDPRT")):
            checked(root, case["files"][kind])
            target = PureWindowsPath(case["paths"][kind])
            require(
                target.is_absolute()
                and target.drive.upper() == "C:"
                and target.suffix.upper() == suffix
                and ".." not in target.parts
                and str(target).casefold() not in targets,
                "origin trial encoded guest target is invalid or duplicated",
            )
            targets.add(str(target).casefold())
    return job


def preflight(job):
    require(
        os.name == "nt",
        "guest target preflight requires Windows and performs no CAD calls",
    )
    rows = [
        {"path": path, "exists": Path(path).exists()}
        for case in job["cases"]
        for path in case["paths"].values()
    ]
    require(
        not any(row["exists"] for row in rows),
        "an exact encoded guest target already exists: "
        + json.dumps([row for row in rows if row["exists"]]),
    )
    return rows


def copy_new(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    with source.open("rb") as first, target.open("xb") as second:
        copyfileobj(first, second)
    require(digest(source) == digest(target), "new owned native working copy differs")


def identity_fields(value):
    return {
        key: value[key]
        for key in ("process_id", "process_creation_filetime", "file_version", "sha256")
    }


def phase(root, job, case, name, baseline, moved):
    import Swapp
    from OracleIdentity import application_identity

    directory = root / "Inspection" / case["name"] / name
    directory.mkdir(parents=True, exist_ok=False)
    rec = Recorder(directory / "Record.json", {"case": case["name"], "phase": name})
    result, controller = {"passed": False, "case": case["name"], "phase": name}, None
    source_draw = Path(case["paths"]["drawing"])
    child = Path(case["paths"]["child"])
    edited = name in ("edit-move-save", "reopen-edited")
    input_drawing = (
        source_draw
        if name == "open-save"
        else Path(
            (moved if name == "reopen-edited" else baseline)["drawing_file"]["path"]
        )
    )
    expected_child = (
        case["files"]["child"]["sha256"]
        if name == "open-save"
        else (
            moved["child_file"]["sha256"]
            if name == "reopen-edited"
            else baseline["child_file"]["sha256"]
        )
    )
    with Swapp.Dismisser() as dialogs:
        try:
            require(
                digest(child) == expected_child
                and digest(source_draw) == case["files"]["drawing"]["sha256"],
                "owned working input changed before its native phase",
            )
            rec.call("guard reserved idle oracle", Swapp.sweep)
            controller = rec.call("start owned origin lifecycle oracle", Swapp.Sw)
            native = rec.call(
                "verify exact native executable", application_identity, controller.app
            )
            require(
                native["version_matches"]
                and native["sha256"] == ORACLE
                and controller.revision == "34.5.2",
                "wrong native build",
            )
            result["identity"] = identity_fields(native)
            author = RectangleAuthor(controller.app, rec, Swapp)
            if name == "open-save":
                model, errors, warnings = rec.call(
                    "open owned writable spatial-text child copy",
                    controller.open,
                    child,
                    read_only=False,
                )
                result["initial_child_open_status"] = [errors, warnings]
                require(
                    model is not None and errors == warnings == 0,
                    "spatial-text child failed to open cleanly",
                )
                result["child_initial"] = child_state(author, model, case, False, True)
                require(
                    author.get(model, "ForceRebuild3", False),
                    "spatial-text child initial rebuild failed",
                )
                result["child_rebuilt"] = child_state(author, model, case, False)
                errors_ref, warnings_ref = Swapp.byref_long(), Swapp.byref_long()
                ok = rec.call(
                    "save owned spatial-text child working copy",
                    Swapp.invoke,
                    model,
                    "Save3",
                    Swapp.SAVE_SILENT,
                    errors_ref,
                    warnings_ref,
                )
                save_status = [bool(ok), int(errors_ref.value), int(warnings_ref.value)]
                require(
                    save_status == [True, 0, 0],
                    "initial spatial-text child save failed or warned",
                )
                result["initial_child_save_status"] = save_status
                result["child_after_initial_save"] = child_state(
                    author, model, case, False
                )
            if name == "edit-move-save":
                model, errors, warnings = rec.call(
                    "open owned writable child copy",
                    controller.open,
                    child,
                    read_only=False,
                )
                require(
                    model is not None and errors == warnings == 0,
                    "owned child copy failed to open cleanly",
                )
                require(
                    author.get(model, "ForceRebuild3", False),
                    "initial child rebuild failed",
                )
                result["child_before_edit"] = child_state(author, model, case, False)
                parameter = author.get(model, "Parameter", case["edit"]["parameter"])
                status = author.get(
                    parameter,
                    "SetSystemValue3",
                    case["edit"]["value_m"],
                    1,
                    Swapp.nothing(),
                )
                require(
                    status == 0 and author.get(model, "ForceRebuild3", False),
                    "driving child edit failed",
                )
                result["child_after_edit"] = child_state(author, model, case, True)
                errors_ref, warnings_ref = Swapp.byref_long(), Swapp.byref_long()
                ok = rec.call(
                    "save owned edited child working copy",
                    Swapp.invoke,
                    model,
                    "Save3",
                    Swapp.SAVE_SILENT,
                    errors_ref,
                    warnings_ref,
                )
                save_status = [bool(ok), int(errors_ref.value), int(warnings_ref.value)]
                require(
                    save_status == [True, 0, 0], "edited child save failed or warned"
                )
                result["child_save_status"] = save_status
            model, errors, warnings = rec.call(
                "open exact linked drawing readonly",
                controller.open,
                input_drawing,
                doctype=3,
                read_only=True,
            )
            result.update(open_errors=errors, open_warnings=warnings)
            require(
                model is not None and errors == warnings == 0,
                "origin drawing failed to open cleanly",
            )
            author.model = model
            result["initial"] = observe(
                author,
                model,
                case,
                input_drawing,
                edited,
                name == "reopen-edited",
                True,
            )
            require(
                author.get(model, "ForceRebuild3", False),
                "origin drawing rebuild failed",
            )
            result["rebuilt"] = observe(
                author, model, case, input_drawing, edited, name == "reopen-edited"
            )
            if name == "edit-move-save":
                drawing = author.typed(model, "DrawingDoc")
                sentinel = author.typed(author.get(drawing, "GetFirstView"), "View")
                view = author.typed(author.get(sentinel, "GetNextView"), "View")
                target = [
                    a + b
                    for a, b in zip(
                        case["view"]["position_m"],
                        case["edit"]["view_move_m"],
                        strict=True,
                    )
                ]
                set_view_position(author, view, target)
                require(
                    author.get(model, "ForceRebuild3", False),
                    "edited drawing move failed",
                )
                result["edited"] = observe(
                    author, model, case, input_drawing, True, True
                )
            current = result.get("edited", result["rebuilt"])
            if baseline is not None:
                require(
                    current["child"]["profile_ids"]
                    == baseline["saved"]["child"]["profile_ids"]
                    and current["child"]["entity_roles"]
                    == baseline["saved"]["child"]["entity_roles"],
                    "native lifecycle changed actual child profile or entity identities",
                )
            if name in ("open-save", "edit-move-save"):
                target = directory / "SavedDrawing.SLDDRW"
                require(not target.exists(), "native drawing derivative already exists")
                status = rec.call(
                    "save new origin drawing derivative",
                    controller.save_as,
                    model,
                    target,
                )
                require(
                    status == (True, 0, 0) and target.is_file(),
                    "native drawing derivative failed or warned",
                )
                current = observe(author, model, case, target, edited, edited)
                result["drawing_save_status"] = list(status)
                result["drawing_file"] = {
                    "path": str(target),
                    "relative_path": target.relative_to(root).as_posix(),
                    "bytes": target.stat().st_size,
                    "sha256": digest(target),
                }
            else:
                result["drawing_file"] = {
                    "path": str(input_drawing),
                    "relative_path": input_drawing.relative_to(root).as_posix(),
                    "bytes": input_drawing.stat().st_size,
                    "sha256": digest(input_drawing),
                }
            result["saved"] = current
            result["passed"] = True
        except Exception as error:
            rec.failure(error)
            result["error"] = repr(error)
        finally:
            if controller is not None:
                try:
                    controller.close()
                except Exception as error:
                    rec.failure(error, cleanup=True)
                result["controller_diagnostics"] = controller.diagnostics
    result.update(dialogs=dialogs.log, progress_windows=dialogs.progress)
    result["passed"] = bool(
        result["passed"]
        and rec.data["first_failure"] is None
        and not rec.data["cleanup_errors"]
        and not dialogs.log
        and not result.get("controller_diagnostics")
    )
    if result["passed"]:
        snapshot = directory / "ChildSnapshot.SLDPRT"
        copy_new(child, snapshot)
        result["child_file"] = {
            "path": str(snapshot),
            "relative_path": snapshot.relative_to(root).as_posix(),
            "bytes": snapshot.stat().st_size,
            "sha256": digest(snapshot),
            "encoded_native_path": str(child),
        }
        if (
            name not in ("open-save", "edit-move-save")
            and digest(child) != expected_child
        ):
            rec.failure(
                ValueError("readonly phase modified the native child working copy")
            )
            result["passed"] = False
        if digest(source_draw) != case["files"]["drawing"]["sha256"]:
            rec.failure(ValueError("native drawing working original was modified"))
            result["passed"] = False
    rec.data.update(
        native_result=result,
        passed=result["passed"],
        numeric_checks=len(rec.data["checks"]),
        finished_at=time.time(),
    )
    rec.flush()
    result.update(
        record_sha256=digest(rec.path), numeric_checks=len(rec.data["checks"])
    )
    return result


def run(packet, expected):
    require(
        os.name == "nt",
        "native origin lifecycle requires the root owned Windows oracle",
    )
    import Swapp
    from InspectFresh import inspect, healthy

    job = verify(packet, expected)
    root = packet.parent
    targets = preflight(job)
    output = root / "Inspection"
    output.mkdir(exist_ok=False)
    result = {
        "schema": SCHEMA,
        "packet_sha256": expected,
        "passed": False,
        "phases": {},
        "preflight": targets,
        "hidden_inputs_read": 0,
        "native_acceptance": False,
        "heldout_acceptance": False,
        "source_original_admission": False,
        "typed_origin_join_pending": True,
        "typed_text_depth_persistence_pending": True,
        "annotation_api_position_is_stored_text_point": False,
    }

    def checkpoint():
        write_json(output / "Result.json", result)

    def control(name):
        entry = {"passed": False, "result": {}}
        result["phases"][name] = entry
        row = inspect(
            checked(root, job["control"]), result=entry["result"], checkpoint=checkpoint
        )
        native = row.get("oracle_identity")
        entry["passed"] = bool(healthy(row) and native and native["sha256"] == ORACLE)
        if native:
            entry["identity"] = identity_fields(native)
        checkpoint()
        return entry["passed"]

    before, after = False, False
    try:
        before = control("ControlBefore")
        if before:
            for case in job["cases"]:
                for kind in ("child", "drawing"):
                    copy_new(
                        checked(root, case["files"][kind]), Path(case["paths"][kind])
                    )
            for case in job["cases"]:
                baseline = moved = None
                for name in PHASES:
                    row = phase(root, job, case, name, baseline, moved)
                    result["phases"][case["name"] + "/" + name] = row
                    checkpoint()
                    if not row["passed"]:
                        raise ValueError("native origin phase failed")
                    if name == "open-save":
                        baseline = row
                    if name == "edit-move-save":
                        moved = row
    except Exception as error:
        result["error"] = repr(error)
    finally:
        after = control("ControlAfter")
        verify(packet, expected)
        identities = [
            row["identity"] for row in result["phases"].values() if "identity" in row
        ]
        starts = {
            (row["process_id"], row["process_creation_filetime"]) for row in identities
        }
        matching_controls = False
        if before and after:
            first = result["phases"]["ControlBefore"]["result"]
            last = result["phases"]["ControlAfter"]["result"]
            matching_controls = (
                first["bodies"] == last["bodies"] == 1
                and all(
                    isclose(
                        first["mass"][key],
                        last["mass"][key],
                        rel_tol=5e-7,
                        abs_tol=1e-15,
                    )
                    for key in ("volume", "area")
                )
                and all(
                    isclose(a, b, rel_tol=5e-7, abs_tol=1e-10)
                    for a, b in zip(
                        first["mass"]["com"], last["mass"]["com"], strict=True
                    )
                )
            )
        result.update(
            controls_healthy=before and after and matching_controls,
            distinct_native_processes=len(starts),
            packet_inputs_unchanged=True,
            native_lifecycle_passed=len(starts)
            == len(result["phases"])
            == 2 + len(job["cases"]) * len(PHASES)
            and all(row["passed"] for row in result["phases"].values()),
        )
        result["passed"] = bool(
            result["controls_healthy"] and result["native_lifecycle_passed"]
        )
        checkpoint()
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Measure matched ISO and ANSI origin-linked pairs through ordinary COM lifecycle and separate typed host joins"
    )
    parser.add_argument("command", choices=("verify", "preflight", "run"))
    parser.add_argument("packet", type=Path)
    parser.add_argument("--packet-sha256", required=True)
    args = parser.parse_args()
    packet = args.packet.resolve(strict=True)
    job = verify(packet, args.packet_sha256)
    if args.command == "verify":
        print(
            json.dumps(
                {"passed": True, "processes_started": 0, "hidden_inputs_read": 0}
            )
        )
        return 0
    if args.command == "preflight":
        print(
            json.dumps(
                {"passed": True, "targets": preflight(job), "processes_started": 0}
            )
        )
        return 0
    result = run(packet, args.packet_sha256)
    print(
        json.dumps(
            {
                key: result[key]
                for key in (
                    "passed",
                    "controls_healthy",
                    "distinct_native_processes",
                    "native_acceptance",
                    "typed_origin_join_pending",
                )
            }
        )
    )
    return 0 if result["passed"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
