from codecs import lookup
from collections import Counter
from importlib import import_module
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from TraceCfgFont import ARCHIVE, CASES, REVISION, ROOT, PinnedSdk, audit_run, descriptor, digest, require

LABELS = "moLabelDefs_c"
BASE = "moDrViewLabelData_c"
DESCENDANTS = {
    "moDetailLabelData_c", "moSectionLabelData_c", "moAuxLabelData_c",
    "moOrthoLabelData_c", "moMiscLabelData_c", BASE,
}


def trace_case(run, bodies, name, data, version, header):
    read_schema = bodies.ReadSchemaMut
    counts = Counter()
    children, bases = [], []
    label = {}

    def trace(frame, layout):
        usage = frame.ContextValue.UsageValue
        if layout != LABELS and LABELS not in usage.SchemaPath:
            return read_schema(frame, layout)
        counts[layout] += 1
        if layout != LABELS and layout not in DESCENDANTS:
            return read_schema(frame, layout)
        reader = frame.ReaderValue
        start, before = reader.Cursor.GetOffset(), reader.MapValue.Snapshot()
        base = reader.MapValue.BaseValue
        lane = list(usage.FieldPath)
        conditions = frame.ContextValue.FlagsValue.get("conditions", 0)
        result = read_schema(frame, layout)
        end, after = reader.Cursor.GetOffset(), reader.MapValue.Snapshot()
        require(base == reader.MapValue.BaseValue == 4
                and before.CounterValue == after.CounterValue
                and len(before.EntriesValue) == len(after.EntriesValue)
                and all(left is right for left, right in zip(before.EntriesValue, after.EntriesValue, strict=True)),
                "the direct label call changed the real archive map")
        row = {"layout": layout, "interval": [start, end], "owner_fields": lane,
               "map_counter": before.CounterValue, "conditions": conditions,
               "wire_sha256": digest(data[start:end])}
        if layout == LABELS:
            class_entry, part_entry, header_entry = before.EntriesValue[:3]
            require(class_entry.EntryValue is frame.NodeValue.ClassValue
                    and part_entry.EntryValue is frame.NodeValue,
                    "the label definitions do not belong to the native part root")
            label.update(row, part=descriptor(frame.NodeValue), header_alias=descriptor(header_entry.EntryValue),
                         anchor_slots=[class_entry.IndexValue, part_entry.IndexValue, header_entry.IndexValue],
                         map_base=base, native_map_entries=len(before.EntriesValue))
        elif layout == BASE:
            fields = frame.ScopeValue.FieldsValue
            bases.append({**row, "f48": fields["f48"], "f50_present": "f50" in fields})
        else:
            children.append(row)
        return result

    bodies.ReadSchemaMut = trace
    try:
        result = run(data, version, header)
    finally:
        bodies.ReadSchemaMut = read_schema
    require(counts == {LABELS: 1, BASE: 5, **{layout: 1 for layout in DESCENDANTS - {BASE}},
                       "utCharFormat_c": 31, "utLineWidth_c.Serialize0": 10}
            and len(children) == len(bases) == 5 and result.ReportValue["completed"],
            f"{name} did not reach the expected complete native label profile")
    return {"labels": label, "layout_calls": dict(counts), "children": children, "bases": bases,
            "pinned_config_next_slot": result.MapValue.CounterValue}


def main():
    sys.meta_path.insert(0, PinnedSdk())
    config_reader = import_module(ARCHIVE + "Config.ReadConfigMut").ReadConfigMut
    header_reader = import_module(ARCHIVE + "Header.ReadNativeHeader").ReadHeaderGraph
    bodies = import_module(ARCHIVE + "Bodies.ReadBodyMut")
    container = import_module("convert.adapters.solidworks.Container.Container").SldprtArchive
    archive_version = import_module("convert.adapters.solidworks.Container.Archive").ContainerMo
    sources = {name: (path, expected, (ROOT / path).read_bytes())
               for name, (path, expected) in CASES.items()}
    for codec in ("ascii", "latin-1", "cp1252", "utf-16-le"):
        lookup(codec)
    sys.addaudithook(audit_run)
    controls = {}
    for name, (path, expected, source) in sources.items():
        require(digest(source) == expected, "wrong tracked part source")
        archive = container.from_bytes(source)
        version = archive_version(archive.streams)
        require(archive.format_version == 4 and version == 19000, "wrong configuration profile")
        data = archive.require("Contents/Config-0")
        header = archive.require("Contents/Config-0-ModelHeader")
        result = trace_case(config_reader, bodies, name, data, version, header_reader(header, version))
        result.update(path=path, source_sha256=expected, config_sha256=digest(data), header_sha256=digest(header))
        controls[name] = result
    print(json.dumps({"pinned_archive_reader": REVISION, "format_version": 4, "archive_version": 19000,
                      "native_controls": controls, "runtime_external_accesses": 0},
                     indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
