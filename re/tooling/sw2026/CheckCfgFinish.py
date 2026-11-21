from argparse import ArgumentParser
import json
from pathlib import Path
from struct import pack
import sys

HERE = Path(__file__).resolve()
sys.path[:0] = [str(HERE.parents[3] / "src"), str(HERE.parent)]

from CfgFinishWire import authored
from TraceCfgFinish import FINISH, REVISION, ROLES, field_digest, guard_runtime, source
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
from convert.adapters.solidworks.Archive.Maps.MapSnapshot import MapSnapshot
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
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
    for path, interval in rows.items():
        if path[:len(role)] != role:
            continue
        require(first <= interval["interval"][0] < interval["interval"][1] <= last,
                "finish child lies outside its parent")
        contained = fields
        for key in path[len(role):]:
            contained = contained[key]
        finished.append(check_scope(contained, interval, config, part, maps))
    require(len(finished) == 4, "finish body lost one of its embedded records")
    return finished


def native_case(name):
    trace = json.loads(RECEIPT.read_bytes())
    require(trace["trace_revision"] == REVISION, "finish source trace pin changed")
    case = trace["cases"][name]
    path, expected = source.CASES[name]
    data = (source.ROOT / path).read_bytes()
    require(case["path"] == path and digest(data) == expected == case["file_sha256"],
            "tracked original changed")
    external = guard_runtime()
    archive = SldprtArchive.from_bytes(data)
    config = archive.require("Contents/Config-0")
    header = archive.require("Contents/Config-0-ModelHeader")
    require(archive.format_version == 4 and ContainerMo(archive.streams) == 19000
            and digest(config) == case["config_sha256"] and digest(header) == case["header_sha256"],
            "native archive stream proof differs")
    seed = ReadPartStart(archive)
    rows = {tuple(row["role"]): row for row in case["rows"]}
    counters = {row["map_counter"] for row in rows.values()}
    (counter,) = counters
    maps = ArchiveMaps(counter, MapSnapshot(counter, seed.MapValue.EntriesValue))
    maps.BaseValue = seed.BaseValue
    (header_alias,) = HeaderRefNodes(seed.HeaderValue, 19000)
    require(maps.EntryMap[3].EntryValue is header_alias and maps.BaseValue == 4
            and all(row["map_identity_preserved"] and row["map_entries"] == counter - 1
                    for row in rows.values()), "real header role or physical traversal proof differs")
    checks = [row for role in ROLES for row in exact_role(role, rows, config, seed.RootValue, maps)]
    require(not external, "bounded native verification used external data")
    return {"case": name, "runtime_external_accesses": len(external), "native_source": expected,
            "map_anchors": list(maps.EntryMap), "map_base": maps.BaseValue, "map_counter": maps.CounterValue,
            "exact_intervals": checks}


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
