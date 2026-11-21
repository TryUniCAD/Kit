from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from convert import open_document


def inventory_sources(path, expected_digest):
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_digest:
        raise ValueError("neutral source inventory digest changed")
    inventory = json.loads(raw)
    rows = inventory["inputs"]
    hashes = {row["sha256"] for row in rows}
    if len(rows) != len(hashes) or len(hashes) != inventory["distinct_sha256"]:
        raise ValueError("each neutral source identity must appear exactly once")
    return rows


def source_bytes(row):
    for candidate in row["paths"]:
        try:
            data = Path(candidate).read_bytes()
        except FileNotFoundError:
            continue
        if len(data) != row["bytes"] or hashlib.sha256(data).hexdigest() != row["sha256"]:
            raise ValueError("neutral source no longer matches its inventory")
        return data
    raise FileNotFoundError("no location remains for the neutral source identity")


def measure(rows, inventory_digest):
    status = Counter()
    definitions = Counter()
    features = Counter()
    relations = Counter()
    assembly_count = 0
    diagnostic_count = 0
    for row in rows:
        try:
            document = open_document(
                source_bytes(row),
                source_format="freecad.fcstd",
                strict=True,
                include_brep=False,
                include_tessellation=False,
            )
        except Exception as error:
            status[f"error:{type(error).__name__}"] += 1
            continue
        status["read"] += 1
        assembly_count += document.assembly is not None
        diagnostic_count += bool(document.diagnostics)
        features.update(set(row["object_types"]))
        definitions.update({
            type(step.definition).__name__
            for step in document.feature_timeline
            if step.definition is not None
        })
        relations.update({
            relation.kind
            for sketch in document.sketches
            for relation in sketch.constraints
        })
    return {
        "schema": "kit.sw2026.neutral-corpus-read-inventory.v1",
        "input_inventory_sha256": inventory_digest,
        "source_count": len(rows),
        "sdk_options": {"strict": True, "include_brep": False, "include_tessellation": False},
        "status_counts": dict(status),
        "assembly_documents": assembly_count,
        "documents_with_diagnostics": diagnostic_count,
        "declared_native_type_documents": dict(features),
        "timeline_definition_documents": dict(definitions),
        "sketch_relation_documents": dict(relations),
        "original_benchmark_membership_verified": False,
        "native_outputs_written": 0,
        "accepted_conversions": 0,
    }


def main():
    parser = argparse.ArgumentParser(description="Measure strict FreeCAD neutral reads against a hash-locked source inventory")
    parser.add_argument("inventory", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--inventory-sha256", required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output must not exist")
    rows = inventory_sources(args.inventory, args.inventory_sha256)
    result = measure(rows, args.inventory_sha256)
    with args.output.open("x") as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps({"source_count": len(rows), "status_counts": result["status_counts"]}))
    return 0 if result["status_counts"].get("read") == len(rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
