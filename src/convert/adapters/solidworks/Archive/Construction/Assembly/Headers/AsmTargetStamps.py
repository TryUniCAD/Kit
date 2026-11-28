from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadRows,
    RequireRecord,
)


# manager header target stamps fold every direct generated occurrence while preserving the native first transform stamp replacement and unsigned wrapping
def AsmTargetStamps(OwnerValue: ArchiveNode) -> tuple[int, int]:
    GeometryValue = FieldInt(OwnerValue.FieldsValue, "f1300")
    TransformValue = 101
    RowsValue = ReadRows(
        RequireRecord(RequireRecord(OwnerValue.FieldsValue["f68"])["list"])["items"]
    )
    if len(RowsValue) != FieldInt(OwnerValue.FieldsValue, "f1560"):
        raise ValueError(
            "assembly target stamps require the complete direct occurrence list"
        )
    for RowValue in RowsValue:
        Reference = ArchiveNode.RequireNode(RowValue["o"])
        if Reference.FieldsValue.get("owner") is not OwnerValue:
            raise ValueError(
                "assembly target stamp occurrence has a different actual owner"
            )
        GeometryValue = (
            GeometryValue + FieldInt(Reference.FieldsValue, "f3f4")
        ) & 0xFFFFFFFF
        IncomingValue = FieldInt(Reference.FieldsValue, "f3f0")
        TransformValue = (
            IncomingValue
            if TransformValue == 101
            else (TransformValue + IncomingValue) & 0xFFFFFFFF
        )
    return GeometryValue, TransformValue
