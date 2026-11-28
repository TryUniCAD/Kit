from typing import Literal

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Cuts.ReadSingleNode import (
    ReadSingleNode,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckTreeAlias import (
    CheckTreeAlias,
)
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# the actual operation must own both distinct mapped face records in each saved chooser
def ReadChooserPair(
    LinkValue: NativeLink,
    OwnerValue: ArchiveNode,
    FieldName: Literal["f4a8", "f4c0"],
) -> tuple[ArchiveNode, ArchiveNode]:
    Fields = OwnerValue.FieldsValue
    if Fields.get("has_" + FieldName) != 1:
        raise ValueError("saved stock chooser has no active owner")
    Chooser = NativeRecord(Fields.get(FieldName))
    if Chooser.get("f68") is not OwnerValue:
        raise ValueError("saved stock chooser is detached from its operation")
    Choice = ReadSingleNode(Chooser.get("f48"), "moPerBodyChooserData_c")
    Faces = NativeRecord(Choice.FieldsValue.get("f08"))
    RowsValue = NativeRows(Faces.get("items"))
    if Faces.get("n") != 2 or len(RowsValue) != 2:
        raise ValueError("saved stock chooser has alternate face count")
    First = RequireNative(RowsValue[0].get("o"), "moFaceRef_c")
    Second = RequireNative(RowsValue[1].get("o"), "moFaceRef_c")
    if First is Second:
        raise ValueError("saved stock chooser repeats a face owner")
    CheckTreeAlias(LinkValue, (Choice, First, Second))
    return First, Second
