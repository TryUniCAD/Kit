from convert.adapters.solidworks.Archive.Construction.SketchDimensions.DimBaseFields import (
    DimBaseFields,
)
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.MakePointRef import (
    MakePointRef,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# coincidence must reference the external origin and local corner through distinct actual point handles
def MakeCornerRel(
    SketchValue: ArchiveNode, PointValues: tuple[ArchiveNode, ...]
) -> dict[str, object]:
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
            "h1": MakePointRef(SketchValue, PointValues, PointValues[-1]),
            "h2": MakePointRef(SketchValue, PointValues, PointValues[0]),
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
