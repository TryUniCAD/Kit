from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
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


# saved cap representatives can only reference the paired local caps and their one live arc
def CheckCacheFace(
    FaceValue: ArchiveNode, BossValue: ArchiveNode, CapValue: int, ArcMark: int
) -> tuple[ArchiveNode, ArchiveNode, ArchiveNode]:
    Fields = FaceValue.FieldsValue
    if (
        (Fields.get("f60"), Fields.get("f64"), Fields.get("f08"), Fields.get("fe8"))
        != (1, 0, 3, 768)
        or any(
            Fields.get(NameValue) != 0
            for NameValue in ("f70", "f48", "nd0", "has_f18", "nf0")
        )
        or Fields.get("f40") is not None
        or Fields.get("fd0")
        or Fields.get("ff0")
    ):
        raise ValueError("SOLIDWORKS attached circle has alternate face references")
    CapFields, ArcFields, Empty = NativeRows(Fields.get("f10"))
    CapFace, CapFile = ReadFaceRef(
        CapFields, "moEndFaceSurfIdRep_c", CapValue, BossValue
    )
    ArcFace, ArcFile = ReadFaceRef(
        ArcFields, "moFromSktEntSurfIdRep_c", ArcMark, BossValue
    )
    if Empty.get("f08") is not None or CapFile is not ArcFile:
        raise ValueError(
            "SOLIDWORKS attached circle face cache has an external reference"
        )
    return CapFace, ArcFace, CapFile
