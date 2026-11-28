from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "src"))

from Classes import registry
from RoundTrip import PLANS, REQUIRED, one
from StringCorpus import GraphProof, LoadModels, SourceProof
from TreeNames import document_views, read_object, require
from convert.adapters.solidworks.Container.Container import SldprtArchive

CORPUS = ROOT / "re/solidworks/v2026/corpus/view-probes"
RECEIPT = ROOT / "re/solidworks/measurements/2026/VisibleViewProbe02.json"
RESOLVED = "Contents/Config-0-ResolvedFeatures"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def fixture_inputs():
    manifest = read_object(CORPUS / "Manifest.json")
    proof = read_object(CORPUS / "SourceEvidence.json")
    receipt = read_object(RECEIPT)
    require(manifest["schema"] == "kit.sw2026.view-probe-fixtures.v1", "unexpected view fixture manifest")
    require(manifest["is_writer_output"] is manifest["native_acceptance_inherited"] is manifest["heldout_native_payloads_read"] is False, "view fixture scope differs")
    require(proof["manifest_sha256"] == digest((CORPUS / "Manifest.json").read_bytes()), "view fixture manifest hash differs")
    require(proof["privacy_ledger_sha256"] == manifest["privacy_ledger_sha256"] == digest((CORPUS / "PrivacyLedger.json").read_bytes()), "view fixture privacy ledger differs")
    require(proof["source_receipt_sha256"] == manifest["source_receipt_sha256"] == digest(RECEIPT.read_bytes()), "view native receipt differs")
    require(proof["source_job_sha256"] == manifest["source_job_sha256"] == receipt["job_sha256"], "view native job differs")
    for key, filename in (("preparer_sha256", "PrepareViewProbe.py"), ("privacy_helper_sha256", "PrepareCurveCorpus.py"), ("saved_helper_sha256", "PrepareSavedCircles.py")):
        require(proof[key] == digest((HERE.parent / filename).read_bytes()), "view preparation source differs")
    require(proof["archive_schemas_executed"] is proof["container_outputs_reparsed"] is proof["heldout_native_payloads_read"] is False, "view preparation scope differs")
    require(receipt["passed"] and receipt["controls_healthy"] and receipt["control_immutable"] and receipt["postflight_no_cad_process"] and receipt["license_process_ids_unchanged"], "view native batch is incomplete")
    require(receipt["native_acceptance"] is receipt["heldout_acceptance"] is False, "view native scope differs")
    require(manifest["generator_revision"] == receipt["generator"]["source_revision"], "view generator revision differs")
    observations = {(c["name"], p["phase"]): p for c in receipt["cases"] for p in c["phases"]}
    requests = {x["name"]: x for x in receipt["requests"]}
    expected_files = {f"{name}-{phase}.SLDPRT" for name, phase in observations}
    records = manifest["records"]
    require(len(requests) == len(receipt["cases"]) == 5 and len(records) == len(expected_files) == 10, "view fixture membership differs")
    require({x["file"] for x in records} == {x.name for x in CORPUS.glob("*.SLDPRT")} == expected_files, "view native file membership differs")
    for entry in records:
        phase = observations[entry["name"], entry["phase"]]
        require(phase["passed"] and phase["source_immutable"] and phase["initial_state"]["passed"], "view native phase did not pass")
        require(entry["source_sha256"] == phase["saved_sha256"], "view native saved hash differs")
        require(entry["is_writer_output"] is entry["native_acceptance_inherited"] is False, "view derivative was misclassified")
        request = requests[entry["name"]]
        document = request["request"]["document"]
        target = {key: document[key] for key in ("center_m", "radius_m", "depth_m", "plane_axis", "sketch_name", "extrusion_name", "end_condition", "reverse_direction")}
        target.update(mode=document["circle_dimension"]["mode"], view_request=request["view_request"], native_saved_pose=phase["saved_pose"])
        require(entry["expected"] == target, "view fixture target differs from the native request or observation")
    return manifest, records


def inspect_file(entry):
    path = CORPUS / entry["file"]
    require(not path.is_symlink() and path.resolve().parent == CORPUS.resolve(), "view fixture escaped its corpus")
    raw = path.read_bytes()
    require(digest(raw) == entry["sha256"] and len(raw) == entry["bytes"], "view prepared hash differs")
    archive = SldprtArchive.from_bytes(raw, path)
    streams = {x["name"]: x for x in entry["streams"]}
    require(len(streams) == len(entry["streams"]) and set(archive.streams) == set(streams), "view fixture stream membership differs")
    for name, value in archive.streams.items():
        require(digest(value) == streams[name]["sha256"] and len(value) == streams[name]["bytes"], "view fixture stream hash differs")
    reg = registry()
    plans = {**PLANS, **reg.plans}
    primary = one(path, [*REQUIRED, "Header2"], reg, plans, False, True)
    linked = one(path, [RESOLVED], reg, plans, True, True)
    result = {"file": entry["file"], "name": entry["name"], "phase": entry["phase"], "sha256": entry["sha256"], "source_sha256": entry["source_sha256"], "primary": primary, "linked": linked, "passed": False}
    require(primary["passed"] is True and linked["passed"] is True, "view complete archive comparison failed")
    models = LoadModels(archive, reg)
    result["native_saved_pose"] = entry["expected"]["native_saved_pose"]
    result["view_request"] = entry["expected"]["view_request"]
    result["document_view_state"] = document_views(models["Contents/Definition"]["document"].head)
    result["linked_graph"] = GraphProof(models[RESOLVED]["document"], models[RESOLVED]["reader"], RESOLVED, models["Contents/Config-0"])
    require(result["linked_graph"]["unresolved_references"] == 0, "view graph has unresolved references")
    require(path.read_bytes() == raw, "view fixture changed during decoding")
    result["source_immutable"] = result["passed"] = True
    return result


def main():
    parser = argparse.ArgumentParser(description="Decode complete visible view intervention archives and report typed transforms alongside native poses")
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    report = {"schema": "kit.sw2026.view-probe-reader.v1", "passed": False, "is_writer_output": False, "native_acceptance_inherited": False, "heldout_native_payloads_read": False, "active_camera_mapping_established": False, "pid": os.getpid(), "files": [], "scope": "Complete archive and graph decoding with independent native API observations; no assumed API-to-wire formula or writer acceptance"}
    try:
        manifest, entries = fixture_inputs()
        report["manifest_sha256"] = digest((CORPUS / "Manifest.json").read_bytes())
        report["source_receipt_sha256"] = manifest["source_receipt_sha256"]
        report["source_proof"] = [{"file": str(path.relative_to(ROOT)), "sha256": digest(path.read_bytes())} for path in (Path(__file__), HERE / "TreeNames.py")] + SourceProof()
        for entry in entries:
            try:
                record = inspect_file(entry)
            except Exception as error:
                record = {"file": entry["file"], "passed": False, "error": repr(error), "trace": traceback.format_exc(limit=10)}
            report["files"].append(record)
        report["file_count"] = len(report["files"])
        report["stream_count"] = sum(len(x.get(kind, {}).get("streams", {})) for x in report["files"] for kind in ("primary", "linked"))
        report["document_transform_count"] = sum(2 for x in report["files"] if "document_view_state" in x)
        report["passed"] = len(report["files"]) == 10 and all(x["passed"] for x in report["files"])
    except Exception as error:
        report.update(error=repr(error), trace=traceback.format_exc(limit=10))
    with args.report.open("x", encoding="utf-8") as output:
        output.write(json.dumps(report, indent=2, ensure_ascii=True, allow_nan=False) + "\n")
    print(json.dumps({key: report[key] for key in ("passed", "file_count", "stream_count", "document_transform_count") if key in report}))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
