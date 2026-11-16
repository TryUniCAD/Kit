from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PrepareCurveCorpus import (
    MAX_DECODED, Privacy, checked_path, container_api, digest, dimension_identities,
    json_bytes, prepare_case, read_json, sanitize, validate_case, validate_identity,
)

NOTICE = "Oracle-authored discovery/control reader fixtures only; no writer output, held-out payload access or inherited native acceptance"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    require(sys.version_info >= (3, 11), "preparation requires Python 3.11 or newer")
    parser = argparse.ArgumentParser(description="Prepare only locked end-condition discovery/control fixtures through the bounded container API")
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--previews", type=Path, required=True)
    parser.add_argument("--expected-lock-sha256", required=True)
    parser.add_argument("--expected-proof-sha256", required=True)
    parser.add_argument("--redact-name", action="append", required=True)
    args = parser.parse_args()
    source = args.source.absolute()
    require(source.resolve(strict=True) == source and source.is_dir(), "source must be a canonical directory")
    destination, previews = args.destination.absolute(), args.previews.absolute()
    for path in (destination, previews):
        require(not path.exists() and not path.is_symlink() and path.parent.resolve(strict=True) == path.parent, "outputs must be absent under canonical existing parents")
        require(not path.is_relative_to(source) and not source.is_relative_to(path), "outputs must remain separate from native evidence")
    require(destination != previews and not destination.is_relative_to(previews) and not previews.is_relative_to(destination), "fixture and preview outputs must remain separate")
    lock, lock_hash = read_json(checked_path(source, "Lock.json"))
    proof, proof_hash = read_json(checked_path(source, "RootLockVerification.json"))
    repository = Path(__file__).resolve().parents[3]
    spec, spec_hash = read_json(checked_path(repository, "re/tooling/sw2026/EndConditionSpecs.json"))
    require(lock_hash == args.expected_lock_sha256 and proof_hash == args.expected_proof_sha256 and proof["lock_sha256"] == lock_hash, "native lock or owner verification hash differs")
    require(lock["schema"] == "kit-sw2026-end-source-lock/1" and lock["specs_sha256"] == spec_hash, "end-condition lock does not match the neutral specification")
    require(proof["all_checks_passed"] is True and proof["source_cases"] == 16 and proof["native_source_files_hash_verified"] == 18, "complete source-lock verification is missing")
    require(proof["controls_before"] == proof["controls_after"] == ["ControlRectangle", "ControlCircle"], "both independent controls are required before and after")
    require(proof["writer_implementation_started"] is lock["writer_implementation_started"] is False, "source lock was not completed before new writer work")
    require(proof["source_tools"] == lock["tool_hashes"] and proof["source_revision"] == lock["generator_revision"] and proof["batch_sha256"] == lock["batch_sha256"], "owner verification and frozen source identities disagree")
    require(lock["script_sha256"] == lock["tool_hashes"]["AuthorCurves.py"] and lock["oracle"] == spec["oracle"], "author or oracle identity differs")
    all_specs = spec["cases"] + spec["controls"]
    expected = {case["name"]: case for case in all_specs}
    locked = {case["name"]: case for case in lock["cases"]}
    require(len(expected) == len(all_specs) == len(locked) == len(lock["cases"]) == 18 and set(locked) == set(expected), "source-lock membership differs")
    require(all(row["split"] == expected[name]["split"] for name, row in locked.items()), "source split differs from its neutral specification")
    discovery = [case for case in all_specs if case["split"] == "discovery"]
    controls = [case for case in all_specs if case["split"] == "control"]
    require(len(discovery) == 12 and len(controls) == 2, "bounded discovery/control membership differs")
    selected = []
    first, _ = read_json(checked_path(source, "Controls/ControlRectangle/Manifest.json"))
    identity = validate_identity(first["author"]["identity"])
    for group, cases in (("Discovery", discovery), ("Controls", controls)):
        directory = checked_path(source, group, directory=True)
        require({path.name for path in directory.iterdir()} == {case["name"] for case in cases}, "unexpected discovery/control directory")
        for case in cases:
            item = validate_case(source, group, case["name"], proof, identity, locked[case["name"]])
            require(item[0]["case"] == case, "authored case differs from its independent neutral specification")
            selected.append(item)
    privacy = Privacy(args.redact_name, dimension_identities(selected))
    sys.dont_write_bytecode = True
    api, dependencies = container_api(repository)
    files, records, ledgers, images = [], [], [], []
    for item in selected:
        result, record, ledger = prepare_case(api, *item, privacy)
        record["bytes"] = len(result)
        source_archive = api.SldprtArchive.FromBytes(item[2], record["file"], SizeLimit=MAX_DECODED)
        preview = source_archive.streams.get("PreviewPNG")
        require(isinstance(preview, bytes) and preview.startswith(b"\x89PNG\r\n\x1a\n"), "source preview is absent or has another encoding")
        images.append((record["file"] + ".png", preview))
        files.append((record["file"], result))
        records.append(record)
        ledgers.append(ledger)
    ledger = {"schema": "kit.sw2026.end-source-privacy.v1", "notice": NOTICE, "redacted_account_fingerprints": privacy.name_fingerprints, "records": ledgers}
    ledger_raw = json_bytes(ledger)
    manifest = {"schema": "kit.sw2026.end-source-fixtures.v1", "notice": NOTICE, "is_writer_output": False, "native_acceptance_inherited": False, "heldout_native_payloads_read": False, "source_lock_sha256": lock_hash, "owner_verification_sha256": proof_hash, "source_revision": lock["generator_revision"], "privacy_ledger_sha256": digest(ledger_raw), "records": records}
    manifest_raw = json_bytes(manifest)
    changes = []
    evidence = {"schema": "kit.sw2026.end-source-preparation.v1", "notice": NOTICE, "manifest_sha256": digest(manifest_raw), "privacy_ledger_sha256": digest(ledger_raw), "source_lock_sha256": lock_hash, "owner_verification_sha256": proof_hash, "owner_verification": sanitize(proof, privacy, changes, "owner_verification"), "metadata_operations": changes, "preparer_sha256": digest(Path(__file__).read_bytes()), "privacy_helper_sha256": digest(Path(__file__).with_name("PrepareCurveCorpus.py").read_bytes()), "dependencies": dependencies, "file_count": len(records), "stream_count": sum(len(row["streams"]) for row in records), "stream_redactions": sum(len(row["stream_operations"]) for row in ledgers), "archive_schemas_executed": False, "container_outputs_reparsed": False, "heldout_native_payloads_read": False, "native_acceptance_inherited": False, "is_writer_output": False}
    for name, value in (("Manifest.json", manifest), ("PrivacyLedger.json", ledger), ("SourceEvidence.json", evidence)):
        require(not privacy.private_json(value), "private publication metadata remains")
        files.append((name, json_bytes(value)))
    for root, outputs in ((destination, files), (previews, images)):
        root.mkdir(exist_ok=False)
        for name, data in outputs:
            with (root / name).open("xb") as target:
                target.write(data)
    print(json_bytes({"prepared": len(records), "manifest_sha256": digest(manifest_raw), "source_lock_sha256": lock_hash, "archive_schemas_executed": False, "heldout_native_payloads_read": False}).decode(), end="")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"preparation failed: {type(error).__name__}: {error}", file=sys.stderr)
        raise SystemExit(2)
