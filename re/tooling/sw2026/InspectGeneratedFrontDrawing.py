from __future__ import annotations

import argparse
import json
from pathlib import Path, PureWindowsPath
from shutil import copyfile

import AuthorCurves as curves
from InspectFrontDrawingMap import TOOL_NAMES as FRONT_TOOLS, phase


SCHEMA = "kit.sw2026.generated-front-drawing-trial.v1"
INPUT_NAMES = ("NativePristine", "NativeReduced", "GeneratedInput")
TOOL_NAMES = (*FRONT_TOOLS, "InspectGeneratedFrontDrawing.py")


def input_files(root, row):
    directory = root / row["name"]
    return directory / row["drawing"]["filename"], directory / row["part"]["filename"]


def read_job(packet, packet_hash, tools_hash):
    curves.require(curves.digest(packet) == packet_hash, "generated front drawing packet hash differs")
    tool_file = Path(__file__).with_name("GuestTools.json")
    curves.require(curves.digest(tool_file) == tools_hash, "generated front drawing tool manifest hash differs")
    tools = json.loads(tool_file.read_bytes())
    curves.require(set(tools) == set(TOOL_NAMES), "generated front drawing tool set differs")
    for name, digest in tools.items():
        curves.require(curves.digest(tool_file.with_name(name)) == digest, f"front drawing trial tool changed: {name}")
    job = json.loads(packet.read_bytes())
    rows = job["inputs"]
    curves.require(job["schema"] == SCHEMA and job["writer_output_count"] == 2 and job["native_acceptance"] is False,
                   "packet must describe a source-only drawing and generated child trial")
    curves.require(tuple(row["name"] for row in rows) == INPUT_NAMES, "generated front drawing trial inputs differ")
    for row in rows:
        pair = (row["drawing"], row["part"])
        for item, suffix in zip(pair, (".slddrw", ".sldprt"), strict=True):
            name = PureWindowsPath(item["filename"])
            curves.require(name.name == item["filename"] and name.suffix.casefold() == suffix, "invalid front drawing trial filename")
        for path, item in zip(input_files(packet.parent, row), pair, strict=True):
            curves.require(path.stat().st_size == item["bytes"] and curves.digest(path) == item["sha256"], "front drawing trial input changed")
    curves.require(rows[0]["part"] == rows[1]["part"] and rows[1]["stream_roles"] == rows[2]["stream_roles"],
                   "paired native drawing probes must use the same child and isolate the generated stream set")
    return job


def observe(sw, identify, *, root, row, name, output, oracle, control_tree):
    source, source_part = input_files(root, row)
    generated = row["name"] == "GeneratedInput"
    if generated:
        drawing, part = source, source_part
        tree = row["tree"]
    else:
        working = output / "MatchedControl"
        drawing, part = working / source.name, working / source_part.name
        copyfile(source, drawing)
        copyfile(source_part, part)
        tree = control_tree
    directory = output / name
    expected = row["expected"]
    common = {"child": part, "original_child": expected["view"]["resolved_reference_path"],
              "child_hash": row["part"]["sha256"], "oracle": oracle}
    first = phase(sw, identify, directory=directory / "OpenEditSave", native=drawing, sha256=row["drawing"]["sha256"],
                  expected=expected, tree=tree, edit=True, **common)
    reopened = None
    if first["passed"]:
        derivative = directory / "OpenEditSave" / "EditedDrawing.SLDDRW"
        reopened = phase(sw, identify, directory=directory / "FreshReopen", native=derivative,
                         sha256=first["derivative_sha256"], expected=first["edited"], tree=first["tree"], edit=False, **common)
    return {"source_sha256": row["drawing"]["sha256"], "open_edit_save": first, "fresh_reopen": reopened,
            "passed": bool(first["passed"] and reopened is not None and reopened["passed"])}


def run(packet, packet_hash, tools_hash):
    job = read_job(packet, packet_hash, tools_hash)
    import Swapp
    from OracleIdentity import application_identity

    output = packet.parent / "GeneratedFrontResults"
    output.mkdir(exist_ok=False)
    (output / "MatchedControl").mkdir(exist_ok=False)
    pristine, reduced, generated = job["inputs"]
    results = {"schema": "kit.sw2026.generated-front-drawing-result.v1", "packet_sha256": packet_hash,
               "tools_sha256": tools_hash, "writer_output_count": 2, "heldout_inputs_tested": 0, "lanes": {}}

    def measure(name, row, tree):
        result = observe(Swapp, application_identity, root=packet.parent, row=row, name=name, output=output,
                         oracle=job["oracle_sha256"], control_tree=tree)
        results["lanes"][name] = result
        curves.write_json(output / "Progress.json", results)
        return result

    tree = None
    try:
        before = measure("ControlBefore", pristine, None)
        if before["passed"]:
            tree = before["open_edit_save"]["tree"]
            measure("ReducedControl", reduced, tree)
            measure("GeneratedPair", generated, None)
    finally:
        measure("ControlAfter", pristine, tree)
    read_job(packet, packet_hash, tools_hash)
    phases = [entry for lane in results["lanes"].values() for entry in (lane["open_edit_save"], lane["fresh_reopen"]) if entry is not None]
    identities = {item["oracle_identity"]["process_creation_filetime"] for item in phases if "oracle_identity" in item}
    results["distinct_processes"] = len(identities)
    results["input_files_immutable"] = True
    lanes = results["lanes"]
    results["interpretable"] = (len(identities) == len(phases) and all(lanes[key]["passed"] for key in ("ControlBefore", "ControlAfter"))
                                and "ReducedControl" in lanes and "GeneratedPair" in lanes)
    results["generated_trial_passed"] = results["interpretable"] and lanes["GeneratedPair"]["passed"]
    curves.write_json(output / "GeneratedFrontResults.json", results)
    return results


def main():
    parser = argparse.ArgumentParser(description="Measure the independently generated ordinary front view and the disclosed native control")
    parser.add_argument("packet", type=Path)
    parser.add_argument("--packet-sha256", required=True)
    parser.add_argument("--tools-sha256", required=True)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    if args.verify_only:
        read_job(args.packet, args.packet_sha256, args.tools_sha256)
        return 0
    report = run(args.packet.resolve(), args.packet_sha256, args.tools_sha256)
    print(json.dumps({key: report[key] for key in ("interpretable", "generated_trial_passed", "distinct_processes")}))
    return 0 if report["interpretable"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
