from convert.adapters.Fusion.Native.Circular.Snapshots.SnapFaces import (
    BodyFaces,
    FaceCoedges,
)
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.TagAttrib import TagAttrib
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)


# sketch sheets cannot substitute for absent physical solid face or rim identities
def CheckTagOwners(State: GeometryState) -> None:
    Solids = tuple(
        BodyFaces(State, Entity)
        for Entity in State.Entities
        if isinstance(Entity, BodyNode) and len(BodyFaces(State, Entity)) == 3
    )
    if len(Solids) != 1:
        raise ValueError("Native circular span has no unique solid label scope")
    Required = {State.Entities.index(FaceValue) for FaceValue in Solids[0]}
    Required.update(
        Coedge.EdgeRef
        for FaceValue in Solids[0]
        for Coedge in FaceCoedges(State, FaceValue)
    )
    Actual = tuple(
        Entity.Links.OwnerRef
        for Entity in State.Entities
        if isinstance(Entity, TagAttrib)
        and not isinstance(State.Entities[Entity.Links.OwnerRef], BodyNode)
    )
    if len(Required) != 5 or len(Actual) != 5 or set(Actual) != Required:
        raise ValueError("Native circular span labels do not cover the physical solid")
