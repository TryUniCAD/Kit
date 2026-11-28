from __future__ import annotations

import argparse
import json
from pathlib import Path
from shutil import copyfile

import AuthorCurves as curves
from DrawingCacheCases import NATIVE_NAME
from InspectBlankDrawingPair import TOOL_NAMES as PAIR_TOOLS, observe
from InspectDrawingCache import phase
from InspectDrawingSaveModes import MODES, save_phase


SCHEMA = "kit.sw2026.blank-drawing-container-framing.v1"
CASES = ("Pristine", "ReducedVendorFraming", "ReducedKitFraming")
TOOL_NAMES = (*PAIR_TOOLS, "InspectDrawingSaveModes.py", "InspectBlankDrawingFraming.py")


def input_path(root, row):
    return root / "Inputs" / row["name"] / NATIVE_NAME


def read_packet(path, expected_hash):
    curves.require(curves.digest(path) == expected_hash, "drawing framing packet digest differs")
    request = json.loads(path.read_bytes())
    curves.require(request["schema"] == SCHEMA and request["writer_output_count"] == 0 and not request["native_acceptance"],
                   "framing experiment requires disclosed native input")
    rows = request["cases"]
    curves.require(tuple(row["name"] for row in rows) == CASES, "drawing framing cases differ")
    curves.require(rows[0]["sha256"] == request["control_sha256"] and rows[1]["sha256"] != rows[2]["sha256"],
                   "drawing framing needs the original control and distinct encodings")
    for name in TOOL_NAMES:
        curves.require(curves.digest(Path(__file__).with_name(name)) == request["tool_hashes"][name], f"drawing framing tool changed: {name}")
    for row in rows:
        source = input_path(path.parent, row)
        curves.require(source.stat().st_size == row["bytes"] and curves.digest(source) == row["sha256"], "a locked framing input changed")
        curves.require(row["expected"]["view"] is None and row["expected"] == rows[0]["expected"], "framing experiment requires the same blank design")
    offline = path.parent / "PhysicalComparison.json"
    curves.require(curves.digest(offline) == request["offline_sha256"], "offline framing comparison changed")
    return request


def run(path, expected_hash):
    request = read_packet(path, expected_hash)
    import Swapp
    from OracleIdentity import application_identity

    output = path.parent / "ContainerFramingResults"
    output.mkdir(exist_ok=False)
    working = output / "MatchedDrawing"
    pristine, vendor, kit = request["cases"]
    oracle = request["oracle_sha256"]
    report = {"schema": "kit.sw2026.blank-drawing-framing-result.v1", "packet_sha256": expected_hash, "controls": [],
              "lanes": [], "writer_output_count": 0, "native_acceptance": False, "heldout_inputs_tested": 0}

    def control(label, tree):
        result = observe(Swapp, application_identity, row=pristine, source=input_path(path.parent, pristine),
                         directory=output / label, oracle=oracle, tree=tree)
        report["controls"].append({"name": label, **result})
        curves.write_json(output / "Progress.json", report)
        return result

    def measure(row, mode, tree):
        working.mkdir(exist_ok=False)
        matched = working / NATIVE_NAME
        copyfile(input_path(path.parent, row), matched)
        first = save_phase(Swapp, application_identity, row=row, mode=mode, working=working, source=matched,
                           oracle=oracle, expected_tree=tree)
        target = working / first["save_target_relative_path"]
        reopened = None
        if first["passed"]:
            reopened = phase(Swapp, application_identity, directory=working / "fresh_reopen", native=target,
                             expected_hash=first["save_target_sha256"], expected=first["expected_reopen"],
                             tree=first["tree"], oracle_sha=oracle, edit=False)
        name = row["name"] + mode
        result = {"name": name, "framing": row["name"], "mode": mode, "input_sha256": row["sha256"],
                  "matched_input": matched.relative_to(output).as_posix(), "matched_save": target.relative_to(output).as_posix(),
                  "open_and_save": first, "fresh_reopen": reopened, "passed": bool(first["passed"] and reopened and reopened["passed"])}
        working.rename(output / name)
        report["lanes"].append(result)
        curves.write_json(output / "Progress.json", report)
        return result

    tree = None
    try:
        before = control("ControlBefore", None)
        if before["passed"]:
            tree = before["open_edit_save"]["tree"]
            for mode in MODES:
                if measure(vendor, mode, tree)["passed"]:
                    measure(kit, mode, tree)
    except Exception as error:
        report["exception"] = repr(error)
    finally:
        control("ControlAfter", tree)
    read_packet(path, expected_hash)
    lanes = report["lanes"]
    comparisons = tuple(zip(lanes[::2], lanes[1::2], strict=True)) if len(lanes) == 4 else ()
    phases = [item for row in report["controls"] for key in ("open_edit_save", "fresh_reopen") if (item := row[key]) is not None]
    phases += [item for row in lanes for key in ("open_and_save", "fresh_reopen") if (item := row[key]) is not None]
    identities = {item["oracle_identity"]["process_creation_filetime"] for item in phases if "oracle_identity" in item}
    same_paths = bool(comparisons) and all(a[key] == b[key] for a, b in comparisons for key in ("matched_input", "matched_save"))
    brackets = len(report["controls"]) == 2 and all(row["passed"] for row in report["controls"])
    report.update(distinct_processes=len(identities), inputs_immutable=True, same_physical_paths=same_paths,
                  controls_healthy=brackets, interpretable=bool(same_paths and brackets and len(identities) == len(phases)
                            and "exception" not in report and all(a["passed"] for a, _ in comparisons)))
    curves.write_json(output / "DrawingBlankFramingResults.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description="Compare only the archive framing of the same disclosed blank drawing")
    parser.add_argument("packet", type=Path)
    parser.add_argument("--packet-sha256", required=True)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    if args.verify_only:
        read_packet(args.packet, args.packet_sha256)
        return 0
    report = run(args.packet.resolve(), args.packet_sha256)
    print(json.dumps({key: report[key] for key in ("controls_healthy", "same_physical_paths", "distinct_processes", "interpretable")}))
    return 0 if report["interpretable"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
