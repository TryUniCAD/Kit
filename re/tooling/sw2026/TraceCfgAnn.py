from codecs import lookup
from importlib import import_module
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

import TraceCfgFont as owner

REVISION = "e4093f012e61a6a4e2aafb029b376dcb23c50e9b"
LAYOUTS = {"moAnnotationDefs_c", "moBaseAnnotationDefs_c", "moGTolDataHelper_c", "moGTolDlgDataFrame_c"}


def capture(reader, body, data, version, header):
    read_schema = body.ReadSchemaMut
    rows = []

    def trace(frame, layout):
        if layout not in LAYOUTS:
            read_schema(frame, layout)
            return
        usage = frame.ContextValue.UsageValue
        cursor, maps = frame.ReaderValue.Cursor, frame.ReaderValue.MapValue
        start, before, fields = cursor.GetOffset(), maps.Snapshot(), list(usage.FieldPath)
        conditions = frame.ContextValue.FlagsValue.get("conditions", 0)
        read_schema(frame, layout)
        end, after = cursor.GetOffset(), maps.Snapshot()
        class_entry, part_entry, alias = before.EntriesValue[:3]
        owner.require(maps.BaseValue == 4 and before.CounterValue == after.CounterValue
                      and all(a is b for a, b in zip(before.EntriesValue, after.EntriesValue, strict=True))
                      and class_entry.EntryValue is frame.NodeValue.ClassValue and part_entry.EntryValue is frame.NodeValue,
                      "annotation embedding changed the physical part alias or archive map")
        scope = frame.ScopeValue.FieldsValue
        keys = {"moBaseAnnotationDefs_c": ("f44",), "moGTolDataHelper_c": ("n08",),
                "moGTolDlgDataFrame_c": ("f148", "f10", "f18", "n2b8")}.get(layout, ())
        rows.append({"layout": layout, "interval": [start, end], "wire_sha256": owner.digest(data[start:end]),
                     "map_counter": before.CounterValue, "conditions": conditions, "field_path": fields,
                     "map_anchor_slots": [class_entry.IndexValue, part_entry.IndexValue, alias.IndexValue],
                     "part": owner.descriptor(frame.NodeValue), "alias": owner.descriptor(alias.EntryValue),
                     "selectors": {key: scope[key] for key in keys}})

    body.ReadSchemaMut = trace
    try:
        graph = reader(data, version, header)
    finally:
        body.ReadSchemaMut = read_schema
    owner.require(graph.ReportValue["completed"], "pinned reader did not consume the original configuration")
    owner.require(len(rows) == 14, "source did not reach all ten annotation bases, both owners and two frames")
    return rows, graph.MapValue.CounterValue


def main():
    owner.REVISION = REVISION
    sys.meta_path.insert(0, owner.PinnedSdk())
    container = import_module("convert.adapters.solidworks.Container.Container").SldprtArchive
    version_of = import_module("convert.adapters.solidworks.Container.Archive").ContainerMo
    config_reader = import_module(owner.ARCHIVE + "Config.ReadConfigMut").ReadConfigMut
    header_reader = import_module(owner.ARCHIVE + "Header.ReadNativeHeader").ReadHeaderGraph
    body = import_module(owner.ARCHIVE + "Bodies.ReadBodyMut")
    sources = {name: (path, expected, (owner.ROOT / path).read_bytes())
               for name, (path, expected) in owner.CASES.items()}
    for codec in ("ascii", "latin-1", "cp1252", "utf-16-le"):
        lookup(codec)
    sys.addaudithook(owner.audit_run)
    cases = {}
    for name, (path, expected, source) in sources.items():
        owner.require(owner.digest(source) == expected, "tracked source was changed")
        archive = container.from_bytes(source)
        version = version_of(archive.streams)
        owner.require(archive.format_version == 4 and version == 19000, "unsupported tracked source version")
        config = archive.require("Contents/Config-0")
        header = archive.require("Contents/Config-0-ModelHeader")
        rows, end = capture(config_reader, body, config, version, header_reader(header, version))
        cases[name] = {"path": path, "part_sha256": expected, "config_sha256": owner.digest(config),
                       "header_sha256": owner.digest(header), "config_bytes": len(config), "config_next_slot": end,
                       "rows": rows}
    print(json.dumps({"trace_revision": REVISION, "archive_version": 19000, "format_version": 4,
                      "native_launches": 0, "runtime_external_accesses": 0, "cases": cases},
                     indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
