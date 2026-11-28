from convert.adapters.solidworks.Archive.Construction.Dimensions.MakePoint import (
    MakePoint,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.FrameXform import (
    FrameXform,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.PlaneFrame import (
    PlaneFrame,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# the plane data begins uninitialized in native axis and border caches until the real rebuild
def MakeOffsetData(
    FrameValue: PlaneFrame,
    RefFields: dict[str, object],
    DisplayValue: ArchiveNode | None,
    IsReversed: bool,
) -> ArchiveNode:
    return ArchiveNode(
        RuntimeClass("moFaceRefPlnData_c", 1),
        {
            "root": MakePoint(
                XValue=FrameValue.OriginValue[0],
                YValue=FrameValue.OriginValue[1],
                ZValue=FrameValue.OriginValue[2],
            ),
            "normal": MakePoint(
                XValue=FrameValue.NormalValue[0],
                YValue=FrameValue.NormalValue[1],
                ZValue=FrameValue.NormalValue[2],
            ),
            "f20": FrameXform(FrameValue),
            **dict.fromkeys(("b0", "b1", "b2", "b3"), 0.0),
            "f48": None,
            "f50": 0,
            "f54": -4,
            "f58": -4,
            "old_e5": 0,
            "f5c": 5,
            "f60": 0,
            "f64": 0,
            "f68": None,
            "f70": None,
            "f78": None,
            "f90": RefFields,
            "f98": DisplayValue,
            "fa0": int(IsReversed),
            "fa4": 1,
            "has_fa8": 0,
            "fb4": 0,
        },
    )
