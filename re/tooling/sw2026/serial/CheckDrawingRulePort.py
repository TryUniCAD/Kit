from __future__ import annotations

import argparse
import json
from pathlib import Path

from CheckDrawingDefinitions import DISCLOSED, SOURCE_LOCK, checked_artifacts, digest, require
from CheckDrawingPrefix import concept_registry, project_model, read_concept
from DrawingReadRules import VERSION, compile_methods
from ReadDrawingConcept import ConceptReader

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Drawing.Identity.DrawingIdentity import CheckDrawLane


def normalize_fields(value):
    if isinstance(value, ArchiveNode):
        return ("node", value.IndexValue)
    if isinstance(value, tuple) and len(value) == 2 and value[0] == "A":
        return value[1]
    if isinstance(value, dict):
        return {key: normalize_fields(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return tuple(normalize_fields(item) for item in value)
    return value


def compare_maps(left_map, right_map):
    require(tuple(left_map) == tuple(right_map), "drawing concept map indices differ")
    objects = 0
    for index in left_map:
        left, right = left_map[index].EntryValue, right_map[index].EntryValue
        if isinstance(left, ArchiveNode) and isinstance(right, ArchiveNode):
            require(
                (left.ClassValue, left.StartOffset, left.EndOffset, left.IndexValue)
                == (right.ClassValue, right.StartOffset, right.EndOffset, right.IndexValue),
                f"drawing object boundary differs for archive slot {index}",
            )
            require(
                normalize_fields(left.FieldsValue) == normalize_fields(right.FieldsValue),
                f"drawing fields differ for archive slot {index}",
            )
            objects += 1
        else:
            require(left == right, f"drawing runtime descriptor differs for archive slot {index}")
    return objects


def case_result(root, case, rules):
    saved, authored, _ = checked_artifacts(root, case)
    archive = SldprtArchive.from_bytes(saved)
    version = CheckDrawLane(archive)
    require(version == VERSION, "source belongs to a different schema release")
    definition = archive.require("Contents/Definition")
    model, reference, audit = read_concept(definition, concept_registry(), version)
    port = ConceptReader(definition, version, rules)
    port_model = port.root()
    graph = port.reader
    require(
        graph.Cursor.GetOffset() == reference.p
        and graph.MapValue.CounterValue == reference.count
        and set(port.calls) == set(audit["used_schemas"]),
        "drawing port advanced a different cursor, map or method set",
    )
    require(port_model.IndexValue == model.IndexValue, "drawing root object identity differs")
    count = compare_maps(graph.MapValue.EntryMap, reference._maps.EntryMap)
    return {
        "name": case["name"],
        "source_sha256": digest(saved),
        "concept_prefix_bytes": reference.p,
        "map_next_index": reference.count,
        "object_count": count,
        "method_count": len(port.calls),
        "native_views": project_model(model, authored),
    }


def main():
    parser = argparse.ArgumentParser(description="Compare source-only drawing read rules using the SDK graph primitives")
    parser.add_argument("corpus", type=Path)
    parser.add_argument("--source-lock", type=Path, default=SOURCE_LOCK)
    args = parser.parse_args()
    lock = args.source_lock.read_bytes()
    cases = {case["name"]: case for case in json.loads(lock)["cases"] if case["name"] in DISCLOSED}
    rules = compile_methods()
    result = {
        "schema": "kit.sw2026.drawing-rule-port.v1",
        "source_lock_sha256": digest(lock),
        "native_archive_version": VERSION,
        "source_rule_sha256": digest(json.dumps(rules, sort_keys=True, separators=(",", ":")).encode()),
        "cases": [case_result(args.corpus, cases[name], rules) for name in DISCLOSED],
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
