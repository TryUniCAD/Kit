from convert.adapters.solidworks.Archive.Construction.SketchDimensions.DimBaseFields import (
    DimBaseFields,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# ordinary binary logical records share one local constructor with the actual relation code and ordered handles
def MakeBinaryDim(
    SketchValue: ArchiveNode,
    CodeValue: int,
    FirstHandle: ArchiveNode,
    SecondHandle: ArchiveNode,
) -> dict[str, object]:
    return {
        **DimBaseFields(),
        "_sketch": SketchValue,
        "f80": CodeValue,
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
