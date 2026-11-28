from convert.adapters.solidworks.Archive.Construction.Datums.Angles.AngleGeometry import (
    AngleGeometry,
)
from convert.adapters.solidworks.Archive.Construction.Datums.Angles.DatumVector import (
    DatumPoint,
    KHingeAxis,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakePoint import (
    MakePoint,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.FrameXform import (
    FrameXform,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# each local constrained plane selection owns its distinct default pick coordinates
def AnglePick() -> dict[str, object]:
    return {"u": 0.5, "v": 0.5, "f20": MakePoint()}


# two active selections and the separate unselected row form the measured angular constraint
def MakeAngleData(
    PlaneValue: ArchiveNode,
    RightPick: ArchiveNode,
    AxisPick: ArchiveNode,
    Geometry: AngleGeometry,
    AngleValue: float,
) -> ArchiveNode:
    AngleRow = ArchiveNode(
        RuntimeClass("moRefPlaneAngleGeom_c", 1),
        {"f08": RightPick, **AnglePick(), "f38": AngleValue, "f40": 0},
    )
    Coincident = RuntimeClass("moRefPlaneCoincidentGeom_c", 1)
    Interface = ArchiveNode(
        RuntimeClass("moConstraintRefplaneInterfaceData_c", 1),
        {
            "f08": AngleRow,
            "f10": ArchiveNode(Coincident, {"f08": AxisPick, **AnglePick()}),
            "f18": ArchiveNode(Coincident, {"f08": None, **AnglePick()}),
        },
    )
    FrameValue = Geometry.PlaneValue
    Fields: dict[str, object] = {
        "owner": PlaneValue,
        "root": DatumPoint(FrameValue.OriginValue),
        "normal": DatumPoint(FrameValue.NormalValue),
        "f20": FrameXform(FrameValue),
        **{f"b{Index}": Value for Index, Value in enumerate(Geometry.BordersValue)},
        "f48": None,
        "f50": 0,
        "f54": -4,
        "f58": -4,
        "old_e5": 0,
        "f5c": 22,
        "f60": 0,
        "f64": 0,
        "f68": None,
        "f70": None,
        "f78": None,
        "f88": Interface,
        "f148": int(3 * KHingeAxis[2]),
    }
    return ArchiveNode(
        RuntimeClass("moConstraintCoincLineAtAnglePlaneRefplaneData_c", 1), Fields
    )
