from __future__ import annotations

import argparse
import json
import traceback
from pathlib import Path

from AssemblySources import CONFIG, HEADER, RESOLVED, ROOT, decoded_state, digest, read_object, require
from Classes import registry
from Core import Obj
from RoundTrip import PLANS, REQUIRED, one
from Streams import load_rooted
from defs.ConfigPart import load_config
from convert.adapters.solidworks.Container.Container import SldprtArchive


CORPUS = ROOT / "re/solidworks/v2026/corpus/assembly-synchronized"
LOCK = ROOT / "re/solidworks/v2026/heldout/AssemblySyncSourceLock.json"
CASES = ("A12SyncedEmpty", "A13SyncedSingle", "A14SyncedRepeat")


def inputs():
    manifest = read_object(CORPUS / "Manifest.json")
    proof = read_object(CORPUS / "SourceEvidence.json")
    lock = read_object(LOCK)
    require(manifest["schema"] == "kit.sw2026.synchronized-assembly-fixtures.v1" and proof["schema"] == "kit.sw2026.synchronized-assembly-preparation.v1", "unexpected synchronized fixture metadata")
    require(manifest["heldout_payloads_read"] is manifest["native_acceptance"] is proof["heldout_payloads_read"] is False and manifest["writer_output_count"] == 0, "synchronized corpus has unsupported scope")
    require(proof["archive_schemas_executed"] is proof["container_outputs_reparsed"] is False, "synchronized preparation exceeded its boundary")
    require(proof["manifest_sha256"] == digest((CORPUS / "Manifest.json").read_bytes()) and manifest["privacy_ledger_sha256"] == digest((CORPUS / "PrivacyLedger.json").read_bytes()), "synchronized fixture manifest or ledger changed")
    require(manifest["source_lock_sha256"] == digest(LOCK.read_bytes()) and lock["passed"] and lock["controls_healthy"] and lock["heldout_results_sealed"], "synchronized source lock changed")
    tooling = ROOT / "re/tooling/sw2026"
    require(proof["preparer_sha256"] == digest((tooling / "PrepareSyncedAssemblies.py").read_bytes()) and proof["base_preparer_sha256"] == digest((tooling / "PrepareAssemblySources.py").read_bytes()), "synchronized fixture preparer changed")
    require(proof["child_preparer_sha256"] == digest((tooling / "PrepareSyncedChild.py").read_bytes()), "synchronized child preparer changed")
    docs = {(row["name"], row["role"]): row for row in manifest["records"]}
    discovery = {row["name"]: row for row in lock["cases"] if row["split"] == "discovery"}
    require(tuple(discovery) == CASES and len(docs) == len(manifest["records"]) == 5, "synchronized discovery membership differs")
    for index, name in enumerate(CASES):
        row = discovery[name]
        parent = docs[name, "parent"]
        require(parent["file"] == name + ".SLDASM" and parent["source_sha256"] == row["native_sha256"], "synchronized parent pairing differs")
        if index:
            child = docs[name, "child"]
            require(child["file"] == name + "Child.SLDPRT" and child["source_sha256"] == row["synchronized_child"]["native_sha256"], "synchronized child pairing differs")
    require({p.name for p in CORPUS.glob("*.SLD*")} == {row["file"] for row in docs.values()}, "unexpected native payloads in synchronized corpus")
    return docs


def child_state(archive, reg):
    header_doc, _ = load_rooted(archive.require(HEADER), reg, 1, 19000)
    config_doc, _ = load_config(archive.require(CONFIG), reg, 19000, archive=archive, name=CONFIG)
    headers = [node for node in header_doc.roots if isinstance(node, Obj) and node.cls == "moHeader_c"]
    require(not header_doc.tail and not config_doc.tail and len(headers) == 1, "synchronized child archive projection is incomplete")
    require(len(config_doc.roots) == 1 and config_doc.roots[0].cls == "moPart_c", "synchronized child is not an ordinary part")
    return {"f40": headers[0]["f40"], "f48": headers[0]["f48"], "f1300": config_doc.roots[0]["f1300"]}


def inspect(entry):
    path = CORPUS / entry["file"]
    require(not path.is_symlink() and path.resolve().parent == CORPUS.resolve(), "synchronized fixture is outside its corpus")
    raw = path.read_bytes()
    require(len(raw) == entry["bytes"] and digest(raw) == entry["sha256"], "synchronized fixture changed")
    archive = SldprtArchive.from_bytes(raw, path)
    actual = {name: (len(data), digest(data)) for name, data in archive.streams.items()}
    planned = {row["name"]: (row["bytes"], row["sha256"]) for row in entry["streams"]}
    require(len(planned) == len(entry["streams"]) and planned == actual, "synchronized stream identities do not match their ledger")
    reg = registry()
    report = one(path, list(REQUIRED), reg, {**PLANS, **reg.plans}, True, False)
    result = {"file": path.name, "sha256": entry["sha256"], "passed": report["passed"], "roundtrip": report}
    compared = report["streams"]
    if all(compared.get(key, {}).get("passed") for key in (CONFIG, HEADER, RESOLVED)):
        result["wire_state"] = decoded_state(archive, reg, True) if entry["role"] == "parent" else child_state(archive, reg)
    require(path.read_bytes() == raw, "synchronized fixture was mutated")
    result["passed"] = result["passed"] and "wire_state" in result
    return result


def inspect_pair(docs, name, count):
    parent = inspect(docs[name, "parent"])
    child = inspect(docs[name, "child"]) if count else None
    records = [parent, child] if child is not None else [parent]
    row = {"name": name, "records": records, "passed": all(item["passed"] for item in records)}
    if row["passed"]:
        stamps = parent["wire_state"]["reference_update_fields"]
        require(len(stamps) == count, "synchronized assembly reference count differs")
        if child is not None:
            state = child["wire_state"]
            row["reference_checks"] = [
                {"archive_index": stamp["archive_index"], "update_matches_child": stamp["fields"]["f3e0"] == state["f40"], "time_matches_child": stamp["fields"]["f3e8"] == state["f48"], "geometry_matches_child": stamp["fields"]["f3f4"] == state["f1300"]}
                for stamp in stamps
            ]
    return row


def main():
    parser = argparse.ArgumentParser(description="Compare synchronized assembly reference state with the exact saved child")
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    report = {"schema": "kit.sw2026.synchronized-assembly-readback.v1", "passed": False, "heldout_payloads_read": False, "native_acceptance": False, "writer_output_count": 0, "cases": []}
    try:
        docs = inputs()
        for count, name in enumerate(CASES):
            try:
                result = inspect_pair(docs, name, count)
            except Exception as error:
                result = {"name": name, "passed": False, "error": repr(error), "trace": traceback.format_exc(limit=8)}
            report["cases"].append(result)
        report["stream_comparisons"] = sum(len(item["roundtrip"]["streams"]) for row in report["cases"] for item in row.get("records", []))
        report["passed"] = report["stream_comparisons"] == 35 and all(row["passed"] for row in report["cases"])
    except Exception as error:
        report.update(error=repr(error), trace=traceback.format_exc(limit=8))
    with args.report.open("x", encoding="utf-8") as output:
        output.write(json.dumps(report, ensure_ascii=True, allow_nan=False, indent=2) + "\n")
    print(json.dumps({"passed": report["passed"], "stream_comparisons": report.get("stream_comparisons", 0), "cases": [{k:row[k] for k in ("name", "passed", "error") if k in row} for row in report["cases"]]}))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
