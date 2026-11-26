# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import argparse
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import re
import time

from ProbeAcceptance import committed_pin, git
import SourceBossPlan as contract
from SourceBossProbe import (
    DRIVERS,
    PROGRAMS,
    REVISION,
    SPECIFICATION,
    SPECIFICATION_SHA256,
    GitSnapshot,
    candidate_evidence,
    source_geometry,
    source_report,
)
from VerifyWitness import check_process
from WitnessMeasurements import check_controls, check_readback, original_orientations


# Match the exact input to the independent source reopen and rerun every typed candidate check.
def inspect_candidate(directory, manifest_sha, archive_sha, revision):
    root = contract.direct_directory(directory)
    manifest, report = contract.read_object(root / contract.MANIFEST, manifest_sha)
    archive = contract.read_file(root / contract.ARCHIVE, contract.ARCHIVE_LIMIT)
    generated = report["codec_revision"]
    contract.require(
        type(report["schema"]) is int
        and report["schema"] == 1
        and report["qualification"] == "candidate_requires_licensed_target_acceptance"
        and re.fullmatch(r"[0-9a-f]{40}", generated)
        and report["source_capture_revision"] == REVISION
        and report["source_specification_sha256"] == SPECIFICATION_SHA256
        and report["generator_sources"]
        == {
            name: committed_pin(revision, contract.AUTHORING / name)["sha256"]
            for name in PROGRAMS
        },
        "P03 manifest does not bind the verified source generators and discovery specification",
    )
    (selected,) = [
        entry for entry in report["candidates"] if entry["variant"] == "baseline-a"
    ]
    contract.require(
        selected["file"] == contract.ARCHIVE
        and selected["archive_sha256"] == contract.check_digest(archive_sha)
        and contract.pin(archive)
        == {"size_bytes": selected["archive_bytes"], "sha256": archive_sha},
        "P03 baseline archive differs from its independently supplied manifest or digest",
    )
    source, observation = source_case(report)
    snapshot = GitSnapshot(contract.REPO)
    sizes, edges, _, feature_id = source_geometry(snapshot, source)
    contract.require(
        sizes == contract.ORIGINAL_MM,
        "P03 source does not measure the planned baseline",
    )
    spec = snapshot.blob(REVISION, SPECIFICATION)
    contract.require(
        contract.pin(spec)["sha256"] == SPECIFICATION_SHA256,
        "P03 source specification bytes changed",
    )
    tolerances = snapshot.parse_document(spec, SPECIFICATION)["comparison_tolerances"]
    evidence = candidate_evidence(
        source, archive, sizes, edges, observation, tolerances
    )
    original = {
        "file": contract.ARCHIVE,
        "variant": source["variant"],
        "source": source["source"],
        "source_sketch_dimensions": {
            name: source["dimensions"][name]["source"] for name in DRIVERS[:2]
        },
        "source_origin": source["anchor"]["source_origin_coincidence"],
        "source_feature_id": feature_id,
        "source_boss": source["boss"]["source"],
        "source_reopen_observation_sha256": contract.pin(
            json.dumps(observation, sort_keys=True, allow_nan=False).encode()
        )["sha256"],
        **evidence,
    }
    contract.require(
        json.loads(json.dumps(original, allow_nan=False)) == selected,
        "P03 baseline re-read did not reproduce its complete saved typed evidence",
    )
    return (
        archive,
        manifest,
        {
            "input": {"file": contract.ARCHIVE, **contract.pin(archive)},
            "manifest": {"file": contract.MANIFEST, **contract.pin(manifest)},
            "original_generation_revision": generated,
            "verified_program_revision": revision,
            "source_capture_revision": REVISION,
            "source_archive": selected["source"]["sha256"],
            "source_reopen_observation_sha256": selected[
                "source_reopen_observation_sha256"
            ],
            "source_receipt": report["source_receipt"],
        },
    )


# The program's positive XY baseline is joined with the originally pinned SOLIDWORKS receipt.
def source_case(report):
    mapping = source_report()
    receipt = mapping["receipts"]["P03"]
    contract.require(
        receipt == report["source_receipt"],
        "P03 manifest provenance differs from the recorded source receipt",
    )
    (source,) = [
        row
        for row in mapping["cases"]
        if row["recipe"] == "P03" and row["variant"] == "baseline-a"
    ]
    path = receipt["measurements"]["path"]
    snapshots = GitSnapshot(contract.REPO)
    raw = snapshots.blob(REVISION, path)
    contract.require(
        contract.pin(raw)["sha256"] == receipt["measurements"]["sha256"],
        "P03 source reopen observations changed",
    )
    observations = snapshots.parse_document(raw, path)["observations"]["reopened_files"]
    return source, observations[Path(source["source"]["path"]).name]


# Prepare launchers on the licensed host so their absolute paths bind that checkout.
def prepare(directory, output, manifest_sha, archive_sha, build):
    output = output.resolve()
    contract.require(
        not output.is_relative_to(contract.REPO)
        and not output.exists()
        and re.fullmatch(r"[0-9]+(?:\.[0-9]+){2}", build),
        "Use a new private witness directory and specify the exact Fusion build",
    )
    revision = git("rev-parse", "--verify", "HEAD^{commit}").decode().strip()
    pins = {name: committed_pin(revision, path) for name, path in contract.PINS.items()}
    archive, manifest, candidate = inspect_candidate(
        directory, manifest_sha, archive_sha, revision
    )
    fresh = contract.load_helper(contract.PINS["fresh_process"], pins["fresh_process"])
    plan = {
        "schema": 1,
        "scope": contract.SCOPE,
        "prepared_unix_seconds": int(time.time()),
        "source_revision": revision,
        "fusion_version": build,
        "candidate": candidate,
        "pins": pins,
    }
    output.mkdir(mode=0o700)
    inputs = output / "inputs"
    inputs.mkdir(mode=0o700)
    fresh["write_new"](inputs / contract.ARCHIVE, archive)
    fresh["write_new"](inputs / contract.MANIFEST, manifest)
    path = output / "plan.json"
    plan_sha = fresh["write_json"](path, plan)
    for phase in ("a", "b"):
        launcher = fresh["launcher"](
            contract.REPO / contract.PINS["runtime"],
            pins["runtime"]["sha256"],
            path,
            plan_sha,
            phase,
        )
        fresh["write_new"](output / f"phase-{phase}.py", launcher)
    return {
        "status": "prepared_for_licensed_fusion",
        "directory": str(output),
        "plan_sha256": plan_sha,
        "candidate": candidate,
    }


def replay_launch_file(fresh, pins, plan_path, plan_sha, phase, host):
    if host == "licensed_macos":
        return fresh["launcher"](
            contract.REPO / contract.PINS["runtime"],
            pins["runtime"]["sha256"],
            plan_path,
            plan_sha,
            phase,
        )
    message = (
        f"P03 phase {phase} of plan {plan_sha} is offline-only. "
        "Prepare and reseal on the approved licensed macOS host."
    )
    return f"raise RuntimeError({message!r})\n".encode("utf-8")


def prepare_replay(paths, digests, output, build):
    from ApplicationWorkers.ApplicationProtocol import exclusive_rename, sync_directory
    from SourceBossReplayIntake import inspect_replay

    contract.require(not output.is_symlink(), "Use a new private witness directory")
    output = output.resolve()
    contract.require(
        not output.is_relative_to(contract.REPO)
        and not output.exists()
        and re.fullmatch(r"[0-9]+(?:\.[0-9]+){2}", build),
        "Use a new private witness directory and specify the exact Fusion build",
    )
    revision = git("rev-parse", "--verify", "HEAD^{commit}").decode().strip()
    pins = {
        name: committed_pin(revision, relpath)
        for name, relpath in contract.pinned_paths(2).items()
    }
    payloads, candidate = inspect_replay(paths, digests, revision)
    fresh = contract.load_helper(contract.PINS["fresh_process"], pins["fresh_process"])
    host = {"darwin": "licensed_macos", "win32": "offline_windows"}.get(
        sys.platform, "offline_other"
    )
    plan = {
        "schema": 2,
        "scope": contract.SCOPE,
        "preparation_host": host,
        "execution_paths": contract.execution_paths(output / "plan.json") if host == "licensed_macos" else None,
        "prepared_unix_seconds": int(time.time()),
        "source_revision": revision,
        "fusion_version": build,
        "candidate": candidate,
        "pins": pins,
    }
    with TemporaryDirectory(prefix=".kit-p03-plan-", dir=output.parent) as temp:
        staging = Path(temp) / "witness"
        staging.mkdir(mode=0o700)
        inputs = staging / "inputs"
        inputs.mkdir(mode=0o700)
        for role, name in contract.REPLAY_FILES.items():
            fresh["write_new"](inputs / name, payloads[role])
        plan_path = staging / "plan.json"
        plan_sha = fresh["write_json"](plan_path, plan)
        for phase in ("a", "b"):
            launcher = replay_launch_file(fresh, pins, output / "plan.json", plan_sha, phase, host)
            fresh["write_new"](staging / f"phase-{phase}.py", launcher)
        contract.read_plan(plan_path, plan_sha)
        for role, path in paths.items():
            limit = contract.ARCHIVE_LIMIT if role == "input" else contract.METADATA_LIMIT
            contract.require(
                contract.read_file(path, limit) == payloads[role],
                f"P03 replay {role} changed during native plan preparation",
            )
        exclusive_rename(staging, output)
        sync_directory(output.parent)
    return {
        "status": "prepared_for_licensed_fusion" if host == "licensed_macos" else "prepared_p03_custody_offline",
        "directory": str(output),
        "preparation_host": host,
        "plan_sha256": plan_sha,
        "candidate": candidate,
    }


def inspect_prepared_replay(root, plan):
    from SourceBossReplayIntake import inspect_replay

    candidate = plan["candidate"]
    rows = {"input": candidate["input"], "manifest": candidate["manifest"], **candidate["replay_inputs"]}
    paths = {role: root / "inputs" / name for role, name in contract.REPLAY_FILES.items()}
    digests = {role: rows[role]["sha256"] for role in ("input", "manifest", "request", "witness")}
    _, verified = inspect_replay(paths, digests, plan["source_revision"])
    fresh = contract.load_helper(contract.PINS["fresh_process"], plan["pins"]["fresh_process"])
    plan_path = root / "plan.json"
    plan_sha = contract.pin(contract.read_file(plan_path))["sha256"]
    for phase in ("a", "b"):
        expected = replay_launch_file(fresh, plan["pins"], plan_path, plan_sha, phase, plan["preparation_host"])
        contract.require(
            contract.read_file(root / f"phase-{phase}.py") == expected,
            f"Prepared P03 phase {phase} launcher changed",
        )
    return verified

# Validate the retained plan without running native launchers or writing evidence.
def inspect_plan(root, digest):
    root = contract.direct_directory(root)
    plan = contract.read_plan(root / "plan.json", digest)
    revision = plan["source_revision"]
    contract.require(
        plan["pins"]
        == {
            name: committed_pin(revision, path)
            for name, path in contract.pinned_paths(plan["schema"]).items()
        },
        "Retained P03 helpers or control differ from their Git source",
    )
    candidate = plan["candidate"]
    if plan["schema"] == 2:
        verified = inspect_prepared_replay(root, plan)
    else:
        _, _, verified = inspect_candidate(
            root / "inputs",
            candidate["manifest"]["sha256"],
            candidate["input"]["sha256"],
            revision,
        )
    contract.require(
        verified == candidate,
        "P03 retained plan does not match its verified source evidence",
    )
    return plan


# Accept only complete measurements bound to the plan and externally held phase hashes.
def read_phase(root, phase, digest, plan, plan_sha):
    path = contract.direct_directory(root / f"phase-{phase}")
    _, receipt = contract.read_object(path / "receipt.json", digest)
    measurement_sha = receipt["measurements_sha256"]
    _, reading = contract.read_object(path / "measurements.json", measurement_sha)
    fields = {
        "schema": 1,
        "scope": contract.SCOPE,
        "phase": phase,
        "status": "complete",
        "plan_sha256": plan_sha,
    }
    contract.require(
        set(receipt) == {*fields, "measurements_sha256"}
        and all(
            all(row[key] == value for key, value in fields.items())
            and type(row["schema"]) is int
            for row in (receipt, reading)
        )
        and reading["claim"] == "licensed P03 research candidate witness"
        and reading["errors"] == []
        and all(
            reading[key] == plan[key]
            for key in ("source_revision", "pins", "candidate", "fusion_version")
        ),
        f"Retained P03 phase {phase} is incomplete or does not bind the exact plan",
    )
    return reading, measurement_sha


# Recheck both process lifetimes, readbacks and isolated edits from their sealed observations.
def verify(root, plan_sha, phase_a_sha, phase_b_sha):
    root = contract.direct_directory(root)
    plan = inspect_plan(root, plan_sha)
    first, first_measurement_sha = read_phase(root, "a", phase_a_sha, plan, plan_sha)
    second, second_measurement_sha = read_phase(root, "b", phase_b_sha, plan, plan_sha)
    prepared = plan["prepared_unix_seconds"]
    a_process = check_process(first, prepared)
    b_process = check_process(second, prepared)
    restored = first["restored_archive"]
    contract.require(
        restored["file"] == "restored.f3d"
        and second["previous_measurements_sha256"] == first_measurement_sha
        and a_process["pid"] != b_process["pid"]
        and a_process["start_unix_seconds"] < b_process["start_unix_seconds"]
        and int(first["ended_unix_seconds"]) <= b_process["start_unix_seconds"]
        and first["ended_unix_seconds"] <= second["started_unix_seconds"],
        "P03 Phase B does not bind a genuinely fresh process with the exact archived restoration",
    )
    contract.read_pinned(
        root / "phase-a" / restored["file"], restored, contract.ARCHIVE_LIMIT
    )
    shape = contract.load_helper(contract.PINS["shape"], plan["pins"]["shape"])
    measure = contract.load_helper(contract.PINS["measure"], plan["pins"]["measure"])
    outcome = verify_observations(plan, first, second, restored, measure, shape)
    return {
        "status": "verified_licensed_p03_boss_witness",
        "scope": contract.SCOPE,
        "fusion_version": plan["fusion_version"],
        "source_revision": plan["source_revision"],
        "plan_sha256": plan_sha,
        "phase_a_receipt_sha256": phase_a_sha,
        "phase_a_measurements_sha256": first_measurement_sha,
        "phase_a_process": a_process,
        "phase_b_receipt_sha256": phase_b_sha,
        "phase_b_measurements_sha256": second_measurement_sha,
        "phase_b_process": b_process,
        "input_archive_sha256": plan["candidate"]["input"]["sha256"],
        "restored_archive_sha256": restored["sha256"],
        **outcome,
    }


# Compare the native baseline, three independently edited solids and fresh reopened result.
def verify_observations(plan, first, second, restored, measure, shape):
    baseline = contract.ORIGINAL_MM
    orientations = original_orientations(
        first["readback"]["before_recompute"], baseline[:2]
    )
    orientation_record = {str(key): list(value) for key, value in orientations.items()}
    check = measure["check_snapshot"]
    common = vars(contract)
    for phase, pin in ((first, plan["candidate"]["input"]), (second, restored)):
        check_controls(phase, plan["pins"]["control"])
        reading = phase["readback"]
        check_readback(reading, pin)
        before = check(
            reading["before_recompute"], baseline, orientations, shape, common
        )
        after = check(reading["after_recompute"], baseline, orientations, shape, common)
        contract.require(
            before == after == first["initial"] == second["reopened_expressions"]
            and phase["size_orientations"] == orientation_record,
            "P03 native baseline or reopened expressions differ after recompute",
        )
    contract.require(
        set(first["edits"]) == contract.EDITS_MM.keys(),
        "P03 native edit roster differs",
    )
    edits = {}
    for axis, (name, length) in enumerate(contract.EDITS_MM.items()):
        record = first["edits"][name]
        sizes = list(baseline)
        sizes[axis] = length
        expected = first["initial"]
        changed = check(record["edited"], sizes, orientations, shape, common)
        returned = check(record["restored"], baseline, orientations, shape, common)
        contract.require(
            record["requested_mm"] == length
            and record["original_expression"] == expected[name]
            and record["edit_compute_all_return"]
            is record["restore_compute_all_return"]
            is True
            and changed[name] != expected[name]
            and all(
                changed[key] == value for key, value in expected.items() if key != name
            )
            and returned == expected,
            f"P03 independent edit or restoration differs: {name}",
        )
        edits[name] = {
            "volume_mm3": record["edited"]["volume_mm3"],
            "center_of_mass_mm": record["edited"]["center_of_mass_mm"],
        }
    return {
        "healthy_control_count": 4,
        "initial_volume_mm3": first["readback"]["after_recompute"]["volume_mm3"],
        "fresh_reopened_volume_mm3": second["readback"]["after_recompute"][
            "volume_mm3"
        ],
        "edited_bodies": edits,
    }


# Keep preparation, read-only custody inspection and receipt verification distinct.
def main():
    parser = argparse.ArgumentParser(
        description="Prepare or verify one source-derived P03 Fusion witness"
    )
    command = parser.add_subparsers(dest="command", required=True)
    prepare_command = command.add_parser("prepare")
    prepare_command.add_argument("--candidate", type=Path, required=True)
    prepare_command.add_argument("--output", type=Path, required=True)
    prepare_command.add_argument("--manifest-sha256", required=True)
    prepare_command.add_argument("--archive-sha256", required=True)
    prepare_command.add_argument("--fusion-version", required=True)
    replay_command = command.add_parser("prepare-replay")
    replay_command.add_argument("--candidate", type=Path, required=True)
    replay_command.add_argument("--output", type=Path, required=True)
    replay_command.add_argument("--manifest-sha256", required=True)
    replay_command.add_argument("--archive-sha256", required=True)
    replay_command.add_argument("--fusion-version", required=True)
    replay_command.add_argument("--request", type=Path, required=True)
    replay_command.add_argument("--request-sha256", required=True)
    replay_command.add_argument("--source-witness", type=Path, required=True)
    replay_command.add_argument("--source-witness-sha256", required=True)
    replay_command.add_argument("--seed-helper", type=Path, required=True)
    replay_command.add_argument("--snapshot-builder", type=Path, required=True)
    replay_command.add_argument("--snapshot-owners", type=Path, required=True)
    for name in ("inspect-plan", "verify"):
        subparser = command.add_parser(name)
        subparser.add_argument("--witness", type=Path, required=True)
        subparser.add_argument("--plan-sha256", required=True)
        if name == "verify":
            subparser.add_argument("--phase-a-receipt-sha256", required=True)
            subparser.add_argument("--phase-b-receipt-sha256", required=True)
    args = parser.parse_args()
    if args.command == "prepare":
        result = prepare(
            args.candidate,
            args.output,
            args.manifest_sha256,
            args.archive_sha256,
            args.fusion_version,
        )
    elif args.command == "prepare-replay":
        paths = {
            "input": args.candidate / contract.ARCHIVE,
            "manifest": args.candidate / contract.MANIFEST,
            "request": args.request,
            "witness": args.source_witness,
            "seed_helper": args.seed_helper,
            "snapshot_builder": args.snapshot_builder,
            "snapshot_owners": args.snapshot_owners,
        }
        digests = {
            "input": args.archive_sha256,
            "manifest": args.manifest_sha256,
            "request": args.request_sha256,
            "witness": args.source_witness_sha256,
        }
        result = prepare_replay(paths, digests, args.output, args.fusion_version)
    elif args.command == "inspect-plan":
        plan = inspect_plan(args.witness, args.plan_sha256)
        result = {
            "status": "verified_prepared_p03_custody",
            "plan_sha256": args.plan_sha256,
            "candidate": plan["candidate"],
        }
        if plan["schema"] == 2:
            result["preparation_host"] = plan["preparation_host"]
    else:
        result = verify(
            args.witness,
            args.plan_sha256,
            args.phase_a_receipt_sha256,
            args.phase_b_receipt_sha256,
        )
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
