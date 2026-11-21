from argparse import ArgumentParser
from codecs import lookup
from dataclasses import replace
from functools import partial
import json
from pathlib import Path
from struct import pack
from subprocess import check_output
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[3]
sys.path[:0] = [str(ROOT / "src"), str(HERE.parent)]

from CheckCfgSection import DIRECT, PART, PrefixObserved, digest, make_frame, new_object, section_rule, sized
from CheckCfgSectionWrite import ASSEMBLY, VERSION, aliases_from, typed_writer, write_model
from MakeHeadAliasCase import DIRECTORY, SELF, header
from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.ReadBodyMut import ReadBodyMut
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadFieldsMut import ReadFieldsMut
from convert.adapters.solidworks.Archive.Bodies.WriteBodyMut import WriteBodyMut
from convert.adapters.solidworks.Archive.Header.HeaderRefNodes import HeaderRefNodes
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Maps.BindNodesMut import BindNodesMut
from convert.adapters.solidworks.Archive.Maps.FindObject import FindObject
from convert.adapters.solidworks.Archive.Maps.ObjectIndex import ObjectIndex
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader
from convert.adapters.solidworks.Archive.Reading.ReadGraphNode import ReadNodeMut
from convert.adapters.solidworks.Archive.Reading.ReadSectSpan import ReadSectSpan
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive

LEAD = (NativeField("Scalar", "fb0", "i32"), NativeField("Scalar", "fb4", "u32"))
AUTHORED = {"one": (1, -37), "two": (2, 613)}
SOURCE_REVISION = "5554733fde548afabdc6db221f387163d15e9497"
NATIVE = {
    "a0": (
        "A0_one", "66965b66e14bacb506b147fa354e6708aa207c7589efbf8e5f3d3fbe7cf453f8",
        "7525e1d3c8cc4a7fd0badcfca220434868c3d75835d89f63305729e78a686a2b",
        "8ed41cbefe04dde1b76328c273f93a81e3f105f4fbbb43e1305cf9b0476d9a4d",
        "98cd9d7146a2605b60a6fd9fb269265f2363574ca58ef3c1fdf39e486f410fb8",
        (69, 65), ((22, 3133), (3137, 24828)),
    ),
    "a1": (
        "A1_two", "594559a38ea2a077850a823e808ed7f79c559bfac743eab7c9ab4aa75cf252e4",
        "9ed41ae9b8ad6bc38804a84d1463ec4d7fb70717ff8d539357ee9d5a777c45d7",
        "d104518bb0d5d4fdbb8595bc3a7627e9c6870b71758a35c538ae7edc600cc5bb",
        "1be858bb7a88b225639ee939785387e7ba4fdcfda3cf5d945dbcc670f240772a",
        (80, 73, 77), ((22, 3643), (3647, 25338)),
    ),
}
OWNER_ERROR = "unsupported SOLIDWORKS direct part header owner"
ALIAS_ERROR = "SOLIDWORKS direct part header needs distinct new aliases"


def guard():
    for codec in ("ascii", "utf-16-le", "latin-1", "cp1252"):
        lookup(codec)
    accessed = []

    def deny(event, args):
        if event in {"open", "socket.connect", "subprocess.Popen", "os.system", "os.exec",
                     "os.posix_spawn", "ctypes.dlopen"}:
            accessed.append(event)
            raise PermissionError(f"assembly direct action requested runtime access {event}")

    sys.addaudithook(deny)
    return accessed


def sections(cursor):
    result = []
    for _ in range(2):
        section = ReadSectSpan(cursor)
        result.append((section.GetOffset(), section.GetEnd()))
        cursor = BinaryReader(cursor.BytesValue, section.GetEnd())
    assert cursor.GetRemaining() == 0
    return tuple(result)


def check_aliases(maps, aliases):
    slots = tuple(range(3, 3 + len(aliases)))
    assert maps.BaseValue == maps.CounterValue == 3 + len(aliases)
    assert tuple(FindObject(maps, slot) for slot in slots) == aliases
    return slots


def model_layout(alias_count):
    links = tuple(NativeField("Node", f"reference{index}") for index in range(alias_count))
    return section_rule(DIRECT, *LEAD), section_rule(*links)


def author_case(count, word):
    header_data = header(SELF, DIRECTORY[:count])
    aliases = aliases_from(header_data)
    layout = model_layout(len(aliases))
    fields = {"fb0": word, "fb4": VERSION}
    fields.update({f"reference{index}": alias for index, alias in enumerate(reversed(aliases))})
    writer = typed_writer(layout, aliases, owner=ASSEMBLY)
    node = ArchiveNode(ASSEMBLY, fields)
    output = write_model(writer, node)
    assert ObjectIndex(writer.MapValue, node) == 2
    check_aliases(writer.MapValue, aliases)
    return {"header": header_data.hex(), "config": output.hex()}


def rejected(writer, node, message):
    outer = writer.OutputValue
    try:
        write_model(writer, node)
    except ValueError as error:
        assert str(error) == message
        assert writer.OutputValue is outer and writer.NestingDepth == 0
        assert bytes(outer) == new_object(node.ClassValue, b"")
        return message
    raise AssertionError("the incompatible direct owner or alias was accepted")


def detached_body(writer, owner):
    assert ObjectIndex(writer.MapValue, owner) == 2
    same_type = ArchiveNode(owner.ClassValue, {})
    assert ObjectIndex(writer.MapValue, same_type) is None
    WriteBodyMut(writer, same_type)


def authored_refusals(aliases):
    node = ArchiveNode(ASSEMBLY, {})
    nested = typed_writer(
        (section_rule(NativeField("Node", "child")),), aliases, owner=PART,
        children={ASSEMBLY.NameValue: (DIRECT,)},
    )
    detached = typed_writer((DIRECT,), aliases, owner=ASSEMBLY)
    detached.NodeBody = detached_body
    used = typed_writer((DIRECT,), aliases, owner=ASSEMBLY)
    BindNodesMut(used.MapValue, aliases[:1])
    return {
        "wrong_version": rejected(typed_writer((DIRECT,), aliases, version=18900, owner=ASSEMBLY),
                                  node, "SOLIDWORKS typed body grammar requires archive version 19000"),
        "nested": rejected(nested, ArchiveNode(PART, {"child": node}), OWNER_ERROR),
        "detached": rejected(detached, node, OWNER_ERROR),
        "duplicate_alias": rejected(typed_writer((DIRECT,), aliases[:1] * 2, owner=ASSEMBLY),
                                     node, ALIAS_ERROR),
        "already_mapped_alias": rejected(used, node, ALIAS_ERROR),
        "absent_alias": rejected(typed_writer((DIRECT,), owner=ASSEMBLY), node, ALIAS_ERROR),
    }


def author():
    accessed = guard()
    authored = {case: author_case(*values) for case, values in AUTHORED.items()}
    refusals = authored_refusals(aliases_from(header(SELF, DIRECTORY)))
    assert not accessed
    return {"authored": authored, "refusals": refusals}


def inspect_authored(case, record):
    count, word = AUTHORED[case]
    header_data = bytes.fromhex(record["header"])
    data = bytes.fromhex(record["config"])
    aliases = aliases_from(header_data)
    prior_slots = tuple(item.IndexValue for item in aliases)
    links = tuple(range(3 + count, 2, -1))
    expected = new_object(
        ASSEMBLY, sized(pack("<iI", word, VERSION)) + sized(b"".join(pack("<H", slot) for slot in links))
    )
    assert data == expected
    layout = model_layout(count + 1)
    context = BodyContext(VERSION, {ASSEMBLY.NameValue: layout}, {}, {ASSEMBLY.NameValue: (1,)},
                          DirectNodes=aliases)
    cursor = BinaryReader(data)
    reader = GraphReader(cursor, ArchiveMaps(1), partial(ReadBodyMut, context))
    node = ReadNodeMut(reader)
    assert node.ClassValue == ASSEMBLY and node.IndexValue == 2
    assert node.EndOffset == len(data) == cursor.GetOffset()
    assert (node.FieldsValue["fb0"], node.FieldsValue["fb4"]) == (word, VERSION)
    slots = check_aliases(reader.MapValue, aliases)
    assert all(node.FieldsValue[f"reference{index}"] is FindObject(reader.MapValue, slot)
               for index, slot in enumerate(links))
    assert tuple(item.IndexValue for item in aliases) == prior_slots
    return {"bytes": len(data), "config_sha256": digest(data), "header_sha256": digest(header_data),
            "sections": sections(BinaryReader(data, 18)), "standalone_header_slots": prior_slots,
            "map_base": reader.MapValue.BaseValue, "configured_slots": slots, "references": links,
            "map_counter": reader.MapValue.CounterValue, "lead_words": (word, VERSION)}


def inspect(issued):
    accessed = guard()
    result = {case: inspect_authored(case, record) for case, record in issued["authored"].items()}
    assert not accessed
    return result


def observe_direct(frame, rules):
    node = frame.NodeValue
    reader = frame.ReaderValue
    cursor = reader.Cursor
    assert (node.ClassValue, node.IndexValue, cursor.GetOffset()) == (ASSEMBLY, 2, 22)
    before = (reader.MapValue.BaseValue, reader.MapValue.CounterValue)
    ReadFieldsMut(frame, (DIRECT,))
    assert before == (1, 3) and cursor.GetOffset() == 22
    slots = check_aliases(reader.MapValue, frame.ContextValue.DirectNodes)
    after = (reader.MapValue.BaseValue, reader.MapValue.CounterValue)
    ReadFieldsMut(frame, rules)
    words = tuple(node.FieldsValue[name] for name in ("fb0", "fb4"))
    assert words == (0, VERSION) and cursor.GetOffset() == 30
    raise PrefixObserved({"lead_words": words, "lead_end": cursor.GetOffset(), "direct_extent": (22, 22),
                          "map_before": before, "map_after": after, "configured_slots": slots})


def observe_native_root(context, reader, node):
    original = reader.Cursor
    assert original.GetOffset() == 18
    frame = replace(make_frame(context, reader, node), FieldsReader=observe_direct)
    try:
        ReadFieldsMut(frame, (section_rule(*LEAD),))
    except PrefixObserved:
        assert reader.Cursor is original and original.GetOffset() == 18
        raise
    raise AssertionError("the boundary observation attempted a complete configuration read")


def native(case):
    name, source_hash, header_hash, config_hash, mates_hash, prior_slots, windows = NATIVE[case]
    relative = f"re/solidworks/v2026/corpus/assemblies/{name}.SLDASM"
    source = check_output(("git", "show", f"{SOURCE_REVISION}:{relative}"), cwd=ROOT, timeout=30)
    assert digest(source) == source_hash
    accessed = guard()
    archive = SldprtArchive.from_bytes(source)
    version = ContainerMo(archive.streams)
    assert archive.format_version == 4 and version == VERSION
    header_data = archive.require("Contents/Config-0-ModelHeader")
    config = archive.require("Contents/Config-0")
    mates = archive.require("Contents/Config-0-MatesList")
    assert tuple(map(digest, (header_data, config, mates))) == (header_hash, config_hash, mates_hash)
    assert sections(BinaryReader(config, 18)) == windows
    aliases = HeaderRefNodes(ReadHeaderGraph(header_data, version), version)
    assert tuple(item.IndexValue for item in aliases) == prior_slots
    context = BodyContext(version, {}, {}, {}, DirectNodes=aliases)
    reader = GraphReader(BinaryReader(config), ArchiveMaps(1), partial(observe_native_root, context))
    try:
        ReadNodeMut(reader)
    except PrefixObserved as outcome:
        assert tuple(item.IndexValue for item in aliases) == prior_slots
        assert not accessed
        return {**outcome.report, "source_path": relative, "source_sha256": source_hash,
                "model_header_sha256": header_hash, "config_sha256": config_hash,
                "mates_sha256": mates_hash, "mates_bytes": len(mates),
                "standalone_header_slots": prior_slots, "sections": windows}
    raise AssertionError("the real assembly root did not execute the direct header action")


def report(with_native):
    command = (sys.executable, "-I", "-B", str(HERE))
    issued = check_output((*command, "author"), timeout=45)
    authored = json.loads(check_output((*command, "inspect"), input=issued, timeout=45))
    result = {"authored": authored, "refusals": json.loads(issued)["refusals"],
              "guarded_processes": 2, "runtime_external_accesses": 0}
    if with_native:
        result["native_prefixes"] = {case: json.loads(check_output((*command, case), timeout=45))
                                     for case in NATIVE}
        result["guarded_processes"] += len(NATIVE)
        result["native_source_revision"] = SOURCE_REVISION
    return result


def main():
    parser = ArgumentParser(description="Measure shared SOLIDWORKS assembly direct header actions")
    parser.add_argument("mode", choices=("measure", "measure-native", "author", "inspect", *NATIVE))
    mode = parser.parse_args().mode
    if mode == "author":
        result = author()
    elif mode == "inspect":
        result = inspect(json.load(sys.stdin))
    elif mode in NATIVE:
        result = native(mode)
    else:
        result = report(mode == "measure-native")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
