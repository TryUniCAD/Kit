from __future__ import annotations

import argparse
from pathlib import Path

from PrepareCurveCorpus import Privacy, checked_path, container_api, digest, json_bytes, read_bytes, read_json
from PrepareSavedCircles import dimension_names, prepare, require


def select_sources(receipt, job, source):
    require(receipt["schema"] == "kit.sw2026.visible-view-probe.v1", "unexpected visible view receipt")
    require(receipt["passed"] and receipt["controls_healthy"] and receipt["control_immutable"], "visible view batch or controls did not pass")
    require(receipt["native_acceptance"] is receipt["heldout_acceptance"] is False, "visible view scope differs")
    require(len(receipt["controls"]) == 2 and all(x["healthy"] for x in receipt["controls"]), "visible view controls differ")
    requests = {x["name"]: x for x in job["cases"]}
    require(len(requests) == len(job["cases"]) == len(receipt["cases"]) == 5, "visible view case membership differs")
    require(set(requests) == {x["name"] for x in receipt["cases"]}, "visible view request membership differs")
    selected = []
    for case in receipt["cases"]:
        require(case["passed"] and case["fresh_process"], "visible view case did not pass")
        require([x["phase"] for x in case["phases"]] == ["open-save", "fresh-reopen"], "visible view phases differ")
        document = requests[case["name"]]["request"]["document"]
        require(document["feature_kind"] == "extrusion" and document["profile_kind"] == "circle", "unexpected generated profile")
        first, second = case["phases"]
        require(first["source_sha256"] == requests[case["name"]]["sha256"] and first["saved_sha256"] == second["source_sha256"], "visible view source chain differs")
        for phase in case["phases"]:
            require(phase["passed"] and phase["source_immutable"] and phase["initial_state"]["passed"], "visible view native phase did not pass")
            require(phase["oracle_identity"]["sha256"] == job["oracle_sha256"] and phase["oracle_identity"]["version_matches"], "visible view oracle identity differs")
            relative = f"{case['name']}/{phase['phase']}/{case['name']}ViewSaved.SLDPRT"
            raw = read_bytes(checked_path(source, relative))
            require(len(raw) == phase["saved_bytes"] and digest(raw) == phase["saved_sha256"], "saved view source identity differs")
            expected = {key: document[key] for key in ("center_m", "radius_m", "depth_m", "plane_axis", "sketch_name", "extrusion_name", "end_condition", "reverse_direction")}
            expected.update(mode=document["circle_dimension"]["mode"], view_request=requests[case["name"]]["view_request"], native_saved_pose=phase["saved_pose"])
            selected.append((case["name"], phase, raw, expected, relative))
    return selected


def main():
    parser = argparse.ArgumentParser(description="Prepare complete native view intervention fixtures without executing archive schemas")
    parser.add_argument("source", type=Path)
    parser.add_argument("receipt", type=Path)
    parser.add_argument("job", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--expected-receipt-sha256", required=True)
    parser.add_argument("--redact-name", action="append", required=True)
    args = parser.parse_args()
    source = args.source.resolve(strict=True)
    require(source == args.source.absolute() and source.is_dir(), "view source must be a canonical directory")
    destination = args.destination.absolute()
    require(destination.parent.resolve(strict=True) == destination.parent and not destination.exists() and not destination.is_symlink(), "view destination must be unused beneath a canonical parent")
    receipt, receipt_sha = read_json(args.receipt)
    job, job_sha = read_json(args.job)
    require(receipt_sha == args.expected_receipt_sha256 and job_sha == receipt["job_sha256"], "visible view receipt or job hash differs")
    selected = select_sources(receipt, job, source)
    names = dimension_names(receipt["cases"])
    require(bool(names), "native dimension identifiers are absent")
    privacy = Privacy(args.redact_name, names)
    api, modules = container_api(Path(__file__).resolve().parents[3])
    outputs, records, ledgers, previews = prepare(api, selected, privacy)
    notice = "Native-saved visible camera interventions on unchanged generated input; diagnostic reader fixtures only, no new writer output or inherited acceptance"
    ledger = {"schema": "kit.sw2026.view-probe-privacy.v1", "notice": notice, "dimension_names": sorted(names), "redacted_account_fingerprints": privacy.name_fingerprints, "records": ledgers}
    ledger_raw = json_bytes(ledger)
    manifest = {"schema": "kit.sw2026.view-probe-fixtures.v1", "notice": notice, "is_writer_output": False, "heldout_native_payloads_read": False, "native_acceptance_inherited": False, "source_receipt_sha256": receipt_sha, "source_job_sha256": job_sha, "generator_revision": receipt["generator"]["source_revision"], "privacy_ledger_sha256": digest(ledger_raw), "records": records}
    manifest_raw = json_bytes(manifest)
    proof = {"schema": "kit.sw2026.view-probe-preparation.v1", "notice": notice, "source_receipt_sha256": receipt_sha, "source_job_sha256": job_sha, "manifest_sha256": digest(manifest_raw), "privacy_ledger_sha256": digest(ledger_raw), "preparer_sha256": digest(Path(__file__).read_bytes()), "privacy_helper_sha256": digest(Path(__file__).with_name("PrepareCurveCorpus.py").read_bytes()), "saved_helper_sha256": digest(Path(__file__).with_name("PrepareSavedCircles.py").read_bytes()), "modules": modules, "archive_schemas_executed": False, "container_outputs_reparsed": False, "source_files_unchanged": True, "heldout_native_payloads_read": False, "file_count": len(records), "stream_count": sum(len(x["streams"]) for x in records), "stream_redactions": sum(len(x["stream_operations"]) for x in ledgers), "previews": len(previews)}
    for _, _, raw, _, relative in selected:
        require(read_bytes(checked_path(source, relative)) == raw, "view source changed during preparation")
    for value in (manifest, ledger, proof):
        require(not privacy.private_json(value), "prepared view metadata retains a private context")
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
