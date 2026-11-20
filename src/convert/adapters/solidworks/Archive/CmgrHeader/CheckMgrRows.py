from collections.abc import MutableMapping, Sequence
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.CmgrHeader.ManagerSchemas import (
    KConfigHdrClass,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# null and reused tags bypass body callbacks so each row must still match its owner role
def CheckMgrRows(RootValue: ArchiveNode) -> None:
    ListValue = RootValue.FieldsValue.get("f08")
    if not isinstance(ListValue, MutableMapping):
        raise BodyUnsupported("SOLIDWORKS manager directory requires an embedded list")
    ListFields = CastValue(MutableMapping[str, object], ListValue)
    RowsValue = ListFields.get("items")
    if not isinstance(RowsValue, Sequence) or isinstance(
        RowsValue, (str, bytes, bytearray)
    ):
        raise BodyUnsupported("SOLIDWORKS manager directory requires ordered rows")
    for RowValue in CastValue(Sequence[object], RowsValue):
        if not isinstance(RowValue, MutableMapping):
            raise BodyUnsupported("SOLIDWORKS manager directory requires row fields")
        Fields = CastValue(MutableMapping[str, object], RowValue)
        NodeValue = Fields.get("o")
        if (
            not isinstance(NodeValue, ArchiveNode)
            or NodeValue.ClassValue != KConfigHdrClass
        ):
            raise BodyUnsupported(
                "SOLIDWORKS manager directory row requires a concrete configuration header"
            )
