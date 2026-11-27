from convert.adapters.Fusion.Native.Circular.Snapshots.SnapAccess import SnapEntity
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.CoedgeNode import CoedgeNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.LoopNode import LoopNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.EdgeNode import EdgeNode
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)


# every full circle use must retain reciprocal loop and partner ownership with physical winding
def CheckRimUse(
    State: GeometryState,
    Coedge: CoedgeNode,
    FaceIndex: int,
    RoleName: str,
    Circles: dict[int, str],
    IsFinal: bool,
) -> str:
    Index = State.Entities.index(Coedge)
    LoopValue = SnapEntity(State, Coedge.OwnerLoop, LoopNode)
    Partner = SnapEntity(State, Coedge.Partner, CoedgeNode)
    EdgeValue = SnapEntity(State, Coedge.EdgeRef, EdgeNode)
    EdgeRole = Circles.get(EdgeValue.CurveRef, "")
    if not EdgeRole:
        raise ValueError("Native rim use has another curve carrier")
    if (
        Coedge.NextCoedge != Index
        or Coedge.PriorCoedge != Index
        or Coedge.Pcurve != -1
        or LoopValue.FirstCoedge != Index
        or LoopValue.OwnerFace != FaceIndex
        or Partner.Partner != Index
        or Partner.EdgeRef != Coedge.EdgeRef
        or Partner.Reversed == Coedge.Reversed
    ):
        raise ValueError("Native rim boundary incidence is not reciprocal")
    Expected = (
        (RoleName == "side" and EdgeRole != "bottom")
        or RoleName == "bottom"
        or (IsFinal and RoleName == "top")
    )
    if Coedge.Reversed != Expected:
        raise ValueError("Native rim boundary has another physical orientation")
    return EdgeRole
