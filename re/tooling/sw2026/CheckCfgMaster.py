from argparse import ArgumentParser
from copy import deepcopy
from functools import partial
import json
from pathlib import Path
from struct import pack, unpack_from
import sys

HERE = Path(__file__).resolve()
sys.path[:0] = [str(HERE.parents[3] / "src"), str(HERE.parent)]

from CfgMasterInputs import ROOT, digest, disclosed, fingerprint, guard_runtime, require
from CfgMasterWire import authored
from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.FieldScope import FieldScope
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.ReadBodyMut import ReadBodyMut
from convert.adapters.solidworks.Archive.Bodies.ReadFrame import ReadFrame
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadFieldsMut import ReadFieldsMut
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadSchemaMut import ReadSchemaMut
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteFieldsMut import WriteFieldsMut
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteSchemaMut import WriteSchemaMut
from convert.adapters.solidworks.Archive.Bodies.BodyWriter import BodyWriter
from convert.adapters.solidworks.Archive.Bodies.WriteBodyMut import WriteBodyMut
from convert.adapters.solidworks.Archive.Bodies.WriteFrame import WriteFrame
from convert.adapters.solidworks.Archive.Config.Link.ReadPartStart import ReadPartStart
from convert.adapters.solidworks.Archive.Config.Master.MakeMasterCtx import MakeMasterCtx
from convert.adapters.solidworks.Archive.Config.Master.MasterLayout import KMasterClass, KMasterRule
from convert.adapters.solidworks.Archive.Config.Master.ReadCfgMaster import ReadCfgMaster
from convert.adapters.solidworks.Archive.Config.Master.WriteCfgMaster import WriteCfgMaster
from convert.adapters.solidworks.Archive.Header.HeaderRefNodes import HeaderRefNodes
from convert.adapters.solidworks.Archive.Maps.AddEntryMut import AddEntryMut
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Maps.BindNodesMut import BindNodesMut
from convert.adapters.solidworks.Archive.Maps.MapSnapshot import MapSnapshot
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive

TRACE = ROOT / "re/solidworks/measurements/2026/ConfigSheetMetalTraversal01.json"


def map_check(maps, before):
    base, snapshot = before
    actual = maps.Snapshot()
    require(maps.BaseValue == base and actual == snapshot and all(
        old is new for old, new in zip(snapshot.EntriesValue, actual.EntriesValue, strict=True)
    ), "the bounded owner changed its map")


def measure(payload, part, maps, expected, *, authored_value=None):
    before, original_fields = (maps.BaseValue, maps.Snapshot()), deepcopy(part.FieldsValue)
    result = ReadCfgMaster(payload, 19000, part, maps)
    require(result.ClassValue == KMasterClass and result.IndexValue is None,
            "direct serialization acquired the wrong concrete object or map slot")
    require((result.StartOffset, result.EndOffset) == (0, len(payload)), "relative extent differs")
    require(result.FieldsValue == expected if isinstance(expected, dict)
            else fingerprint(result.FieldsValue) == expected, "one or more modeled fields differ")
    emitted = WriteCfgMaster(result if authored_value is None else authored_value, 19000, part, maps)
    require(emitted == payload, "serialization differs from the independent wire")
    map_check(maps, before)
    require(part.FieldsValue == original_fields, "the enclosing part fields changed")
    return {
        "extent": [result.StartOffset, result.EndOffset],
        "counter": [before[1].CounterValue, maps.CounterValue],
        "class": [result.ClassValue.NameValue, result.ClassValue.SchemaValue],
        "slot": result.IndexValue,
        "mapped_slots": [entry.IndexValue for entry in maps.Snapshot().EntriesValue],
        "wire_sha256": digest(payload),
        "fields_sha256": fingerprint(result.FieldsValue),
        "emitted_sha256": digest(emitted),
        "body_count": result.FieldsValue["n370"],
    }


def native_case():
    source, archive, _, config = disclosed("circle", SldprtArchive, ContainerMo)
    expected = json.loads(TRACE.read_bytes())["controls"]["circle"]["direct_owner"]
    first, last = expected["interval"]
    base, counter = expected["map"]["base"], expected["map"]["counter"]
    old_owner = source["separate_direct_owner"]
    payload = config[first:last]
    require(
        old_owner["start"] == [first, base, counter] and old_owner["end"] == [last, base, counter]
        and digest(payload) == expected["wire_sha256"] == old_owner["wire_sha256"]
        and unpack_from("<i", config, first - 4)[0] == expected["f1014"] == 1,
        "the physical owner boundary differs from both traces",
    )
    external = guard_runtime()
    prefix = ReadPartStart(archive)
    require(prefix.BaseValue == base and prefix.RootValue.IndexValue == expected["part_slot"],
            "the actual archive did not resolve its ordinary part")
    maps = ArchiveMaps(counter, MapSnapshot(counter, prefix.MapValue.EntriesValue))
    maps.BaseValue = base
    (actual_header,) = HeaderRefNodes(prefix.HeaderValue, 19000)
    require(maps.EntryMap[3].EntryValue is actual_header, "header alias is no longer the real owner")
    proof = measure(payload, prefix.RootValue, maps, expected["fields_sha256"])
    require(not external, "native bounded replay attempted external access")
    return {"case": "native", "interval": [first, last], "proof": proof,
            "runtime_external_accesses": len(external)}


def refuse(label, reason, execute):
    try:
        execute()
    except ValueError as error:
        require(reason in str(error), f"{label} refused at an unexpected boundary: {error}")
        return label
    raise ValueError(f"{label} was not refused")


def authored_maps():
    maps = ArchiveMaps(1)
    descriptor = RuntimeClass("moPart_c", 1)
    part = ArchiveNode(descriptor, {}, IndexValue=2)
    header = ArchiveNode(RuntimeClass("moExtObject_c", 1), {})
    AddEntryMut(maps, descriptor)
    AddEntryMut(maps, part)
    BindNodesMut(maps, (header,))
    return part, maps


def direct_reader(payload, part, maps, factory=None):
    context = MakeMasterCtx(19000, part, maps)
    lead = b"prefix!"
    cursor = BinaryReader(lead + payload, len(lead))
    reader = GraphReader(cursor, maps, partial(ReadBodyMut, context), NodeFactory=factory)
    return ReadFrame(context, reader, FieldScope({}), part, ReadSchemaMut, ReadFieldsMut)


def refuse_reader(label, reason, payload, part, maps, factory=None):
    frame = direct_reader(payload, part, maps, factory)
    initial = frame.ReaderValue.Cursor.GetOffset()
    before = (maps.BaseValue, maps.Snapshot())
    result = refuse(label, reason, lambda: ReadFieldsMut(frame, KMasterRule))
    require(frame.ReaderValue.Cursor.GetOffset() == initial and not frame.ScopeValue.FieldsValue,
            "a refused direct body published a cursor or a field")
    map_check(maps, before)
    return result


def refuse_writer(label, reason, node, part, maps):
    context = MakeMasterCtx(19000, part, maps)
    original = b"writer!"
    writer = BodyWriter(maps, context, WriteBodyMut, bytearray(original))
    frame = WriteFrame(writer, FieldScope({"f1018": node}), part, WriteSchemaMut, WriteFieldsMut)
    before = (maps.BaseValue, maps.Snapshot())
    result = refuse(label, reason, lambda: WriteFieldsMut(frame, KMasterRule))
    require(writer.OutputValue == original, "a refused direct body published bytes")
    map_check(maps, before)
    return result


def flag_case(node):
    field = NativeField("Scalar", "item", "i32")
    rule = (NativeField("Virtual", "", MaskValue=31, ModeValue="Flag", BodyValue=(field,)),)
    expected_value = -127
    results = []
    for flag in (True, False, 1):
        context = BodyContext(19000, {}, {(KMasterClass.NameValue, 31): flag}, {})
        wire = pack("<i", expected_value)
        expected_wire = wire if flag is True else b""
        maps = ArchiveMaps(4)
        reader = GraphReader(BinaryReader(expected_wire), maps, partial(ReadBodyMut, context))
        read_frame = ReadFrame(context, reader, FieldScope({}), node, ReadSchemaMut, ReadFieldsMut)
        writer = BodyWriter(maps, context, WriteBodyMut)
        write_frame = WriteFrame(writer, FieldScope({"item": expected_value}), node, WriteSchemaMut, WriteFieldsMut)
        if type(flag) is not bool:
            for step in (lambda: ReadFieldsMut(read_frame, rule), lambda: WriteFieldsMut(write_frame, rule)):
                refuse("nonboolean_virtual", "virtual flag requires a boolean target", step)
            require(not writer.OutputValue and not read_frame.ScopeValue.FieldsValue and
                    reader.Cursor.GetOffset() == 0, "virtual refusal changed archive state")
            results.append("nonboolean_refused")
            continue
        ReadFieldsMut(read_frame, rule)
        WriteFieldsMut(write_frame, rule)
        require(writer.OutputValue == expected_wire and not reader.Cursor.GetRemaining()
                and read_frame.ScopeValue.FieldsValue == ({"item": expected_value} if flag else {}),
                "virtual flag did not preserve the wire and typed fields")
        results.append(len(expected_wire))
    return results


def wire_case():
    part, maps = authored_maps()
    external = guard_runtime()
    payload, node = authored()
    expected = {**node.FieldsValue, "n370": 0}
    proof = measure(payload, part, maps, expected, authored_value=node)
    require("n370" not in node.FieldsValue, "derived count mutated the authored object")
    frame = direct_reader(payload, part, maps)
    ReadFieldsMut(frame, KMasterRule)
    direct = frame.ScopeValue.FieldsValue["f1018"]
    extent = [direct.StartOffset, direct.EndOffset]
    require(extent == [7, 7 + len(payload)] and not frame.ReaderValue.Cursor.GetRemaining(),
            "untagged body did not preserve the caller cursor origin")

    foreign = ArchiveNode(RuntimeClass("moFolder_c", 1), dict(node.FieldsValue))
    mapped = ArchiveNode(KMasterClass, dict(node.FieldsValue))
    AddEntryMut(maps, mapped)
    child_name = KMasterClass.NameValue.encode("ascii")
    new_child = pack("<HHH", 65535, 1, len(child_name)) + child_name + payload
    active = ArchiveNode(KMasterClass, {**node.FieldsValue, "f18": maps.EntryMap[3].EntryValue})
    populated = ArchiveNode(KMasterClass, {**node.FieldsValue, "f358": [{}]})
    conditional = ArchiveNode(KMasterClass, {**node.FieldsValue, "f200": "alternate"})
    before = (maps.BaseValue, maps.Snapshot())
    refusals = [
        refuse_reader("foreign_node", "wrong concrete class", payload, part, maps, lambda _: foreign),
        refuse_reader("mapped_node", "already owns an archive slot", payload, part, maps, lambda _: mapped),
        refuse_reader("truncated", "truncated SOLIDWORKS archive field", payload[:-1], part, maps),
        refuse_reader("new_mapped_child", "may not change its archive map", new_child + payload[2:], part, maps),
        refuse_reader("nonempty", "nonempty sheet metal master body list", payload[:-4] + pack("<i", 1), part, maps),
        refuse_reader("negative", "nonempty sheet metal master body list", payload[:-4] + pack("<i", -1), part, maps),
        refuse("trailing", "trailing data", lambda: ReadCfgMaster(payload + b"x", 19000, part, maps)),
        refuse("inherited_link", "unsupported object link",
               lambda: ReadCfgMaster(pack("<H", 3) + payload[2:], 19000, part, maps)),
        refuse("mapped_child", "unsupported mapped child",
               lambda: ReadCfgMaster(new_child + payload[2:], 19000, part, maps)),
        refuse("foreign_part", "requires the inherited part owner",
               lambda: ReadCfgMaster(payload, 19000, ArchiveNode(part.ClassValue, {}, IndexValue=2), maps)),
        refuse("archive_version", "requires archive version 19000",
               lambda: ReadCfgMaster(payload, 18900, part, maps)),
        refuse_writer("store_foreign_node", "wrong concrete class", foreign, part, maps),
        refuse_writer("store_mapped_node", "already owns an archive slot", mapped, part, maps),
        refuse_writer("store_nonempty", "nonempty sheet metal master body list", populated, part, maps),
        refuse("store_inherited_link", "unsupported object link",
               lambda: WriteCfgMaster(active, 19000, part, maps)),
        refuse("store_alternate_context", "unsupported resolved flags",
               lambda: WriteCfgMaster(conditional, 19000, part, maps)),
    ]
    map_check(maps, before)
    flags = flag_case(node)
    require(not external, "authored verification attempted runtime external access")
    return {"case": "wire", "prefixed_extent": extent, "proof": proof, "virtual_flags": flags,
            "refusals": refusals, "runtime_external_accesses": len(external)}


if __name__ == "__main__":
    parser = ArgumentParser(description="Verify the bounded Config-0 direct master reader and emitter")
    parser.add_argument("case", choices=("native", "wire"))
    args = parser.parse_args()
    output = native_case() if args.case == "native" else wire_case()
    print(json.dumps(output, sort_keys=True))
