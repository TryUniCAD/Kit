from functools import partial
from struct import unpack, unpack_from

from CheckCfgMembers import digest, require
from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.FieldScope import FieldScope
from convert.adapters.solidworks.Archive.Bodies.IsBranchTaken import IsBranchTaken
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.ReadFrame import ReadFrame
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadFieldsMut import ReadFieldsMut
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadSchemaMut import ReadSchemaMut
from convert.adapters.solidworks.Archive.Config.Members.CfgMemberTypes import KViewClass
from convert.adapters.solidworks.Archive.Config.Members.CheckCfgMember import CheckCfgMember
from convert.adapters.solidworks.Archive.Config.Members.MemberLayouts import KMemberLayouts
from convert.adapters.solidworks.Archive.Config.Members.ReadMemBodyMut import ReadMemBodyMut
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader
from convert.adapters.solidworks.Archive.Tags.ReadTag import ReadTag


def span_payload(config, witness):
    start, base, _ = witness["start"]
    end, end_base, _ = witness["end"]
    data = config[start:end]
    require(4 <= start <= end <= len(config) and base == end_base == 4
            and len(data) == witness["width"] and digest(data) == witness["wire_sha256"],
            "the pinned native field span no longer matches the physical source")
    return data


def check_branch(config, witness):
    data = span_payload(config, witness)
    mode, field, mask = witness["mode"], witness["field"], witness["mask"]
    start, base, counter = witness["start"]
    require((base, counter) == tuple(witness["end"][1:]), "native branch changed its recorded map")
    fields, compared = {}, None
    if mode == "NotCondition":
        require(field == "" and mask == 0x80 and unpack("<i", data) == (0,),
                "native clear-bit branch no longer owns the zero f160 word")
        raw_words = [0]
    else:
        expected = ("kind", 2) if mode == "Equals" else ("n10c4", 0)
        require((field, mask) == expected, "unqualified native comparison role")
        (compared,) = unpack_from("<i", config, start - 4)
        fields[field] = compared
        raw_words = list(unpack("<Hii", data)) if mode == "Equals" else []
        require(raw_words == ([0, -1431655766, -1145324613] if mode == "Equals" else [])
                and (mode != "Greater" or not data), "the native comparison body changed")
    context = BodyContext(19000, {}, {}, {}, FlagsValue={"conditions": witness["conditions"]})
    rule = NativeField("Branch", field, ModeValue=mode, MaskValue=mask)
    outcome = IsBranchTaken(context, FieldScope(fields), rule)
    require(compared == witness["compared"] and outcome is witness["predicate"],
            "the production predicate differs from the pinned native context")
    return {"mode": mode, "field": field, "mask": mask, "compared": compared, "predicate": outcome,
            "conditions": witness["conditions"], "raw_words": raw_words,
            "start": witness["start"], "end": witness["end"], "width": len(data),
            "wire_sha256": digest(data)}


def check_repeat(config, witness, prefix):
    wire = span_payload(config, witness)
    start, base, next_before = witness["start"]
    end, _, next_after = witness["end"]
    tag, _ = ReadTag(wire, 0)
    require(tag.KindValue == "NewClass" and witness["field"] == "f9f8"
            and witness["mask"] == witness["rows"] == 10,
            "the native ten-view repeat no longer starts with its class tag")
    anchors = prefix.MapValue.EntriesValue
    maps = ArchiveMaps(prefix.BaseValue, prefix.MapValue)
    maps.CounterValue = next_before
    flags = {"conditions": witness["conditions"]}
    context = BodyContext(19000, KMemberLayouts, {}, {KViewClass.NameValue: (KViewClass.SchemaValue,)},
                          FlagsValue=flags)
    cursor = BinaryReader(config[:end], start)
    reader = GraphReader(cursor, maps, partial(ReadMemBodyMut, context, KViewClass))
    fields = {}
    frame = ReadFrame(context, reader, FieldScope(fields), prefix.RootValue, ReadSchemaMut, ReadFieldsMut)
    rules = (NativeField("Repeat", "f9f8", ModeValue="Fixed", MaskValue=10,
                         BodyValue=(NativeField("Node", "o"),)),)
    ReadFieldsMut(frame, rules)
    entries = maps.Snapshot().EntriesValue
    new_entries = entries[len(anchors):]
    require(cursor.GetOffset() == end and len(fields["f9f8"]) == 10
            and maps.BaseValue == base == prefix.BaseValue and maps.CounterValue == next_after
            and all(left is right for left, right in zip(anchors, entries[:len(anchors)], strict=True))
            and [slot.IndexValue for slot in new_entries] == list(range(next_before, next_after))
            and new_entries[0].EntryValue == KViewClass
            and flags["conditions"] == witness["conditions"] and flags["ctx87c"] == 0,
            "the native repeat changed its map, owners or framing")
    rows = []
    offset = start
    for row, entry in zip(fields["f9f8"], new_entries[1:], strict=True):
        view = row["o"]
        CheckCfgMember(view, KViewClass, maps)
        require(view is entry.EntryValue and view.IndexValue == entry.IndexValue
                and view.StartOffset == offset and view.EndOffset > offset,
                "a native view did not occupy its real object slot and span")
        rows.append({"name": view.FieldsValue["f358"], "class": view.ClassValue.NameValue,
                     "schema": view.ClassValue.SchemaValue, "index": view.IndexValue,
                     "interval": [view.StartOffset, view.EndOffset]})
        offset = view.EndOffset
    require(offset == end and context.UsageValue.SchemaCalls[KViewClass.NameValue] == 10,
            "the repeat did not decode each complete native view body")
    return {"field": "f9f8", "start": witness["start"], "end": witness["end"], "width": len(wire),
            "wire_sha256": digest(wire), "class_slot": new_entries[0].IndexValue,
            "anchor_slots": [x.IndexValue for x in anchors], "views": rows}


def check_mode_witnesses(config, witnesses, prefix):
    branches = [row for row in witnesses if row["action"] == "Branch"]
    repeats = [row for row in witnesses if row["action"] == "Repeat"]
    require([row["mode"] for row in branches] == ["Equals", "Greater", "NotCondition"]
            and [row["mode"] for row in repeats] == ["Fixed"],
            "the physical mode witness inventory is incomplete")
    return {"branch_witnesses": [check_branch(config, row) for row in branches],
            "native_repeat": check_repeat(config, repeats[0], prefix)}
