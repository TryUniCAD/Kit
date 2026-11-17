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
MANAGER_HEADER = "Contents/CMgrHdr2"


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


def child_state(archive, reg, header):
    config_doc, _ = load_config(archive.require(CONFIG), reg, 19000, archive=archive, name=CONFIG)
    require(not config_doc.tail, "synchronized child archive projection is incomplete")
    require(len(config_doc.roots) == 1 and config_doc.roots[0].cls == "moPart_c", "synchronized child is not an ordinary part")
    return {"f40": header["f40"], "f48": header["f48"], "f1300": config_doc.roots[0]["f1300"]}


def typed_header(archive, reg, stream, cls):
    document, reader = load_rooted(archive.require(stream), reg, 1, 19000)
    require(not document.tail and not reader.left(), f"{stream} projection has unread bytes")
    headers = [node for node in document.roots if isinstance(node, Obj) and node.cls == cls]
    require(len(headers) == 1, f"{stream} has no unique {cls} owner")
    return headers[0]


def save_times(archive, reg, headers):
    manager = typed_header(archive, reg, MANAGER_HEADER, "dmConfigMgrHeader_c")
    configurations = [row["o"] for row in manager["f08"]["items"]]
    require(all(isinstance(node, Obj) and node.cls == "dmConfigHeader_c" for node in configurations), "configuration manager header contains an unexpected entry")
    return {
        "self_file_modified_at": {stream: None if header["f38"] is None else header["f38"]["f60"] for stream, header in headers.items()},
        "configuration_manager_saved_at": manager["f60"],
        "configuration_tree_sort_order": manager["f68"],
        "configuration_headers": [node.f for node in configurations],
    }


def reference_entry(node):
    require(isinstance(node, Obj) and node.cls == "moExtObject_c", "ordinary external directory has an unexpected object kind")
    definition = node["shared"]
    stem = definition["h10"]
    selected = node["refcfg"]
    return {
        "class": node.cls,
        "document_kind": definition["f20"],
        "filename_stem": stem["f08"] if isinstance(stem, Obj) else None,
        "creation_timestamp": definition["f28"],
        "reference_index": node["f78"],
        "configuration": {"id": selected["f10"], "name": selected["f08"]},
        "registration_counts": {key: node[key] for key in ("f48", "f4c", "f50")},
        "timestamps": {key: node[key] for key in ("f60", "f70")},
        "persisted_state": {key: node[key] for key in ("f54", "f58")},
    }


def file_directory(headers):
    result = {}
    for stream, header in headers.items():
        listing = header["f30"]
        owner = header["f38"]
        entries = [] if listing is None else [reference_entry(row["o"]) for row in listing["items"]]
        result[stream] = {
            "entries": entries,
            "self": None if owner is None else reference_entry(owner),
            "list_class": None if listing is None else listing.cls,
            "array_slots": len(entries) + int(owner is not None),
            "active_component_count": header["fc4"],
        }
    return result


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
    report = one(path, [*REQUIRED, MANAGER_HEADER], reg, {**PLANS, **reg.plans}, True, False)
    result = {"file": path.name, "sha256": entry["sha256"], "passed": report["passed"], "roundtrip": report}
    compared = report["streams"]
    if all(compared.get(key, {}).get("passed") for key in (CONFIG, HEADER, RESOLVED, MANAGER_HEADER)):
        headers = {stream: typed_header(archive, reg, stream, "moHeader_c") for stream in ("Header2", HEADER)}
        result["wire_state"] = decoded_state(archive, reg, True) if entry["role"] == "parent" else child_state(archive, reg, headers[HEADER])
        result["save_times"] = save_times(archive, reg, headers)
        if entry["role"] == "parent":
            result["external_file_directories"] = file_directory(headers)
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
        bindings = [entry["external_binding"] for entry in stamps]
        require(all(binding["header_alias"] and binding["class"] == "moExtObject_c" for binding in bindings), "occurrence does not point to a typed header object")
        require(len({binding["direct_index"] for binding in bindings}) == int(count > 0), "repeated occurrences do not share one external header object")
        require(all(parent["wire_state"][key]["unresolved_references"] == 0 for key in ("configuration_graph", "resolved_graph")), "synchronized assembly graph still has unresolved references")
        if child is not None:
            state = child["wire_state"]
            row["reference_checks"] = [
                {"archive_index": stamp["archive_index"], "update_matches_child": stamp["fields"]["f3e0"] == state["f40"], "time_matches_child": stamp["fields"]["f3e8"] == state["f48"], "geometry_matches_child": stamp["fields"]["f3f4"] == state["f1300"]}
                for stamp in stamps
            ]
            times = child["save_times"]
            directory_checks = {}
            for stream, directory in parent["external_file_directories"].items():
                require(len(directory["entries"]) == 1, "synchronized disclosure requires the one referenced child file")
                entry = directory["entries"][0]
                directory_checks[stream] = {
                    "modified_matches_child_self": entry["timestamps"]["f60"] == times["self_file_modified_at"][HEADER],
                    "saved_matches_child_manager": entry["timestamps"]["f70"] == times["configuration_manager_saved_at"],
                }
            row["external_file_time_checks"] = directory_checks
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
        report["external_file_time_comparisons"] = sum(len(checks) for row in report["cases"] for checks in row.get("external_file_time_checks", {}).values())
        report["passed"] = report["stream_comparisons"] == 40 and report["external_file_time_comparisons"] == 8 and all(row["passed"] for row in report["cases"])
    except Exception as error:
        report.update(error=repr(error), trace=traceback.format_exc(limit=8))
    with args.report.open("x", encoding="utf-8") as output:
        output.write(json.dumps(report, ensure_ascii=True, allow_nan=False, indent=2) + "\n")
    print(json.dumps({"passed": report["passed"], "stream_comparisons": report.get("stream_comparisons", 0), "cases": [{k:row[k] for k in ("name", "passed", "error") if k in row} for row in report["cases"]]}))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
