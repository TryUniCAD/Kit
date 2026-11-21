from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadRows,
    RequireNode,
)
from convert.adapters.solidworks.Core.TypedMates.CheckPerpSelect import CheckPerpSelect


# perpendicular source admission requires both detached selection owners to agree with the ordered actual resolved references
def CheckPerpRefs(NodeValue: ArchiveNode, ModelValue: ArchiveNode) -> None:
    SelectedRows = ReadRows(NodeValue.FieldsValue.get("f3c8"))
    ResolvedRows = ReadRows(NodeValue.FieldsValue.get("f410"))
    if tuple(FieldInt(RowValue, "k") for RowValue in SelectedRows) != (0, 1):
        raise ValueError("perpendicular detached selection order is unsupported")
    for SelectedRow, ResolvedRow in zip(SelectedRows, ResolvedRows, strict=True):
        CheckPerpSelect(
            RequireNode(SelectedRow.get("o"), "moPlaneRef_w"),
            RequireNode(ResolvedRow.get("o"), "moPlaneRef_w"),
            ModelValue,
        )
