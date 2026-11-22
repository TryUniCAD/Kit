from argparse import ArgumentParser
from importlib import import_module
import json
from pathlib import Path
from struct import pack
import sys

HERE = Path(__file__).resolve()
sys.path[:0] = [str(HERE.parents[3] / "src"), str(HERE.parent)]

from CfgFinishWire import authored
from FinishSdkPin import pinned_config
from TraceCfgFinish import FINISH, REVISION, ROLES, capture, field_digest, guard_runtime, source, wanted
from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyWriter import BodyWriter
from convert.adapters.solidworks.Archive.Bodies.FieldScope import FieldScope
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.FinishFields import KFinishFields
from convert.adapters.solidworks.Archive.Bodies.WriteBodyMut import WriteBodyMut
from convert.adapters.solidworks.Archive.Bodies.WriteFrame import WriteFrame
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteFieldsMut import WriteFieldsMut
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteSchemaMut import WriteSchemaMut
from convert.adapters.solidworks.Archive.Config.Finish.ReadCfgFinish import ReadCfgFinish
from convert.adapters.solidworks.Archive.Config.Link.CheckPartRoot import KPartRoot
from convert.adapters.solidworks.Archive.Config.Link.ReadPartStart import ReadPartStart
from convert.adapters.solidworks.Archive.Header.HeaderRefNodes import HeaderRefNodes
from convert.adapters.solidworks.Archive.Maps.AddEntryMut import AddEntryMut
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Maps.BindNodesMut import BindNodesMut
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.ExternalClass import ExternalClass
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive

RECEIPT = source.ROOT / "re/solidworks/measurements/2026/ConfigFinishPhysical01.json"
require, digest = source.require, source.digest


def map_state(maps):
    return (maps.BaseValue, maps.Snapshot(), dict(maps.ClassLookup), dict(maps.ObjectLookup))


def check_map(maps, before):
    after = map_state(maps)
    require(after == before and all(old is current for old, current in
                                    zip(before[1].EntriesValue, after[1].EntriesValue, strict=True)),
            "finish helper changed the inherited map")


def emit(fields, layout, part, maps):
    before = map_state(maps)
    context = BodyContext(19000, KFinishFields, {}, {})
    writer = BodyWriter(maps, context, WriteBodyMut)
    frame = WriteFrame(writer, FieldScope(fields), part, WriteSchemaMut, WriteFieldsMut)
    WriteSchemaMut(frame, layout)
    check_map(maps, before)
    return bytes(writer.OutputValue)


def check_scope(fields, row, config, part, maps):
    first, last = row["interval"]
    original = config[first:last]
    require(digest(original) == row["wire_sha256"] and field_digest(fields) == row["fields_sha256"],
            "finish owner field or wire digest differs from the physical trace")
    require(emit(fields, row["layout"], part, maps) == original,
            "finish owner did not re-emit its entire interval")
    return {key: row[key] for key in ("layout", "interval", "role", "fields_sha256", "wire_sha256")}


def exact_role(role, rows, config, part, maps):
    row = rows[role]
    first, last = row["interval"]
    before = map_state(maps)
    fields = ReadCfgFinish(config[first:last], 19000, part, maps)
    check_map(maps, before)
    finished = []
    for path in wanted():
        if path[:len(role)] != role:
            continue
        interval = rows[path]
        require(first <= interval["interval"][0] < interval["interval"][1] <= last,
                "finish child lies outside its parent")
        contained = fields
        for key in path[len(role):]:
            contained = contained[key]
        finished.append(check_scope(contained, interval, config, part, maps))
    require(len(finished) == 4, "finish body lost one of its embedded records")
    return finished


def map_checkpoint(role, maps):
    slots = list(maps.EntryMap)
    require(slots == list(range(1, maps.CounterValue)) and maps.BaseValue == 4,
            "native finish checkpoint has an incomplete or reordered map")
    rows = []
    for slot, cell in maps.EntryMap.items():
        item = cell.EntryValue
        if isinstance(item, (RuntimeClass, ExternalClass)):
            require(maps.ClassLookup.get(item) == slot, "native class inverse lookup differs from its slot")
            kind, descriptor, index = "class", item, None
        else:
            require(isinstance(item, ArchiveNode) and maps.ObjectLookup.get(id(item)) == slot,
                    "native object inverse lookup differs from its slot")
            kind, descriptor, index = "object", item.ClassValue, item.IndexValue
        definition = descriptor.SchemaValue if isinstance(descriptor, RuntimeClass) else descriptor.IndexValue
        rows.append([slot, kind, descriptor.NameValue, type(descriptor).__name__, definition, index])
    classes, objects = len(maps.ClassLookup), len(maps.ObjectLookup)
    require(classes + objects == len(slots) and classes > 0 and objects > 0, "native finish map lost mixed membership")
    return {"role": role, "base": maps.BaseValue, "counter": maps.CounterValue,
            "slots": slots, "classes": classes, "objects": objects, "slot_sha256": field_digest(rows)}


def trace_live_case(case, data):
    with pinned_config():
        reader = import_module(source.ARCHIVE + "Config.ReadConfigMut").ReadConfigMut
        header_reader = import_module(source.ARCHIVE + "Header.ReadNativeHeader").ReadHeaderGraph
        body = import_module(source.ARCHIVE + "Bodies.ReadBodyMut")
        external = guard_runtime()
        archive = SldprtArchive.from_bytes(data)
        config = archive.require("Contents/Config-0")
        header_bytes = archive.require("Contents/Config-0-ModelHeader")
        require(archive.format_version == 4 and ContainerMo(archive.streams) == 19000
                and digest(config) == case["config_sha256"] and digest(header_bytes) == case["header_sha256"],
                "native archive stream proof differs")
        seed = ReadPartStart(archive)
        (seed_alias,) = HeaderRefNodes(seed.HeaderValue, 19000)
        header = header_reader(header_bytes, 19000)
        (linked_header,) = HeaderRefNodes(header, 19000)
        prefix = [entry.IndexValue for entry in seed.MapValue.EntriesValue]
        require(prefix == [1, 2, 3] and seed.BaseValue == 4 and seed_alias.ClassValue == linked_header.ClassValue,
                "current SDK did not recover the native part and header prefix")

        checkpoints, checks = [], []

        def replay(role, rows, part, maps):
            require(part.ClassValue == seed.RootValue.ClassValue and part.IndexValue == seed.RootValue.IndexValue
                    and maps.EntryMap[3].EntryValue is linked_header, "finish helper received a foreign native prefix")
            checkpoints.append(map_checkpoint(role, maps))
            checks.extend(exact_role(role, rows, config, part, maps))

        native_rows, terminal = capture(reader, body, config, 19000, header, linked_header, replay)
        require(native_rows == case["rows"] and terminal == case["config_next_slot"],
                "live physical boundaries differ from the pinned receipt")
        require([row["role"] for row in checkpoints] == list(ROLES) and not external,
                "bounded native verification missed a checkpoint or used external data")
        return {"runtime_external_accesses": len(external), "prefix_anchors": prefix,
                "native_checkpoints": checkpoints, "exact_intervals": checks}


def native_case(name):
    trace = json.loads(RECEIPT.read_bytes())
    require(trace["trace_revision"] == REVISION, "finish source trace pin changed")
    case = trace["cases"][name]
    path, expected = source.CASES[name]
    data = (source.ROOT / path).read_bytes()
    require(case["path"] == path and digest(data) == expected == case["file_sha256"],
            "tracked original changed")
    return {"case": name, "native_source": expected, "trace_revision": REVISION} | trace_live_case(case, data)


def authored_root():
    maps = ArchiveMaps(1)
    part = ArchiveNode(KPartRoot, {}, IndexValue=2)
    AddEntryMut(maps, KPartRoot)
    AddEntryMut(maps, part)
    BindNodesMut(maps, (ArchiveNode(RuntimeClass("AuthoredHeader_c", 1), {}),))
    for base in range(4, 69, 4):
        descriptor = RuntimeClass(f"AuthoredFinish{base:03d}_c", 1)
        AddEntryMut(maps, descriptor)
        for slot in range(base + 1, min(base + 4, 69)):
            AddEntryMut(maps, ArchiveNode(descriptor, {"key": slot % 3}, IndexValue=slot))
    require(list(maps.EntryMap) == list(range(1, 69)), "authored map lacks an inherited slot")
    return part, maps


def refuses(label, expected, action):
    try:
        action()
    except ValueError as error:
        require(expected in str(error), f"{label} failed at the wrong boundary: {error}")
        return label
    raise ValueError(f"{label} crossed the finish helper boundary")


def wire_case():
    part, maps = authored_root()
    before = map_state(maps)
    external = guard_runtime()
    fields, wire = authored()
    read = ReadCfgFinish(wire, 19000, part, maps)
    check_map(maps, before)
    require(read == fields and emit(fields, FINISH, part, maps) == wire,
            "independent wire or authored fields did not round trip")
    wrong_part = ArchiveNode(KPartRoot, {}, IndexValue=part.IndexValue)
    refusals = [
        refuses("truncated", "truncated SOLIDWORKS archive field",
                lambda: ReadCfgFinish(wire[:-1], 19000, part, maps)),
        refuses("trailing", "trailing data",
                lambda: ReadCfgFinish(wire + b"\x00", 19000, part, maps)),
        refuses("wrong_version", "requires archive version 19000",
                lambda: ReadCfgFinish(wire, 18900, part, maps)),
        refuses("unmapped_part", "requires its inherited part owner",
                lambda: ReadCfgFinish(wire, 19000, wrong_part, maps)),
        refuses("noncanonical_text", "noncanonical length prefix",
                lambda: ReadCfgFinish(wire[:4] + pack("<BH", 255, wire[4]) + wire[5:], 19000, part, maps)),
    ]
    check_map(maps, before)
    require(not external, "authored finish helper used external data")
    return {"case": "wire", "runtime_external_accesses": len(external), "bytes": len(wire),
            "wire_sha256": digest(wire), "fields_sha256": field_digest(read), "refusals": refusals,
            "maps": {"base": maps.BaseValue, "counter": maps.CounterValue, "entries": len(maps.EntryMap),
                     "classes": len(maps.ClassLookup), "objects": len(maps.ObjectLookup)},
            "outer_font": read["fc0"]["f08"], "leader_font": read["f128"]["f08"]["f08"]}


if __name__ == "__main__":
    parser = ArgumentParser(description="Check a bounded ordinary Config-0 finish helper layout")
    parser.add_argument("case", choices=("ladder", "concave", "wire"))
    name = parser.parse_args().case
    result = wire_case() if name == "wire" else native_case(name)
    print(json.dumps(result, sort_keys=True, allow_nan=False))
