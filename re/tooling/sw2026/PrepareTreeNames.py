from __future__ import annotations

import argparse
from pathlib import Path

from PrepareCurveCorpus import Privacy, checked_path, container_api, digest, json_bytes, read_bytes, read_json
from PrepareSavedCircles import dimension_names, prepare, require


def select_sources(receipt, job, source):
    require(receipt["schema"] == "kit.sw2026.recursive-tree-measurement.v1", "unexpected recursive-tree receipt")
    require(receipt["observational_rung_passed"] is True and receipt["candidate_phases"] == 8 and receipt["numeric_count"] == 164, "recursive-tree observations are incomplete")
    require(receipt["native_acceptance"] is receipt["heldout_acceptance"] is receipt["heldout_native_payloads_read"] is False, "recursive-tree scope differs")
    require(len(receipt["controls"]) == 2 and all(x["healthy"] for x in receipt["controls"]), "recursive-tree controls did not pass")
    requests = {x["name"]: x for x in job["cases"]}
    require(len(requests) == len(job["cases"]) == len(receipt["cases"]) == 4, "recursive-tree case membership differs")
    require(set(requests) == {x["name"] for x in receipt["cases"]}, "recursive-tree requests differ")
    selected = []
    for case in receipt["cases"]:
        require(case["passed"] and case["fresh_process"], "recursive-tree case did not pass")
        require([x["phase"] for x in case["phases"]] == ["open-save", "fresh-reopen"], "recursive-tree phases differ")
        document = requests[case["name"]]["request"]["document"]
        require(document["feature_kind"] == "extrusion" and document["profile_kind"] == "circle", "unexpected generated profile")
        for phase in case["phases"]:
            require(phase["passed"] and phase["source_immutable"] and phase["initial_state"]["passed"], "recursive-tree native phase did not pass")
            require(phase["oracle_identity"]["sha256"] == job["oracle_sha256"] and phase["oracle_identity"]["version_matches"], "recursive-tree oracle identity differs")
            relative = f"{case['name']}/{phase['phase']}/{case['name']}TreeSaved.SLDPRT"
            raw = read_bytes(checked_path(source, relative))
            require(len(raw) == phase["saved_bytes"] and digest(raw) == phase["saved_sha256"], "saved tree source identity differs")
            expected = {key: document[key] for key in ("center_m", "radius_m", "depth_m", "plane_axis", "sketch_name", "extrusion_name", "end_condition", "reverse_direction")}
            expected["mode"] = document["circle_dimension"]["mode"]
            if "reverse_depth_m" in document:
                expected["reverse_depth_m"] = document["reverse_depth_m"]
            selected.append((case["name"], phase, raw, expected, relative))
    return selected


def main():
    parser = argparse.ArgumentParser(description="Prepare hash-bound saved-tree reader fixtures without executing archive schemas")
    parser.add_argument("source", type=Path)
    parser.add_argument("receipt", type=Path)
    parser.add_argument("job", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--expected-receipt-sha256", required=True)
    parser.add_argument("--redact-name", action="append", required=True)
    args = parser.parse_args()
    source = args.source.resolve(strict=True)
    require(source == args.source.absolute() and source.is_dir(), "saved-tree source must be a canonical directory")
    destination = args.destination.absolute()
    require(destination.parent.resolve(strict=True) == destination.parent and not destination.exists() and not destination.is_symlink(), "saved-tree destination must be unused beneath a canonical parent")
    receipt, receipt_sha = read_json(args.receipt)
    job, job_sha = read_json(args.job)
    require(receipt_sha == args.expected_receipt_sha256 and job_sha == receipt["job_sha256"], "recursive-tree receipt or job hash differs")
    selected = select_sources(receipt, job, source)
    names = dimension_names(receipt["cases"])
    require(bool(names), "qualified native dimension identifiers are absent")
    privacy = Privacy(args.redact_name, names)
    api, modules = container_api(Path(__file__).resolve().parents[3])
    outputs, records, ledgers, previews = prepare(api, selected, privacy)
    notice = "Native-saved derivatives of existing generated inputs; diagnostic reader fixtures only, no new writer output or inherited native acceptance"
    ledger = {"schema": "kit.sw2026.saved-tree-privacy.v1", "notice": notice, "dimension_names": sorted(names), "redacted_account_fingerprints": privacy.name_fingerprints, "records": ledgers}
    ledger_raw = json_bytes(ledger)
    manifest = {"schema": "kit.sw2026.saved-tree-fixtures.v1", "notice": notice, "is_writer_output": False, "heldout_native_payloads_read": False, "native_acceptance_inherited": False, "source_receipt_sha256": receipt_sha, "source_job_sha256": job_sha, "generator_revision": receipt["generator"]["source_revision"], "privacy_ledger_sha256": digest(ledger_raw), "records": records}
    manifest_raw = json_bytes(manifest)
    proof = {"schema": "kit.sw2026.saved-tree-preparation.v1", "notice": notice, "source_receipt_sha256": receipt_sha, "source_job_sha256": job_sha, "manifest_sha256": digest(manifest_raw), "privacy_ledger_sha256": digest(ledger_raw), "preparer_sha256": digest(Path(__file__).read_bytes()), "privacy_helper_sha256": digest(Path(__file__).with_name("PrepareCurveCorpus.py").read_bytes()), "saved_helper_sha256": digest(Path(__file__).with_name("PrepareSavedCircles.py").read_bytes()), "modules": modules, "archive_schemas_executed": False, "container_outputs_reparsed": False, "source_files_unchanged": True, "heldout_native_payloads_read": False, "file_count": len(records), "stream_count": sum(len(x["streams"]) for x in records), "stream_redactions": sum(len(x["stream_operations"]) for x in ledgers), "previews": len(previews)}
    for _, _, raw, _, relative in selected:
        require(read_bytes(checked_path(source, relative)) == raw, "saved-tree source changed during preparation")
    for value in (manifest, ledger, proof):
        require(not privacy.private_json(value), "prepared tree metadata retains a private context")
    destination.mkdir()
    for filename, raw in [*outputs, ("Manifest.json", manifest_raw), ("PrivacyLedger.json", ledger_raw), ("SourceEvidence.json", json_bytes(proof))]:
        with (destination / filename).open("xb") as output:
            output.write(raw)
    if previews:
        (destination / "Previews").mkdir()
        for filename, raw in previews:
            with (destination / "Previews" / filename).open("xb") as output:
                output.write(raw)
    print(json_bytes({key: proof[key] for key in ("file_count", "stream_count", "stream_redactions", "previews", "manifest_sha256")}).decode("ascii"), end="")


if __name__ == "__main__":
    main()
