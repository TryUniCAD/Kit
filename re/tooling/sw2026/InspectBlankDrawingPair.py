from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from shutil import copyfileobj

import AuthorCurves as curves
from DrawingCacheCases import NATIVE_NAME, TOOL_NAMES as CACHE_TOOL_NAMES
from InspectDrawingCache import phase


SCHEMA = "kit.sw2026.blank-drawing-pair.v1"
GENERATED_NAME = "KitBlankSheetProbe.SLDDRW"
CASES = ("Pristine", "ReducedNative", "Baseline", "ThreadFlag")
KINDS = ("locked-control", "native-stream-reduction", "generated", "generated")
TOOL_NAMES = (*CACHE_TOOL_NAMES, "InspectBlankDrawingPair.py")


def input_path(root, row):
    return root / "Inputs" / row["name"] / row["filename"]


def read_packet(path, expected_sha):
    curves.require(curves.digest(path) == expected_sha, "blank drawing pair packet changed")
    request = json.loads(path.read_bytes())
    rows = request["cases"]
    curves.require(request["schema"] == SCHEMA and request["native_acceptance"] is False, "wrong drawing pair version")
    curves.require(tuple(row["name"] for row in rows) == CASES and tuple(row["kind"] for row in rows) == KINDS,
                   "drawing pair cases differ from the declared experiment")
    tools = request["tool_hashes"]
    curves.require(set(tools) == set(TOOL_NAMES), "drawing pair has missing tool identities")
    for name in TOOL_NAMES:
        curves.require(curves.digest(Path(__file__).with_name(name)) == tools[name], f"drawing pair tool changed: {name}")
    for row in rows:
        name = GENERATED_NAME if row["kind"] == "generated" else NATIVE_NAME
        curves.require(row["filename"] == name and row["expected"]["view"] is None, "unexpected drawing filename or view")
        source = input_path(path.parent, row)
        curves.require(source.stat().st_size == row["bytes"] and curves.digest(source) == row["sha256"], "drawing pair source changed")
    curves.require(rows[0]["sha256"] == request["control_sha256"], "pristine drawing differs from its lock")
    baseline, changed = rows[2:]
    curves.require(all(baseline[key] == changed[key] for key in ("expected", "expected_tree", "streams")),
                   "generated cases must test the same design")
    curves.require(baseline["sha256"] != changed["sha256"] and rows[1]["streams"] == baseline["streams"],
                   "drawing pair stream roles or candidate identities differ")
    curves.require(curves.digest(path.parent / "OfflinePair.json") == request["offline_pair_sha256"], "offline pairing evidence changed")
    return request


def observe(sw, identify, *, row, source, directory, oracle, tree):
    edit_directory = directory / "open_edit_save"
    first = phase(sw, identify, directory=edit_directory, native=source, expected_hash=row["sha256"],
                  expected=row["expected"], tree=tree, oracle_sha=oracle, edit=True)
    target = edit_directory / "EditedDrawing.SLDDRW"
    second = None
    if first["passed"]:
        second = phase(sw, identify, directory=directory / "fresh_reopen", native=target,
                       expected_hash=first["derivative_sha256"], expected=first["edited"], tree=first["tree"],
                       oracle_sha=oracle, edit=False)
    return {"input_sha256": row["sha256"], "open_edit_save": first, "fresh_reopen": second,
            "save_target_bytes": target.stat().st_size if target.is_file() else None,
            "passed": bool(first["passed"] and second and second["passed"])}


def run(path, expected_sha):
    request = read_packet(path, expected_sha)
    import Swapp
    from OracleIdentity import application_identity

    root = path.parent
    output = root / "Results"
    output.mkdir(exist_ok=False)
    rows = request["cases"]
    cases = []
    report = {"schema": "kit.sw2026.blank-drawing-pair-result.v1", "packet_sha256": expected_sha,
              "cases": cases, "heldout_inputs_tested": 0, "native_acceptance": False}
    oracle = request["oracle_sha256"]
    working = output / "GeneratedComparison"

    def capture(*, name, row, tree):
        source = input_path(root, row)
        directory = output / name
        if row["kind"] == "generated":
            working.mkdir(exist_ok=False)
            staged = working / GENERATED_NAME
            with source.open("rb") as reader, staged.open("xb") as writer:
                copyfileobj(reader, writer)
            result = observe(Swapp, application_identity, row=row, source=staged, directory=working, oracle=oracle, tree=tree)
            result["matched_input_relative_path"] = staged.relative_to(output).as_posix()
            result["matched_save_relative_path"] = (working / "open_edit_save" / "EditedDrawing.SLDDRW").relative_to(output).as_posix()
            working.rename(directory)
        else:
            result = observe(Swapp, application_identity, row=row, source=source, directory=directory, oracle=oracle, tree=tree)
        result.update(name=name, kind=row["kind"])
        cases.append(result)
        curves.write_json(output / "Progress.json", report)
        return result

    before = reduced = after = None
    control_tree = None
    try:
        before = capture(name="ControlBefore", row=rows[0], tree=None)
        if before["passed"]:
            control_tree = before["open_edit_save"]["tree"]
            reduced = capture(name="ReducedNative", row=rows[1], tree=control_tree)
            if reduced["passed"]:
                for row in rows[2:]:
                    capture(name=row["name"], row=row, tree=row["expected_tree"])
    except Exception as error:
        report["exception"] = repr(error)
    finally:
        try:
            after = capture(name="ControlAfter", row=rows[0], tree=control_tree)
        except Exception as error:
            report["control_after_exception"] = repr(error)
        try:
            read_packet(path, expected_sha)
            report["inputs_immutable"] = True
        except Exception as error:
            report.update(inputs_immutable=False, immutability_error=repr(error))
        phases = [record[key] for record in cases for key in ("open_edit_save", "fresh_reopen") if record[key] is not None]
        identities = [step["oracle_identity"]["process_creation_filetime"] for step in phases if "oracle_identity" in step]
        controls = [bool(result and result["passed"]) for result in (before, reduced, after)]
        generated = [row for row in cases if row["kind"] == "generated"]
        matched_paths = len(generated) == 2 and all(
            generated[0][field] == generated[1][field] for field in ("matched_input_relative_path", "matched_save_relative_path")
        )
        interpretable = (report["inputs_immutable"] and all(controls) and matched_paths and
                         len(identities) == len(set(identities)) == len(phases) and "exception" not in report)
        report.update(controls_healthy=controls, matched_paths=matched_paths, distinct_processes=len(set(identities)),
                      interpretable=interpretable)
        curves.write_json(output / "DrawingBlankPairResults.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description="Measure a paired generated blank drawing change at identical native paths")
    parser.add_argument("packet", type=Path)
    parser.add_argument("--packet-sha256", required=True)
    args = parser.parse_args()
    curves.require(re.fullmatch(r"[0-9a-f]{64}", args.packet_sha256) is not None, "pinned drawing packet hash required")
    report = run(args.packet.resolve(), args.packet_sha256)
    print(json.dumps({key: report[key] for key in ("interpretable", "controls_healthy", "matched_paths", "distinct_processes")}))
    return 0 if report["interpretable"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
