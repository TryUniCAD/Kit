from __future__ import annotations

import argparse
import hashlib
import json
import sys
import traceback
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "src"))

from Classes import registry
from Core import Obj
from RoundTrip import PLANS, REQUIRED, one
from Streams import load_rooted
from StringCorpus import GraphProof, SourceProof
from TreeNames import read_object, require
from defs.ConfigPart import load_config
from defs.ResolvedCore import load_resolved
from convert.adapters.solidworks.Container.Container import SldprtArchive

CORPUS = ROOT / "re/solidworks/v2026/corpus/assembly-discovery"
RECEIPT = ROOT / "re/solidworks/measurements/2026/AssemblySourceAttempt02.json"
NAMES = ("A07EmptyAssembly", "A08SingleAssembly", "A09RepeatedAssembly")
HEADER = "Contents/Config-0-ModelHeader"
CONFIG = "Contents/Config-0"
RESOLVED = CONFIG + "-ResolvedFeatures"
REFERENCE_CLASSES = {"moReference_c", "moReferenceInternal_c", "moReferenceBrowser_c", "moReferenceModel_c"}
UPDATE_FIELDS = ("f3e0", "f3e8", "f3f0", "f3f4", "f3f8", "f400", "f408", "f4d8")


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def fixture_inputs():
    manifest = read_object(CORPUS / "Manifest.json")
    proof = read_object(CORPUS / "SourceEvidence.json")
    receipt = read_object(RECEIPT)
    require(manifest["schema"] == "kit.sw2026.assembly-discovery-fixtures.v1" and proof["schema"] == "kit.sw2026.assembly-discovery-preparation.v1", "assembly discovery fixture schema differs")
    require(manifest["is_writer_output"] is manifest["native_acceptance"] is manifest["heldout_payloads_read"] is proof["heldout_payloads_read"] is False, "assembly fixture scope differs")
    require(proof["archive_schemas_executed"] is proof["container_outputs_reparsed"] is False, "assembly preparation exceeded its container-only scope")
    require(proof["manifest_sha256"] == digest((CORPUS / "Manifest.json").read_bytes()), "assembly discovery manifest changed")
    require(proof["privacy_ledger_sha256"] == manifest["privacy_ledger_sha256"] == digest((CORPUS / "PrivacyLedger.json").read_bytes()), "assembly privacy ledger changed")
    require(proof["source_receipt_sha256"] == manifest["source_receipt_sha256"] == digest(RECEIPT.read_bytes()), "assembly source receipt changed")
    require(proof["preparer_sha256"] == digest((HERE.parent / "PrepareAssemblySources.py").read_bytes()), "assembly fixture preparer changed")
    require(receipt["controls_healthy"] and receipt["eligible_for_heldout"] is False and receipt["passed"] is False, "assembly source coverage changed")
    files = manifest["records"]
    require(tuple(row["name"] for row in files) == NAMES and len(files) == manifest["reader_fixture_count"] == 3, "assembly discovery fixture membership differs")
    require({p.name for p in CORPUS.glob("*.SLDASM")} == {row["file"] for row in files} == {name + ".SLDASM" for name in NAMES}, "assembly discovery native file membership differs")
    observations = {row["name"]: row for row in receipt["discovery_diagnostics"]}
    native = {row["name"]: row for row in receipt["cases"] if row["split"] == "discovery"}
    for row in files:
        require(row["split"] == "discovery" and row["source_sha256"] == native[row["name"]]["native_sha256"], "assembly native discovery identity differs")
        require(row["source_reopen_warnings"] == observations[row["name"]]["open_warnings"], "assembly original load warning changed")
    return files


def reference_updates(model_map, resolved_map):
    rows, seen = [], set()
    for stream, reader in ((CONFIG, model_map), (RESOLVED, resolved_map)):
        for index, entry in sorted(reader.table.items()):
            if entry[0] != "obj":
                continue
            node = entry[1]
            if not isinstance(node, Obj) or node.cls not in REFERENCE_CLASSES or id(node) in seen:
                continue
            seen.add(id(node))
            fields = {key: node.f.get(key) for key in UPDATE_FIELDS}
            require(all(type(value) is int for value in fields.values()), f"unmodeled update fields in {node.cls}")
            rows.append({"class": node.cls, "stream": stream, "archive_index": index, "fields": fields})
    return rows


def decoded_state(archive, reg, resolved_complete):
    model_doc, model_map = load_config(archive.require(CONFIG), reg, 19000, archive=archive, name=CONFIG)
    header_doc, header_map = load_rooted(archive.require(HEADER), reg, 1, 19000)
    require(not model_doc.tail and not header_doc.tail, "assembly projection has unread bytes")
    require(len(model_doc.roots) == 1 and model_doc.roots[0].cls == "moAssembly_c", "assembly root class differs")
    model = model_doc.roots[0]
    headers = [item for item in header_doc.roots if isinstance(item, Obj) and item.cls == "moHeader_c"]
    require(len(headers) == 1, "assembly header has no unique typed owner")
    header = headers[0]
    fields = {key: model.f.get(key) for key in ("f1560", "f1570", "f1a18", "f1a20", "f1a28", "f1674")}
    count = Counter(item[1].cls for item in model_map.table.values() if item[0] == "obj" and isinstance(item[1], Obj))
    result = {
        "assembly_owned_fields": fields,
        "self_component_class": model["f990"].cls if isinstance(model.f.get("f990"), Obj) else None,
        "header_scalar_fields": {key: header.f.get(key) for key in ("f40", "f48", "fc4")},
        "configuration_graph": GraphProof(model_doc, model_map, CONFIG),
        "header_graph": GraphProof(header_doc, header_map, HEADER),
        "configuration_class_counts": dict(sorted(count.items())),
    }
    if resolved_complete:
        resolved_doc, resolved_map = load_resolved(archive.require(RESOLVED), reg, 19000, archive=archive, name=RESOLVED, seed=model_map.map_state())
        require(not resolved_doc.tail and not resolved_map.left(), "assembly resolved projection has unread bytes")
        result["resolved_graph"] = GraphProof(resolved_doc, resolved_map, RESOLVED, {"document": model_doc, "reader": model_map})
        result["reference_update_fields"] = reference_updates(model_map, resolved_map)
    return result


def inspect_file(entry):
    path = CORPUS / entry["file"]
    require(not path.is_symlink() and path.resolve().parent == CORPUS.resolve(), "assembly fixture escaped its corpus")
    raw = path.read_bytes()
    require(len(raw) == entry["bytes"] and digest(raw) == entry["sha256"], "prepared assembly fixture changed")
    archive = SldprtArchive.from_bytes(raw, path)
    streams = {row["name"]: row for row in entry["streams"]}
    require(len(streams) == len(entry["streams"]) and set(streams) == set(archive.streams), "assembly discovery stream membership differs")
    require(all(digest(data) == streams[name]["sha256"] and len(data) == streams[name]["bytes"] for name, data in archive.streams.items()), "assembly discovery stream identity differs")
    reg = registry()
    result = {"file": entry["file"], "prepared_sha256": entry["sha256"], "original_sha256": entry["source_sha256"], "native_reopen_warnings": entry["source_reopen_warnings"], "passed": False}
    result["roundtrip"] = one(path, list(REQUIRED), reg, {**PLANS, **reg.plans}, True, False)
    observed = result["roundtrip"]["streams"]
    if all(observed.get(key, {}).get("passed") for key in (CONFIG, HEADER)):
        result["wire_state"] = decoded_state(archive, reg, observed.get(RESOLVED, {}).get("passed", False))
    require(path.read_bytes() == raw, "assembly discovery input changed during decoding")
    result["passed"] = result["roundtrip"]["passed"] and "wire_state" in result
    return result


def main():
    parser = argparse.ArgumentParser(description="Correlate three immutable assembly discovery saves without establishing native writer support")
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    result = {"schema": "kit.sw2026.assembly-discovery-decoding.v1", "passed": False, "native_acceptance": False, "heldout_payloads_read": False, "writer_output_count": 0, "files": []}
    try:
        result["source_proof"] = [{"file": str(Path(__file__).relative_to(ROOT)), "sha256": digest(Path(__file__).read_bytes())}, *SourceProof()]
        for entry in fixture_inputs():
            try:
                value = inspect_file(entry)
            except Exception as error:
                value = {"file": entry["file"], "passed": False, "error": repr(error), "trace": traceback.format_exc(limit=8)}
            result["files"].append(value)
        result["comparison_count"] = sum(len(row.get("roundtrip", {}).get("streams", {})) for row in result["files"])
        result["passed"] = len(result["files"]) == 3 and result["comparison_count"] == 21 and all(row["passed"] for row in result["files"])
    except Exception as error:
        result.update(error=repr(error), trace=traceback.format_exc(limit=8))
    with args.report.open("x", encoding="utf-8") as out:
        out.write(json.dumps(result, ensure_ascii=True, allow_nan=False, indent=2) + "\n")
    print(json.dumps({"passed": result["passed"], "comparisons": result.get("comparison_count", 0), "files": [{key: row[key] for key in ("file", "passed", "error") if key in row} for row in result["files"]]}))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
