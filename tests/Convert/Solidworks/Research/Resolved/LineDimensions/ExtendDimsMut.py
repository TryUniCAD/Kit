from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows


# compact and extended entity references must resolve to the same owned points and lines through complete stream reading
def ExtendDimsMut(SketchValue: ArchiveNode) -> None:
    FieldsValue = NativeRecord(SketchValue.FieldsValue["dims"])
    for RowValue in NativeRows(FieldsValue["val_g2"]):
        DriverValue = ArchiveNode.RequireNode(RowValue["d"])
        for NameValue in ("h1", "h2"):
            HandleValue = ArchiveNode.RequireNode(DriverValue.FieldsValue[NameValue])
            HandleValue.FieldsValue["f18"] = HandleValue.FieldsValue["idx"]
            HandleValue.FieldsValue["idx"] = 30591
    for RowValue in NativeRows(FieldsValue["log_g1"]):
        LogicalValue = NativeRecord(RowValue["d"])
        HandleValue = ArchiveNode.RequireNode(LogicalValue["h1"])
        HandleValue.FieldsValue["f18"] = HandleValue.FieldsValue["idx"]
        HandleValue.FieldsValue["idx"] = 30591
