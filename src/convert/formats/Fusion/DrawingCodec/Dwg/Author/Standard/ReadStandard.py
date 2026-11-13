from functools import cache as CacheValue
from json import loads as LoadJson
from pathlib import Path

from convert.formats.Fusion.DocumentCodec.Values.ReadObjects import (
    IsTrueValue,
    ReadInteger,
    ReadObject,
    ReadSeries,
    ReadString,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftRow import DraftEed, DraftRow
from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftValue import DraftLink
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Standard.DraftStandard import (
    DraftStandard,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Standard.ReadDraftJson import (
    ReadDraftJson,
    ReadDraftRecord,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgClassRow import DwgClassRow


def ReadClassRow(Value: object) -> DwgClassRow:
    Fields = ReadObject(Value)
    return DwgClassRow(
        ReadInteger(Fields["ClassNumber"]),
        ReadInteger(Fields["ProxyFlags"]),
        ReadString(Fields["AppName"]),
        ReadString(Fields["CppName"]),
        ReadString(Fields["DxfName"]),
        IsTrueValue(Fields["WasZombie"]),
        ReadInteger(Fields["ItemClassId"]),
        0,
        ReadInteger(Fields["DwgVersion"]),
        ReadInteger(Fields["MaintVersion"]),
        0,
        0,
    )


def ReadEedBlock(Value: object) -> DraftEed:
    AppValue, ItemsValue = ReadSeries(Value)
    AppLink = ReadDraftJson(AppValue)
    if not isinstance(AppLink, DraftLink):
        raise ValueError(
            "Authored DWG standard extended data needs an application link"
        )
    return DraftEed(AppLink, ReadDraftRecord(ItemsValue))


def ReadDraftRow(Value: object) -> DraftRow:
    KeyText, ClassName, CommonValue, ClassValue, EedValue = ReadSeries(Value)
    return DraftRow(
        ReadString(KeyText),
        ReadString(ClassName),
        ReadDraftRecord(CommonValue),
        ReadDraftRecord(ClassValue),
        tuple(ReadEedBlock(Entry) for Entry in ReadSeries(EedValue)),
    )


def ReadStandard(Source: Path) -> DraftStandard:
    Fields = ReadObject(LoadJson(Source.read_text(encoding="utf-8")))
    Fixed = (ReadSeries(Entry) for Entry in ReadSeries(Fields["Fixed"]))
    Slots = (ReadSeries(Entry) for Entry in ReadSeries(Fields["Slots"]))
    return DraftStandard(
        tuple(ReadClassRow(Entry) for Entry in ReadSeries(Fields["Classes"])),
        ReadDraftRecord(Fields["HeaderVars"]),
        tuple((ReadString(KeyText), ReadInteger(Handle)) for KeyText, Handle in Fixed),
        tuple(
            (
                ReadString(SlotName),
                tuple(ReadDraftJson(Member) for Member in ReadSeries(Items)),
            )
            for SlotName, Items in Slots
        ),
        tuple(ReadDraftRow(Entry) for Entry in ReadSeries(Fields["Rows"])),
    )


@CacheValue
def IsoStandard() -> DraftStandard:
    return ReadStandard(Path(__file__).with_name("IsoStandard.json"))
