from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import AuthorCurves as curves
from DrawingCacheCases import NATIVE_NAME, TOOL_NAMES as CACHE_TOOL_NAMES
from InspectDrawingCache import phase


TRIAL_SCHEMA = "kit.sw2026.blank-drawing-native-trial.v1"
CASE_NAMES = ("Pristine", "Repacked", "ReducedNative", "GeneratedBlank")
INPUT_KINDS = ("locked-control", "repacked-control", "native-stream-reduction", "generated")
TOOL_NAMES = (*CACHE_TOOL_NAMES, "InspectBlankDrawing.py")


def input_path(root, row):
    return root / "Inputs" / row["name"] / row["filename"]


def read_packet(path, expected_hash):
    curves.require(curves.digest(path) == expected_hash, "blank-drawing trial packet changed")
    request = json.loads(path.read_bytes())
    rows = request["cases"]
    curves.require(request["schema"] == TRIAL_SCHEMA and request["native_acceptance"] is False, "unexpected blank drawing trial version")
    curves.require(tuple(row["name"] for row in rows) == CASE_NAMES and tuple(row["kind"] for row in rows) == INPUT_KINDS,
                   "blank drawing candidate kinds differ from the frozen trial")
    hashes = request["tool_hashes"]
    curves.require(set(hashes) == set(TOOL_NAMES), "blank drawing trial has missing tool identities")
    for name in TOOL_NAMES:
        curves.require(curves.digest(Path(__file__).with_name(name)) == hashes[name], f"blank drawing trial tool changed: {name}")
    curves.require(rows[0]["sha256"] == request["control_sha256"], "locked pristine source hash differs")
    for row in rows:
        filename = row["filename"]
        curves.require(re.fullmatch(r"[A-Za-z0-9_-]+\.SLDDRW", filename) is not None, "unsupported trial file name")
        curves.require(row["kind"] == "generated" or filename == NATIVE_NAME, "native diagnostic must retain the locked control name")
        native = input_path(path.parent, row)
        curves.require(native.stat().st_size == row["bytes"] and curves.digest(native) == row["sha256"], f"blank drawing input changed: {row['name']}")
        curves.require(row["expected"]["view"] is None, "this trial requires an unlinked empty sheet")
    curves.require(rows[2]["streams"] == rows[3]["streams"], "the reduced native and generated packages must use the same stream roles")
    return request


def measure(sw, identify, *, root, output, name, row, oracle, tree):
    directory = output / name
    first = phase(sw, identify, directory=directory / "open_edit_save", native=input_path(root, row),
                  expected_hash=row["sha256"], expected=row["expected"], tree=tree, oracle_sha=oracle, edit=True)
    second = None
    if first["passed"]:
        second = phase(sw, identify, directory=directory / "fresh_reopen", native=directory / "open_edit_save" / "EditedDrawing.SLDDRW",
                       expected_hash=first["derivative_sha256"], expected=first["edited"], tree=first["tree"], oracle_sha=oracle, edit=False)
    return {"name": name, "kind": row["kind"], "input_sha256": row["sha256"], "open_edit_save": first, "fresh_reopen": second,
            "passed": bool(first["passed"] and second is not None and second["passed"])}


def run(path, expected_hash):
    request = read_packet(path, expected_hash)
    import Swapp
    from OracleIdentity import application_identity

    output = path.parent / "Results"
    output.mkdir(exist_ok=False)
    rows = request["cases"]
    report = {"schema": "kit.sw2026.blank-drawing-native-result.v1", "packet_sha256": expected_hash,
              "cases": [], "native_acceptance": False, "heldout_inputs_tested": 0}
    generic = {"root": path.parent, "output": output, "oracle": request["oracle_sha256"]}
    before = after = None
    tree = None

    def record(*, name, row, expected_tree):
        result = measure(Swapp, application_identity, name=name, row=row, tree=expected_tree, **generic)
        report["cases"].append(result)
        curves.write_json(output / "Progress.json", report)
        return result

    try:
        before = record(name="ControlBefore", row=rows[0], expected_tree=None)
        if before["passed"]:
            tree = before["open_edit_save"]["tree"]
            for row in rows[1:]:
                predicted = row["expected_tree"] if row["kind"] == "generated" else tree
                record(name=row["name"], row=row, expected_tree=predicted)
    except Exception as error:
        report["exception"] = repr(error)
    finally:
        try:
            after = record(name="ControlAfter", row=rows[0], expected_tree=tree)
        except Exception as error:
            report["control_after_exception"] = repr(error)
        try:
            read_packet(path, expected_hash)
            report["inputs_immutable"] = True
        except Exception as error:
            report.update(inputs_immutable=False, immutability_error=repr(error))
        phases = [row[key] for row in report["cases"] for key in ("open_edit_save", "fresh_reopen") if row[key] is not None]
        times = [phase["oracle_identity"]["process_creation_filetime"] for phase in phases if "oracle_identity" in phase]
        results = {row["name"]: row["passed"] for row in report["cases"]}
        controls = [bool(row and row["passed"]) for row in (before, after)]
        independent = len(times) == len(set(times)) == len(phases)
        interpretable = bool(report["inputs_immutable"] and controls == [True, True] and results.get("Repacked") and independent and "exception" not in report)
        report.update(control_results=controls, distinct_processes=len(set(times)), interpretable=interpretable,
                      reduced_native_passed=bool(results.get("ReducedNative")),
                      generated_discovery_passed=bool(interpretable and results.get("GeneratedBlank")))
        curves.write_json(output / "DrawingBlankResults.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description="Measure a generated empty drawing and a native stream reduction on the pinned oracle")
    parser.add_argument("packet", type=Path)
    parser.add_argument("--packet-sha256", required=True)
    args = parser.parse_args()
    curves.require(re.fullmatch(r"[0-9a-f]{64}", args.packet_sha256) is not None, "blank drawing packet hash required")
    report = run(args.packet.resolve(), args.packet_sha256)
    print(json.dumps({key: report[key] for key in ("interpretable", "reduced_native_passed", "generated_discovery_passed", "distinct_processes")}))
    return 0 if report["interpretable"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
