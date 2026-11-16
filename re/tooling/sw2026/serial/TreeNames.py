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
from Core import Obj
from RoundTrip import PLANS, REQUIRED, one
from StringCorpus import GraphProof, LoadModels, SourceProof
from convert.adapters.solidworks.Container.Container import SldprtArchive

CORPUS = ROOT / "re/solidworks/v2026/corpus/tree-saves"
RECEIPT = ROOT / "re/solidworks/measurements/2026/TreeNamesInspection01.json"
GENERATED = ROOT / "re/solidworks/measurements/2026/EndHeldoutProcesses55d0.json"
RESOLVED = "Contents/Config-0-ResolvedFeatures"


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def read_object(path):
    value = json.loads(path.read_bytes())
    require(isinstance(value, dict), "expected a JSON object")
    return value


def fixture_inputs():
    manifest = read_object(CORPUS / "Manifest.json")
    proof = read_object(CORPUS / "SourceEvidence.json")
    receipt = read_object(RECEIPT)
    generated = read_object(GENERATED)
    require(manifest["schema"] == "kit.sw2026.saved-tree-fixtures.v1", "unexpected tree-fixture manifest")
    require(manifest["is_writer_output"] is manifest["native_acceptance_inherited"] is manifest["heldout_native_payloads_read"] is False, "tree-fixture scope differs")
    require(proof["manifest_sha256"] == digest((CORPUS / "Manifest.json").read_bytes()), "tree-fixture manifest hash differs")
    require(proof["privacy_ledger_sha256"] == manifest["privacy_ledger_sha256"] == digest((CORPUS / "PrivacyLedger.json").read_bytes()), "tree-fixture privacy ledger differs")
    require(proof["source_receipt_sha256"] == manifest["source_receipt_sha256"] == digest(RECEIPT.read_bytes()), "tree native receipt differs")
    require(proof["source_job_sha256"] == manifest["source_job_sha256"] == receipt["job_sha256"], "tree native job differs")
    for key, filename in (("preparer_sha256", "PrepareTreeNames.py"), ("privacy_helper_sha256", "PrepareCurveCorpus.py"), ("saved_helper_sha256", "PrepareSavedCircles.py")):
        require(proof[key] == digest((HERE.parent / filename).read_bytes()), "tree-fixture preparation source differs")
    require(proof["archive_schemas_executed"] is proof["container_outputs_reparsed"] is proof["heldout_native_payloads_read"] is False, "tree-fixture preparation scope differs")
    require(manifest["generator_revision"] == receipt["generator"]["source_revision"] == generated["source_revision"], "tree generator revision differs")
    observations = {(c["name"], p["phase"]): p for c in receipt["cases"] for p in c["phases"]}
    requests = {x["name"]: x["record_projection"]["request"]["document"] for x in generated["cases"]}
    expected_files = {f"{name}-{phase}.SLDPRT" for name, phase in observations}
    records = manifest["records"]
    require(len(records) == len(expected_files) == 8 and {x["file"] for x in records} == expected_files, "saved-tree fixture membership differs")
    require({x.name for x in CORPUS.glob("*.SLDPRT")} == expected_files, "unexpected saved-tree native file")
    for item in records:
        phase = observations[item["name"], item["phase"]]
        require(item["source_sha256"] == phase["saved_sha256"], "saved-tree native hash differs")
        require(item["is_writer_output"] is item["native_acceptance_inherited"] is False, "saved-tree source was misclassified")
        document = requests[item["name"]]
        target = {key: document[key] for key in ("center_m", "radius_m", "depth_m", "plane_axis", "sketch_name", "extrusion_name", "end_condition", "reverse_direction")}
        target["mode"] = document["circle_dimension"]["mode"]
        if "reverse_depth_m" in document:
            target["reverse_depth_m"] = document["reverse_depth_m"]
        require(item["expected"] == target, "saved-tree target differs from the original neutral request")
    return manifest, records


def inspect_file(entry):
    path = CORPUS / entry["file"]
    require(not path.is_symlink() and path.resolve().parent == CORPUS.resolve(), "saved-tree fixture escaped its corpus")
    raw = path.read_bytes()
    require(digest(raw) == entry["sha256"] and len(raw) == entry["bytes"], "saved-tree prepared hash differs")
    archive = SldprtArchive.from_bytes(raw, path)
    streams = {x["name"]: x for x in entry["streams"]}
    require(len(streams) == len(entry["streams"]) and set(archive.streams) == set(streams), "saved-tree stream membership differs")
    for name, data in archive.streams.items():
        require(digest(data) == streams[name]["sha256"] and len(data) == streams[name]["bytes"], "saved-tree stream hash differs")
    reg = registry()
    plans = {**PLANS, **reg.plans}
    primary = one(path, [*REQUIRED, "Header2"], reg, plans, False, True)
    linked = one(path, [RESOLVED], reg, plans, True, True)
    result = {"file": entry["file"], "name": entry["name"], "phase": entry["phase"], "sha256": entry["sha256"], "source_sha256": entry["source_sha256"], "primary": primary, "linked": linked, "passed": False}
    require(primary["passed"] is True and linked["passed"] is True, "saved-tree critical archive comparison failed")
    models = LoadModels(archive, reg)
    reader = models[RESOLVED]["reader"]
    objects = {id(x[1]): x[1] for x in reader.table.values() if x[0] == "obj" and isinstance(x[1], Obj)}
    materials = [x for x in objects.values() if x.cls == "moMaterialFolder_c"]
    require(len(materials) == 1, "expected exactly one saved material-folder object")
    material = materials[0]
    name = material["f18"]
    require(isinstance(name, Obj) and name.cls == "moNodeName_c" and isinstance(name["f08"], str) and name["f08"], "saved material-folder name has no proven typed owner")
    result["material_folder"] = {"class": material.cls, "node_name": name["f08"], "name_owner_class": name.cls, "persisted_field_path": "moMaterialFolder_c -> moNode_c.f18 -> moNodeName_c.f08", "material_string": material["f378"], "wire_flags": material["flags380"]}
    result["linked_graph"] = GraphProof(models[RESOLVED]["document"], reader, RESOLVED, models["Contents/Config-0"])
    require(result["linked_graph"]["unresolved_references"] == 0, "saved-tree graph has unresolved references")
    require(path.read_bytes() == raw, "saved-tree source changed during inspection")
    result["source_immutable"] = result["passed"] = True
    return result


def main():
    parser = argparse.ArgumentParser(description="Read complete saved-tree archives and report the typed persisted material-name owner")
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    report = {"schema": "kit.sw2026.saved-tree-reader.v1", "passed": False, "is_writer_output": False, "native_acceptance_inherited": False, "heldout_native_payloads_read": False, "pid": os.getpid(), "files": [], "scope": "Complete archive/graph decoding and diagnostic persisted-name observations; no asserted rename cause or writer acceptance"}
    try:
        manifest, entries = fixture_inputs()
        report["manifest_sha256"] = digest((CORPUS / "Manifest.json").read_bytes())
        report["source_receipt_sha256"] = manifest["source_receipt_sha256"]
        report["source_proof"] = [{"file": str(Path(__file__).relative_to(ROOT)), "sha256": digest(Path(__file__).read_bytes())}, *SourceProof()]
        for entry in entries:
            try:
                value = inspect_file(entry)
            except Exception as error:
                value = {"file": entry["file"], "passed": False, "error": repr(error), "trace": traceback.format_exc(limit=10)}
            report["files"].append(value)
        report["file_count"] = len(report["files"])
        report["stream_count"] = sum(len(x.get(kind, {}).get("streams", {})) for x in report["files"] for kind in ("primary", "linked"))
        report["material_name_count"] = sum("material_folder" in x for x in report["files"])
        report["passed"] = len(report["files"]) == 8 and all(x["passed"] for x in report["files"])
    except Exception as error:
        report.update(error=repr(error), trace=traceback.format_exc(limit=10))
    with args.report.open("x", encoding="utf-8") as output:
        output.write(json.dumps(report, indent=2, ensure_ascii=True, allow_nan=False) + "\n")
    print(json.dumps({key: report[key] for key in ("passed", "file_count", "stream_count", "material_name_count") if key in report}))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
