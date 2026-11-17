from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path

import AuthorCurves as curves
from AuthorDrawingSources import compare_states, snapshot
from DrawingCacheCases import CASES, SCHEMA, TOOL_NAMES, input_file


_EDITED_RATIO = (3.0, 2.0)


def drawing_tree(author):
    total = 0

    def walk(feature, parent, depth):
        nonlocal total
        while feature is not None:
            total += 1
            curves.require(total <= 1000 and depth < 20, "drawing tree exceeds its traversal bound")
            name = str(author.get(feature, "Name"))
            kind = str(author.get(feature, "GetTypeName2"))
            yield (name, kind, parent)
            yield from walk(author.get(feature, "GetFirstSubFeature"), name, depth + 1)
            feature = author.get(feature, "GetNextFeature" if parent is None else "GetNextSubFeature")

    return [list(line) for line in walk(author.get(author.model, "FirstFeature"), None, 0)]


def check_drawing(author, drawing, expected, tree):
    properties = snapshot(author, author.model, drawing, None, None, expected["sheet_properties"][0])
    compare_states(author, properties, expected)
    features = drawing_tree(author)
    curves.require(any(row[0] == properties["sheet"] for row in features), "the active drawing sheet has no live tree node")
    if tree is not None:
        curves.require(features == tree, "drawing tree differs from the unmodified control")
    return properties, features


def read_job(path, packet_digest):
    curves.require(curves.digest(path) == packet_digest, "drawing cache trial manifest differs from its pinned hash")
    request = json.loads(path.read_bytes())
    curves.require(request["schema"] == SCHEMA and request["writer_output_count"] == 0, "wrong cached drawing research job")
    row_keys = tuple((row["name"], row["omitted"]) for row in request["cases"])
    curves.require(row_keys == CASES and not request["native_acceptance"], "unexpected drawing cache omission case order")
    pinned = request["tool_hashes"]
    curves.require(set(pinned) == set(TOOL_NAMES), "missing cache test tool hashes")
    for name in TOOL_NAMES:
        curves.require(curves.digest(Path(__file__).with_name(name)) == pinned[name], f"drawing trial tool changed: {name}")
    for row in request["cases"]:
        case = input_file(path.parent, row["name"])
        curves.require(case.stat().st_size == row["bytes"] and curves.digest(case) == row["sha256"], f"drawing diagnostic copy changed: {row['name']}")
    curves.require(request["cases"][0]["sha256"] == request["control_sha256"], "pristine drawing differs from the source control")
    curves.require(request["expected"]["view"] is None, "drawing cache job requires an unlinked empty sheet")
    return request


def phase(sw, identify, *, directory, native, expected_hash, expected, tree, oracle_sha, edit):
    directory.mkdir(parents=True, exist_ok=False)
    rec = curves.Recorder(directory / "Record.json", {"drawing": native.name, "edit": edit})
    result = {"passed": False}
    controller = author = None
    with sw.Dismisser() as dialogs:
        try:
            curves.require(curves.digest(native) == expected_hash, "drawing input changed before native open")
            rec.call("drawing cache idle guard", sw.sweep)
            controller = rec.call("start fresh drawing oracle", sw.Sw, visible=True)
            identity = rec.call("verify drawing oracle identity", identify, controller.app)
            result["oracle_identity"] = identity
            curves.require(identity["version_matches"] and identity["sha256"] == oracle_sha and controller.revision == "34.5.2", "drawing oracle build differs")
            author = curves.CurveAuthor(controller.app, rec, sw)
            author.model, errors, warnings = rec.call("open drawing diagnostic", controller.open, native, doctype=3, read_only=True)
            result.update(open_errors=errors, open_warnings=warnings)
            curves.require(author.model is not None and errors == warnings == 0, "drawing cache trial could not open cleanly")
            drawing = author.typed(author.model, "DrawingDoc")
            result["initial"], result["tree"] = check_drawing(author, drawing, expected, tree)
            curves.require(bool(author.get(author.model, "ForceRebuild3", False)), "drawing rebuild failed")
            result["rebuilt"], _ = check_drawing(author, drawing, expected, result["tree"])
            if edit:
                sheet = author.typed(author.get(drawing, "GetCurrentSheet"), "Sheet")
                curves.require(bool(author.get(sheet, "SetScale", *_EDITED_RATIO, False, False)), "drawing scale edit failed")
                curves.require(bool(author.get(author.model, "EditRebuild3")), "drawing scale edit rebuild failed")
                wanted = list(expected["sheet_properties"])
                wanted[2:4] = _EDITED_RATIO
                result["edited"], _ = check_drawing(author, drawing, {**expected, "sheet_properties": wanted}, result["tree"])
                derivative = directory / "EditedDrawing.SLDDRW"
                result["save_status"] = rec.call("save edited drawing diagnostic", controller.save_as, author.model, derivative)
                curves.require(result["save_status"] == (True, 0, 0), "drawing scale save failed or warned")
                result["derivative_sha256"] = curves.digest(derivative)
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
    result["source_immutable"] = native.is_file() and curves.digest(native) == expected_hash
    result.update(dialogs=dialogs.log, progress_windows=dialogs.progress)
    result["passed"] = bool(
        result["passed"] and result["source_immutable"] and not dialogs.log and not result.get("controller_diagnostics")
        and rec.data["first_failure"] is None and not rec.data["cleanup_errors"]
    )
    rec.data.update(result=result, passed=result["passed"], finished_at=time.time())
    rec.flush()
    return {**result, "record_sha256": curves.digest(directory / "Record.json")}


def measure(sw, identify, *, name, row, root, output, request, tree=None):
    directory = output / name
    result = {"name": name, "omitted": row["omitted"], "source_sha256": row["sha256"]}
    first = phase(
        sw, identify, directory=directory / "open_edit_save", native=input_file(root, row["name"]),
        expected_hash=row["sha256"], expected=request["expected"], tree=tree, oracle_sha=request["oracle_sha256"], edit=True,
    )
    result["open_edit_save"] = first
    second = None
    if first["passed"]:
        second = phase(
            sw, identify, directory=directory / "fresh_reopen", native=directory / "open_edit_save" / "EditedDrawing.SLDDRW",
            expected_hash=first["derivative_sha256"], expected=first["edited"], tree=first["tree"], oracle_sha=request["oracle_sha256"], edit=False,
        )
    result["fresh_reopen"] = second
    result["passed"] = bool(first["passed"] and second is not None and second["passed"])
    return result


def run(path, packet_digest):
    request = read_job(path, packet_digest)
    import Swapp
    from OracleIdentity import application_identity

    output = path.parent / "Results"
    output.mkdir(exist_ok=False)
    rows = request["cases"]
    reports = []
    report = {
        "schema": "kit.sw2026.drawing-cache-result.v1", "packet_sha256": packet_digest,
        "control_sha256": request["control_sha256"], "cases": reports, "writer_output_count": 0, "native_acceptance": False,
    }
    controls = (None, None)
    generic = dict(root=path.parent, output=output, request=request)
    try:
        before = measure(Swapp, application_identity, name="ControlBefore", row=rows[0], **generic)
        controls = (before, None)
        reports.append(before)
        curves.write_json(output / "Progress.json", report)
        if before["passed"]:
            tree = before["open_edit_save"]["tree"]
            repacked = measure(Swapp, application_identity, name="Repacked", row=rows[1], tree=tree, **generic)
            reports.append(repacked)
            curves.write_json(output / "Progress.json", report)
            if repacked["passed"]:
                for row in rows[2:]:
                    reports.append(measure(Swapp, application_identity, name=row["name"], row=row, tree=tree, **generic))
                    curves.write_json(output / "Progress.json", report)
    except Exception as error:
        report["exception"] = repr(error)
    finally:
        try:
            tree = controls[0]["open_edit_save"].get("tree") if controls[0] else None
            after = measure(Swapp, application_identity, name="ControlAfter", row=rows[0], tree=tree, **generic)
            controls = (controls[0], after)
            reports.append(after)
        except Exception as error:
            report["control_after_exception"] = repr(error)
        try:
            read_job(path, packet_digest)
            inputs_immutable = True
        except Exception as error:
            inputs_immutable = False
            report["immutability_error"] = repr(error)
        control_results = [bool(row and row["passed"]) for row in controls]
        identities = [
            phase_data["oracle_identity"]["process_creation_filetime"]
            for row in reports for key in ("open_edit_save", "fresh_reopen")
            if (phase_data := row.get(key)) and "oracle_identity" in phase_data
        ]
        repacked_record = next((row for row in reports if row["name"] == "Repacked"), None)
        report.update(
            control_results=control_results, distinct_processes=len(set(identities)),
            inputs_immutable=inputs_immutable, repacked_healthy=bool(repacked_record and repacked_record["passed"]),
            interpretable=inputs_immutable and control_results == [True, True] and bool(repacked_record and repacked_record["passed"]) and len(identities) == len(set(identities)) and "exception" not in report,
        )
        curves.write_json(output / "DrawingCacheResults.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description="Measure a privately prepared blank drawing cache omission batch on the pinned Windows oracle")
    parser.add_argument("packet", type=Path)
    parser.add_argument("--packet-sha256", required=True)
    args = parser.parse_args()
    curves.require(re.fullmatch(r"[0-9a-f]{64}", args.packet_sha256) is not None, "a pinned packet digest is required")
    result = run(args.packet.resolve(), args.packet_sha256)
    print(json.dumps({key: result[key] for key in ("interpretable", "control_results", "repacked_healthy", "distinct_processes")}))
    return 0 if result["interpretable"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
