from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Circles.Attached.Cache.ReadFaceRef import (
    ReadFaceRef,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows


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
