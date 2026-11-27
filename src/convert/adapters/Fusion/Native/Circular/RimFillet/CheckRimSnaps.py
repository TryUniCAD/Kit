from convert.adapters.Fusion.Native.Circular.CircleShape import CircleShape
from convert.adapters.Fusion.Native.Circular.RimFillet.ReadRimSnapshot import (
    ReadRimSnapshot,
)
from convert.adapters.Fusion.Native.Circular.RimFillet.CheckRimGeo import CheckRimGeo
from convert.adapters.Fusion.Native.Circular.RimFillet.CheckRimTrack import (
    CheckRimTrack,
)
from convert.adapters.Fusion.Native.Circular.RimPolicy.RimContext import RimContext
from convert.adapters.Fusion.Native.Circular.DualSnapshots.CheckSnapHead import (
    CheckSnapHead,
)
from convert.adapters.Fusion.Native.Circular.DualSnapshots.CheckSnapLinks import (
    CheckSnapLinks,
)
from convert.adapters.Fusion.Native.Circular.DualSnapshots.ReadSnapRoles import (
    ReadSnapRoles,
)
from convert.adapters.Fusion.Native.Circular.DualSnapshots.CanonicalBody import (
    CanonicalBody,
)
from convert.adapters.Fusion.Native.Circular.DualSnapshots.BodyClosure import (
    BodyClosure,
)
from convert.adapters.Fusion.Native.Circular.DualSnapshots.CheckSheetBody import (
    CheckSheetBody,
)
from convert.adapters.Fusion.Native.Circular.DualSnapshots.CheckSheetFrame import (
    CheckSheetFrame,
)
from convert.adapters.Fusion.Native.Circular.Snapshots.SnapFaces import BodyFaces
from convert.adapters.Fusion.Native.Circular.Snapshots.SnapAccess import SnapEntity
from convert.adapters.Fusion.Native.Graph.GraphValues import NumberValue
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Rectangle.CurveTags import CurveTag
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from interchange.geometry.Models.Transform import KTransformIdentity


# all saved bodies must bind the original cylinder and both source sheets without substituting the final fillet
def CheckRimSnaps(
    Model: DocumentModel,
    Graph: NativeGraph,
    Context: RimContext,
    Shape: CircleShape,
    Prior: GeometryState,
) -> None:
    State = ReadRimSnapshot(Model)
    CheckSnapHead(State, Prior)
    Roles = ReadSnapRoles(State)
    CheckSnapLinks(
        Model, Graph, Context.Extrusion, tuple(RoleName for _, RoleName in Roles)
    )
    Faces, Edges = CheckRimGeo(
        Prior,
        Shape.Geometry.radius,
        NumberValue(Context.Extrusion.Along.Fields["value"]) * 10,
        0.0,
    )
    Cleaned = CheckRimTrack(Prior, Edges["top"], Context.SelectedRef.ObjectId)
    SolidRoot = next(Index for Index, RoleName in Roles if RoleName == "solid")
    if CanonicalBody(Cleaned, Faces["body"]) != CanonicalBody(State, SolidRoot):
        raise ValueError("Native rim snapshot disagrees with its complete predecessor")
    Closures = [BodyClosure(State, SolidRoot)]
    for Index, RoleName in Roles:
        if RoleName == "solid":
            continue
        Closures.append(CheckSheetBody(State, Index, CurveTag(Shape.CurveNode)))
        for FaceValue in BodyFaces(State, SnapEntity(State, Index, BodyNode)):
            CheckSheetFrame(State, FaceValue, Shape, KTransformIdentity)
    if sum(len(Closure) for Closure in Closures) != len(
        State.Entities
    ) - 1 or set().union(*map(set, Closures)) != set(range(1, len(State.Entities))):
        raise ValueError("Native rim snapshot has overlapping or unaccounted records")
