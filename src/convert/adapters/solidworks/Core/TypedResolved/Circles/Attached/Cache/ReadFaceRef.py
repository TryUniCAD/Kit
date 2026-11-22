from collections.abc import Mapping
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# each retained face identity must remain local to the same creating feature
def ReadFaceRef(
    Fields: Mapping[str, object], ClassName: str, SlotValue: int, BossValue: ArchiveNode
) -> tuple[ArchiveNode, ArchiveNode]:
    FaceNode = RequireNative(Fields.get("f08"), ClassName)
    Values = FaceNode.FieldsValue
    Reference = NativeRecord(Values.get("f10"))
    Owner = RequireNative(Reference.get("f10"), "moFR_c")
    Address = NativeRecord(Owner.FieldsValue.get("f10"))
    if (
        Values.get("f38") != SlotValue
        or Values.get("f3c", 0) != 0
        or Reference.get("f08") is not None
        or Address.get("f00") != NativeNodeId(BossValue)
        or type(Address.get("f08")) is not int
    ):
        raise ValueError("SOLIDWORKS attached circle face cache has a foreign producer")
    FileNode = RequireNative(Owner.FieldsValue.get("f08"), "moExtObject_c")
    return FaceNode, FileNode
