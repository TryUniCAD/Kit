from argparse import ArgumentParser
import json
import os
from pathlib import Path, PureWindowsPath
import sys


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from RunSweepSources import PROCESS_COUNT, case_paths
from SealSweepSources import guest_private_path, passed_lock, pinned_json, verify_records
from SweepColdCompare import projection
from SweepColdPacket import COMMON_FILES, LOCK, PRIVATE_SCHEMA, SEALED_CANDIDATES, create, verify
from SweepEvaluationGate import SLOTS, check_native_controls, exact_process, verified_file, verify_result
from SweepEvaluationPacket import METHOD, extract_writer, guest_base, produce, read_method, staged_method, write_files
from SweepModel import require
from SweepPacket import BUILD, ORACLE, digest, job_bytes, verify as verify_source, write_new


def stage(method, pin):
    require(os.name == "nt" and sys.version_info[:2] == (3, 12), "stage only in root-owned Windows CPython 3.12")
    job, _ = read_method(method, pin)
    base = guest_private_path(Path(guest_base(job)))
    require(not base.exists(), "evaluation base already exists")
    data = {name: verified_file(method.parent / name, row["sha256"]) for name, row in job["files"].items()}
    target = base / "Method"
    write_files(target, data | {METHOD: verified_file(method, pin)})
    read_method(target / METHOD, pin)
    return {"method_sha256": pin, "native_processes_started": 0, "protected_inputs_read": 0}


def original_metadata(source, redacted, base):
    source = guest_private_path(source)
    require(not source.is_relative_to(base) and not base.is_relative_to(source), "evaluation overlaps independent original custody")
    packet, capture = source / "Packet", source / "Capture"
    require(all(guest_private_path(path).is_dir() for path in (packet, capture)), "original source locations are not canonical")
    job, spec, _ = verify_source(packet / "SourceJob.json", redacted["source_job_sha256"], permit_private=True)
    source_pin = redacted["source_lock_sha256"]
    lock = pinned_json(capture / "SourceLock.json", source_pin)
    passed_lock(lock, job, redacted["source_job_sha256"])
    require(spec["cohort"] == "heldout" and Path(job["guest_packet"]) == packet and Path(job["guest_capture"]) == capture
            and all(redacted[key] == job[key] for key in ("source_revision", "source_tree", "method_job_sha256", "disclosed_lock_sha256"))
            and all(redacted[key] == lock[key] for key in ("spec_sha256", "prediction_sha256"))
            and redacted["registered_api_sha256"] == lock["api_sha256"], "original job differs from the pre-writer record")
    for role, pin in redacted["controls"].items():
        require(lock["controls"][role]["receipt_sha256"] == pin, "pre-writer bracket digest differs")
    for row, alias in zip(lock["sources"], redacted["slots"], strict=True):
        require(alias["artifact_sha256"] == row["artifact_sha256"]
                and alias["phase_receipt_sha256"] == [phase["receipt_sha256"] for phase in row["phases"]],
                "pre-writer original/edit receipt lineage differs")
    return packet, capture, spec, lock


def comparison(capture, spec, lock):
    verify_records(lock, capture, spec)
    rows = []
    processes = set()
    for phase in lock["controls"].values():
        record = pinned_json(capture / phase["phase"] / "Record.json", phase["receipt_sha256"])
        processes.add(exact_process(record))
    for source, case in zip(lock["sources"], spec["cases"], strict=True):
        folder, _, _ = case_paths(capture, source["slot"], case)
        states, pins = {}, {}
        for row in source["phases"]:
            phase = row["phase"]
            record = pinned_json(folder / phase / "Record.json", row["receipt_sha256"])
            require(record["job"] == {"phase": phase, "case": case} and record["first_failure"] is None
                    and not (record["dialogs"] or record["cleanup_errors"] or record.get("controller_diagnostics"))
                    and len(record["checks"]) == row["checks"] == row["checks_passed"]
                    and all(check["passed"] for check in record["checks"]), "independent native source phase is incomplete")
            processes.add(exact_process(record))
            if phase.endswith("-edit"):
                continue
            role = "original" if phase == "author" else phase.split("-")[0]
            states[role] = projection(record["authored" if phase == "author" else "reopened"])
            pins[role] = row["receipt_sha256"]
        rows.append({"slot": source["slot"], "native_source_sha256": source["artifact_sha256"],
                     "source_receipt_sha256": pins, "states": states})
    require(len(processes) == PROCESS_COUNT, "independent sweep source launches are not distinct")
    return {"source_lock_sha256": digest(capture / "SourceLock.json"), "cases": rows}


def generate(method, pin, job, base, spec):
    writer = base / "Writer"
    root = base / "Generated"
    require(all(not (base / name).exists() for name in ("Writer", "Generated", "Packet", "Records")),
            "protected generation needs a fresh method destination")
    extract_writer(verified_file(method.parent / "Writer.zip", job["files"]["Writer.zip"]["sha256"]), writer, job["writer_research"])
    output, proofs = {}, []
    for relative, case in zip(SEALED_CANDIDATES, spec["cases"], strict=True):
        request = {key: case[key] for key in ("name", "section_radius_m", "path_radius_m")}
        request.update(density_kg_m3=spec["density_kg_m3"], self_locator=str(base / "Packet" / relative))
        output[relative], proof = produce(writer, request)
        proofs.append({"slot": case["name"], **proof})
    require(len({proof["candidate_sha256"] for proof in proofs}) == len(SLOTS), "distinct source models produced the same candidate")
    freeze = {"schema": "kit.sw2026.standard-sweep-heldout-generation.v1", "method_sha256": pin,
              "prewriter_lock_sha256": LOCK, "writer_revision": job["writer_revision"], "sdk_tree": job["sdk_tree"],
              "writer_sha256": job["files"]["Writer.zip"]["sha256"], "candidates": proofs, "native_processes_started": 0}
    write_files(root, output | {"Generation.json": job_bytes(freeze)})
    return output, digest(root / "Generation.json")


def prepare(method, pin, source):
    job, redacted, base = staged_method(method, pin)
    source_packet, source_capture, spec, lock = original_metadata(source, redacted, base)
    output, generation_pin = generate(method, pin, job, base, spec)
    paired = comparison(source_capture, spec, lock)
    require(paired["source_lock_sha256"] == redacted["source_lock_sha256"], "source changed after the candidate freeze")
    data = {name: verified_file(method.parent / name, job["files"][name]["sha256"])
            for name in COMMON_FILES - {"Spec.json", "Predictions.json"}}
    data.update(output)
    data.update({"Spec.json": verified_file(source_packet / "Spec.json", redacted["spec_sha256"]),
                 "Predictions.json": verified_file(source_packet / "Predictions.json", redacted["prediction_sha256"]),
                 "ProtectedComparison.json": job_bytes(paired)})
    packet = base / "Packet"
    native = {"schema": PRIVATE_SCHEMA, "cohort": "heldout", "writer_outputs": len(SLOTS),
              "oracle_build": BUILD, "oracle_sha256": ORACLE, "writer_revision": job["writer_revision"],
              "sdk_tree": job["sdk_tree"], "prewriter_lock_sha256": LOCK, "method_sha256": pin,
              "source_lock_sha256": redacted["source_lock_sha256"], "spec_sha256": redacted["spec_sha256"],
              "registered_api_sha256": redacted["registered_api_sha256"], "generation_sha256": generation_pin,
              "guest_packet": str(packet), "guest_capture": str(base / "Records"), "guest_checkout": job["guest_checkout"],
              "candidates": {name: str(packet / name) for name in SEALED_CANDIDATES}}
    job_pin = create(packet, native, data)
    return {"method_sha256": pin, "generation_sha256": generation_pin, "job_sha256": job_pin,
            "slots": len(SLOTS), "native_processes_started": 0}


def publication_proof(capture, packet, result, paired):
    processes = check_native_controls(result, packet, capture)
    rows = []
    for case, expected in zip(result["cases"], paired["cases"], strict=True):
        slot, paths = case["slot"], case["candidate_sha256"]
        folder = capture / SLOTS[slot]
        require(digest(packet / SEALED_CANDIDATES[slot]) == paths["original"], "candidate changed after oracle")
        records = []
        for row in case["phases"]:
            phase = row["phase"]
            record = pinned_json(folder / phase / "Record.json", row["receipt_sha256"])
            processes.add(exact_process(record))
            require(record["passed"] is record["source_immutable"] is True and record["first_failure"] is None
                    and not (record["dialogs"] or record["cleanup_errors"] or record.get("controller_diagnostics"))
                    and record["native_sha256"] == row["artifact_sha256"] and record["native_bytes"] == row["artifact_bytes"]
                    and record["open_status"] == {"opened": True, "errors": 0, "warnings": 0}
                    and len(record["checks"]) == row["checks_passed"] and all(check["passed"] for check in record["checks"]),
                    "native candidate receipt does not bind a clean open and lifecycle")
            if phase == "candidate-open":
                require(record["cold_ordered_tree"] == expected["states"]["original"]["tree"]
                        and record["cold_solid_count"] == 1 and record["cold_diagnostics"] == 0,
                        "candidate cold tree, body or diagnostics differ")
            else:
                role, _, action = phase.partition("-")
                part = folder / (SLOTS[slot] + role.title() + "Edit.SLDPRT")
                require(digest(part) == paths[role] and record.get("native_save_status") == ([True, 0, 0] if action == "edit" else None),
                        "native candidate edit did not persist intact")
            records.append({"phase": phase, "receipt_sha256": row["receipt_sha256"], "checks": row["checks_passed"]})
        rows.append({"slot": SLOTS[slot], "candidate_sha256": paths, "source_sha256": case["independent_source_sha256"],
                     "phases": records, "paired_numeric_checks": case["paired_numeric_checks"], "passed": True})
    require(len(processes) == result["started_processes"] == PROCESS_COUNT, "native candidate process identities are not distinct")
    return rows


def publish(method, pin, source, native_pin, result_pin, generation_pin, output):
    job, redacted, base = staged_method(method, pin)
    from Swapp import application_pids, owned_process_ids

    share = PureWindowsPath(r"\\Mac\Home\Documents\UniCAD\Oracle121Takeover")
    require(output.is_absolute() and not output.exists() and output.parent.is_dir()
            and PureWindowsPath(output.resolve()).is_relative_to(share), "use a fresh approved share path for the digest-only receipt")
    _, source_capture, source_spec, source_lock = original_metadata(source, redacted, base)
    verify_records(source_lock, source_capture, source_spec)
    packet, capture = base / "Packet", base / "Records"
    native, spec, _ = verify(packet / "SweepJob.json", native_pin, permit_private=True)
    require(native["method_sha256"] == pin and native["generation_sha256"] == generation_pin and spec == source_spec
            and native["source_lock_sha256"] == redacted["source_lock_sha256"] and not application_pids() and not owned_process_ids(),
            "native result does not retain the protected method or the oracle is not idle")
    generation = pinned_json(base / "Generated" / "Generation.json", generation_pin)
    require(generation["method_sha256"] == pin and generation["writer_revision"] == job["writer_revision"]
            and generation["writer_sha256"] == job["files"]["Writer.zip"]["sha256"]
            and generation["prewriter_lock_sha256"] == LOCK and generation["sdk_tree"] == job["sdk_tree"]
            and generation["native_processes_started"] == 0 and len(generation["candidates"]) == len(SLOTS),
            "pre-native model-only freeze differs")
    for slot, proof in enumerate(generation["candidates"]):
        relative = SEALED_CANDIDATES[slot]
        require(proof == {"slot": SLOTS[slot], "candidate_sha256": native["files"][relative]["sha256"],
                          "stream_count": 11, "exact_replays": 3, "blocked_runtime_calls": 0}
                and digest(base / "Generated" / relative) == proof["candidate_sha256"], "guarded generated part changed")
    paired = pinned_json(packet / "ProtectedComparison.json", native["files"]["ProtectedComparison.json"]["sha256"])
    require(paired == comparison(source_capture, source_spec, source_lock), "recorded comparison differs from independent native sources")
    result = json.loads(verified_file(capture / "Result.json", result_pin))
    verify_result(result, native, native_pin, paired)
    rows = publication_proof(capture, packet, result, paired)
    receipt = {"schema": "kit.sw2026.standard-sweep-heldout-proof.v1", "method_sha256": pin,
               "method_revision": job["method_revision"], "writer_revision": job["writer_revision"], "sdk_tree": job["sdk_tree"],
               "oracle_build": BUILD, "oracle_sha256": ORACLE, "prewriter_lock_sha256": LOCK,
               "source_job_sha256": redacted["source_job_sha256"], "source_lock_sha256": redacted["source_lock_sha256"],
               "disclosed_result_sha256": job["disclosed_result_sha256"], "generation_sha256": generation_pin,
               "job_sha256": native_pin, "native_result_sha256": result_pin, "distinct_processes": PROCESS_COUNT,
               "cases": rows, "controls": {key: {"passed": True, "receipt_sha256": value["receipt_sha256"]}
                                             for key, value in result["controls"].items()},
               "blocked_writer_reads": 0, "native_passed": True, "public_sdk_parity": False}
    write_new(output, receipt)
    return {"receipt_sha256": digest(output), "cases_passed": len(rows), "distinct_processes": PROCESS_COUNT}


def main():
    parser = ArgumentParser(description="Prepare and publish a guest-private paired Standard sweep evaluation")
    parser.add_argument("mode", choices=("stage", "prepare", "publish"))
    parser.add_argument("--method", type=Path, required=True)
    parser.add_argument("--method-pin", required=True)
    parser.add_argument("--private-source-root", type=Path)
    parser.add_argument("--job-pin")
    parser.add_argument("--result-pin")
    parser.add_argument("--generation-pin")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        if args.mode == "stage":
            report = stage(args.method, args.method_pin)
        elif args.mode == "prepare":
            report = prepare(args.method, args.method_pin, args.private_source_root)
        else:
            report = publish(args.method, args.method_pin, args.private_source_root,
                             args.job_pin, args.result_pin, args.generation_pin, args.output)
    except Exception as error:
        raise SystemExit(f"{args.mode} refused ({type(error).__name__}); no protected data published") from None
    print(json.dumps(report, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
