from argparse import ArgumentParser
from codecs import lookup
from dataclasses import replace
from functools import partial
import json
from pathlib import Path
from struct import pack, unpack_from
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[3]
sys.path[:0] = [str(ROOT / "src"), str(HERE.parent)]

from CheckCfgMembers import digest, require
from CheckCfgOwners import audit_run
from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.FieldScope import FieldScope
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.GhostFields import KGhostFields
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.ReadBodyMut import ReadBodyMut
from convert.adapters.solidworks.Archive.Bodies.ReadFrame import ReadFrame
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadFieldsMut import ReadFieldsMut
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadSchemaMut import ReadSchemaMut
from convert.adapters.solidworks.Archive.Header.HeaderRefNodes import HeaderRefNodes
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader
from convert.adapters.solidworks.Archive.Reading.ReadGraphNode import ReadNodeMut
from convert.adapters.solidworks.Archive.Reading.ReadSectSpan import ReadSectSpan
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive

MANIFEST = ROOT / "re/solidworks/measurements/2026/ConfigSectionSource01.json"
PART = RuntimeClass("moPart_c", 1)
NAME = RuntimeClass("moNodeName_c", 1)
DIRECT = NativeField("Direct", "")
U32 = NativeField("Scalar", "v", "u32")
NODE = NativeField("Node", "n")
TEXT = NativeField("Text", "t")
GHOST = NativeField("Embed", "fd90", "moGhostBodyIdManager_c.FUN_4bf050e0")


class PrefixObserved(Exception):
    def __init__(self, report):
        super().__init__()
        self.report = report


def load_case(name):
    manifest = json.loads(MANIFEST.read_bytes())
    case = manifest["controls"][name]
    source = (ROOT / case["path"]).read_bytes()
    require(digest(source) == case["part_sha256"], "wrong native model")
    archive = SldprtArchive.from_bytes(source)
    version = ContainerMo(archive.streams)
    require(version == manifest["archive_version"] == 19000
            and archive.format_version == 4, "wrong native archive version")
    config = archive.require(manifest["config_stream"])
    header = archive.require(manifest["header_stream"])
    require(len(config) == case["config_bytes"] and digest(config) == case["config_sha256"]
            and len(header) == case["header_bytes"] and digest(header) == case["header_sha256"],
            "wrong native stream digest or size")
    return config, header, version, case


def make_frame(context, reader, node):
    return ReadFrame(context, reader, FieldScope(node.FieldsValue), node,
                     ReadSchemaMut, ReadFieldsMut)


def section_pair(cursor, case):
    second_cursor = BinaryReader(cursor.BytesValue)
    sections = []
    for expected in case["sections"]:
        expected_start = expected["prefix"]
        section = ReadSectSpan(cursor)
        start, end = section.GetOffset(), section.GetEnd()
        require(cursor.GetOffset() == expected_start and start == expected_start + 4
                and section.BytesValue is cursor.BytesValue, "section fork moved its parent or copied its data")
        require([start, end] == expected["body"] and end - start == expected["length"]
                and unpack_from("<I", cursor.BytesValue, expected_start)[0] == end - start
                and digest(cursor.BytesValue[expected_start:end]) == expected["sha256"],
                "native section declaration differs from reference traversal")
        sections.append(section)
        second_cursor.OffsetValue = end
        cursor = second_cursor
    require(second_cursor.GetRemaining() == 0, "section declarations leave trailing data")
    return sections


def observe_lw(case, frame, rules):
    reader = frame.ReaderValue
    active = reader.Cursor
    node = frame.NodeValue
    context = frame.ContextValue
    assert [active.GetOffset(), active.GetEnd()] == case["sections"][0]["body"]
    assert node.ClassValue == PART and node.StartOffset == 0 and node.EndOffset is None
    assert [reader.MapValue.CounterValue, reader.MapValue.BaseValue] == [case["direct_counter"][0], 1]
    ReadFieldsMut(frame, (DIRECT,))
    assert active.GetOffset() == case["direct_offset"]
    aliases = context.DirectNodes
    assert len(aliases) == 1 and reader.MapValue.EntryMap[3].EntryValue is aliases[0]
    assert aliases[0].IndexValue == case["header_self_slot"]
    assert reader.MapValue.CounterValue == reader.MapValue.BaseValue == case["direct_counter"][1]
    ReadFieldsMut(frame, rules)
    words = [node.FieldsValue[key] for key in ("fb0", "fb4")]
    assert words == case["lead_words"] and active.GetOffset() == case["lead_end"]
    raise PrefixObserved({"lead": words})


def read_lw_prefix(frame, case):
    cursor = frame.ReaderValue.Cursor
    wrapped = replace(frame, FieldsReader=partial(observe_lw, case))
    rules = (NativeField("Scalar", "fb0", "i32"), NativeField("Scalar", "fb4", "u32"))
    start = cursor.GetOffset()
    try:
        ReadFieldsMut(wrapped, (section_rule(*rules),))
    except PrefixObserved as observation:
        assert frame.ReaderValue.Cursor is cursor and cursor.GetOffset() == start
        return observation.report["lead"]
    raise AssertionError("the native section unexpectedly completed")


def read_native_ghost(frame, section, case):
    start, end = case["ghost"]["interval"]
    assert section.GetOffset() <= start <= end <= section.GetEnd()
    assert digest(section.BytesValue[start:end]) == case["ghost"]["sha256"]
    child = BinaryReader(section.BytesValue, start, end)
    reader = frame.ReaderValue
    reader.Cursor = child
    before = reader.MapValue.Snapshot()
    ReadFieldsMut(frame, (GHOST,))
    fields = frame.ScopeValue.FieldsValue["fd90"]
    expected = {"f80": case["ghost"]["f80"], "fe0": case["ghost"]["fe0"], "n": 0, "objects": []}
    assert fields == expected and child.GetOffset() == end
    assert reader.MapValue.Snapshot() == before
    return fields


def observe_root(context, case, reader, node):
    original = reader.Cursor
    assert original.GetOffset() == case["descriptor_bytes"]
    assert digest(original.BytesValue[:original.GetOffset()]) == case["descriptor_sha256"]
    lw, resolved = section_pair(original, case)
    windows = [(section.GetOffset(), section.GetEnd()) for section in (lw, resolved)]
    frame = make_frame(context, reader, node)
    words = read_lw_prefix(frame, case)
    try:
        ghost = read_native_ghost(frame, resolved, case)
    finally:
        reader.Cursor = original
    assert node.EndOffset is None
    raise PrefixObserved({"sections": windows, "lead": words, "header_slot": context.DirectNodes[0].IndexValue,
                          "config_slot": 3, "base": reader.MapValue.BaseValue, "ghost": ghost})


def inspect_native(config, header, version, case):
    header_root = ReadHeaderGraph(header, version)
    aliases = HeaderRefNodes(header_root, version)
    slots = [(node.IndexValue, node.StartOffset, node.EndOffset) for node in aliases]
    context = BodyContext(version, KGhostFields, {}, {}, DirectNodes=aliases)
    reader = GraphReader(BinaryReader(config), ArchiveMaps(1), partial(observe_root, context, case))
    try:
        ReadNodeMut(reader)
    except PrefixObserved as observation:
        assert slots == [(node.IndexValue, node.StartOffset, node.EndOffset) for node in aliases]
        result = observation.report
        result["root_completed"] = False
        return result
    raise AssertionError("the expected part prefix was not visited")


def section_rule(*fields):
    return NativeField("Section", "", BodyValue=fields, MaskValue=1)


def sized(payload):
    return pack("<I", len(payload)) + payload


def new_object(runtime, payload):
    name = runtime.NameValue.encode("ascii")
    return pack("<HHH", 0xFFFF, runtime.SchemaValue, len(name)) + name + payload


def authored_graph():
    row = NativeField("Array", "r", "Count", BodyValue=(NODE,), ModeValue="Positive")
    layout = (section_rule(row, section_rule(U32)), NativeField("Node", "tail"))
    context = BodyContext(19000, {PART.NameValue: layout, NAME.NameValue: (TEXT,)}, {},
                          {PART.NameValue: (1,), NAME.NameValue: (1,)})
    name = new_object(NAME, b"\x03red")
    framed = sized(pack("<H", 1) + name + sized(pack("<I", 57)))
    data = new_object(PART, framed + pack("<H", 4))
    cursor = BinaryReader(data)
    reader = GraphReader(cursor, ArchiveMaps(1), partial(ReadBodyMut, context))
    root = ReadNodeMut(reader)
    node = root.FieldsValue["r"][0]["n"]
    assert node is root.FieldsValue["tail"] is reader.MapValue.EntryMap[4].EntryValue
    assert node.FieldsValue == {"t": ("A", "red")} and root.FieldsValue["v"] == 57
    assert (node.StartOffset, node.EndOffset) == (20, 20 + len(name))
    assert (root.EndOffset, cursor.GetOffset()) == (len(data), len(data))
    assert reader.Cursor is cursor and reader.MapValue.CounterValue == 5
    return [node.StartOffset, node.EndOffset, reader.MapValue.CounterValue]


def author_frame(data, context, owner=PART):
    reader = GraphReader(BinaryReader(data), ArchiveMaps(1), partial(ReadBodyMut, context))
    return make_frame(context, reader, ArchiveNode(owner, {}))


def refuse(label, data, rule, reason, *, version=19000, flags=None, owner=PART):
    context = BodyContext(version, KGhostFields, {}, {}, FlagsValue={} if flags is None else flags)
    frame = author_frame(data, context, owner)
    cursor, map_before = frame.ReaderValue.Cursor, frame.ReaderValue.MapValue.Snapshot()
    flag_before = dict(context.FlagsValue)
    try:
        ReadFieldsMut(frame, (rule,))
    except ValueError as error:
        require(reason in str(error), f"{label} produced a different refusal: {error}")
        assert frame.ReaderValue.Cursor is cursor and cursor.GetOffset() == 0
        assert frame.ReaderValue.MapValue.Snapshot() == map_before
        assert context.FlagsValue == flag_before
        return label
    raise AssertionError(f"{label} unexpectedly decoded")


def authored_refusals():
    count = NativeField("Array", "c", "Count", BodyValue=(NODE,), ModeValue="Positive")
    framework = NativeField("Array", "c", "Framework", BodyValue=(NODE,), ModeValue="Positive")
    return [
        refuse("prefix", b"\x01\0\0", section_rule(U32), "truncated SOLIDWORKS archive field"),
        refuse("oversized", pack("<II", 5, 7), section_rule(U32), "exceeds its remaining stream"),
        refuse("unconsumed", sized(pack("<I", 7) + b"x"), section_rule(U32), "incorrect length"),
        refuse("nested_crossing", pack("<III", 4, 4, 7), section_rule(section_rule(U32)), "exceeds its remaining stream"),
        refuse("scalar_crossing", pack("<II", 3, 7), section_rule(U32), "truncated SOLIDWORKS archive field"),
        refuse("tag_crossing", pack("<IHI", 2, 0x7FFF, 0), section_rule(NODE), "no complete unsigned dword"),
        refuse("descriptor_crossing", pack("<I", 6) + new_object(NAME, b""), section_rule(NODE), "truncated SOLIDWORKS archive field"),
        refuse("vendor_count_crossing", pack("<IHI", 2, 0xFFFF, 1), section_rule(count), "no complete unsigned long"),
        refuse("framework_count_crossing", pack("<IHIQ", 6, 0xFFFF, 0xFFFFFFFF, 1),
               section_rule(framework), "no complete unsigned long long"),
        refuse("text_payload_crossing", pack("<I", 3) + b"\x03abc", section_rule(TEXT), "string payload is truncated"),
        refuse("unicode_length_crossing", pack("<I", 3) + b"\xff\xfe\xff\x01a\x00",
               section_rule(TEXT), "no complete length byte"),
        refuse("wrong_version", sized(b""), section_rule(), "requires archive version 19000", version=18900),
        refuse("skipped_section", sized(b""), section_rule(), "skipped model section", flags={"conditions": 0x80000}),
        refuse("inline_header", b"", DIRECT, "direct model header owner", owner=RuntimeClass("moDrawing_c", 1)),
        refuse("populated_ghost", sized(pack("<iI", 25, 0x10000001)), section_rule(GHOST),
               "moGhostBodyObject_c.FUN_4bf05390"),
    ]


def signed_ghost():
    context = BodyContext(19000, KGhostFields, {}, {})
    frame = author_frame(sized(pack("<iI", 25, 0xF0000000)), context)
    ReadFieldsMut(frame, (section_rule(GHOST),))
    ghost = frame.ScopeValue.FieldsValue["fd90"]
    assert ghost == {"f80": 25, "fe0": -1, "n": 0, "objects": []}
    assert frame.ReaderValue.Cursor.GetRemaining() == 0
    return ghost


def run(name):
    config, header, version, case = load_case(name)
    for codec in ("ascii", "utf-16-le", "latin-1", "cp1252"):
        lookup(codec)
    sys.addaudithook(audit_run)
    result = inspect_native(config, header, version, case)
    result["runtime_external_accesses"] = 0
    if name == "ladder":
        result.update(authored_graph=authored_graph(), signed_ghost=signed_ghost(),
                      refusals=authored_refusals())
    return result


def main():
    parser = ArgumentParser(description="Verify disclosed ordinary model section and ghost bounds")
    parser.add_argument("case", choices=("ladder", "concave"))
    print(json.dumps(run(parser.parse_args().case), sort_keys=True))


if __name__ == "__main__":
    main()
