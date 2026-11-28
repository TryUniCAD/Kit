from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path
from shutil import copyfileobj

import AuthorCurves as curves
from InspectBlankDrawingPair import GENERATED_NAME, input_path, observe, read_packet
from InspectDrawingCache import check_drawing, phase


MODES = ("RebuildSaveAs", "EditSaveInPlace")
EDITED_RATIO = (3.0, 2.0)


def save_rebuilt(sw, controller, author, drawing, mode, expected, tree, source, target):
    if mode == "RebuildSaveAs":
        status = author.rec.call("save rebuilt drawing before editing", controller.save_as, author.model, target)
        return status, expected

    active = author.typed(author.get(drawing, "GetCurrentSheet"), "Sheet")
    curves.require(bool(author.get(active, "SetScale", *EDITED_RATIO, False, False)), "drawing scale edit failed")
    curves.require(bool(author.get(author.model, "EditRebuild3")), "drawing scale rebuild failed")
    props = list(expected["sheet_properties"])
    props[2:4] = EDITED_RATIO
    edited, _ = check_drawing(author, drawing, {**expected, "sheet_properties": props}, tree)
    reported = Path(str(author.get(author.model, "GetPathName")))
    curves.require(reported.is_absolute() and reported.samefile(source), "in-place save must target the owned drawing copy")
    author.get(author.model, "SetSaveFlag")
    curves.require(bool(author.get(author.model, "GetSaveFlag")), "the owned drawing did not become dirty")
    errors, warnings = sw.byref_long(), sw.byref_long()
    ok = author.rec.call("save edited drawing in place", sw.invoke, author.model, "Save3", sw.SAVE_SILENT, errors, warnings)
    return (bool(ok), int(errors.value), int(warnings.value)), edited


def save_phase(sw, identify, *, row, mode, working, source, oracle, expected_tree):
    directory = working / "open_and_save"
    directory.mkdir(exist_ok=False)
    rec = curves.Recorder(directory / "Record.json", {"drawing": source.name, "mode": mode})
    result = {"passed": False}
    staged_sha = row["sha256"]
    controller = author = None
    target = directory / "SavedDrawing.SLDDRW" if mode == "RebuildSaveAs" else source
    with sw.Dismisser() as dialogs:
        try:
            curves.require(curves.digest(source) == staged_sha, "staged drawing differs from its pinned input")
            rec.call("drawing save mode idle guard", sw.sweep)
            controller = rec.call("start fresh drawing oracle", sw.Sw, visible=True)
            identity = rec.call("verify drawing oracle identity", identify, controller.app)
            result["oracle_identity"] = identity
            curves.require(identity["version_matches"] and identity["sha256"] == oracle and controller.revision == "34.5.2", "wrong drawing oracle build")
            author = curves.CurveAuthor(controller.app, rec, sw)
            author.model, errors, warnings = rec.call("open owned drawing copy", controller.open, source, doctype=3, read_only=mode == "RebuildSaveAs")
            result.update(open_errors=errors, open_warnings=warnings)
            curves.require(author.model is not None and errors == warnings == 0, "drawing failed to open cleanly")
            drawing = author.typed(author.model, "DrawingDoc")
            result["initial"], tree = check_drawing(author, drawing, row["expected"], expected_tree)
            result["tree"] = tree
            curves.require(bool(author.get(author.model, "ForceRebuild3", False)), "drawing rebuild failed")
            result["rebuilt"], _ = check_drawing(author, drawing, row["expected"], tree)
            status, wanted = save_rebuilt(sw, controller, author, drawing, mode, result["rebuilt"], tree, source, target)
            result.update(save_status=status, expected_reopen=wanted)
            curves.require(status == (True, 0, 0), "the drawing save failed or warned")
            result["passed"] = True
        except Exception as error:
            rec.failure(error)
        finally:
            if author is not None and author.model is not None:
                try:
                    rec.call("close owned drawing", controller.close_doc, author.model)
                    author.model = None
                except Exception as error:
                    rec.failure(error, cleanup=True)
            if controller is not None:
                try:
                    controller.close()
                except Exception as error:
                    rec.failure(error, cleanup=True)
                result["controller_diagnostics"] = controller.diagnostics
    result["staged_copy_sha256_after"] = curves.digest(source) if source.is_file() else None
    result["save_target_bytes"] = target.stat().st_size if target.is_file() else None
    result["save_target_sha256"] = curves.digest(target) if target.is_file() else None
    result["save_target_relative_path"] = target.relative_to(working).as_posix()
    if mode == "RebuildSaveAs" and result["staged_copy_sha256_after"] != staged_sha:
        result["passed"] = False
    result.update(dialogs=dialogs.log, progress_windows=dialogs.progress)
    result["passed"] = bool(result["passed"] and result["save_target_bytes"] and not dialogs.log
                            and not result.get("controller_diagnostics") and not rec.data["cleanup_errors"])
    rec.data.update(result=result, passed=result["passed"], finished_at=time.time())
    rec.flush()
    return {**result, "record_sha256": curves.digest(directory / "Record.json")}


def run(path, expected_sha, runner_sha):
    curves.require(curves.digest(Path(__file__)) == runner_sha, "drawing save-mode observer bytes changed")
    request = read_packet(path, expected_sha)
    import Swapp
    from OracleIdentity import application_identity

    root = path.parent
    output = root / "SaveModeResults"
    output.mkdir(exist_ok=False)
    working = output / "MatchedDrawing"
    mode_cases, controls = [], []
    report = {"schema": "kit.sw2026.blank-drawing-save-modes.v1", "packet_sha256": expected_sha,
              "runner_sha256": runner_sha, "modes": mode_cases, "controls": controls,
              "native_acceptance": False, "heldout_inputs_tested": 0}
    pristine, reduced, _, generated = request["cases"]
    oracle = request["oracle_sha256"]

    def control(name, tree):
        observed = observe(Swapp, application_identity, row=pristine, source=input_path(root, pristine),
                           directory=output / name, oracle=oracle, tree=tree)
        controls.append({"name": name, **observed})
        curves.write_json(output / "Progress.json", report)
        return observed

    def measure(row, mode, tree, name):
        working.mkdir(exist_ok=False)
        source = working / GENERATED_NAME
        with input_path(root, row).open("rb") as reader, source.open("xb") as writer:
            copyfileobj(reader, writer)
        first = save_phase(Swapp, application_identity, row=row, mode=mode, working=working,
                           source=source, oracle=oracle, expected_tree=tree)
        second = None
        if first["passed"]:
            second = phase(Swapp, application_identity, directory=working / "fresh_reopen",
                           native=working / first["save_target_relative_path"], expected_hash=first["save_target_sha256"],
                           expected=first["expected_reopen"], tree=first["tree"], oracle_sha=oracle, edit=False)
        result = {"name": name, "source_kind": row["kind"], "mode": mode, "input_sha256": row["sha256"],
                  "open_and_save": first, "fresh_reopen": second, "passed": bool(first["passed"] and second and second["passed"])}
        working.rename(output / name)
        mode_cases.append(result)
        curves.write_json(output / "Progress.json", report)
        return result

    before = after = None
    control_tree = None
    try:
        before = control("ControlBefore", None)
        if before["passed"]:
            control_tree = before["open_edit_save"]["tree"]
            for mode in MODES:
                evidence = measure(reduced, mode, control_tree, "ReducedNative" + mode)
                if evidence["passed"]:
                    measure(generated, mode, generated["expected_tree"], "Generated" + mode)
    except Exception as error:
        report["exception"] = repr(error)
    finally:
        try:
            after = control("ControlAfter", control_tree)
        except Exception as error:
            report["control_after_exception"] = repr(error)
        try:
            read_packet(path, expected_sha)
            report["inputs_immutable"] = True
        except Exception as error:
            report.update(inputs_immutable=False, immutability_error=repr(error))
        control_phases = [row[key] for row in controls for key in ("open_edit_save", "fresh_reopen") if row[key] is not None]
        mode_phases = [row[key] for row in mode_cases for key in ("open_and_save", "fresh_reopen") if row[key] is not None]
        phases = control_phases + mode_phases
        identities = [row["oracle_identity"]["process_creation_filetime"] for row in phases if "oracle_identity" in row]
        modes_valid = len(mode_cases) == 4 and all(row["passed"] for row in mode_cases if row["source_kind"] == "native-stream-reduction")
        healthy = bool(before and before["passed"] and after and after["passed"] and modes_valid)
        report.update(controls_healthy=healthy, distinct_processes=len(set(identities)),
                      interpretable=bool(healthy and report["inputs_immutable"] and len(identities) == len(set(identities)) == len(phases)
                                         and "exception" not in report))
        curves.write_json(output / "DrawingBlankSaveModeResults.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description="Compare native drawing SaveAs before edit and Save3 on private writable copies")
    parser.add_argument("packet", type=Path)
    parser.add_argument("--packet-sha256", required=True)
    parser.add_argument("--runner-sha256", required=True)
    args = parser.parse_args()
    curves.require(all(re.fullmatch(r"[0-9a-f]{64}", value) for value in (args.packet_sha256, args.runner_sha256)), "pinned drawing input and tool hashes required")
    result = run(args.packet.resolve(), args.packet_sha256, args.runner_sha256)
    return 0 if result["interpretable"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
