from __future__ import annotations

import argparse
import hashlib
import json
import struct
from collections.abc import Mapping
from pathlib import Path

from Classes import registry
from Core import Obj
from defs.ConfigPart import header_direct_objects, load_config, load_config_compat, store_config_state, store_config_state_compat
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive


def signature(state, direct):
    pins = {id(entry.EntryValue): entry.IndexValue for entry in state.state.EntriesValue if isinstance(entry.EntryValue, ArchiveNode)}
    direct_ids = {id(node) for node in direct}
    embedded, active = {}, set()

    def value(item):
        if isinstance(item, ArchiveNode):
            if id(item) in pins:
                return ("reference", pins[id(item)])
            if id(item) in active:
                return ("embedded_reference", embedded[id(item)])
            label = embedded.setdefault(id(item), len(embedded))
            active.add(id(item))
            return ("embedded", label, item.ClassValue, value(item.FieldsValue))
        if isinstance(item, Mapping):
            return {key: value(child) for key, child in item.items()}
        if isinstance(item, (list, tuple)):
            return (type(item).__name__, [value(child) for child in item])
        if isinstance(item, float):
            return ("float64", struct.pack("<d", item).hex())
        return item

    rows = []
    for entry in state.state.EntriesValue:
        node = entry.EntryValue
        if isinstance(node, ArchiveNode):
            body = "header_alias" if id(node) in direct_ids else value(node.FieldsValue)
            rows.append((entry.IndexValue, node.ClassValue, body, None if body == "header_alias" else (node.StartOffset, node.EndOffset, node.IndexValue)))
        else:
            rows.append((entry.IndexValue, node))
    return state.count, rows


def check(path):
    source = path.read_bytes()
    archive = SldprtArchive.from_bytes(source)
    version = ContainerMo(archive.streams)
    name = "Contents/Config-0"
    data = archive.require(name)
    rules = registry()
    legacy_doc, legacy_ar = load_config_compat(data, rules, version, archive=archive, name=name)
    with rules.track_usage("load", name, sources=archive.streams) as loaded:
        doc, reader = load_config(data, rules, version, archive=archive, name=name)
    with rules.track_usage("store", name) as stored:
        encoded, state = store_config_state(doc, rules, version)
    old_bytes, old_state = store_config_state_compat(legacy_doc, rules, version)
    if old_bytes != data or encoded != data or doc.tail or legacy_doc.tail:
        raise ValueError("configuration bridge changed native bytes or retained an unread tail")
    old_direct = header_direct_objects(legacy_doc.head["model_header"], version)
    direct = header_direct_objects(doc.head["model_header"], version)
    if signature(legacy_ar.map_state(), old_direct) != signature(reader.map_state(), direct):
        raise ValueError("configuration bridge changed decoded fields, aliases, descriptors or positions")
    if signature(old_state, old_direct) != signature(state, direct) or legacy_ar.base != reader.base:
        raise ValueError("configuration bridge changed stored map ownership")
    directions = {"load": loaded.snapshot(), "store": stored.snapshot()}
    for direction, report in directions.items():
        if not report["completed"] or report["provisional_schemas"] or report["missing_schemas"]:
            raise ValueError(f"configuration {direction} usage is incomplete or provisional")
        shared = [item for item in report["shared_schema_usage"] if item["codec"] == "sdk_ordinary_config"]
        if len(shared) != 1 or not shared[0]["admitted"] or not shared[0]["usage"]["completed"]:
            raise ValueError(f"configuration {direction} did not use the complete SDK profile")
    return {"file": path.name, "source_sha256": hashlib.sha256(source).hexdigest(),
            "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
            "output_sha256": hashlib.sha256(encoded).hexdigest(), "byte_identity_passed": True,
            "all_fields_aliases_positions_equal": True, "map_base": reader.base, "map_counter": reader.count,
            "header_direct_count": len(direct), "usage": directions}


def main():
    parser = argparse.ArgumentParser(description="Verify SDK Config linkage against the independent research field reader")
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    if args.report.exists():
        raise ValueError("report path must be unused")
    rows = [check(path) for path in args.files]
    report = {"schema": "kit.sw2026.config-sdk-bridge.v1", "passed": True,
              "files": rows, "public_full_linked_graph": False, "native_application_runs": 0,
              "heldout_payloads_read": False, "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with args.report.open("x", encoding="utf-8") as output:
        json.dump(report, output, indent=2)
        output.write("\n")
    print(f"{len(rows)} complete Config graphs and maps match the research reader")


if __name__ == "__main__":
    main()
