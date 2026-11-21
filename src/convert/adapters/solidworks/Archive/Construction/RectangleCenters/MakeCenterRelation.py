from convert.adapters.solidworks.Archive.Construction.SketchDimensions.MakeBinaryDim import (
    MakeBinaryDim,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# center constraints share the proved two handle coincidence constructor across point line and point point ownership
def MakeCenterRel(
    SketchValue: ArchiveNode, FirstHandle: ArchiveNode, SecondHandle: ArchiveNode
) -> dict[str, object]:
    if (
        FirstHandle.ClassValue != RuntimeClass("sgPointHandle", 1)
        or SecondHandle.ClassValue
        not in (RuntimeClass("sgPointHandle", 1), RuntimeClass("sgLineHandle", 1))
        or any(
            Handle.FieldsValue.get("_sketch") is not SketchValue
            for Handle in (FirstHandle, SecondHandle)
        )
    ):
        raise ValueError(
            "center coincidence requires actual local point and line or point handles"
        )
    return MakeBinaryDim(SketchValue, 9, FirstHandle, SecondHandle)
