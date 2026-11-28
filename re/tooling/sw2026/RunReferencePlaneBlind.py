from __future__ import annotations

import argparse
from base64 import b64decode
from contextlib import redirect_stderr, redirect_stdout
import json
import os
from pathlib import Path
import re
from shutil import copyfile
import subprocess
import sys
import time
import traceback

from AuthorCurves import digest, require, write_json
from InspectPairedReferencePlane import ORACLE, SCHEMA as NATIVE_SCHEMA, SOURCE_LOCK_SHA256, TOOLS as NATIVE_TOOLS, checked


SCHEMA = "kit.sw2026.offset-plane-blind-method.v1"
SOURCE_PACKET_SHA256 = "db56b95bad3543b5949848ce263bc8865c578ead20b688166d0b576310eeda7a"
DISCLOSED_SLOTS = ("D01", "D03", "D04")
SLOTS = ("H01", "H02")
TOOLS = (*NATIVE_TOOLS, Path(__file__).name)
BUILD_PROCESS = "re/tooling/sw2026/ReferencePlanePartProcess.py"


def read(path):
    return json.loads(path.read_bytes())


def attest(path, sha):
    return read(checked(path, sha, path.parent))


def freeze_json(path, value):
    require(not path.exists(), "preserve the registered plane evidence")
    write_json(path, value)
    return digest(path)


def verify(root, sha):
    method = attest(root / "Method.json", sha)
    require(method["schema"] == SCHEMA and method["source_packet_sha256"] == SOURCE_PACKET_SHA256
            and method["source_lock_sha256"] == SOURCE_LOCK_SHA256, "unexpected original offset-plane method")
    require(Path(__file__).resolve().parent == root / "Tools" and set(method["tool_hashes"]) == set(TOOLS),
            "use the complete frozen plane method")
    for name, expected in method["tool_hashes"].items():
        checked(root / "Tools" / name, expected, root / "Tools")
    recipe = attest(root / "Recipe.json", method["recipe_sha256"])
    require(recipe["schema"] == "kit.sw2026.offset-plane-blind-evaluation-recipe.v1" and recipe["state"] == "frozen"
            and recipe["execution_enabled"] is True and recipe["native_acceptance"] is False
            and recipe["format"]["oracle_sha256"] == ORACLE and recipe["source"]["source_lock_sha256"] == SOURCE_LOCK_SHA256,
            "the offset-plane recipe must bind the exact frozen method")
    qualification = recipe["disclosed_generated_qualification"]
    require(qualification["qualified"] and qualification["independent_cases_sufficient_for_declared_scope"]
            and qualification["open_edit_rebuild_save_reopen_0_0"] and qualification["six_significant_figures_geometry"]
            and qualification["source_inputs_immutable"] and qualification["zero_runtime_input_reads"],
            "the declared offset-plane scope requires complete disclosed evidence")
    binding = recipe["frozen_code"]
    require(re.fullmatch(r"[0-9a-f]{40}", binding["writer_revision"]) and binding["complete_code_manifest_sha256"] == method["code_manifest_sha256"]
            and recipe["execution_rules"]["host_heldout_payload_reads"] == 0 and recipe["execution_rules"]["case_inputs_and_detailed_observations_guest_only"],
            "original offset-plane values must stay guest-local")
    manifest = attest(root / "CodeManifest.json", method["code_manifest_sha256"])
    require(all(manifest["files_sha256"].get(name) == value for name, value in binding["writer_files_sha256"].items())
            and manifest["files_sha256"].get(BUILD_PROCESS) == binding["build_process_sha256"]
            and binding["observer_sha256"] == method["tool_hashes"]["InspectPairedReferencePlane.py"]
            and binding["translator_sha256"] == binding["predictor_sha256"] == method["tool_hashes"]["ReferencePlaneSourceRecipe.py"],
            "code and recipe identities differ")
    results = method["disclosed_result_hashes"]
    require(set(results) == set(DISCLOSED_SLOTS) and len(set(results.values())) == len(DISCLOSED_SLOTS),
            "qualification requires independent evidence for each principal plane")
    for name, expected in method["disclosed_result_hashes"].items():
        evidence = attest(root / (name + "Qualification.json"), expected)
        require(evidence["passed"] and evidence["source_generated_paired_acceptance"] and evidence["controls_healthy"]
                and evidence["distinct_processes"] == 4 and evidence["heldout_inputs_read"] == 0,
                "the disclosed source and generated comparison is incomplete")
    lock = attest(root / "SourceLock.json", SOURCE_LOCK_SHA256)
    require(lock["distinct_native_processes"] == 18 and all(row["passed"] for row in lock["records"])
            and all(any(row["case_id"] == slot and row["phase"] == "lock" and row["heldout_source_locked"] for row in lock["records"]) for slot in SLOTS),
            "both original native source slots need their pre-writer lock")
    return method, recipe, manifest, lock


def validate_code(code, manifest, copy_to=None):
    files = manifest["files_sha256"]
    require(set(files) == {path.relative_to(code).as_posix() for path in code.rglob("*.py")}, "frozen plane code set changed")
    for name, expected in files.items():
        path = checked(code / Path(name), expected, code)
        if copy_to is not None:
            relative = path.relative_to(code)
            target = copy_to / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            copyfile(path, target)
            checked(target, expected, copy_to)


def stage_code(root, work, manifest):
    code = work / "CodeRoot"
    code.mkdir()
    validate_code(root / "CodeRoot", manifest, code)
    tools = work / "Tools"
    tools.mkdir()
    for name in NATIVE_TOOLS:
        copyfile(root / "Tools" / name, tools / name)
    for name in ("CodeManifest.json", "SourceLock.json"):
        copyfile(root / name, work / name)
    sys.path[:0] = list(map(str, (tools, code / "re/tooling/sw2026", code / "src", code)))
    return code


def build(work, code, request, prediction):
    from InspectGeneratedReferencePlane import predict

    require(predict(request, prediction["edit_distance_m"]) == prediction["native_observer_prediction"],
            "independent fit-free prediction disagrees")
    request_sha = freeze_json(work / "Request.json", request)
    prediction_sha = freeze_json(work / "Expected.json", prediction)
    results = []
    for index in range(2):
        run = subprocess.run([sys.executable, "-I", "-B", str(code / BUILD_PROCESS)], input=(work / "Request.json").read_bytes(),
                             cwd=code, capture_output=True, timeout=150)
        (work / f"Build{index}.stderr").write_bytes(run.stderr)
        require(run.returncode == 0, "the guarded plane writer failed")
        results.append(json.loads(run.stdout))
    first, second = results
    require(first == second and first["input_runtime_file_access_attempts"] == 0 and all(row["passed"] for row in first["streams"].values()),
            "guarded plane construction or stream proof differs")
    data = b64decode(first["native"].pop("artifact_base64"), validate=True)
    require(len(data) == first["native"]["bytes"], "generated offset-plane length differs")
    name = request["document"]["name"] + ".SLDPRT"
    for folder in ("FrozenGenerated", "GeneratedInput"):
        output = work / folder
        output.mkdir()
        (output / name).write_bytes(data)
        checked(output / name, first["native"]["sha256"], work)
    proof_sha = freeze_json(work / "GuardedBuild.json", first)
    frozen = {"case_sha256": digest(work / "Case.json"), "code_manifest_sha256": digest(work / "CodeManifest.json"),
              "request_sha256": request_sha, "prediction_sha256": prediction_sha, "guarded_build_sha256": proof_sha,
              "generated_sha256": first["native"]["sha256"], "guarded_builds": 2, "runtime_input_reads": 0,
              "native_sources_read": 0}
    return first["native"], frozen, freeze_json(work / "GenerationFreeze.json", frozen)


def original_source(source_packet, slot, lock):
    sys.path.insert(0, str(source_packet.parent / "Tools"))
    try:
        from ReferencePlaneSourcePhase import case_inputs, private_root, verify as verify_source

        packet = verify_source(source_packet, SOURCE_PACKET_SHA256)
        case = case_inputs(source_packet, packet, SOURCE_PACKET_SHA256, slot)
        source_root = private_root(packet, SOURCE_PACKET_SHA256, slot)
    finally:
        sys.path.pop(0)
    record, = [row for row in lock["records"] if row["case_id"] == slot and row["phase"] == "lock"]
    require(record["heldout_source_locked"], "expected the original locked plane source")
    return case, source_root, record


def inspect_packet(work, sha, phase):
    path = checked(work / "PairedTrial.json", sha, work)
    observer = work / "Tools" / "InspectPairedReferencePlane.py"
    return subprocess.run([sys.executable, "-B", str(observer), phase, str(path), "--packet-sha256", sha],
                          stdout=sys.stdout, stderr=sys.stderr).returncode


def prepare(root, work, slot, source_packet, method, recipe, manifest, lock):
    code = stage_code(root, work, manifest)
    case, source_root, record = original_source(source_packet, slot, lock)
    from ReferencePlaneSourceRecipe import source_prediction, source_request

    case_sha = freeze_json(work / "Case.json", case)
    request = source_request(case, work / "GeneratedInput", heldout=True)
    prediction = source_prediction(case, heldout=True)
    generated, frozen, freeze_sha = build(work, code, request, prediction)
    original = attest(source_root / "SavedAuthor.json", record["private_saved_snapshot_sha256"])
    require(original["case"] == case, "actual native observations differ from the selected source")
    from RunSealedNestedSourcePhase import value_hash
    from ReferencePlaneSourcePhase import artifact_manifest, assert_saved

    name = case["name"] + ".SLDPRT"
    related = {"source": source_root / "Native" / name, "edited": source_root / "Native" / (case["name"] + "Edited.SLDPRT")}
    saved = original["result"]["saved_files"]
    assert_saved(saved, related)
    require(value_hash(artifact_manifest(saved)) == record["native_artifact_manifest_sha256"], "original native source files changed")
    controls = work / "Controls"
    controls.mkdir()
    copyfile(related["source"], controls / name)
    checked(controls / name, saved["source"]["sha256"], controls)
    checked(source_packet.parent / "ApiMetadata.json", method["api_metadata_sha256"], source_packet.parent)
    copyfile(source_packet.parent / "ApiMetadata.json", work / "ApiMetadata.json")
    expected = prediction["native_observer_prediction"]
    job = {"schema": NATIVE_SCHEMA, "state": "frozen", "execution_enabled": True, "mode": "heldout", "slot": slot,
           "writer_revision": recipe["frozen_code"]["writer_revision"], "oracle_sha256": ORACLE, "source_lock_sha256": SOURCE_LOCK_SHA256,
           "code_manifest_sha256": method["code_manifest_sha256"], "tool_hashes": {name: method["tool_hashes"][name] for name in NATIVE_TOOLS},
           "api_metadata_sha256": method["api_metadata_sha256"], "case_sha256": case_sha, "request_sha256": frozen["request_sha256"],
           "prediction_sha256": frozen["prediction_sha256"], "generation_freeze_sha256": freeze_sha, "guest_root": str(work),
           "control": {"filename": name, "sha256": saved["source"]["sha256"], "bytes": saved["source"]["bytes"], "prediction": expected},
           "generated": {"filename": name, "sha256": generated["sha256"], "bytes": generated["bytes"],
                         "prediction": expected, "edit_distance_m": prediction["edit_distance_m"]},
           "native_acceptance": False, "heldout_inputs_read": 1, "host_private_payloads_read": 0}
    job_sha = freeze_json(work / "PairedTrial.json", job)
    freeze_json(work / "OriginalCustody.json", {role: {"path": str(path), "sha256": saved[role]["sha256"]} for role, path in related.items()})
    require(inspect_packet(work, job_sha, "verify") == 0, "guest-local plane comparison custody did not verify")
    return {"request_sha256": frozen["request_sha256"], "prediction_sha256": frozen["prediction_sha256"],
            "build_manifest_sha256": freeze_sha, "private_observation_sha256": job_sha}


def measure(work, sha):
    status = inspect_packet(work, sha, "run")
    terminal = work / "Inspection" / "PairedReferencePlaneResults.json"
    evidence = read(terminal)
    require(evidence["packet_sha256"] == sha and evidence["heldout_inputs_read"] == 1, "unexpected private native result")
    originals = read(work / "OriginalCustody.json")
    require(all(digest(Path(row["path"])) == row["sha256"] for row in originals.values()), "original native comparison source changed")
    require(inspect_packet(work, sha, "verify") == 0, "guest-local plane comparison custody changed")
    success = status == 0 and evidence["passed"] and evidence["source_generated_paired_acceptance"]
    success = success and evidence["controls_healthy"] and evidence["immutable_inputs_unchanged"] and evidence["distinct_processes"] == 4
    return bool(success), digest(terminal)


def main():
    parser = argparse.ArgumentParser(description="Generate and compare original offset-plane models in the Windows guest")
    parser.add_argument("phase", choices=("verify", "prepare", "measure"))
    parser.add_argument("root", type=Path)
    parser.add_argument("--method-sha256", required=True)
    parser.add_argument("--slot", choices=SLOTS)
    parser.add_argument("--source-packet", type=Path)
    parser.add_argument("--job-sha256")
    args = parser.parse_args()
    root = args.root.resolve(strict=True)
    method, recipe, manifest, lock = verify(root, args.method_sha256)
    if args.phase == "verify":
        validate_code(root / "CodeRoot", manifest)
        print(json.dumps({"passed": True, "stage": "verified", "code_lock_sha256": args.method_sha256}))
        return 0
    require(os.name == "nt" and args.slot in SLOTS, "original plane preparation and observations stay in the Windows guest")
    base = Path(recipe["guest_private_base"])
    require(base.is_absolute() and re.fullmatch(r"[A-Za-z]:", base.drive) and ".." not in base.parts, "choose a guest-local private evaluation directory")
    work = base / args.slot / "T01"
    if args.phase == "prepare":
        work.mkdir(parents=True)
    else:
        require(work.is_dir(), "the original source has no prepared guest-local packet")
    phase = "build" if args.phase == "prepare" else "qualify"
    public = root / "Progress" / args.slot / "T01" / phase
    public.mkdir(parents=True)
    state = {"schema": SCHEMA, "slot": args.slot, "attempt": "T01", "phase": phase, "stage": "running",
             "started_at": time.time(), "passed": False, "source_lock_sha256": SOURCE_LOCK_SHA256,
             "code_lock_sha256": args.method_sha256, "source_manifest_sha256": method["code_manifest_sha256"]}
    path = public / "Record.json"
    write_json(path, state)
    with (work / (args.phase + "Console.log")).open("x", encoding="utf-8") as log, redirect_stdout(log), redirect_stderr(log):
        try:
            if args.phase == "prepare":
                state.update(prepare(root, work, args.slot, args.source_packet.resolve(strict=True), method, recipe, manifest, lock))
                state["passed"] = True
            else:
                passed, identity = measure(work, args.job_sha256)
                validate_code(work / "CodeRoot", manifest)
                state.update(passed=passed, private_observation_sha256=identity)
                if not passed:
                    state["failure_code"] = "native_comparison_failed"
        except Exception:
            traceback.print_exc()
            state["failure_code"] = "phase_exception"
    state.update(stage="passed" if state["passed"] else "failed", finished_at=time.time())
    require(set(state) <= set(recipe["execution_rules"]["public_progress_fields"]), "unsafe public offset-plane result fields")
    write_json(path, state)
    print(json.dumps(state, sort_keys=True))
    return 0 if state["passed"] else 3


if __name__ == "__main__":
    try:
        status = main()
    except Exception:
        print(json.dumps({"passed": False, "failure_code": "invalid_method_or_stage"}))
        status = 3
    raise SystemExit(status)
