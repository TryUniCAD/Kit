from convert.adapters.solidworks.Archive.Construction.SketchDimensions.DimBaseFields import (
    DimBaseFields,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# center constraints share the proved two handle coincidence constructor across point line and point point ownership
def MakeCenterRelation(
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
    FieldsValue = DimBaseFields()
    FieldsValue.update(
        {
            "_sketch": SketchValue,
            "f80": 9,
            "f90": 2,
            "f94": 0,
            "f98": 0,
            "fa0": 0xFFFE,
            "fa4": 0,
            "h1": FirstHandle,
            "h2": SecondHandle,
            "ff8": 0,
            "ffc": 0,
            "f108": None,
            "f100": 0,
            "f110": -1,
            "f114": -1,
            "f118": 0.0,
            "f120": 0.0,
            "ext1": None,
            "ext2": None,
            "ext3": None,
            "f150": 0,
            "f154": -1,
        }
    )
    return FieldsValue
