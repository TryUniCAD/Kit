from argparse import ArgumentParser
from codecs import lookup
from functools import partial
import json
from pathlib import Path
from struct import pack, unpack, unpack_from
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[3]
sys.path[:0] = [str(ROOT / "src"), str(HERE.parent)]

from CheckCfgMembers import CASES as MEMBER_CASES, digest, refuse, require
from CheckCfgOwners import audit_run
from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Config.Members.CfgMemberTypes import (
    KCfgMemberSchemas, KRelMgrClass, KViewClass,
)
from convert.adapters.solidworks.Archive.Config.Members.CheckCfgMember import CheckCfgMember
from convert.adapters.solidworks.Archive.Config.Members.MemberLayouts import KMemberLayouts
from convert.adapters.solidworks.Archive.Config.Members.MemberVirtuals import KMemberVirtuals
from convert.adapters.solidworks.Archive.Config.Members.ReadCfgMember import ReadCfgMember
from convert.adapters.solidworks.Archive.Config.Members.ReadMemBodyMut import ReadMemBodyMut
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Maps.MapSnapshot import MapSnapshot
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader
from convert.adapters.solidworks.Archive.Reading.ReadGraphNode import ReadNodeMut
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive

MANIFEST = ROOT / "re/solidworks/measurements/2026/ConfigViewSource01.json"
TAIL_FIELDS = ("f388", "f38c", "f378", "n380", "f360", "f394", "n398",
               "f3a8", "f3b8", "n3b0", "f3c0", "f3c8")


def trace_flags(cursor):
    events = []

    class TraceFlags(dict):
        def __setitem__(self, name, value):
            events.append([name, cursor.GetOffset(), self.get(name, 0), value])
            super().__setitem__(name, value)

    return TraceFlags(conditions=0x1000, ctx3d0=1, ctx87c=9), events


def load_case(name):
    manifest = json.loads(MANIFEST.read_bytes())
    require(manifest["runtime_class"] == [KViewClass.NameValue, KViewClass.SchemaValue]
            and manifest["stream"] == "Contents/Config-0", "view source role changed")
    case = manifest["controls"][name]
    relative, part_sha, config_sha, member_owners = MEMBER_CASES[name]
    source = (ROOT / case["path"]).read_bytes()
    require(case["path"].endswith("/" + relative)
            and digest(source) == case["part_sha256"] == part_sha, "native view input changed")
    archive = SldprtArchive.from_bytes(source)
    version = ContainerMo(archive.streams)
    require(archive.format_version == 4 and version == manifest["archive_version"] == 19000,
            "unsupported native view version")
    config = archive.require(manifest["stream"])
    require(len(config) == case["configuration_bytes"]
            and digest(config) == case["configuration_sha256"] == config_sha,
            "view configuration stream changed")
    start, end, counter, relation_sha = member_owners[0]
    relation = config[start:end]
    require(end < case["views"][0]["interval"][0] and digest(relation) == relation_sha,
            "earlier relation evidence changed")
    return version, config, case, relation, counter


def first_seed(version, case, relation, counter):
    manager = ReadCfgMember(relation, version, MapSnapshot(counter, ()), KRelMgrClass)
    entries = manager.MapValue.EntriesValue
    assert [entry.IndexValue for entry in entries] == case["seed_relation_slots"]
    assert entries[-1].EntryValue is manager.RootValue
    first = case["views"][0]["counter"][0]
    assert manager.MapValue.CounterValue < first
    return MapSnapshot(first, entries)


def check_transformation(data, fields):
    offset = 1
    expected = {"has_matrix": data[0]}
    if data[0]:
        expected["f08"] = dict(zip(
            ("m0", "m1", "m2", "m3", "m4", "m5", "m6", "m7", "m8"),
            unpack_from("<9d", data, offset), strict=True,
        ))
        offset += 72
    expected.update(zip(("f58", "f60", "f68", "f70", "f78"),
                        unpack("<4dB", data[offset:]), strict=True))
    assert fields == expected
    return [len(data), fields["has_matrix"], fields["f78"]]


def check_fields(config, row, fields):
    spans = row["embedded_intervals"]
    frame = config[slice(*spans["f358"])]
    assert frame[:3] == b"\xff\xfe\xff" and len(frame) == 4 + frame[3] * 2
    assert fields["f358"] == frame[4:].decode("utf-16-le") == row["name"]
    widths = [check_transformation(config[slice(*spans[name])], fields[name])
              for name in ("f368", "f370")]
    tail = unpack("<Hidiiiiidiii", config[spans["f370"][1]:row["interval"][1]])
    assert tuple(fields[key] for key in TAIL_FIELDS) == tail and fields["f380"] == []
    assert [fields[key] for key in ("n380", "n398", "n3b0")] == [0, 0, 0]
    assert "f398" not in fields and "f3b0" not in fields
    digest_input = json.dumps(fields, sort_keys=True, separators=(",", ":"), allow_nan=False)
    assert digest(digest_input.encode()) == row["field_model_sha256"]
    return widths


def check_slots(node, before, after, row):
    initial = before.EntriesValue
    entries = after.EntriesValue
    new_entries = entries[len(initial):]
    assert all(a is b for a, b in zip(initial, entries[:len(initial)], strict=True))
    assert [before.CounterValue, after.CounterValue] == row["counter"]
    assert new_entries[-1].EntryValue is node
    assert new_entries[-1].IndexValue == node.IndexValue == row["object_slot"]
    if row["row"] == 0:
        descriptor, _new = new_entries
        assert descriptor.IndexValue == row["class_slot"] == before.CounterValue
    else:
        assert len(new_entries) == 1
        descriptor = next(entry for entry in initial if entry.IndexValue == row["class_slot"])
    assert descriptor.EntryValue is node.ClassValue


def native_views(version, config, case, seed):
    native = []
    for row in case["views"]:
        data = config[slice(*row["interval"])]
        assert digest(data) == row["wire_sha256"]
        word, = unpack_from("<H", data)
        assert word == (0xFFFF if row["row"] == 0 else 0x8000 | row["class_slot"])
        decoded = ReadCfgMember(data, version, seed, KViewClass)
        node = decoded.RootValue
        assert node.ClassValue == KViewClass
        assert node.StartOffset == 0 and node.EndOffset == len(data)
        assert decoded.ReportValue["completed"] and decoded.ReportValue["field_calls"]["Context"] == 4
        check_slots(node, seed, decoded.MapValue, row)
        widths = check_fields(config, row, node.FieldsValue)
        assert row["context"] == [
            [row["interval"][1] - 32, 0, 1],
            [row["interval"][1] - 24, 1, 0],
            [row["interval"][1] - 24, 0, 1],
            [row["interval"][1] - 8, 1, 0],
        ]
        native.append({"name": node.FieldsValue["f358"], "slot": node.IndexValue,
                       "class_slot": row["class_slot"], "interval": row["interval"],
                       "transforms": widths, "context_calls": 4})
        seed = decoded.MapValue
    return native, seed


def authored_view(class_slot, *, flag=0, links=(), first_list=0, second_list=0):
    matrix = pack("<9d", 1, 0, 0, 0, 0, 1, 0, -1, 0)
    transform = b"\x01" + matrix + pack("<4dB", 2.5, -1, 3, 4, flag)
    secondary = pack("<B4dB", 0, -1, 2, 0.5, 2, 0)
    name = b"\x04View"
    return b"".join((
        pack("<H", 0x8000 | class_slot), name, transform, secondary,
        pack("<Hidi", 7, -13, 2.25, len(links)),
        b"".join(pack("<H", slot) for slot in links),
        pack("<iii", -9, 11, first_list), b"\x00\x00" if first_list else b"",
        pack("<idi", -12, 3.5, second_list), b"\x00\x00" if second_list else b"",
        pack("<ii", 23, -31),
    ))


def authored_context(data, seed, class_slot):
    cursor = BinaryReader(data)
    state, events = trace_flags(cursor)
    initial = dict(state)
    context = BodyContext(19000, KMemberLayouts, KMemberVirtuals, KCfgMemberSchemas, FlagsValue=state)
    original = seed.EntriesValue
    mapped = ArchiveMaps(seed.CounterValue, seed)
    read_node = partial(ReadMemBodyMut, context, KViewClass)
    node = ReadNodeMut(GraphReader(cursor, mapped, read_node))
    CheckCfgMember(node, KViewClass, mapped)
    assert cursor.GetRemaining() == 0
    assert node.StartOffset == 0 and node.EndOffset == len(data)
    assert node.IndexValue == seed.CounterValue == mapped.CounterValue - 1
    assert mapped.EntryMap[node.IndexValue].EntryValue is node
    assert node.ClassValue is mapped.EntryMap[class_slot].EntryValue
    assert all(mapped.EntryMap[entry.IndexValue] is entry for entry in original)
    assert node.FieldsValue["f358"] == ("A", "View")
    assert node.FieldsValue["f3c0"] == 23 and node.FieldsValue["f3c8"] == -31
    bounded = ReadCfgMember(data, 19000, seed, KViewClass, FlagSeed=initial)
    assert initial == {"conditions": 4096, "ctx3d0": 1, "ctx87c": 9}
    check_slots(bounded.RootValue, seed, bounded.MapValue, {
        "row": 10, "counter": [seed.CounterValue, mapped.CounterValue],
        "class_slot": class_slot, "object_slot": node.IndexValue,
    })
    assert bounded.RootValue.FieldsValue == node.FieldsValue and bounded.FlagsValue == state
    assert bounded.RootValue.StartOffset == 0 and bounded.RootValue.EndOffset == len(data)
    return {"events": events, "flags": dict(state), "slot": node.IndexValue,
            "fields": node.FieldsValue, "member_context_calls": bounded.ReportValue["field_calls"]["Context"],
            "member_flags": dict(bounded.FlagsValue)}


def refusals(seed, class_slot, first, accepted):
    owner = KViewClass
    bad_class = b"moViewData_c"
    return [
        refuse("truncated", accepted[:-1], seed, owner, "truncated SOLIDWORKS archive field"),
        refuse("trailing", accepted + b"\0", seed, owner, "trailing data"),
        refuse("null", b"\0\0", seed, owner, "view member requires its concrete root"),
        refuse("borrowed", pack("<H", first["slot"]), seed, owner, "requires a new root object"),
        refuse("missing_class", accepted, MapSnapshot(seed.CounterValue, ()), owner, "archive class reference"),
        refuse("wrong_version", accepted, seed, owner, "archive version 19000", 18900),
        refuse("wrong_role", pack("<HHH", 0xFFFF, 1, len(bad_class)) + bad_class, seed, owner,
               "unsupported body owner"),
        refuse("populated_links", authored_view(class_slot, links=(first["slot"],)), seed, owner,
               "unqualified SOLIDWORKS view lists"),
        refuse("populated_first_list", authored_view(class_slot, first_list=1), seed, owner,
               "unqualified SOLIDWORKS view lists"),
        refuse("populated_second_list", authored_view(class_slot, second_list=1), seed, owner,
               "unqualified SOLIDWORKS view lists"),
        refuse("selected_transform", authored_view(class_slot, flag=0x20), seed, owner,
               "unsupported SOLIDWORKS body schema mgPerspInfo_c.restore"),
        refuse("unqualified_selector", authored_view(class_slot, flag=0x80), seed, owner,
               "unqualified SOLIDWORKS view transform selector"),
    ]


def run(name):
    version, config, case, relation, relation_counter = load_case(name)
    for codec in ("ascii", "utf-16-le", "latin-1"):
        lookup(codec)
    sys.addaudithook(audit_run)
    seed = first_seed(version, case, relation, relation_counter)
    initial = seed.CounterValue
    rows, result = native_views(version, config, case, seed)
    output = {"views": rows, "counter": [initial, result.CounterValue],
              "inherited": [entry.IndexValue for entry in seed.EntriesValue],
              "runtime_external_accesses": 0}
    if name == "ladder":
        slot = rows[0]["class_slot"]
        independent = authored_view(slot)
        contrast = authored_context(independent, result, slot)
        output.update(authored=contrast, refusals=refusals(result, slot, rows[0], independent))
    return output


def main():
    parser = ArgumentParser(description="Verify the ordinary configuration view group and archive context")
    parser.add_argument("case", choices=("ladder", "concave"))
    print(json.dumps(run(parser.parse_args().case), sort_keys=True))


if __name__ == "__main__":
    main()
