from convert.adapters.Fusion.Native.Circular.CircleShape import CircleShape
from convert.adapters.Fusion.Native.Circular.DualSnapshots.CheckSnapHead import (
    CheckSnapHead,
)
from convert.adapters.Fusion.Native.Graph.GraphValues import CheckIdentity
from convert.adapters.Fusion.Native.Circular.DualSnapshots.BodyClosure import (
    BodyClosure,
)
from convert.adapters.Fusion.Native.Circular.DualSnapshots.CanonicalBody import (
    CanonicalBody,
)
from convert.adapters.Fusion.Native.Circular.DualSnapshots.CheckSheetBody import (
    CheckSheetBody,
)
from convert.adapters.Fusion.Native.Circular.DualSnapshots.CheckSnapLinks import (
    CheckSnapLinks,
)
from convert.adapters.Fusion.Native.Circular.DualSnapshots.ReadSnapRoles import (
    ReadSnapRoles,
)
from convert.adapters.Fusion.Native.Circular.Snapshots.CheckSheets import CheckSheets
from convert.adapters.Fusion.Native.Circular.Snapshots.SnapAccess import SnapEntity
from convert.adapters.Fusion.Native.Circular.Snapshots.SnapFaces import BodyFaces
from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Rectangle.CurveTags import CurveTag
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel


# saved snapshots must independently cover the selected solid and both source sheets before public admission
def CheckDualSnaps(
    Model: DocumentModel,
    Graph: NativeGraph,
    Context: ExtrudeContext,
    Shape: CircleShape,
    LiveState: GeometryState,
) -> None:
    if len(Model.Snapshots) != 1 or not isinstance(
        Model.Snapshots[0].Snapshot, GeometryState
    ):
        raise ValueError("Dual extrusion requires one complete typed saved snapshot")
    State = Model.Snapshots[0].Snapshot
    CheckIdentity(Context.Plane.Fields["transform"])
    CheckIdentity(Context.Sketch.Fields["occurrenceTransform"])
    CheckSnapHead(State, LiveState)
    Roles = ReadSnapRoles(State)
    CheckSnapLinks(Model, Graph, Context, tuple(RoleName for _, RoleName in Roles))
    (LiveRoot,) = (
        Identity
        for Identity, Entity in enumerate(LiveState.Entities)
        if isinstance(Entity, BodyNode)
    )
    SolidRoot = next(Identity for Identity, RoleName in Roles if RoleName == "solid")
    if CanonicalBody(State, SolidRoot) != CanonicalBody(LiveState, LiveRoot):
        raise ValueError(
            "Dual snapshot solid disagrees with its complete live topology"
        )
    Closures = [BodyClosure(State, SolidRoot)]
    SheetFaces: list[FaceNode] = []
    for Identity, RoleName in Roles:
        if RoleName == "solid":
            continue
        Closures.append(CheckSheetBody(State, Identity, CurveTag(Shape.CurveNode)))
        SheetFaces.extend(BodyFaces(State, SnapEntity(State, Identity, BodyNode)))
    CheckSheets(State, tuple(SheetFaces), Shape)
    if sum(len(Closure) for Closure in Closures) != len(
        State.Entities
    ) - 1 or set().union(*map(set, Closures)) != set(range(1, len(State.Entities))):
        raise ValueError("Dual snapshot has overlapping or unaccounted body records")
