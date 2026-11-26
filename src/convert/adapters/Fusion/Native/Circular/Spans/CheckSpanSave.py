from convert.adapters.Fusion.Native.Circular.CircleShape import CircleShape
from convert.adapters.Fusion.Native.Circular.Snapshots.CheckCoverage import (
    CheckCoverage,
)
from convert.adapters.Fusion.Native.Circular.Snapshots.CheckSheets import CheckSheets
from convert.adapters.Fusion.Native.Circular.Snapshots.SnapFaces import BodyFaces
from convert.adapters.Fusion.Native.Circular.Spans.CheckSpanSolid import CheckSpanSolid
from convert.adapters.Fusion.Native.Circular.Spans.CheckSpanTags import CheckSpanTags
from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.Formats.Fusion.GeometryCodec.Frustum.FrustumBody import FrustumBody
from convert.adapters.Fusion.Native.Circular.Spans.CheckSpanCount import CheckSpanCount


# saved solids and separate sketch sections must agree with active history
def CheckSpanSave(
    Snapshot: GeometryState,
    Context: ExtrudeContext,
    Shape: CircleShape,
    Solid: FrustumBody,
    Operations: tuple[int, ...],
    Primary: str,
) -> None:
    CheckSpanCount(Snapshot, True, Solid)
    CheckCoverage(Snapshot)
    Sheets: list[FaceNode] = []
    SolidCount = 0
    for BodyValue in Snapshot.Entities:
        if not isinstance(BodyValue, BodyNode):
            continue
        Faces = BodyFaces(Snapshot, BodyValue)
        if len(Faces) == 1:
            Sheets.extend(Faces)
        else:
            CheckSpanSolid(Snapshot, BodyValue, Solid)
            SolidCount += 1
    if SolidCount != 1:
        raise ValueError("Native circular snapshot has no unique matching solid")
    CheckSheets(Snapshot, tuple(Sheets), Shape)
    if CheckSpanTags(Snapshot, Context, Shape, Solid, Operations, False) != Primary:
        raise ValueError("Native circular span snapshot labels disagree with history")
