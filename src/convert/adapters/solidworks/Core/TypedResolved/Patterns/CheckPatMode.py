from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Lines.IsLineState import IsLineState
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.Patterns.CheckPatOrig import (
    CheckPatOrig,
)
from convert.adapters.solidworks.Core.TypedResolved.ReadParents import ReadParents
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# the witnessed single direction mode excludes additional selections and dimension overrides
def CheckPatMode(PatternValue: ArchiveNode) -> None:
    Fields = PatternValue.FieldsValue
    ShapeValue = NativeRecord(Fields.get("ffa0"))
    ExtraLists = tuple(
        RequireNative(Fields.get(NameValue), "suObList")
        for NameValue in ("f9d8", "f8d8", "f990")
    )
    SeedList = RequireNative(Fields.get("f988"), "suObList")
    if (
        ReadParents(PatternValue)
        or len({SeedList, *ExtraLists}) != 4
        or any(
            Value.FieldsValue.get("n") != 0 or Value.FieldsValue.get("items")
            for Value in ExtraLists
        )
        or any(
            Fields.get(NameValue) is not None
            for NameValue in (
                "f820",
                "f8e0",
                "f950",
                "f1278",
                "f1280",
                "f1290",
                "f12e8",
                "f12f0",
                "f1300",
                "f1308",
            )
        )
        or any(
            Fields.get(NameValue) != 0
            for NameValue in (
                "f129c",
                "fa00",
                "f948",
                "n870",
                "nf30",
                "fa04",
                "fa08",
                "na10",
                "na30",
                "f1128",
                "n930",
                "f112c",
                "f12a4",
                "f12e0",
                "f12e4",
                "f1310",
                "f1314",
                "f1328",
                "f132c",
                "f12a0",
            )
        )
        or any(
            Fields.get(NameValue) != 1
            for NameValue in (
                "f9e0",
                "f9fc",
                "f9f0",
                "f1050",
                "f1054",
                "f1130",
                "f12f8",
                "f12fc",
            )
        )
        or not all(
            IsLineState(Fields.get(NameValue))
            for NameValue in ("f840", "ff50", "f8e8", "f870", "f930")
        )
        or ShapeValue.get("f30") != 1
        or ShapeValue.get("f48") is not None
        or ShapeValue.get("f98") != 0
        or ShapeValue.get("f68") is not None
        or ShapeValue.get("f9c") != 0
        or ShapeValue.get("f18") != {"x": 0.0, "y": 0.0, "z": 0.0}
    ):
        raise ValueError("unsupported saved linear pattern mode or owner")
    for NameValue in ("fa50", "fcb8"):
        CheckPatOrig(Fields.get(NameValue))
