from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Header.HeaderFields import (
    KExtLeadFields,
    KExtTailFields,
    KRefCfgFields,
    KSharedFields,
)
from convert.adapters.solidworks.Archive.Header.NativeFileRef import NativeFileRef
from convert.adapters.solidworks.Archive.Header.ReadHeaderWire import ReadWireFields
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader
from convert.adapters.solidworks.Archive.Reading.ReadNativeText import ReadCStringMut
from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue


# shared file records own path spelling and kind before occurrence state begins
def ReadFileRefMut(ReaderValue: GraphReader, NodeValue: ArchiveNode) -> None:
    Shared = ReadWireFields(ReaderValue, KSharedFields)
    Fields = NodeValue.FieldsValue
    Fields["shared"] = Shared
    Fields.update(ReadWireFields(ReaderValue, KExtLeadFields))
    Reference = ReadWireFields(ReaderValue, KRefCfgFields)
    Fields["refcfg"] = Reference
    Fields.update(ReadWireFields(ReaderValue, KExtTailFields))
    Fields["file"] = NativeFileRef(
        GetHandleText(CastValue(ArchiveNode | None, Shared["h18"])),
        GetHandleText(CastValue(ArchiveNode | None, Shared["h10"])),
        CastValue(int, Shared["f20"]),
        CastValue(CStringValue, Reference["f08"]).TextValue,
    )


# a handle can refer to an already decoded string in the shared archive map
def GetHandleText(Handle: ArchiveNode | None) -> str:
    if Handle is None:
        return ""
    TextValue = Handle.FieldsValue.get("text")
    if not isinstance(TextValue, str):
        raise ValueError("SOLIDWORKS file reference has an incomplete text handle")
    return TextValue


# directory paths must share the serialized text handle grammar with their names
def ReadNameMut(ReaderValue: GraphReader, NodeValue: ArchiveNode) -> None:
    TextValue = ReadCStringMut(ReaderValue.Cursor)
    NodeValue.FieldsValue["value"] = TextValue
    NodeValue.FieldsValue["text"] = TextValue.TextValue
