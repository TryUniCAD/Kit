from codecs import lookup
from importlib import import_module
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

import TraceCfgFont as source

REVISION = "fe592b8e7a4922dccf8298541453baf41d60b001"
FINISH = "moSFDataHelper_c"
ANNOTATION = "moAnnotationDataHelper_c"
FONT = "utCharFormat_c"
ROLES = (("f2e8",), ("f730", "f260"), ("f730", "f268"))


def field_digest(fields):
    return source.digest(json.dumps(fields, separators=(",", ":"), sort_keys=True,
                                    allow_nan=False).encode())


def wanted():
    rows = {}
    for role in ROLES:
        rows[role] = FINISH
        rows[role + ("fc0",)] = FONT
        rows[role + ("f128",)] = ANNOTATION
        rows[role + ("f128", "f08")] = FONT
    return rows


def guard_runtime():
    events = []

    def observe(event, args):
        try:
            source.audit_run(event, args)
        except PermissionError:
            events.append(event)
            raise

    for codec in ("ascii", "latin-1", "cp1252", "utf-16-le"):
        lookup(codec)
    sys.addaudithook(observe)
    return events


def capture(reader, body, data, version, header, linked_header):
    expected = wanted()
    records = {}
    run = body.ReadSchemaMut

    def instrument(frame, layout):
        path = frame.ContextValue.UsageValue.FieldPath
        if "fae0" not in path:
            return run(frame, layout)
        role = tuple(path[path.index("fae0") + 1:])
        if expected.get(role) != layout:
            return run(frame, layout)

        tape = frame.ReaderValue.Cursor
        maps = frame.ReaderValue.MapValue
        start, base, before = tape.GetOffset(), maps.BaseValue, maps.Snapshot()
        run(frame, layout)
        end, after = tape.GetOffset(), maps.Snapshot()
        source.require(role not in records and base == maps.BaseValue == 4 and before == after
                       and all(old is current for old, current in
                               zip(before.EntriesValue, after.EntriesValue, strict=True)),
                       "an embedded finish interval changed its full physical map")
        class_anchor, part_anchor, header_anchor = before.EntriesValue[:3]
        source.require(
            [class_anchor.IndexValue, part_anchor.IndexValue, header_anchor.IndexValue] == [1, 2, 3]
            and class_anchor.EntryValue is frame.NodeValue.ClassValue
            and part_anchor.EntryValue is frame.NodeValue
            and header_anchor.EntryValue is linked_header,
            "finish helper lost the actual part or ModelHeader alias",
        )
        records[role] = {
            "role": list(role),
            "layout": layout,
            "interval": [start, end],
            "wire_sha256": source.digest(data[start:end]),
            "fields_sha256": field_digest(frame.ScopeValue.FieldsValue),
            "map_base": base,
            "map_counter": before.CounterValue,
            "map_entries": len(before.EntriesValue),
            "map_identity_preserved": True,
        }

    body.ReadSchemaMut = instrument
    try:
        graph = reader(data, version, header)
    finally:
        body.ReadSchemaMut = run
    source.require(graph.ReportValue["completed"] and records.keys() == expected.keys(),
                   "pinned Config-0 did not visit all three finish roles and their fonts")
    return [records[role] for role in expected], graph.MapValue.CounterValue


def main():
    source.REVISION = REVISION
    sys.meta_path.insert(0, source.PinnedSdk())
    container = import_module("convert.adapters.solidworks.Container.Container").SldprtArchive
    version_of = import_module("convert.adapters.solidworks.Container.Archive").ContainerMo
    reader = import_module(source.ARCHIVE + "Config.ReadConfigMut").ReadConfigMut
    header_reader = import_module(source.ARCHIVE + "Header.ReadNativeHeader").ReadHeaderGraph
    header_refs = import_module(source.ARCHIVE + "Header.HeaderRefNodes").HeaderRefNodes
    body = import_module(source.ARCHIVE + "Bodies.ReadBodyMut")
    originals = {name: (path, expected, (source.ROOT / path).read_bytes())
                 for name, (path, expected) in source.CASES.items()}
    external = guard_runtime()
    cases = {}
    for name, (path, expected, data) in originals.items():
        source.require(source.digest(data) == expected, "disclosed source identity changed")
        archive = container.from_bytes(data)
        version = version_of(archive.streams)
        source.require(archive.format_version == 4 and version == 19000,
                       "finish-helper evidence requires format 4 and archive version 19000")
        config = archive.require("Contents/Config-0")
        header_bytes = archive.require("Contents/Config-0-ModelHeader")
        header = header_reader(header_bytes, version)
        (linked_header,) = header_refs(header, version)
        rows, terminal = capture(reader, body, config, version, header, linked_header)
        cases[name] = {"path": path, "file_sha256": expected, "config_bytes": len(config),
                       "config_sha256": source.digest(config), "header_sha256": source.digest(header_bytes),
                       "config_next_slot": terminal, "rows": rows}
    source.require(not external, "physical traversal attempted external access")
    print(json.dumps({"trace_revision": REVISION, "archive_version": 19000, "format_version": 4,
                      "native_launches": 0, "runtime_external_accesses": len(external), "cases": cases},
                     indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
