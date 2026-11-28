from convert.adapters.solidworks.Archive.Construction.Geometry.PlaneFrame import (
    PlaneFrame,
)
from convert.adapters.solidworks.Archive.Construction.Origin.OriginGraph import (
    OriginGraph,
)
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.ReadPointPair import (
    ReadPointPair,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# external origin wrappers compute backup position from actual geometry while retaining source proven constructor state
def MakeOriginWrap(
    SelectionValue: ArchiveNode, OriginValue: OriginGraph, FrameValue: PlaneFrame
) -> ArchiveNode:
    FirstCoord, SecondCoord = ReadPointPair(OriginValue.PointValue)
    PositionValue = tuple(
        FrameValue.OriginValue[IndexValue]
        + FirstCoord * FrameValue.AxisU[IndexValue]
        + SecondCoord * FrameValue.AxisV[IndexValue]
        for IndexValue in range(3)
    )
    BackupValue = ArchiveNode(
        RuntimeClass("moPointBackedUpData_c", 1),
        {"f08": dict(zip("xyz", PositionValue, strict=True))},
    )
    return ArchiveNode(
        RuntimeClass("moSketchExtRef_w", 1),
        {
            "f58": SelectionValue,
            "f60": None,
            "f68": 0,
            "f6c": 0,
            "f08": 101,
            "has_f10": 0,
            "has_f18": 0,
            "f0c": -1,
            "f20": 0,
            "f74": -12345,
            "f78": -12345,
            "f7c": -12345,
            "f50": 0,
            "f70": 19000,
            "f34": 0,
            "f30": 0,
            "f98": 0,
            "f38": -1,
            "fb0": 0,
            "fb8": BackupValue,
        },
    )
