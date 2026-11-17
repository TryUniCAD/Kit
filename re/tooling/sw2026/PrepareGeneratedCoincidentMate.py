from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from shutil import copyfile

from AuthorCurves import digest, require, write_json
from InspectGeneratedCoincidentMate import (
    CONTROL_CHILD, CONTROL_NAME, DIMENSIONS, SCHEMA, SOURCE_LOCK_SHA, SOURCE_SPECS_SHA, TOOL_FILES,
    checked, validate_case,
)


TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parents[2]
LOCK = ROOT / "re/solidworks/v2026/heldout/AssemblyPlanarMateSourceLock01.json"
SPECS = TOOLS / "AssemblyMateSourceSpecs01.json"
RUNNER = "InspectGeneratedCoincidentMate.py"


def pinned_json(path, sha, owner):
    return json.loads(checked(path, sha, owner=owner).read_bytes())


def control_source(directory, output):
    lock = pinned_json(LOCK, SOURCE_LOCK_SHA, ROOT)
    require(lock["passed"] and lock["controls_healthy"] and lock["heldout_results_sealed"], "planar source lock is not intact")
    source, = (row for row in lock["cases"] if row["name"] == CONTROL_NAME and row["split"] == "discovery")
    require(source["passed"] and source["synchronized_child"]["path_basename"] == CONTROL_CHILD, "A17 is not the synchronized native source")
    relative = directory.relative_to(output.parent)
    require(relative.parts[-2:] == (CONTROL_NAME, "author") and not directory.is_relative_to(output), "choose only the disclosed A17 source directory")
    reopened = pinned_json(directory.parent / "fresh-reopen" / "Record.json", source["record_sha256"][1], directory.parent)
    native = reopened["assembly_result"]
    identity = native["oracle_identity"]
    require(native["passed"] and native["source_immutable"] and native["open_errors"] == native["open_warnings"] == 0 and
            identity["version_matches"] and identity["sha256"] == lock["oracle_sha256"], "disclosed A17 has no matching clean native reopen")
    authored, = (row for row in pinned_json(SPECS, SOURCE_SPECS_SHA, ROOT)["cases"] if row["name"] == CONTROL_NAME and row["split"] == "discovery")
    require(authored == reopened["job"]["case"], "A17 observation differs from the authored control spec")
    observation = native["rebuilt"]
    case = {
        "name": CONTROL_NAME, "child": CONTROL_CHILD, "configuration": "Default", "fixed_occurrence": authored["fixed_occurrence"],
        "placements": authored["placements"], "mates": [row | {"name": "Coincident1"} for row in authored["mates"]],
        "occurrence_names": [row["name"] for row in observation["occurrences"]], "rectangle_position": "centered",
        "dimensions_m": dict(zip(DIMENSIONS, (0.04, 0.02, 0.01), strict=True)),
    }
    validate_case(case)
    expected_tree = [[row[key] for key in ("name", "type", "parent")] for row in observation["tree"]]
    expected_order = [case["occurrence_names"][index] for index, _ in case["mates"][0]["planes"]]
    require([row["occurrence"] for row in observation["mates"][0]["entities"]] == expected_order, "A17 native ordered mate participants differ from the authored control")
    files = {}
    for name, row in ((CONTROL_NAME + ".SLDASM", source), (CONTROL_CHILD, source["synchronized_child"])):
        files[name] = {"sha256": row["native_sha256"], "bytes": row["native_bytes"]}
        checked(directory / name, row["native_sha256"], owner=directory, size=row["native_bytes"])
    return {"case": case, "relative_directory": relative.as_posix(), "expected_tree": expected_tree, "files": files,
            "native_reopen_sha256": source["record_sha256"][1],
            "expected_child_stamp": native["reopened_child_stamp"]}, lock["oracle_sha256"]


def generated_source(arguments, control, directory):
    prediction = arguments.prediction.resolve(strict=True)
    authored = pinned_json(prediction, arguments.prediction_sha256, prediction.parent)
    stem = Path(authored["child"]).stem
    case = authored | {"rectangle_position": "corner", "edit_depth_m": arguments.edit_depth_m,
                       "occurrence_names": authored.get("occurrence_names", [stem + "-1", stem + "-2"])}
    validate_case(case)
    metadata = arguments.generator_report.resolve(strict=True)
    generator = pinned_json(metadata, arguments.generator_report_sha256, metadata.parent)
    require(generator["schema"] == "kit.sw2026.generated-coincident-mate-bundle.v1" and generator["native_acceptance"] is False and
            generator["heldout_inputs_tested"] == generator["input_runtime_file_access_attempts"] == 0 and generator["writer_output_count"] == 2 and
            generator["authored_prediction_sha256"] == arguments.prediction_sha256, "generator report differs from the authored pair or its pre-native scope")
    require(re.fullmatch(r"[0-9a-f]{40}", arguments.writer_revision), "freeze the writer Git revision before freezing the oracle deck")
    files = {}
    for name, role, sha in ((case["name"] + ".SLDASM", "assembly", arguments.parent_sha256), (case["child"], "child", arguments.child_sha256)):
        content = checked(directory / name, sha, owner=directory)
        files[name] = {"sha256": sha, "bytes": content.stat().st_size}
        reported = generator[role]
        require(set(reported) == {"bytes", "sha256", "streams"} and {key: reported[key] for key in files[name]} == files[name] and
                files[name]["bytes"] > 0, "generated proof files differ from the sanitized structural report")
    native_names = control["case"]["occurrence_names"]
    names = dict(zip(native_names, case["occurrence_names"], strict=True))
    tree = [[names.get(name, name), kind, names.get(parent, parent)] for name, kind, parent in control["expected_tree"]]
    return {"case": case, "files": files, "expected_tree": tree, "authored_prediction_sha256": arguments.prediction_sha256,
            "generator_report_sha256": arguments.generator_report_sha256, "writer_revision": arguments.writer_revision}


def prepare(arguments):
    output = arguments.output.resolve()
    source = arguments.disclosed_control.resolve(strict=True)
    generated_dir = arguments.generated.resolve(strict=True)
    require(not output.exists() and output.parent.is_dir() and not output.is_relative_to(ROOT), "choose an unused private deck outside the checkout")
    require(not source.is_relative_to(ROOT) and not generated_dir.is_relative_to(ROOT) and source != generated_dir, "native proof inputs must come from separate private directories")
    control, oracle_sha = control_source(source, output)
    generated = generated_source(arguments, control, generated_dir)
    output.mkdir()
    guest = output / "Tools"
    guest.mkdir()
    frozen = output / "FrozenGenerated"
    frozen.mkdir()
    for name in generated["files"]:
        copyfile(generated_dir / name, frozen / name)
    for source_path, name in ((arguments.prediction, "AuthoredPrediction.json"), (arguments.generator_report, "GeneratorReport.json")):
        copyfile(source_path, output / name)
    write_json(output / "Prediction.json", generated["case"])
    generated["prediction_sha256"] = digest(output / "Prediction.json")
    tools = {}
    for name in TOOL_FILES:
        copyfile(TOOLS / name, guest / name)
        tools[name] = digest(guest / name)
    manifest = output / "Trial.json"
    write_json(manifest, {
        "schema": SCHEMA, "source_lock_sha256": SOURCE_LOCK_SHA, "source_specs_sha256": SOURCE_SPECS_SHA,
        "oracle_sha256": oracle_sha, "tool_hashes": tools, "preparer_sha256": digest(__file__), "native_acceptance": False,
        "generated": generated, "control": control, "heldout_inputs_tested": 0,
    })
    sha = digest(manifest)
    subprocess.run([sys.executable, "-B", str(guest / RUNNER), str(manifest), "--packet-sha256", sha, "--verify-only"],
                   check=True, capture_output=True, timeout=25)
    return {"packet": str(manifest), "packet_sha256": sha, "runner_sha256": tools[RUNNER],
            "generated_sha256": {name: row["sha256"] for name, row in generated["files"].items()}}


def main():
    parser = argparse.ArgumentParser(description="Freeze the first generated coincident mate native proof outside the checkout")
    parser.add_argument("prediction", type=Path)
    parser.add_argument("generator_report", type=Path)
    parser.add_argument("generated", type=Path)
    parser.add_argument("disclosed_control", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--prediction-sha256", required=True)
    parser.add_argument("--generator-report-sha256", required=True)
    parser.add_argument("--parent-sha256", required=True)
    parser.add_argument("--child-sha256", required=True)
    parser.add_argument("--writer-revision", required=True)
    parser.add_argument("--edit-depth-m", type=float, required=True)
    print(json.dumps(prepare(parser.parse_args()), sort_keys=True))


if __name__ == "__main__":
    main()
