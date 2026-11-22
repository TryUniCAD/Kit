from convert.adapters.Fusion.Native.Circular.Snapshots.SnapFaces import (
    BodyFaces,
    FaceCoedges,
)
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.ConeNode import ConeNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.PlaneNode import PlaneNode
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.Formats.Fusion.GeometryCodec.Frustum.FrustumBody import FrustumBody
from convert.adapters.Fusion.Native.Circular.Spans.CheckSpanSide import CheckSpanSide
from convert.adapters.Fusion.Native.Circular.Spans.CheckSpanCap import CheckSpanCap
from convert.adapters.Fusion.Native.Circular.Spans.CheckSpanUses import CheckSpanUses


# closed circular solids must contain one side and two correctly oriented caps
def CheckSpanSolid(
    State: GeometryState, BodyValue: BodyNode, Model: FrustumBody
) -> None:
    Faces = BodyFaces(State, BodyValue)
    if len(Faces) != 3:
        raise ValueError("Native circular span requires three closed solid faces")
    Levels: set[float] = set()
    SideCount = 0
    for FaceValue in Faces:
        if FaceValue.DoubleSided or FaceValue.Contained is not None:
            raise ValueError("Native circular span contains a sheet face")
        Surface = State.Entities[FaceValue.Surface]
        Coedges = FaceCoedges(State, FaceValue)
        if isinstance(Surface, ConeNode):
            CheckSpanSide(Surface, FaceValue, Coedges, Model)
            SideCount += 1
        elif isinstance(Surface, PlaneNode):
            Levels.add(CheckSpanCap(Surface, FaceValue, Coedges, Model))
        else:
            raise ValueError("Native circular span contains a noncylindrical surface")
        CheckSpanUses(State, FaceValue, Coedges, Surface, Model)
    Lower = Model.BasePoint[2] / 10
    if SideCount != 1 or Levels != {Lower, Lower + Model.Height / 10}:
        raise ValueError("Native circular span is missing a side or distinct cap")
