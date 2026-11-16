from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path

from PrepareCurveCorpus import (
    MAX_DECODED, MAX_FILE, MAX_STREAM, Privacy, binary_redaction, checked_path,
    container_api, digest, json_bytes, read_bytes, read_json, xml_redaction,
)

PHASES = ("open-save", "fresh-reopen", "edited-fresh-reopen")
NAMES = ("CircleRadiusBoss", "CircleDiameterBoss")
ORACLE = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
NOTICE = "Vendor-saved derivatives of generated research inputs; reader evidence only, not new writer outputs or inherited native acceptance"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def dimension_names(value):
    found = set()
    if isinstance(value, str):
        if re.fullmatch(r"D[1-9][0-9]*@[^@<>/\\\r\n\x00]+@[^@<>/\\\r\n\x00]+\.Part", value):
            found.add(value)
    elif isinstance(value, list):
        for item in value:
            found.update(dimension_names(item))
    elif isinstance(value, dict):
        for item in value.values():
            found.update(dimension_names(item))
    return found


def sources(receipt, job, source):
    require(receipt["schema"] == "kit.sw2026.circle-boss-edit-rung.v1", "unexpected native receipt")
    require(receipt["body_and_edit_rung_passed"] is True, "native body rung did not pass")
    require(receipt["all_numeric_match_6_significant_figures"] is True and receipt["numeric_count"] == 200, "native numeric receipt is incomplete")
    require(receipt["native_acceptance"] is False and receipt["heldout_native_payloads_read"] is False, "receipt scope differs")
    require(len(receipt["controls"]) == 2 and all(item["healthy"] is True for item in receipt["controls"]), "original controls did not pass")
    require([item["name"] for item in receipt["cases"]] == list(NAMES), "unexpected native membership")
    requests = {item["name"]: item for item in job["cases"]}
    require(set(requests) == set(NAMES) and len(job["cases"]) == 2, "unexpected job membership")
    selected = []
    for case in receipt["cases"]:
        require(case["passed"] is True and case["fresh_process"] is True, "native case did not pass")
        require([item["phase"] for item in case["phases"]] == list(PHASES), "unexpected native phases")
        spec = requests[case["name"]]
        document = spec["request"]["document"]
        require(document["profile_kind"] == "circle" and document["feature_kind"] == "blind_extrusion" and document["plane_axis"] == "z", "unsupported neutral source")
        require(document["circle_dimension"]["fix_center"] is True, "neutral center is not fixed")
        for phase in case["phases"]:
            identity = phase["oracle_identity"]
            require(phase["passed"] is True and phase["source_immutable"] is True, "native phase did not pass")
            require(identity["version_matches"] is True and identity["file_version"] == "34.5.2.0604" and identity["sha256"] == ORACLE and identity["pe_machine"] == "0x8664", "native build differs")
            require(phase["open_errors"] == phase["open_warnings"] == 0, "native phase has load diagnostics")
            radial_factor = 1.0 if phase["phase"] == PHASES[0] else spec["edit_factor"]
            depth_factor = 1.0 if phase["phase"] == PHASES[0] else spec["depth_edit_factor"]
            require(phase["saved_factor"] == radial_factor and phase["saved_depth_factor"] == depth_factor, "saved edit factors differ")
            relative = f"{case['name']}/{phase['phase']}/{case['name']}Saved.SLDPRT"
            native = checked_path(source, relative)
            raw = read_bytes(native)
            require(len(raw) == phase["saved_bytes"] and digest(raw) == phase["saved_sha256"], "native saved source hash differs")
            expected = {
                "sketch_name": document["sketch_name"], "extrusion_name": document["extrusion_name"],
                "center_m": document["center_m"], "radius_m": document["radius_m"] * radial_factor,
                "depth_m": document["depth_m"] * depth_factor,
                "mode": document["circle_dimension"]["mode"], "plane_axis": document["plane_axis"],
                "radial_factor": radial_factor, "depth_factor": depth_factor,
            }
            require(all(math.isfinite(value) and value > 0 for value in (expected["radius_m"], expected["depth_m"])), "invalid neutral targets")
            selected.append((case["name"], phase, raw, expected, relative))
    return selected


def prepare(api, selected, privacy):
    outputs, records, ledgers, previews = [], [], [], []
    for name, phase, raw, expected, relative in selected:
        filename = f"{name}-{phase['phase']}.SLDPRT"
        archive = api.SldprtArchive.FromBytes(raw, filename, SizeLimit=MAX_DECODED)
        require({key.split("/", 1)[0] for key in archive.streams if key.startswith("_MO_VERSION_")} == {"_MO_VERSION_19000"}, "unexpected saved format")
        require(sorted(key for key in archive.streams if re.fullmatch(r"Contents/Config-\d+", key)) == ["Contents/Config-0"], "unexpected saved configuration set")
        items, streams, operations = [], [], []
        total = 0
        for stream in archive.records:
            require(not privacy.private(stream.name), "private native stream name")
            total += len(stream.data)
            require(len(stream.data) <= MAX_STREAM and total <= MAX_DECODED, "saved fixture exceeds stream bound")
            if stream.name.endswith(".xml"):
                prepared, changes, spans = xml_redaction(stream.name, stream.data, privacy)
            else:
                prepared, changes = binary_redaction(stream.name, stream.data, privacy, additional_metadata_streams=("Contents/CMgr", "Contents/Config-0-ResolvedFeatures"))
                spans = []
            require(len(prepared) == len(stream.data) and not privacy.scan(prepared, spans), f"unrecognized private context: {filename}/{stream.name}")
            covered = {index for change in changes for index in range(change["offset"], change["offset"] + change["bytes"])}
            require(all(a == b or index in covered for index, (a, b) in enumerate(zip(stream.data, prepared))), "unrecorded metadata modification")
            items.append((stream.name, prepared))
            streams.append({"name": stream.name, "bytes": len(prepared), "source_sha256": digest(stream.data), "sha256": digest(prepared), "privacy_operations": len(changes)})
            operations.extend({"stream": stream.name, **change} for change in changes)
            if stream.name == "PreviewPNG":
                require(prepared.startswith(b"\x89PNG\r\n\x1a\n"), "unexpected preview encoding")
                previews.append((filename + ".png", prepared))
        result = api.BuildSldprt(items, Template=raw)
        require(len(result) <= MAX_FILE, "prepared saved file exceeds bound")
        records.append({
            "name": name, "phase": phase["phase"], "file": filename,
            "source_relative": relative, "source_sha256": digest(raw), "source_bytes": len(raw),
            "sha256": digest(result), "bytes": len(result), "expected": expected,
            "streams": streams, "is_writer_output": False, "native_acceptance_inherited": False,
        })
        ledgers.append({"file": filename, "source_sha256": digest(raw), "sha256": digest(result), "stream_operations": operations, "unchanged_encoded_stream_lengths": True, "container_output_reparsed": False})
        outputs.append((filename, result))
    return outputs, records, ledgers, previews


def main():
    parser = argparse.ArgumentParser(description="Prepare hash-bound saved-circle reader fixtures without executing archive schemas")
    parser.add_argument("source", type=Path)
    parser.add_argument("receipt", type=Path)
    parser.add_argument("job", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--expected-receipt-sha256", required=True)
    parser.add_argument("--redact-name", action="append", required=True)
    arguments = parser.parse_args()
    source = arguments.source.resolve(strict=True)
    require(source == arguments.source.absolute() and source.is_dir(), "source must be a canonical directory")
    destination = arguments.destination.absolute()
    require(destination.parent.resolve(strict=True) == destination.parent and not destination.exists() and not destination.is_symlink(), "destination must be new beneath a canonical existing parent")
    receipt, receipt_hash = read_json(arguments.receipt)
    job, job_hash = read_json(arguments.job)
    require(receipt_hash == arguments.expected_receipt_sha256 and job_hash == receipt["job"]["sha256"], "receipt or job hash differs")
    selected = sources(receipt, job, source)
    names = dimension_names(receipt["cases"])
    require(bool(names), "native qualified dimension identities are absent")
    privacy = Privacy(arguments.redact_name, names)
    api, modules = container_api(Path(__file__).resolve().parents[3])
    outputs, records, ledgers, previews = prepare(api, selected, privacy)
    ledger = {"schema": "kit.sw2026.saved-circle-privacy.v1", "notice": NOTICE, "dimension_names": sorted(names), "redacted_account_fingerprints": privacy.name_fingerprints, "records": ledgers}
    ledger_raw = json_bytes(ledger)
    manifest = {
        "schema": "kit.sw2026.saved-circle-fixtures.v1", "notice": NOTICE,
        "is_writer_output": False, "heldout_native_payloads_read": False, "native_acceptance_inherited": False,
        "source_receipt_sha256": receipt_hash, "source_job_sha256": job_hash,
        "generator_revision": receipt["generator"]["source_revision"],
        "privacy_ledger_sha256": digest(ledger_raw), "records": records,
    }
    manifest_raw = json_bytes(manifest)
    proof = {
        "schema": "kit.sw2026.saved-circle-preparation.v1", "notice": NOTICE,
        "source_receipt_sha256": receipt_hash, "source_job_sha256": job_hash,
        "manifest_sha256": digest(manifest_raw), "privacy_ledger_sha256": digest(ledger_raw),
        "preparer_sha256": digest(Path(__file__).read_bytes()),
        "privacy_helper_sha256": digest(Path(__file__).with_name("PrepareCurveCorpus.py").read_bytes()),
        "modules": modules, "archive_schemas_executed": False, "container_outputs_reparsed": False,
        "source_files_unchanged": True, "heldout_native_payloads_read": False,
        "file_count": len(records), "prepared_bytes": sum(len(raw) for _, raw in outputs),
        "stream_count": sum(len(item["streams"]) for item in records),
        "stream_redactions": sum(len(item["stream_operations"]) for item in ledgers),
    }
    for name, phase, raw, expected, relative in selected:
        require(read_bytes(checked_path(source, relative)) == raw, "source changed during preparation")
    destination.mkdir()
    for filename, raw in [*outputs, ("Manifest.json", manifest_raw), ("PrivacyLedger.json", ledger_raw), ("SourceEvidence.json", json_bytes(proof))]:
        with (destination / filename).open("xb") as output:
            output.write(raw)
    if previews:
        (destination / "Previews").mkdir()
        for filename, raw in previews:
            with (destination / "Previews" / filename).open("xb") as output:
                output.write(raw)
    print(json.dumps({"files": proof["file_count"], "bytes": proof["prepared_bytes"], "streams": proof["stream_count"], "redactions": proof["stream_redactions"], "previews": len(previews), "manifest_sha256": digest(manifest_raw)}))


if __name__ == "__main__":
    main()
