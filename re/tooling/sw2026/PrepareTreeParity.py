from __future__ import annotations

import argparse
from pathlib import Path

from PrepareCurveCorpus import Privacy, checked_path, container_api, digest, json_bytes, read_bytes, read_json
from PrepareSavedCircles import ORACLE, dimension_names, prepare, require

PHASES = ("open-save", "edit-save", "edited-fresh")
NOTICE = "Native-saved derivatives of two existing generated tree predictions; reader fixtures only, not new writer outputs or additional held-out family acceptance"


def targets(document, phase):
    factors = phase["saved_factors"]
    require(factors == ([1.0, 1.0, 1.0] if phase["phase"] == PHASES[0] else [1.07, 0.89, 1.0]), "native saved edit factors differ")
    value = {key: document[key] for key in ("center_m", "radius_m", "depth_m", "plane_axis", "sketch_name", "extrusion_name", "end_condition", "reverse_direction")}
    value.update(radius_m=document["radius_m"] * factors[0], depth_m=document["depth_m"] * factors[1], mode=document["circle_dimension"]["mode"])
    value.update(native_frame=phase["snapshot"]["frame"], native_saved_pose=phase["scenes"]["saved"]["pose"])
    return value


def select_sources(receipt, generated, job, source):
    require(receipt["schema"] == "kit.sw2026.paired-tree-measurements.v1", "unexpected paired-tree receipt")
    require(receipt["passed"] and receipt["bounded_tree_pose_rung_passed"] and receipt["controls_healthy"] and receipt["inputs_immutable"], "paired-tree native measurements did not pass")
    require(receipt["native_acceptance"] is receipt["heldout_acceptance"] is False, "paired-tree acceptance scope differs")
    require(receipt["postflight_no_cad_process"] and receipt["license_process_ids_unchanged"], "paired-tree native cleanup is incomplete")
    require(len(receipt["controls"]) == 2 and all(x["healthy"] for x in receipt["controls"]), "paired-tree controls differ")
    require(receipt["generated_candidate_phases"] == 6 and receipt["numeric_checks"] == 840 and receipt["all_ordered_trees_equal"], "paired-tree native evidence is incomplete")
    requests = {x["name"]: x for x in job["cases"]}
    predictions = {x["name"]: x for x in generated["outputs"]}
    require(len(requests) == len(predictions) == len(receipt["cases"]) == 2, "paired-tree case membership differs")
    require(set(requests) == set(predictions) == {x["name"] for x in receipt["cases"]}, "paired-tree requests differ")
    require(generated["writer_revision"] == receipt["generator"]["writer_revision"], "paired-tree writer revisions differ")
    selected = []
    for case in receipt["cases"]:
        require(case["passed"] and case["fresh_processes"], "paired-tree case did not pass")
        request = requests[case["name"]]
        prediction = predictions[case["name"]]
        require(request["request"] == prediction["request"] and request["sha256"] == prediction["sha256"], "paired-tree neutral prediction differs")
        document = request["request"]["document"]
        require(document["feature_kind"] == "extrusion" and document["profile_kind"] == "circle" and document["end_condition"] == "blind", "unexpected paired-tree profile")
        require([x["phase"] for x in case["candidate"]] == list(PHASES), "paired-tree saved phases differ")
        for phase in case["candidate"]:
            require(phase["lane"] == "candidate" and phase["passed"] and phase["source_immutable"] and phase["initial_state"]["passed"], "paired-tree candidate phase did not pass")
            require(not phase["view_setters_called"] and phase["open_errors"] == phase["open_warnings"] == 0, "paired-tree candidate load or observation differs")
            identity = phase["oracle_identity"]
            require(identity["version_matches"] and identity["sha256"] == job["oracle_sha256"] == ORACLE and identity["file_version"] == "34.5.2.0604", "paired-tree oracle identity differs")
            relative = f"{case['name']}/candidate/{phase['phase']}/{case['name']}PairedSaved.SLDPRT"
            raw = read_bytes(checked_path(source, relative))
            require(len(raw) == phase["saved_bytes"] and digest(raw) == phase["saved_sha256"], "paired-tree saved source identity differs")
            selected.append((case["name"], phase, raw, targets(document, phase), relative))
    return selected


def main():
    parser = argparse.ArgumentParser(description="Prepare six candidate-saved tree fixtures without executing archive schemas or opening original held-out payloads")
    parser.add_argument("source", type=Path)
    parser.add_argument("receipt", type=Path)
    parser.add_argument("generated", type=Path)
    parser.add_argument("job", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--expected-receipt-sha256", required=True)
    parser.add_argument("--redact-name", action="append", required=True)
    args = parser.parse_args()
    source = args.source.resolve(strict=True)
    require(source == args.source.absolute() and source.is_dir(), "paired-tree source must be a canonical directory")
    destination = args.destination.absolute()
    require(destination.parent.resolve(strict=True) == destination.parent and not destination.exists() and not destination.is_symlink(), "paired-tree destination must be unused beneath a canonical parent")
    receipt, receipt_sha = read_json(args.receipt)
    generated, generated_sha = read_json(args.generated)
    job, job_sha = read_json(args.job)
    require(receipt_sha == args.expected_receipt_sha256 and job_sha == receipt["job_sha256"] and generated_sha == receipt["prediction_receipt_sha256"], "paired-tree evidence identity differs")
    selected = select_sources(receipt, generated, job, source)
    names = dimension_names(receipt["cases"])
    require(bool(names), "qualified native dimension identifiers are absent")
    privacy = Privacy(args.redact_name, names)
    api, modules = container_api(Path(__file__).resolve().parents[3])
    outputs, records, ledgers, previews = prepare(api, selected, privacy)
    ledger = {"schema": "kit.sw2026.tree-parity-privacy.v1", "notice": NOTICE, "dimension_names": sorted(names), "redacted_account_fingerprints": privacy.name_fingerprints, "records": ledgers}
    ledger_raw = json_bytes(ledger)
    manifest = {"schema": "kit.sw2026.tree-parity-fixtures.v1", "notice": NOTICE, "is_writer_output": False, "heldout_native_payloads_read": False, "native_acceptance_inherited": False, "source_receipt_sha256": receipt_sha, "prediction_receipt_sha256": generated_sha, "source_job_sha256": job_sha, "generator_revision": generated["writer_revision"], "privacy_ledger_sha256": digest(ledger_raw), "records": records}
    manifest_raw = json_bytes(manifest)
    proof = {"schema": "kit.sw2026.tree-parity-preparation.v1", "notice": NOTICE, "source_receipt_sha256": receipt_sha, "prediction_receipt_sha256": generated_sha, "source_job_sha256": job_sha, "manifest_sha256": digest(manifest_raw), "privacy_ledger_sha256": digest(ledger_raw), "preparer_sha256": digest(Path(__file__).read_bytes()), "privacy_helper_sha256": digest(Path(__file__).with_name("PrepareCurveCorpus.py").read_bytes()), "saved_helper_sha256": digest(Path(__file__).with_name("PrepareSavedCircles.py").read_bytes()), "modules": modules, "archive_schemas_executed": False, "container_outputs_reparsed": False, "source_files_unchanged": True, "heldout_native_payloads_read": False, "file_count": len(records), "stream_count": sum(len(x["streams"]) for x in records), "stream_redactions": sum(len(x["stream_operations"]) for x in ledgers), "previews": len(previews)}
    for _, _, raw, _, relative in selected:
        require(read_bytes(checked_path(source, relative)) == raw, "paired-tree saved source changed during preparation")
    for value in (manifest, ledger, proof):
        require(not privacy.private_json(value), "paired-tree prepared metadata retains a private context")
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
