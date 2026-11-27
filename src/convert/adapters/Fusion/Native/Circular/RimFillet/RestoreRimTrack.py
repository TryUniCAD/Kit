from dataclasses import replace as ReplaceData

from convert.Formats.Fusion.BrepCodec.Journal.Attributes.TrackAttrib import TrackAttrib
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.TagAttrib import TagAttrib
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.EdgeNode import EdgeNode
from convert.Formats.Fusion.BrepCodec.Journal.Permutation.RemapEntity import RemapEntity
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.adapters.Fusion.Native.Circular.Snapshots.SnapAccess import SnapEntity


# the comparison only tracker removal must be bijective for every retained entity and reference
def RestoreRimTrack(
    State: GeometryState, Index: int, Tracker: TrackAttrib
) -> GeometryState:
    Mapping = tuple(
        Ordinal + (Ordinal >= Index) for Ordinal in range(len(State.Entities))
    )
    Entities = [RemapEntity(Entity, Mapping) for Entity in State.Entities]
    Entities.insert(Index, Tracker)
    Expanded = ReplaceData(State, Entities=tuple(Entities))
    Owner = SnapEntity(Expanded, Tracker.Links.OwnerRef, EdgeNode)
    Following = SnapEntity(Expanded, Tracker.Links.NextAttrib, TagAttrib)
    Entities[Tracker.Links.OwnerRef] = ReplaceData(
        Owner, Prefix=ReplaceData(Owner.Prefix, Attribute=Index)
    )
    Entities[Tracker.Links.NextAttrib] = ReplaceData(
        Following, Links=ReplaceData(Following.Links, PriorAttrib=Index)
    )
    return ReplaceData(State, Entities=tuple(Entities))
