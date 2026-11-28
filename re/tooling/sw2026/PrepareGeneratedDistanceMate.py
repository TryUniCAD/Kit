from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from shutil import copyfile
import subprocess
import sys

from AuthorCurves import digest, require, write_json
from InspectGeneratedCoincidentMate import DIMENSIONS, SOURCE_LOCK_SHA, SOURCE_SPECS_SHA, checked, pair_paths
from InspectGeneratedDistanceMate import (
    CANDIDATE, CANDIDATE_CHILD, CONTROL, CONTROL_CHILD, CONTROL_DIRECTORY, MATE, ORACLE_VERSION, SCHEMA, SCRIPT, TOOL_FILES,
    distance, gap, validate_case,
)


WRITER_REVISION = "c4fda5661f92ed77d8b743be0d1940035bdd50fa"
WRITER_ROOT = "re/tooling/sw2026"
RECEIPT_PATH = "re/solidworks/measurements/2026/GeneratedDistanceMateBundle01.json"
LOCK = "re/solidworks/v2026/heldout/AssemblyPlanarMateSourceLock01.json"
SPECS = f"{WRITER_ROOT}/AssemblyMateSourceSpecs01.json"
HANDOFF_SHA = "519fa8e66315c1bbf3407ec79410b793520ceb6957d653832d02fa5278c27ced"


def committed(repo, path, expected=None):
    payload = subprocess.check_output(["git", "show", f"{WRITER_REVISION}:{path}"], cwd=repo, timeout=10)
    if expected is not None:
        require(hashlib.sha256(payload).hexdigest() == expected, f"committed writer artifact differs: {path}")
    return payload


def control_source(repo, output):
    source = json.loads(committed(repo, LOCK, SOURCE_LOCK_SHA))
    specs = json.loads(committed(repo, SPECS, SOURCE_SPECS_SHA))
    require(source["passed"] and source["controls_healthy"] and source["heldout_results_sealed"]
            and source["oracle_file_version"] == ORACLE_VERSION, "disclosed source lock is not qualified")
    pinned, = (row for row in source["cases"] if row["name"] == CONTROL and row["split"] == "discovery")
    authored, = (row for row in specs["cases"] if row["name"] == CONTROL and row["split"] == "discovery")
    parent = output.parent / CONTROL_DIRECTORY
    require(parent.resolve(strict=True) == parent and not parent.is_relative_to(repo), "control custody must be the exact disclosed author directory")
    record_path = checked(parent.parent / "fresh-reopen/Record.json", pinned["record_sha256"][1], owner=parent.parent)
    record = json.loads(record_path.read_bytes())
    observed = record["assembly_result"]
    identity = observed["oracle_identity"]
    require(pinned["passed"] and pinned["synchronized_child"]["path_basename"] == CONTROL_CHILD and record["job"]["case"] == authored
            and observed["passed"] and observed["source_immutable"] and observed["open_errors"] == observed["open_warnings"] == 0
            and identity["version_matches"] and identity["file_version"] == ORACLE_VERSION and identity["sha256"] == source["oracle_sha256"],
            "disclosed A18 lacks its matching clean reopen")
    snapshot = observed["rebuilt"]
    case = authored | {
        "child": CONTROL_CHILD, "configuration": "Default", "rectangle_position": "centered",
        "dimensions_m": dict(zip(DIMENSIONS, (0.04, 0.02, 0.01), strict=True)),
        "occurrence_names": [row["name"] for row in snapshot["occurrences"]],
        "mates": [row | {"name": MATE} for row in authored["mates"]],
    }
    validate_case(case)
    mate, = snapshot["mates"]
    require(mate["dimension_m"] == distance(case) == gap(case) and mate["dimension_name"] == f"D1@{MATE}@{CONTROL}.Assembly"
            and mate["type"] == 5 and mate["alignment"] == 0 and not mate["flipped"]
            and [row["occurrence"] for row in mate["entities"]] == case["occurrence_names"]
            and [row["fixed"] for row in snapshot["occurrences"]] == [True, False], "disclosed A18 native mate differs from the control contract")
    files = {
        name: {"sha256": row["native_sha256"], "bytes": row["native_bytes"]}
        for name, row in ((CONTROL + ".SLDASM", pinned), (CONTROL_CHILD, pinned["synchronized_child"]))
    }
    pair_paths(parent, case, files)
    return {
        "case": case, "relative_directory": CONTROL_DIRECTORY.as_posix(), "files": files,
        "native_reopen_sha256": pinned["record_sha256"][1], "initial_child_stamp": observed["reopened_child_stamp"],
        "expected_tree": [[row[key] for key in ("name", "type", "parent")] for row in snapshot["tree"]],
    }, source["oracle_sha256"]


def generated_source(repo, source, control):
    handoff = json.loads(checked(source / "Handoff.json", HANDOFF_SHA, owner=source).read_bytes())
    receipt_sha = handoff["evidence"][RECEIPT_PATH]
    receipt_bytes = committed(repo, RECEIPT_PATH, receipt_sha)
    receipt = json.loads(receipt_bytes)
    for name, sha in receipt["writer_tool_hashes"].items():
        path = f"{WRITER_ROOT}/{name}"
        require(sha == handoff["evidence"][path], f"builder handoff differs: {name}")
        committed(repo, path, sha)
    inputs = {
        name: checked(source / "Candidate" / name, handoff["candidate_files"][name], owner=source / "Candidate")
        for name in ("Request.json", "Prediction.json", "GeneratorReport.json")
    }
    prediction = json.loads(inputs["Prediction.json"].read_bytes())
    report = json.loads(inputs["GeneratorReport.json"].read_bytes())
    source_hashes = {name: digest(path) for name, path in inputs.items()}
    require(receipt["candidate"] == report and receipt["guarded_report_sha256"] == source_hashes["GeneratorReport.json"]
            and report["authored_prediction_sha256"] == source_hashes["Prediction.json"] and report["request_sha256"] == source_hashes["Request.json"]
            and report["schema"] == "kit.sw2026.generated-distance-mate-bundle.v1" and report["split"] == "discovery"
            and report["heldout_inputs_tested"] == report["input_runtime_file_access_attempts"] == 0
            and report["native_acceptance"] is False and report["writer_output_count"] == 2, "generated discovery pair differs from the guarded writer")
    sizes = prediction["dimensions_m"]
    case = prediction | {"dimensions_m": dict(zip(DIMENSIONS, (sizes["width"], sizes["height"], sizes["depth"]), strict=True))}
    require(case["name"] == CANDIDATE and case["child"] == CANDIDATE_CHILD and case["rectangle_position"] == "corner", "unexpected generated discovery case")
    validate_case(case)
    inspection = report["inspection"]
    first, second = (row["detached"] for row in inspection["wrappers"])
    points = [row["world_origin"] for row in (first, second)]
    normal = first["world_normal"]
    stored_gap = math.fsum(normal[axis] * (points[1][axis] - points[0][axis]) for axis in "xyz")
    evidence = inspection["distance"]
    require(stored_gap == evidence["initial_signed_separation_m"] == case["initial_signed_separation_m"] == gap(case)
            and evidence["distance_m"] == distance(case) and gap(case) < distance(case)
            and evidence["parameter_name"] == "D1" and evidence["presentation_phase"] == "constructor"
            and inspection["mate_fields"]["f0c"] == 1 and inspection["mate_fields"]["f3b8"] == 0,
            "typed storage must distinguish authored separation, driving D1 and initial solver state")
    files = {}
    for name, role in ((CANDIDATE + ".SLDASM", "assembly"), (CANDIDATE_CHILD, "child")):
        encoded = report[role]
        require(set(encoded) == {"bytes", "sha256", "streams"} and encoded["sha256"] == handoff["candidate_files"][name], "unsanitized or mismatched writer output")
        files[name] = {key: encoded[key] for key in ("bytes", "sha256")}
    assembled = pair_paths(source / "Candidate", case, files)
    names = dict(zip(control["case"]["occurrence_names"], case["occurrence_names"], strict=True))
    return {
        "case": case, "files": files, "writer_revision": WRITER_REVISION, "writer_tool_hashes": receipt["writer_tool_hashes"],
        "source_artifact_sha256": source_hashes | {"StructuralReceipt.json": receipt_sha},
        "authored_gap_m": stored_gap, "expected_solved_gap_m": distance(case), "planned_edit_target_m": case["planned_distance_edit_m"],
        "expected_tree": [[names.get(name, name), kind, names.get(parent, parent)] for name, kind, parent in control["expected_tree"]],
    }, inputs, receipt_bytes, assembled


def prepare(repo, source, output):
    require(output.parent.is_dir() and not output.exists() and not output.is_symlink() and not output.is_relative_to(repo)
            and not output.is_relative_to(source) and not source.is_relative_to(repo), "choose an unused external distance deck")
    control, oracle = control_source(repo, output)
    generated, inputs, receipt_bytes, assembled = generated_source(repo, source, control)
    output.mkdir()
    frozen = output / "FrozenGenerated"
    frozen.mkdir()
    for name, path in inputs.items():
        copyfile(path, output / name)
    (output / "StructuralReceipt.json").write_bytes(receipt_bytes)
    for path in assembled:
        copyfile(path, frozen / path.name)
    staging = output / "Tools"
    staging.mkdir()
    for name in TOOL_FILES:
        (staging / name).write_bytes(committed(repo, f"{WRITER_ROOT}/{name}"))
    copyfile(SCRIPT, staging / SCRIPT.name)
    manifest = output / "Trial.json"
    write_json(manifest, {
        "schema": SCHEMA, "read_only": True, "heldout_inputs_tested": 0, "native_acceptance": False,
        "tool_hashes": {path.name: digest(path) for path in sorted(staging.iterdir())},
        "preparer_sha256": digest(__file__), "source_lock_sha256": SOURCE_LOCK_SHA, "source_specs_sha256": SOURCE_SPECS_SHA,
        "control": control, "generated": generated, "oracle_sha256": oracle, "oracle_file_version": ORACLE_VERSION,
    })
    sha = digest(manifest)
    subprocess.run([sys.executable, "-B", str(staging / SCRIPT.name), "verify", str(manifest), "--packet-sha256", sha],
                   check=True, timeout=25)
    return {"packet": str(manifest), "packet_sha256": sha, "observer_sha256": digest(staging / SCRIPT.name), "writer_revision": WRITER_REVISION}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Freeze the exact generated distance trial and pin disclosed A18 controls")
    for parameter in ("repository", "candidate_source", "output"):
        parser.add_argument(parameter, type=Path)
    args = parser.parse_args()
    print(json.dumps(prepare(args.repository.resolve(strict=True), args.candidate_source.resolve(strict=True), args.output.absolute()), sort_keys=True))
