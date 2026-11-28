from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows


# external and local point handles must keep their real namespaces through the serialized extended index branch
def ExtendOriginMut(SketchValue: ArchiveNode) -> None:
    Dimensions = NativeRecord(SketchValue.FieldsValue["dims"])
    Relation = NativeRecord(NativeRows(Dimensions["log_g2"])[0]["d"])
    PointValue = NativeRecord(NativeRows(SketchValue.FieldsValue["points"])[4]["point"])
    ExternalValue = ArchiveNode.RequireNode(PointValue["ext"])
    WrapperValue = ArchiveNode.RequireNode(ExternalValue.FieldsValue["f08"])
    Selection = ArchiveNode.RequireNode(WrapperValue.FieldsValue["f58"])
    Handles = tuple(
        ArchiveNode.RequireNode(Relation[NameValue]) for NameValue in ("h1", "h2")
    )
    for HandleValue in (
        *Handles,
        ArchiveNode.RequireNode(Selection.FieldsValue["f0f8"]),
    ):
        HandleValue.FieldsValue["f18"] = HandleValue.FieldsValue["idx"]
        HandleValue.FieldsValue["idx"] = 30591
    SketchValue.FieldsValue["dims"] = Dimensions
