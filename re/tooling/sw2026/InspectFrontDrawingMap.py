from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from shutil import copyfile

import AuthorCurves as curves
from AuthorDrawingSources import compare_states, edit_position, snapshot
from DrawingCacheCases import TOOL_NAMES as CACHE_TOOLS
from InspectDrawingCache import drawing_tree


SCHEMA = "kit.sw2026.front-detailing-edge-map-diagnostic.v1"
SOURCES = ("D01FrontView", "D02MovedFrontView")
VARIANTS = ("Pristine", "Repacked", "OmitDetailingEdgeMap")
PART_FILE = "GeneratedChildFile.SLDPRT"
TOOL_NAMES = (*CACHE_TOOLS, "InspectFrontDrawingMap.py")


def source_path(root, case, variant):
    return root / case["name"] / variant["name"] / (case["name"] + ".SLDDRW")


def read_job(packet, expected_hash, tools_hash):
    curves.require(curves.digest(packet) == expected_hash, "front drawing diagnostic packet hash differs")
    path = Path(__file__).with_name("GuestTools.json")
    curves.require(curves.digest(path) == tools_hash, "front drawing tool manifest hash differs")
    tools = json.loads(path.read_bytes())
    curves.require(set(tools) == set(TOOL_NAMES), "front drawing diagnostic tool set differs")
    for name, digest in tools.items():
        curves.require(curves.digest(path.with_name(name)) == digest, f"front drawing diagnostic tool changed: {name}")
    request = json.loads(packet.read_bytes())
    curves.require(request["schema"] == SCHEMA and request["writer_output_count"] == 0 and request["native_acceptance"] is False,
                   "front drawing packet must describe native diagnostics")
    curves.require(tuple(case["name"] for case in request["cases"]) == SOURCES, "front drawing diagnostic requires both disclosed sources")
    for case in request["cases"]:
        curves.require(tuple(row["name"] for row in case["cases"]) == VARIANTS, "front drawing case variants differ")
        curves.require(case["changed_streams"] == ["Contents/Definition"], "front drawing omission must only change Definition")
        view = case["expected"]["view"]
        curves.require(view and view["orientation"] == "*Front" and view["scale"] == 1 and view["configuration"],
                       "front drawing diagnostic requires one ordinary front view")
        for variant in case["cases"]:
            native = source_path(packet.parent, case, variant)
            curves.require(native.stat().st_size == variant["bytes"] and curves.digest(native) == variant["sha256"],
                           "front drawing input bytes differ")
            curves.require(curves.digest(native.with_name(PART_FILE)) == case["part_sha256"], "front drawing child bytes differ")
    return request


def locked_child(author, drawing, original_child, staged_child, child_hash):
    sheet = author.typed(author.get(drawing, "GetFirstView"), "View")
    view = author.typed(author.get(sheet, "GetNextView"), "View")
    part = author.get(view, "ReferencedDocument")
    curves.require(part is not None, "front drawing view did not resolve its model")
    actual = Path(author.get(part, "GetPathName")).resolve()
    allowed = (staged_child.resolve(), Path(original_child).resolve())
    matches = actual in allowed or any(candidate.is_file() and actual.samefile(candidate) for candidate in allowed)
    curves.require(matches and curves.digest(actual) == child_hash, "resolved child differs from the staged or original locked source")
    return actual


def project(author, drawing, expected, staged_child, original_child, child_hash):
    view = expected["view"]
    child = locked_child(author, drawing, original_child, staged_child, child_hash)
    request = {key: view[key] for key in ("orientation", "position_m", "scale")}
    paper = expected["sheet_properties"][0]
    state = snapshot(author, author.model, drawing, request, child, paper)
    compare_states(author, state, {**expected, "view": {**view, "resolved_reference_path": str(child)}})
    return state, request, child, paper


def translated(expected, edited):
    previous, actual = expected["view"], edited["view"]
    model_to_view = list(previous["model_to_view"])
    for axis in (0, 1):
        model_to_view[9 + axis] += actual["position_m"][axis] - previous["position_m"][axis]
    return {**expected, "view": {**previous, "position_m": actual["position_m"], "outline_m": actual["outline_m"],
                                 "model_to_view": model_to_view}}


def phase(sw, identify, *, directory, native, sha256, expected, child, original_child, child_hash, oracle, tree, edit):
    directory.mkdir(parents=True, exist_ok=False)
    rec = curves.Recorder(directory / "Record.json", {"drawing": native.name, "edit_position": edit})
    result = {"passed": False}
    controller = author = actual_child = None
    with sw.Dismisser() as dialogs:
        try:
            curves.require(curves.digest(native) == sha256 and curves.digest(child) == child_hash, "owned front drawing input changed")
            rec.call("front drawing idle guard", sw.sweep)
            controller = rec.call("start fresh front drawing oracle", sw.Sw, visible=True)
            identity = rec.call("verify front drawing oracle identity", identify, controller.app)
            result["oracle_identity"] = identity
            curves.require(identity["version_matches"] and identity["sha256"] == oracle and controller.revision == "34.5.2", "wrong front drawing oracle build")
            author = curves.CurveAuthor(controller.app, rec, sw)
            author.model, errors, warnings = rec.call("open matched front drawing", controller.open, native, doctype=3, read_only=True)
            result.update(open_errors=errors, open_warnings=warnings)
            curves.require(author.model is not None and errors == warnings == 0, "front drawing failed to open cleanly")
            drawing = author.typed(author.model, "DrawingDoc")
            result["initial"], _, actual_child, _ = project(author, drawing, expected, child, original_child, child_hash)
            result["tree"] = drawing_tree(author)
            curves.require(tree is None or tree == result["tree"], "front drawing tree differs from the pristine control")
            curves.require(bool(author.get(author.model, "ForceRebuild3", False)), "front drawing rebuild failed")
            rebuilt, request, actual_child, paper = project(author, drawing, expected, child, original_child, child_hash)
            result["rebuilt"] = rebuilt
            curves.require(drawing_tree(author) == result["tree"], "front drawing rebuild changed its feature tree")
            if edit:
                edited = edit_position(author, author.model, drawing, request, actual_child, paper, rebuilt)
                compare_states(author, edited, translated(rebuilt, edited))
                curves.require(drawing_tree(author) == result["tree"], "view movement changed its drawing feature tree")
                result["edited"] = edited
                target = directory / "EditedDrawing.SLDDRW"
                result["save_status"] = rec.call("save front drawing position edit", controller.save_as, author.model, target)
                curves.require(result["save_status"] == (True, 0, 0), "front drawing save failed or warned")
                curves.require(target.is_file() and target.stat().st_size > 0, "front drawing save produced no bytes")
                result.update(derivative_sha256=curves.digest(target), derivative_bytes=target.stat().st_size)
            result["passed"] = True
        except Exception as error:
            rec.failure(error)
        finally:
            if author is not None and author.model is not None:
                try:
                    rec.call("close owned front drawing", controller.close_doc, author.model)
                    author.model = None
                except Exception as error:
                    rec.failure(error, cleanup=True)
            if controller is not None:
                try:
                    controller.close()
                except Exception as error:
                    rec.failure(error, cleanup=True)
                result["controller_diagnostics"] = controller.diagnostics
    immutable = native.is_file() and curves.digest(native) == sha256 and child.is_file() and curves.digest(child) == child_hash
    immutable = bool(immutable and (actual_child is None or actual_child.is_file() and curves.digest(actual_child) == child_hash))
    result.update(input_immutable=immutable, dialogs=dialogs.log, progress_windows=dialogs.progress)
    result["passed"] = bool(result["passed"] and immutable and not dialogs.log and not result.get("controller_diagnostics")
                            and rec.data["first_failure"] is None and not rec.data["cleanup_errors"])
    rec.data.update(result=result, passed=result["passed"], finished_at=time.time())
    rec.flush()
    return {**result, "record_sha256": curves.digest(directory / "Record.json")}


def observe(sw, identify, *, source, working, directory, row, case, oracle, tree):
    native = working / source.name
    child = working / PART_FILE
    copyfile(source, native)
    copyfile(source.with_name(PART_FILE), child)
    common = {"child": child, "original_child": case["expected"]["view"]["resolved_reference_path"],
              "child_hash": case["part_sha256"], "oracle": oracle}
    first = phase(sw, identify, directory=directory / "OpenEditSave", native=native, sha256=row["sha256"],
                  expected=case["expected"], tree=tree, edit=True, **common)
    reopened = None
    if first["passed"]:
        reopened = phase(sw, identify, directory=directory / "FreshReopen", native=directory / "OpenEditSave/EditedDrawing.SLDDRW",
                         sha256=first["derivative_sha256"], expected=first["edited"], tree=first["tree"], edit=False, **common)
    return {"source_sha256": row["sha256"], "open_edit_save": first, "fresh_reopen": reopened,
            "passed": bool(first["passed"] and reopened is not None and reopened["passed"])}


def run(packet, expected_hash, tools_hash):
    request = read_job(packet, expected_hash, tools_hash)
    import Swapp
    from OracleIdentity import application_identity

    output = packet.parent / "FrontMapResults"
    output.mkdir(exist_ok=False)
    report = {"schema": "kit.sw2026.front-detailing-edge-map-result.v1", "packet_sha256": expected_hash,
              "tool_manifest_sha256": tools_hash, "cases": [], "writer_output_count": 0, "native_acceptance": False,
              "heldout_inputs_tested": 0}
    for case in request["cases"]:
        lanes = {}
        record = {"name": case["name"], "lanes": lanes}
        report["cases"].append(record)
        working = output / case["name"] / "MatchedInput"
        working.mkdir(parents=True, exist_ok=False)
        tree = None

        def measure(label, row):
            lanes[label] = observe(Swapp, application_identity, source=source_path(packet.parent, case, row), working=working,
                                   directory=working.parent / label, row=row, case=case, oracle=request["oracle_sha256"], tree=tree)
            curves.write_json(output / "Progress.json", report)
            return lanes[label]

        pristine, repacked, omitted = case["cases"]
        try:
            before = measure("ControlBefore", pristine)
            if before["passed"]:
                tree = before["open_edit_save"]["tree"]
                if measure("Repacked", repacked)["passed"]:
                    measure("OmitDetailingEdgeMap", omitted)
        except Exception as error:
            record["exception"] = repr(error)
        finally:
            try:
                measure("ControlAfter", pristine)
            except Exception as error:
                record["control_after_exception"] = repr(error)
    read_job(packet, expected_hash, tools_hash)
    phases = [phase for case in report["cases"] for lane in case["lanes"].values()
              for phase in (lane["open_edit_save"], lane["fresh_reopen"]) if phase is not None]
    times = [phase["oracle_identity"]["process_creation_filetime"] for phase in phases if "oracle_identity" in phase]
    report["inputs_immutable"] = True
    report["distinct_processes"] = len(set(times))
    report["interpretable"] = len(set(times)) == len(phases) and all(
        "exception" not in case and "control_after_exception" not in case
        and all(case["lanes"].get(key, {}).get("passed") for key in ("ControlBefore", "Repacked", "ControlAfter"))
        and "OmitDetailingEdgeMap" in case["lanes"] for case in report["cases"]
    )
    report["omission_passed"] = bool(report["interpretable"] and all(case["lanes"]["OmitDetailingEdgeMap"]["passed"] for case in report["cases"]))
    curves.write_json(output / "FrontMapResults.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description="Measure omission of the detailing edge map in the two disclosed ordinary front views")
    parser.add_argument("packet", type=Path)
    parser.add_argument("--packet-sha256", required=True)
    parser.add_argument("--tools-sha256", required=True)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    if args.verify_only:
        read_job(args.packet, args.packet_sha256, args.tools_sha256)
        return 0
    report = run(args.packet.resolve(), args.packet_sha256, args.tools_sha256)
    print(json.dumps({key: report[key] for key in ("interpretable", "omission_passed", "distinct_processes")}))
    return 0 if report["interpretable"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
