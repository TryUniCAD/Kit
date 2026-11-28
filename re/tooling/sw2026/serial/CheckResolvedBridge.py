from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from Classes import registry
from defs.ConfigPart import load_config
from defs.ResolvedCore import load_resolved, load_resolved_compat, store_resolved_state, store_resolved_state_compat
from ResolvedSignature import resolved_signature
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive


def check(path):
    source = path.read_bytes()
    archive = SldprtArchive.from_bytes(source)
    version = ContainerMo(archive.streams)
    rules = registry()
    config_name = "Contents/Config-0"
    config, first = load_config(archive.require(config_name), rules, version, archive=archive, name=config_name)
    if config.tail:
        raise ValueError("configuration seed is incomplete")
    seed = first.map_state()
    name = config_name + "-ResolvedFeatures"
    data = archive.require(name)
    legacy_doc, legacy_ar = load_resolved_compat(data, rules, version, archive=archive, name=name, seed=seed)
    with rules.track_usage("load", name, sources=archive.streams) as loaded:
        doc, reader = load_resolved(data, rules, version, archive=archive, name=name, seed=seed)
    with rules.track_usage("store", name) as stored:
        encoded, state = store_resolved_state(doc, rules, version, seed=seed)
    old_bytes, old_state = store_resolved_state_compat(legacy_doc, rules, version, seed=seed)
    if encoded != data or old_bytes != data or doc.tail or legacy_doc.tail:
        raise ValueError("resolved bridge changed wire bytes or retained an unread tail")
    old_extra = legacy_doc.head.get("mbsm")
    new_extra = doc.head.get("mbsm")
    if resolved_signature(legacy_ar.map_state(), None if old_extra is None else old_extra.f) != resolved_signature(reader.map_state(), None if new_extra is None else new_extra.f):
        raise ValueError("resolved bridge changed decoded fields, aliases, positions or inline mapping")
    if resolved_signature(old_state) != resolved_signature(state) or reader.base != legacy_ar.base:
        raise ValueError("resolved bridge changed stored map membership or base")
    directions = {"load": loaded.snapshot(), "store": stored.snapshot()}
    for direction, report in directions.items():
        if not report["completed"] or report["provisional_schemas"] or report["missing_schemas"]:
            raise ValueError(f"resolved {direction} usage is incomplete or provisional")
        shared = [item for item in report["shared_schema_usage"] if item["codec"] == "sdk_ordinary_resolved"]
        if len(shared) != 1 or not shared[0]["admitted"] or not shared[0]["usage"]["completed"]:
            raise ValueError(f"resolved {direction} did not use the complete SDK profile")
    return {"file": path.name, "source_sha256": hashlib.sha256(source).hexdigest(), "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(), "output_sha256": hashlib.sha256(encoded).hexdigest(),
            "byte_identity_passed": True, "all_fields_aliases_positions_equal": True,
            "map_base": reader.base, "map_counter": reader.count, "root_count": len(doc.roots),
            "inline_mbsm_present": new_extra is not None, "usage": directions}


def main():
    parser = argparse.ArgumentParser(description="Check the actual SDK resolved bridge against the research field reader")
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    if args.report.exists():
        raise ValueError("report path must be unused")
    rows = [check(path) for path in args.files]
    report = {"schema": "kit.sw2026.resolved-sdk-bridge.v1", "passed": True, "files": rows,
              "public_full_linked_graph": False, "native_application_runs": 0, "heldout_payloads_read": False,
              "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with args.report.open("x", encoding="utf-8") as output:
        json.dump(report, output, indent=2)
        output.write("\n")
    print(f"{len(rows)} complete resolved graphs and maps match the research reader")


if __name__ == "__main__":
    main()
