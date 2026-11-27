from convert.adapters.Fusion.Native.Circular.CircleShape import CircleShape
from convert.adapters.Fusion.Native.Circular.DualSnapshots.CheckPlaneFrame import (
    CheckPlaneFrame,
)
from convert.adapters.Fusion.Native.Circular.DualSnapshots.CheckRimFrame import (
    CheckRimFrame,
)
from convert.adapters.Fusion.Native.Circular.Snapshots.SnapAccess import SnapEntity
from convert.adapters.Fusion.Native.Circular.Snapshots.SnapFaces import FaceCoedges
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.EdgeNode import EdgeNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.PlaneNode import PlaneNode
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.Geometry.Extrude.Circular.DualSide.DualFrame import DualFrame
from interchange.geometry.Models.Transform import KTransformIdentity, Transform


# different source sheet roles require world profile placement and unchanged local sketch geometry
def CheckSheetFrame(
    State: GeometryState, FaceValue: FaceNode, Shape: CircleShape, Frame: Transform
) -> None:
    if FaceValue.Reversed or FaceValue.Contained != (
        False if FaceValue.DoubleSided else None
    ):
        raise ValueError("Dual snapshot sheet has unsupported face orientation")
    Placed = DualFrame(
        Frame if FaceValue.DoubleSided else KTransformIdentity, Shape.Geometry
    )
    CheckPlaneFrame(SnapEntity(State, FaceValue.Surface, PlaneNode), Placed)
    Coedges = FaceCoedges(State, FaceValue)
    if len(Coedges) != 1 or Coedges[0].Partner != -1 or Coedges[0].Reversed:
        raise ValueError("Dual snapshot sheet requires one open full circle loop")
    CheckRimFrame(
        State,
        SnapEntity(State, Coedges[0].EdgeRef, EdgeNode),
        Placed,
        Shape.Geometry.radius,
    )
