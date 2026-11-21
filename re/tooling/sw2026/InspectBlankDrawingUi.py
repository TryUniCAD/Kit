from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from shutil import copyfileobj

import AuthorCurves as curves
from DrawingCacheCases import NATIVE_NAME
from InspectBlankDrawingPair import TOOL_NAMES as PAIR_TOOLS, observe


SCHEMA = "kit.sw2026.blank-drawing-ui-trial.v1"
TOOL_NAMES = (*PAIR_TOOLS, "InspectBlankDrawingUi.py")
CASES = (
    ("Pristine", ()),
    ("ReducedRepack", ()),
    ("ViewportAbsent", ("viewport",)),
    ("UiLineTablesEmpty", ("line_tables",)),
    ("UiOwnersEmpty", ("environment_and_bom",)),
    ("AllThreeEmpty", ("viewport", "line_tables", "environment_and_bom")),
)


def input_path(root, row):
    return root / "Inputs" / row["name"] / NATIVE_NAME


def read_packet(path, expected_sha):
    curves.require(curves.digest(path) == expected_sha, "blank drawing UI packet changed")
    request = json.loads(path.read_bytes())
    rows = request["cases"]
    curves.require(request["schema"] == SCHEMA and request["writer_output_count"] == 0, "wrong drawing diagnostic packet")
    curves.require(tuple((row["name"], tuple(row["omitted"])) for row in rows) == CASES, "unexpected blank drawing UI cases")
    tools = request["tool_hashes"]
    curves.require(set(tools) == set(TOOL_NAMES), "drawing UI packet has missing source tools")
    for name in TOOL_NAMES:
        curves.require(curves.digest(Path(__file__).with_name(name)) == tools[name], f"drawing UI tool changed: {name}")
    curves.require(rows[0]["sha256"] == request["control_sha256"], "pristine control differs from its source lock")
    for row in rows:
        native = input_path(path.parent, row)
        curves.require(native.stat().st_size == row["bytes"] and curves.digest(native) == row["sha256"], "a drawing UI input changed")
        curves.require(row["expected"]["view"] is None and row["expected"] == rows[0]["expected"], "expected one disclosed blank sheet")
    return request


def run(path, expected_sha):
    request = read_packet(path, expected_sha)
    import Swapp
    from OracleIdentity import application_identity

    root = path.parent
    output = root / "Results"
    output.mkdir(exist_ok=False)
    working = output / "MatchedDrawing"
    rows = request["cases"]
    observed = []
    report = {"schema": "kit.sw2026.blank-drawing-ui-result.v1", "packet_sha256": expected_sha,
              "cases": observed, "writer_output_count": 0, "native_acceptance": False}

    def capture(name, row, tree):
        working.mkdir(exist_ok=False)
        staged = working / NATIVE_NAME
        with input_path(root, row).open("rb") as source, staged.open("xb") as copy:
            copyfileobj(source, copy)
        result = observe(Swapp, application_identity, row=row, source=staged, directory=working,
                         oracle=request["oracle_sha256"], tree=tree)
        result.update(name=name, omitted=row["omitted"])
        working.rename(output / name)
        observed.append(result)
        curves.write_json(output / "Progress.json", report)
        return result

    before = repack = after = None
    tree = None
    try:
        before = capture("ControlBefore", rows[0], None)
        if before["passed"]:
            tree = before["open_edit_save"]["tree"]
            repack = capture(rows[1]["name"], rows[1], tree)
            if repack["passed"]:
                for row in rows[2:]:
                    capture(row["name"], row, tree)
    except Exception as error:
        report["exception"] = repr(error)
    finally:
        try:
            after = capture("ControlAfter", rows[0], tree)
        except Exception as error:
            report["control_after_exception"] = repr(error)
        try:
            read_packet(path, expected_sha)
            report["inputs_immutable"] = True
        except Exception as error:
            report.update(inputs_immutable=False, immutability_error=repr(error))
        phases = [case[key] for case in observed for key in ("open_edit_save", "fresh_reopen") if case[key] is not None]
        processes = [phase["oracle_identity"]["process_creation_filetime"] for phase in phases if "oracle_identity" in phase]
        controls = [bool(result and result["passed"]) for result in (before, repack, after)]
        report.update(control_results=controls, distinct_processes=len(set(processes)),
                      interpretable=(len(observed) == len(rows) + 1 and all(controls) and report["inputs_immutable"]
                                     and len(set(processes)) == len(processes) == len(phases) and "exception" not in report))
        curves.write_json(output / "DrawingBlankUiResults.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description="Measure typed UI field omissions on a disclosed native blank drawing")
    parser.add_argument("packet", type=Path)
    parser.add_argument("--packet-sha256", required=True)
    args = parser.parse_args()
    curves.require(re.fullmatch(r"[0-9a-f]{64}", args.packet_sha256) is not None, "pinned drawing packet hash required")
    result = run(args.packet.resolve(), args.packet_sha256)
    return 0 if result["interpretable"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
