from collections.abc import Mapping, Sequence
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.CmgrHeader.ReadMgrHeader import ReadMgrHeader
from convert.adapters.solidworks.Archive.CmgrHeader.WriteMgrHeader import WriteMgrHeader
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue


# property scope tests must vary the effective native directory rather than the value cache
def ChangeTextHdr(BufferValue: bytes) -> bytes:
    GraphValue = ReadMgrHeader(BufferValue, 19000)
    ListValue = CastValue(Mapping[str, object], GraphValue.RootValue.FieldsValue["f08"])
    (RowValue,) = CastValue(Sequence[Mapping[str, object]], ListValue["items"])
    NodeValue = ArchiveNode.RequireNode(RowValue["o"])
    NodeValue.FieldsValue["f10"] = CStringValue("different manager configuration", True)
    OutputValue, _ = WriteMgrHeader(GraphValue.RootValue, 19000)
    return OutputValue
