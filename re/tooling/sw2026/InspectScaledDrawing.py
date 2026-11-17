from __future__ import annotations

import argparse
import json
from pathlib import Path, PureWindowsPath
from shutil import copyfile

import AuthorCurves as curves
from InspectFrontDrawingMap import TOOL_NAMES as FRONT_TOOLS, phase


SCHEMA = "kit.sw2026.generated-scaled-drawing-trial.v1"
RESULT_SCHEMA = "kit.sw2026.generated-scaled-drawing-native-result.v1"
GENERATED_NAMES = ("GeneratedFront", "GeneratedTop", "GeneratedRight", "GeneratedIsometric")
ORIENTATIONS = ("*Front", "*Top", "*Right", "*Isometric")
TOOL_NAMES = (*FRONT_TOOLS, "InspectScaledDrawing.py")
SOURCE_LOCK_SHA256 = "99c3e345182c20853445bd7240a881d6fce22d397961779445961d61718a3298"
ORACLE_SHA256 = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"


def relative_file(root, name):
    relative = PureWindowsPath(name)
    curves.require(not relative.is_absolute() and relative.parts and ".." not in relative.parts,
                   "scaled drawing packet requires contained relative files")
    return root.joinpath(*relative.parts)


def input_files(root, row):
    directory = relative_file(root, row["directory"])
    return tuple(directory / row[kind]["filename"] for kind in ("drawing", "part"))


def read_packet(packet, packet_sha, tools_sha, runner_sha):
    curves.require(curves.digest(packet) == packet_sha, "scaled drawing packet changed")
    tool_file = Path(__file__).with_name("GuestTools.json")
    curves.require(curves.digest(tool_file) == tools_sha, "scaled drawing tools manifest changed")
    tools = json.loads(tool_file.read_bytes())
    curves.require(set(tools) == set(TOOL_NAMES), "scaled drawing tool dependency set differs")
    for name, expected in tools.items():
        curves.require(curves.digest(tool_file.with_name(name)) == expected, f"scaled drawing tool changed: {name}")
    curves.require(curves.digest(Path(__file__)) == tools["InspectScaledDrawing.py"] == runner_sha,
                   "scaled drawing runner changed")
    job = json.loads(packet.read_bytes())
    curves.require(job["schema"] == SCHEMA and job["native_acceptance"] is False
                   and job["heldout_inputs_tested"] == 0 and job["writer_output_count"] == 8
                   and job["oracle_sha256"] == ORACLE_SHA256 and job["source_lock_sha256"] == SOURCE_LOCK_SHA256,
                   "scaled drawing trial identity differs")
    for name, expected in job["source_artifacts"].items():
        curves.require(curves.digest(relative_file(packet.parent, name)) == expected,
                       f"scaled drawing construction artifact changed: {name}")
    rows = job["inputs"]
    curves.require(tuple(row["name"] for row in rows) == ("NativePristine", *GENERATED_NAMES),
                   "scaled drawing trial case order differs")
    trees = []
    drawings = set()
    parts = set()
    for index, row in enumerate(rows):
        for kind, suffix in (("drawing", ".slddrw"), ("part", ".sldprt")):
            item = row[kind]
            name = PureWindowsPath(item["filename"])
            curves.require(name.name == item["filename"] and name.suffix.casefold() == suffix,
                           "scaled drawing trial filename differs")
        for path, item in zip(input_files(packet.parent, row), (row["drawing"], row["part"]), strict=True):
            curves.require(path.is_file() and path.stat().st_size == item["bytes"] and curves.digest(path) == item["sha256"],
                           "scaled drawing trial input changed")
        if not index:
            curves.require(row["kind"] == "native-pristine" and row["source_case"] == "D00ScaledFront",
                           "scaled drawing control is not the disclosed pristine source")
            continue
        curves.require(row["kind"] == "neutral-generated" and row["expected"]["view"]["orientation"] == ORIENTATIONS[index - 1],
                       "scaled drawing generated orientation differs")
        proof = json.loads(relative_file(packet.parent, row["construction"]).read_bytes())
        prediction = json.loads(relative_file(packet.parent, row["prediction"]).read_bytes())
        curves.require(proof["native_acceptance"] is False and proof["input_runtime_file_access_attempts"] == 0
                       and proof["inspection"]["readback_exact"] and proof["inspection"]["detailing_bucket_count"] == 0,
                       "scaled drawing pair lacks its guarded exact graph proof")
        curves.require(proof["drawing"]["sha256"] == row["drawing"]["sha256"]
                       and proof["part"]["sha256"] == row["part"]["sha256"]
                       and prediction["expected"] == row["expected"] and prediction["tree"] == row["tree"]
                       and prediction["corner_count"] == 8 and prediction["independent_preflight_passed"],
                       "scaled drawing generated prediction or artifacts differ")
        curves.require(len(row["tree"]) == 16, "scaled drawing expected tree has the wrong node count")
        trees.append(row["tree"])
        drawings.add(row["drawing"]["sha256"])
        parts.add(row["part"]["sha256"])
    curves.require(len(drawings) == len(parts) == 4 and all(tree == trees[0] for tree in trees),
                   "scaled drawing requires four independent pairs and one explicit tree")
    checks = json.loads((packet.parent / "PreparationChecks.json").read_bytes())
    curves.require(checks["guarded_build_count"] == 8 and checks["runtime_input_file_access_attempts"] == 0
                   and checks["all_twice_identical"] and checks["writer_sources_immutable"]
                   and checks["neutral_job_immutable"] and checks["native_control_immutable"],
                   "scaled drawing preparation did not qualify")
    return job


def observe(sw, identify, *, root, row, name, output, oracle, tree):
    source, source_part = input_files(root, row)
    if row["kind"] == "native-pristine":
        working = output / name / "MatchedControl"
        working.mkdir(parents=True, exist_ok=False)
        drawing, part = working / source.name, working / source_part.name
        copyfile(source, drawing)
        copyfile(source_part, part)
    else:
        drawing, part = source, source_part
        tree = row["tree"]
    directory = output / name
    expected = row["expected"]
    common = {"child": part, "original_child": expected["view"]["resolved_reference_path"],
              "child_hash": row["part"]["sha256"], "oracle": oracle}
    first = phase(sw, identify, directory=directory / "OpenEditSave", native=drawing,
                  sha256=row["drawing"]["sha256"], expected=expected, tree=tree, edit=True, **common)
    reopened = None
    if first["passed"]:
        derivative = directory / "OpenEditSave" / "EditedDrawing.SLDDRW"
        reopened = phase(sw, identify, directory=directory / "FreshReopen", native=derivative,
                         sha256=first["derivative_sha256"], expected=first["edited"], tree=first["tree"], edit=False, **common)
    return {"source_sha256": row["drawing"]["sha256"], "child_sha256": row["part"]["sha256"],
            "open_edit_save": first, "fresh_reopen": reopened,
            "passed": bool(first["passed"] and reopened is not None and reopened["passed"])}


def run(packet, packet_sha, tools_sha, runner_sha):
    job = read_packet(packet, packet_sha, tools_sha, runner_sha)
    import Swapp
    from OracleIdentity import application_identity

    output = packet.parent / "ScaledDrawingResults"
    output.mkdir(exist_ok=False)
    result = {"schema": RESULT_SCHEMA, "packet_sha256": packet_sha, "tools_sha256": tools_sha,
              "runner_sha256": runner_sha, "writer_output_count": 8, "heldout_inputs_tested": 0,
              "source_lock_sha256": job["source_lock_sha256"], "lanes": {}}

    def measure(name, row, tree):
        lane = observe(Swapp, application_identity, root=packet.parent, row=row, name=name,
                       output=output, oracle=job["oracle_sha256"], tree=tree)
        result["lanes"][name] = lane
        curves.write_json(output / "Progress.json", result)
        return lane

    tree = None
    try:
        before = measure("ControlBefore", job["inputs"][0], None)
        if before["passed"]:
            tree = before["open_edit_save"]["tree"]
            for row in job["inputs"][1:]:
                measure(row["name"], row, row["tree"])
    except Exception as error:
        result["batch_error"] = str(error)
    finally:
        try:
            measure("ControlAfter", job["inputs"][0], tree)
        except Exception as error:
            result["final_control_error"] = str(error)
    try:
        read_packet(packet, packet_sha, tools_sha, runner_sha)
        immutable = True
    except Exception as error:
        immutable = False
        result["final_custody_error"] = str(error)
    lanes = result["lanes"]
    phases = [phase_value for lane in lanes.values() for phase_value in (lane["open_edit_save"], lane["fresh_reopen"])
              if phase_value is not None]
    identities = {(item["oracle_identity"]["process_id"], item["oracle_identity"]["process_creation_filetime"])
                  for item in phases if "oracle_identity" in item}
    controls = all(lanes.get(name, {}).get("passed") for name in ("ControlBefore", "ControlAfter"))
    attempted = all(name in lanes for name in GENERATED_NAMES)
    result.update(distinct_processes=len(identities), phase_count=len(phases), input_files_immutable=immutable,
                  controls_healthy=controls, generated_cases_attempted=attempted,
                  interpretable=bool(immutable and controls and attempted and len(identities) == len(phases)))
    result["scaled_drawing_trial_passed"] = bool(
        result["interpretable"] and len(identities) == len(phases) == 12 and len(lanes) == 6
        and all(lane["passed"] for lane in lanes.values()) and "batch_error" not in result
        and "final_control_error" not in result and "final_custody_error" not in result
    )
    curves.write_json(output / "ScaledDrawingResults.json", result)
    return result


def main():
    parser = argparse.ArgumentParser(description="Measure four generated scaled standard drawing views with pristine brackets")
    parser.add_argument("packet", type=Path)
    parser.add_argument("--packet-sha256", required=True)
    parser.add_argument("--tools-sha256", required=True)
    parser.add_argument("--runner-sha256", required=True)
    parser.add_argument("--verify-only", action="store_true")
    arguments = parser.parse_args()
    packet = arguments.packet.resolve()
    if arguments.verify_only:
        read_packet(packet, arguments.packet_sha256, arguments.tools_sha256, arguments.runner_sha256)
        print(json.dumps({"custody_verified": True, "writer_output_count": 8, "vendor_runtime_executed": False}))
        return 0
    result = run(packet, arguments.packet_sha256, arguments.tools_sha256, arguments.runner_sha256)
    print(json.dumps({key: result[key] for key in ("scaled_drawing_trial_passed", "interpretable", "distinct_processes",
                                                  "phase_count", "controls_healthy", "input_files_immutable")}))
    return 0 if result["scaled_drawing_trial_passed"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
