from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from base64 import b64decode
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from AuthorCurves import digest, require, write_json
from FreezeSealedNestedEvaluation import SCHEMA, WRITER_REVISION
from InspectSealedNestedAssembly import measure
from NestedAssemblySourcePlan import checked
from RunSealedNestedSourcePhase import opaque_identity, value_hash
from SealedNestedAssemblyPlan import source_prediction, source_request, source_semantics
from SealedNestedEvaluationState import load_build, prior_phase, private_trial, source_snapshot, verify


PHASES = ("before", "build", "generated", "reopen", "after", "qualify")
PUBLIC_KEYS = {"stage", "progress_at", "identity", "finished_at", "passed", "private_record_sha256", "code_lock_sha256", "build_lock_sha256",
               "request_sha256", "prediction_sha256", "generated_artifact_manifest_sha256", "saved_artifact_manifest_sha256", "qualified", "private_console_sha256"}


def builder_process(code_root, request, directory):
    directory.mkdir(exist_ok=False)
    environment = os.environ.copy()
    environment.update(PYTHONDONTWRITEBYTECODE="1", PYTHONNOUSERSITE="1")
    command = [sys.executable, "-B", str(code_root / "re/tooling/sw2026/NestedAssemblyBundleProcess.py"), str(code_root)]
    result = subprocess.run(command, input=json.dumps(request, allow_nan=False).encode(), capture_output=True, timeout=180,
                            cwd=code_root, env=environment)
    (directory / "Stdout.json").write_bytes(result.stdout)
    (directory / "Stderr.log").write_bytes(result.stderr)
    require(result.returncode == 0 and not result.stderr, "the frozen guarded writer failed in its separate private process")
    report = json.loads(result.stdout)
    require(report["schema"] == "kit.sw2026.generated-nested-assembly-bundle.v1" and report["root"] == request["root"] and
            report["input_runtime_file_access_attempts"] == 0 and report["native_acceptance"] is False and
            set(report["documents"]) == {row["id"] for row in request["definitions"]}, "the guarded writer did not generate the complete sealed request")
    return report


def probe_case():
    return {"name": "DisclosedGuestProbe", "split": "discovery", "parts": [{"name": "ProbePlate", "depth_m": 0.00731}],
            "assemblies": [{"name": "ProbeModule", "occurrences": [{"target": "ProbePlate", "placement": {
                "axis": "x", "angle_deg": 17.0, "translation_m": [0.013, -0.017, 0.021]}}]},
                           {"name": "ProbeRoot", "occurrences": [{"target": "ProbeModule", "placement": {
                               "axis": "y", "angle_deg": -23.0, "translation_m": [0.071, 0.029, -0.033]}}]}],
            "edit": {"part": "ProbePlate", "depth_m": 0.01019}}


def build(packet_path, packet, source_lock, source_phase, private, slot, sha, publish):
    code_lock = private / "CodeLocked.json"
    require(not code_lock.exists(), "a sealed request can only be exposed under a new immutable code lock")
    write_json(code_lock, {"packet_sha256": sha, "code_manifest_sha256": packet["code_manifest_sha256"], "tools_sha256": packet["tools_sha256"],
                           "writer_revision": WRITER_REVISION, "source_lock_sha256": packet["source_lock_sha256"], "locked_at": time.time()})
    publish(stage="code_locked", code_lock_sha256=digest(code_lock))
    code_root = packet_path.parent / "CodeRoot"
    sys.path.insert(0, str(code_root))
    synthetic = source_request(probe_case(), private / "ProbeInput")
    builder_process(code_root, synthetic, private / "EnvironmentProbe")
    exposure = time.time()
    case, snapshot = source_snapshot(packet, source_lock, source_phase, slot)
    bundle = source_request(case, private / "GeneratedInput")
    prediction = source_prediction(case)
    source_semantics(case, snapshot, prediction)
    request_path, expected_path = private / "Request.json", private / "Expected.json"
    write_json(request_path, bundle)
    write_json(expected_path, prediction)
    request_lock = private / "RequestLock.json"
    write_json(request_lock, {"packet_sha256": sha, "code_lock_sha256": digest(code_lock), "request_sha256": digest(request_path),
                              "prediction_sha256": digest(expected_path), "source_specification_sha256": value_hash(case),
                              "source_native_manifest_sha256": value_hash(snapshot["artifact_manifest"]), "source_exposed_at": exposure, "locked_at": time.time()})
    publish(stage="request_locked", request_sha256=digest(request_path), prediction_sha256=digest(expected_path))
    started = time.time()
    publish(stage="guarded_build")
    first = builder_process(code_root, bundle, private / "BuildOne")
    second = builder_process(code_root, bundle, private / "BuildTwo")
    require(first == second, "two private frozen writer processes produced different generated records or bytes")
    frozen = private / "FrozenGenerated"
    frozen.mkdir(exist_ok=False)
    files = {}
    for name, row in first["documents"].items():
        filename = prediction["definitions"][name]["file"]
        path = frozen / filename
        path.write_bytes(b64decode(row["blob"], validate=True))
        require(path.stat().st_size == row["bytes"] and digest(path) == row["sha256"], "sealed generated bytes differ from their guarded result")
        files[name] = {"file": filename, "sha256": row["sha256"], "bytes": row["bytes"]}
    code_state = json.loads(code_lock.read_bytes())
    request_state = json.loads(request_lock.read_bytes())
    require(code_state["locked_at"] <= exposure <= request_state["locked_at"] <= started and digest(request_path) == request_state["request_sha256"] and
            digest(expected_path) == request_state["prediction_sha256"], "source-before-execution request lock or prediction changed")
    manifest = {row["file"]: {"sha256": row["sha256"], "bytes": row["bytes"]} for row in files.values()}
    lock = {"packet_sha256": sha, "writer_revision": WRITER_REVISION, "code_lock_sha256": digest(code_lock), "request_lock_sha256": digest(request_lock),
            "request_sha256": digest(request_path), "prediction_sha256": digest(expected_path), "runtime_file_read_attempts": 0,
            "two_process_byte_identity": True, "source_before_execution_verified": True, "files": files,
            "generated_artifact_manifest_sha256": value_hash(manifest), "build_started_at": started, "build_finished_at": time.time()}
    write_json(private / "BuildLock.json", lock)
    return {"build_lock_sha256": digest(private / "BuildLock.json"), "request_sha256": lock["request_sha256"],
            "prediction_sha256": lock["prediction_sha256"], "generated_artifact_manifest_sha256": value_hash(manifest)}


def control(packet, output, raw, publish):
    from ReplayNestedAssemblyReopen import inspect_case, source_cases

    case, paths, prior = source_cases(Path(packet["disclosed_results_guest"]))["N02MixedRepeated"]
    publish(stage="native_control")
    result = inspect_case(case, paths, prior, output)
    write_json(raw, result)
    require(result["passed"] is True and result["source_files_unchanged"] is True, "the disclosed nested native bracket failed")
    return {"identity": opaque_identity(result["oracle_identity"])}


def qualify(packet, source_lock, source_phase, private, public, sha, slot, trial, attempt):
    rows = [prior_phase(public, phase, attempt if phase in ("reopen", "after") else 1, sha, slot, trial, identity=True)
            for phase in ("before", "generated", "reopen", "after")]
    require(len({row["identity"]["process_creation_filetime"] for row in rows}) == 4 and
            all(first["finished_at"] <= second["started_at"] for first, second in zip(rows, rows[1:])), "sealed native phases are not distinct and bracketed")
    build_state = prior_phase(public, "build", 1, sha, slot, trial)
    require(rows[0]["finished_at"] <= build_state["started_at"] <= build_state["finished_at"] <= rows[1]["started_at"], "the sealed build is outside its native brackets")
    for row in [*rows, build_state]:
        checked(private / row["phase"] / str(row["attempt"]) / "Private.json", row["private_record_sha256"], private)
    lock, _, _ = load_build(private, public, sha, slot, trial)
    request = json.loads(checked(private / "RequestLock.json", lock["request_lock_sha256"], private).read_bytes())
    code = json.loads(checked(private / "CodeLocked.json", lock["code_lock_sha256"], private).read_bytes())
    require(lock["source_before_execution_verified"] is True and code["locked_at"] <= request["source_exposed_at"] <= request["locked_at"] <= lock["build_started_at"],
            "the sealed writer was not frozen before source exposure and execution")
    require(rows[1]["saved_artifact_manifest_sha256"] == rows[2]["saved_artifact_manifest_sha256"], "saved sealed dependencies changed across fresh reopen")
    case, snapshot = source_snapshot(packet, source_lock, source_phase, slot)
    require(value_hash(case) == request["source_specification_sha256"] and value_hash(snapshot["artifact_manifest"]) == request["source_native_manifest_sha256"],
            "the locked source specification or native siblings changed during evaluation")
    result = {"qualified": True, "source_before_execution_verified": True, "controls_healthy": True, "distinct_processes": 4,
              "saved_artifact_manifest_sha256": rows[2]["saved_artifact_manifest_sha256"], "generated_artifact_manifest_sha256": lock["generated_artifact_manifest_sha256"],
              "source_inputs_immutable": True, "host_heldout_payloads_read": 0, "heldout_results_remain_sealed": True,
              "phase_record_sha256": [row["private_record_sha256"] for row in rows]}
    return result


def run(args, packet_path, packet, source_lock, source_phase):
    require(os.name == "nt", "sealed evaluation runs only in the Windows guest")
    require(re.fullmatch(r"[A-Za-z0-9]{1,16}", args.trial) and 1 <= args.attempt <= 99 and
            (args.attempt == 1 or args.phase in ("reopen", "after", "qualify")), "invalid sealed evaluation trial or attempt")
    public = packet_path.parent / "Progress" / f"Slot{args.slot:02d}" / args.trial
    output = public / args.phase / str(args.attempt)
    require(output.resolve().is_relative_to(packet_path.parent), "sealed progress escaped its packet")
    output.mkdir(parents=True, exist_ok=False)
    state = {"schema": SCHEMA, "packet_sha256": args.packet_sha256, "slot": args.slot, "trial": args.trial, "phase": args.phase, "attempt": args.attempt,
             "stage": "verifying", "passed": False, "started_at": time.time()}

    def publish(**changes):
        require(set(changes) <= PUBLIC_KEYS, "a private native detail cannot be published")
        state.update(changes)
        write_json(output / "Record.json", state)

    publish()
    raw = None
    try:
        private = private_trial(packet, args.packet_sha256, args.slot, args.trial)
        private_run = private / args.phase / str(args.attempt)
        private_run.mkdir(parents=True, exist_ok=False)
        raw = private_run / "Private.json"
        console = private_run / "Console.log"
        with console.open("w", encoding="utf-8") as stream, redirect_stdout(stream), redirect_stderr(stream):
            if args.phase in ("before", "after"):
                result = control(packet, private_run, raw, publish)
            elif args.phase == "build":
                prior_phase(public, "before", 1, args.packet_sha256, args.slot, args.trial, identity=True)
                result = build(packet_path, packet, source_lock, source_phase, private, args.slot, args.packet_sha256, publish)
            elif args.phase == "qualify":
                result = qualify(packet, source_lock, source_phase, private, public, args.packet_sha256, args.slot, args.trial, args.attempt)
                write_json(raw, result)
                result = {key: result[key] for key in ("qualified", "generated_artifact_manifest_sha256", "saved_artifact_manifest_sha256")}
            else:
                lock, bundle, prediction = load_build(private, public, args.packet_sha256, args.slot, args.trial)
                previous = None
                if args.phase == "reopen":
                    previous = prior_phase(public, "generated", 1, args.packet_sha256, args.slot, args.trial, identity=True)
                result = measure(args.phase, private, lock["files"], bundle, prediction, raw, publish, previous)
            if not raw.exists():
                write_json(raw, result)
            verify(packet_path, args.packet_sha256)
        publish(**result, stage="passed", passed=True, finished_at=time.time(), private_record_sha256=digest(raw), private_console_sha256=digest(console))
    except Exception as error:
        if raw is not None:
            failure = raw if not raw.exists() else raw.with_name("Failure.json")
            write_json(failure, {"error": repr(error), "finished_at": time.time()})
        publish(stage="failed", passed=False, finished_at=time.time())
    return {key: state[key] for key in ("slot", "phase", "stage", "passed")}


def summarize(args, packet_path, packet):
    slots, native = [], []
    for slot in (1, 2):
        public = packet_path.parent / "Progress" / f"Slot{slot:02d}" / args.trial
        phases = [prior_phase(public, phase, args.attempt if phase in ("reopen", "after", "qualify") else 1,
                              args.packet_sha256, slot, args.trial, identity=phase in ("before", "generated", "reopen", "after")) for phase in PHASES]
        require(phases[-1]["qualified"] is True and all(first["finished_at"] <= second["started_at"] for first, second in zip(phases, phases[1:])),
                "the sealed slot is incomplete or not ordered")
        slot_phases = []
        for row in phases:
            file = public / row["phase"] / str(row["attempt"]) / "Record.json"
            item = {key: row[key] for key in ("phase", "attempt", "started_at", "finished_at", "passed", "private_record_sha256")}
            item["public_record_sha256"] = digest(file)
            if "identity" in row:
                item["identity"] = row["identity"]
                native.append(row)
            slot_phases.append(item)
        slots.append({"slot": slot, "qualified": True, "phases": slot_phases,
                      "generated_artifact_manifest_sha256": phases[-1]["generated_artifact_manifest_sha256"],
                      "saved_artifact_manifest_sha256": phases[-1]["saved_artifact_manifest_sha256"]})
    native.sort(key=lambda row: row["started_at"])
    require(len(native) == len({row["identity"]["process_creation_filetime"] for row in native}) == 8 and
            all(first["finished_at"] <= second["started_at"] for first, second in zip(native, native[1:])), "sealed oracle identities are reused or overlap")
    result = {"schema": "kit.sw2026.sealed-nested-writer-public-result.v1", "packet_sha256": args.packet_sha256,
              "writer_revision": WRITER_REVISION, "code_manifest_sha256": packet["code_manifest_sha256"], "source_lock_sha256": packet["source_lock_sha256"],
              "tools_sha256": packet["tools_sha256"], "heldout_profiles_native_passed": True, "controls_healthy": True,
              "distinct_native_processes": 8, "source_before_execution_verified_by_frozen_guest": True,
              "host_heldout_payloads_read": 0, "heldout_results_remain_sealed": True, "native_acceptance": False,
              "public_adapter_writer_qualified": False, "slots": slots}
    file = packet_path.parent / "Progress/EvaluationResults.json"
    if file.exists():
        require(json.loads(file.read_bytes()) == result, "the immutable sealed public result differs")
    else:
        write_json(file, result)
    return {"passed": True, "slots_qualified": 2, "distinct_native_processes": 8, "public_result_sha256": digest(file)}


def main():
    parser = argparse.ArgumentParser(description="Evaluate a frozen nested writer against one opaque guest-only source slot without publishing private designs")
    modes = parser.add_subparsers(dest="mode", required=True)
    for name in ("verify", "run", "summarize"):
        command = modes.add_parser(name)
        command.add_argument("packet", type=Path)
        command.add_argument("--packet-sha256", required=True)
        if name == "run":
            command.add_argument("slot", type=int, choices=(1, 2))
            command.add_argument("trial")
            command.add_argument("phase", choices=PHASES)
            command.add_argument("--attempt", type=int, default=1)
        if name == "summarize":
            command.add_argument("--trial", default="T01")
            command.add_argument("--attempt", type=int, default=1)
    args = parser.parse_args()
    try:
        path = args.packet.resolve(strict=True)
        packet, source_lock, source_phase = verify(path, args.packet_sha256)
        if args.mode == "verify":
            print(json.dumps({"verified_packet": args.packet_sha256, "host_heldout_payloads_read": 0}))
            return 0
        result = summarize(args, path, packet) if args.mode == "summarize" else run(args, path, packet, source_lock, source_phase)
    except Exception:
        result = {"stage": "failed", "passed": False}
    print(json.dumps(result, sort_keys=True))
    return int(not result["passed"])


if __name__ == "__main__":
    raise SystemExit(main())
