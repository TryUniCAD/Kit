from __future__ import annotations

import argparse
from pathlib import Path

import PrepareAssemblySources
import PrepareSyncedChild
from PrepareAssemblySources import AssemblyPrivacy, prepare_archive
from PrepareCurveCorpus import checked_path, container_api, digest, json_bytes, read_bytes, read_json
from PrepareSavedCircles import require
from PrepareSyncedChild import child_archive


NAMES = ("A12SyncedEmpty", "A13SyncedSingle", "A14SyncedRepeat")


def collect(source, lock):
    require(lock["schema"] == "kit.sw2026.ordinary-assembly-source-lock.v1", "unexpected assembly source lock schema")
    require(lock["passed"] and lock["controls_healthy"] and lock["control_immutable"] and lock["distinct_processes"] == 12, "synchronized assembly source batch did not pass")
    require(lock["heldout_results_sealed"] and lock["writer_output_count"] == 0 and lock["native_acceptance"] is False, "assembly source collection exceeds its scope")
    rows = tuple(row for row in lock["cases"] if row["split"] == "discovery")
    require(tuple(row["name"] for row in rows) == NAMES and all(row["passed"] and row["phases"] == 2 for row in rows), "unexpected synchronized discovery cohort")
    for index, row in enumerate(rows):
        name = row["name"]
        parent = name + ".SLDASM"
        yield name, "parent", parent, checked_path(source, f"{name}/author/{parent}"), row
        child = row["synchronized_child"]
        require((child is None) == (index == 0), "synchronized discovery child membership differs")
        if child is not None:
            require(child["path_basename"] == "CohortChild.SLDPRT", "unexpected synchronized child basename")
            yield name, "child", name + "Child.SLDPRT", checked_path(source, f"{name}/author/CohortChild.SLDPRT"), child


def prepare(source, lock_path, destination, accounts):
    lock, lock_hash = read_json(lock_path)
    api, modules = container_api(Path(__file__).resolve().parents[3])
    privacy = AssemblyPrivacy(accounts, source.parent.name)
    outputs, records, ledger, previews = [], [], [], []
    for name, role, filename, path, expected in collect(source, lock):
        raw = read_bytes(path)
        require(len(raw) == expected["native_bytes"] and digest(raw) == expected["native_sha256"], "synchronized native discovery input changed")
        method = prepare_archive if role == "parent" else child_archive
        data, streams, operations, pictures = method(api, raw, filename, privacy)
        require(read_bytes(path) == raw, "native file changed during preparation")
        sha = digest(data)
        records.append({"name": name, "role": role, "file": filename, "sha256": sha, "bytes": len(data), "source_sha256": digest(raw), "streams": streams})
        ledger.append({"file": filename, "prepared_sha256": sha, "operations": operations})
        outputs.append((filename, data))
        previews.extend(pictures)
    require(len(outputs) == 5, "synchronized discovery must contain three parents and two children")
    privacy_record = {"schema": "kit.sw2026.synchronized-assembly-privacy.v1", "redacted_account_fingerprints": privacy.name_fingerprints, "records": ledger}
    ledger_bytes = json_bytes(privacy_record)
    manifest = {"schema": "kit.sw2026.synchronized-assembly-fixtures.v1", "source_lock_sha256": lock_hash, "privacy_ledger_sha256": digest(ledger_bytes), "heldout_payloads_read": False, "writer_output_count": 0, "native_acceptance": False, "records": records}
    manifest_bytes = json_bytes(manifest)
    proof = {"schema": "kit.sw2026.synchronized-assembly-preparation.v1", "manifest_sha256": digest(manifest_bytes), "preparer_sha256": digest(Path(__file__).read_bytes()), "base_preparer_sha256": digest(Path(PrepareAssemblySources.__file__).read_bytes()), "child_preparer_sha256": digest(Path(PrepareSyncedChild.__file__).read_bytes()), "data_files": len(outputs), "streams": sum(len(row["streams"]) for row in records), "redactions": sum(len(row["operations"]) for row in ledger), "previews": len(previews), "modules": modules, "archive_schemas_executed": False, "container_outputs_reparsed": False, "heldout_payloads_read": False}
    require(all(not privacy.private_json(value) for value in (privacy_record, manifest, proof)), "synchronized assembly preparation retained private metadata")
    destination.mkdir()
    for filename, payload in [*outputs, ("Manifest.json", manifest_bytes), ("PrivacyLedger.json", ledger_bytes), ("SourceEvidence.json", json_bytes(proof))]:
        with (destination / filename).open("xb") as out:
            out.write(payload)
    if previews:
        folder = destination / "Previews"
        folder.mkdir()
        for filename, payload in previews:
            require((folder / filename).parent == folder, "synchronized preview escaped its directory")
            with (folder / filename).open("xb") as file:
                file.write(payload)
    return proof


def main():
    parser = argparse.ArgumentParser(description="Prepare synchronized native assembly discovery data without reading held-out payloads or executing archive schemas")
    parser.add_argument("source", type=Path)
    parser.add_argument("source_lock", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--redact-name", action="append", required=True)
    args = parser.parse_args()
    source = args.source.absolute()
    destination = args.destination.absolute()
    require(source.resolve(strict=True) == source and source.is_dir(), "synchronized assembly source directory is not canonical")
    require(destination.parent.resolve(strict=True) == destination.parent and not destination.exists() and not destination.is_symlink(), "synchronized assembly destination must be unused")
    proof = prepare(source, args.source_lock, destination, args.redact_name)
    print(json_bytes({key: proof[key] for key in ("data_files", "streams", "redactions", "previews", "manifest_sha256")}).decode("ascii"), end="")


if __name__ == "__main__":
    main()
