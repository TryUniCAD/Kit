from pathlib import PureWindowsPath

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    FieldText,
    RequireNode,
    RequireRecord,
)
from convert.adapters.solidworks.Assembly.PlanarMates.PlanarContext import PlanarChild


# shared header and archive body readers expose the same decoded string handle identity
def ReadFileText(HandleValue: object) -> str:
    Handle = RequireNode(HandleValue, "moCStringHandle_c")
    Fields = Handle.FieldsValue
    TextValues = tuple(
        FieldText(Fields, FieldName)
        for FieldName in ("text", "f08")
        if FieldName in Fields
    )
    if "value" in Fields:
        TypedValue = Fields["value"]
        if not isinstance(TypedValue, CStringValue) or not TypedValue.TextValue:
            raise ValueError(
                "native file handle requires a nonempty typed string value"
            )
        TextValues = (*TextValues, TypedValue.TextValue)
    if not TextValues or len(set(TextValues)) != 1:
        raise ValueError("native file handle text representations differ or are absent")
    return TextValues[0]


# repeated names or basenames cannot establish the referenced part file identity
def ReadFileKey(Reference: ArchiveNode) -> tuple[str, str, int, int]:
    FileFields = RequireRecord(Reference.FieldsValue.get("shared"))
    return (
        ReadFileText(FileFields.get("h10")),
        ReadFileText(FileFields.get("h18")),
        FieldInt(FileFields, "f20"),
        FieldInt(FileFields, "f28"),
    )


# wrapper references need the same file configuration and epoch before selecting a datum
def ReadChildStamp(
    Wrapper: ArchiveNode,
    Occurrence: ArchiveNode,
    ChildValue: PlanarChild,
    ConfigId: int,
    ConfigName: str,
    SourceName: str,
) -> int:
    Selected = RequireRecord(Occurrence.FieldsValue.get("f3c0"))
    if (
        FieldInt(Wrapper.FieldsValue, "f0c") != ConfigId
        or FieldInt(Selected, "f10") != ConfigId
        or FieldText(Selected, "f08") != ConfigName
    ):
        raise ValueError("mate wrapper child configuration differs")
    Header = RequireNode(ChildValue.HeaderNode, "moHeader_c")
    Stamp = FieldInt(Header.FieldsValue, "f40")
    if (FieldInt(Wrapper.FieldsValue, "f08") & 0xFFFFFFFF) != Stamp or FieldInt(
        Occurrence.FieldsValue, "f3e0"
    ) != Stamp:
        raise ValueError("mate wrapper child update is stale")
    External = RequireNode(Occurrence.FieldsValue.get("f3b0"), "moExtObject_c")
    ChildFile = RequireNode(Header.FieldsValue.get("f38"), "moExtObject_c")
    ExternalKey = ReadFileKey(External)
    if (
        ExternalKey != ReadFileKey(ChildFile)
        or ExternalKey[2] != 2
        or PureWindowsPath(ExternalKey[1]).name.casefold() != SourceName
    ):
        raise ValueError("mate wrapper targets a different part identity")
    return Stamp
