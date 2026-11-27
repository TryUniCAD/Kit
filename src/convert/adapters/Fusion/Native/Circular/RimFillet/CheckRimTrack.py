from dataclasses import replace as ReplaceData

from convert.adapters.Fusion.Native.Circular.RimFillet.RestoreRimTrack import (
    RestoreRimTrack,
)
from convert.adapters.Fusion.Native.Circular.Snapshots.SnapAccess import SnapEntity
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.TrackAttrib import TrackAttrib
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.TagAttrib import TagAttrib
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.EdgeNode import EdgeNode
from convert.Formats.Fusion.BrepCodec.Journal.Permutation.RemapEntity import RemapEntity
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)


# only the actual selected edge tracker may be absent from the saved predecessor comparison
def CheckRimTrack(
    State: GeometryState, OwnerIndex: int, ReferenceId: int
) -> GeometryState:
    Tracks = tuple(
        (Index, Entity)
        for Index, Entity in enumerate(State.Entities)
        if isinstance(Entity, TrackAttrib)
    )
    if len(Tracks) != 1:
        raise ValueError("Native rim predecessor has unaccounted tracking records")
    Index, Tracker = Tracks[0]
    Owner = SnapEntity(State, OwnerIndex, EdgeNode)
    Following = SnapEntity(State, Tracker.Links.NextAttrib, TagAttrib)
    if (
        Tracker.TrackedId != ReferenceId
        or Tracker.Links.OwnerRef != OwnerIndex
        or Tracker.Links.PriorAttrib != -1
        or Owner.Prefix.Attribute != Index
        or Following.Links.OwnerRef != OwnerIndex
        or Following.Links.PriorAttrib != Index
    ):
        raise ValueError("Native rim tracker does not belong to its actual selection")
    Entities = list(State.Entities)
    Entities[OwnerIndex] = ReplaceData(
        Owner, Prefix=ReplaceData(Owner.Prefix, Attribute=Tracker.Links.NextAttrib)
    )
    Entities[Tracker.Links.NextAttrib] = ReplaceData(
        Following, Links=ReplaceData(Following.Links, PriorAttrib=-1)
    )
    Mapping = tuple(
        Ordinal - (Ordinal > Index) if Ordinal != Index else -1
        for Ordinal in range(len(Entities))
    )
    Cleaned = ReplaceData(
        State,
        Entities=tuple(
            RemapEntity(Entity, Mapping)
            for Ordinal, Entity in enumerate(Entities)
            if Ordinal != Index
        ),
    )
    if RestoreRimTrack(Cleaned, Index, Tracker) != State:
        raise ValueError("Native rim tracker normalization is not reversible")
    return Cleaned
