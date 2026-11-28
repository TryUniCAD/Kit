from convert.adapters.Fusion.Native.Graph.IntegerValue import IntegerValue
from convert.Formats.Fusion.BrepCodec.Journal.Writing.MakeEntityNode import (
    MakeEntityNode,
)
from dataclasses import replace as ReplaceData
from typing import cast as CastValue
from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.Formats.Fusion.BrepCodec.Journal.JournalEntity import KJournalEntity
from convert.Formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.Formats.Fusion.BrepCodec.Journal.Permutation.RemapEntity import RemapEntity
from convert.Formats.Fusion.BrepCodec.Journal.Planar.MakeLiveTable import MakeLiveTable
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.CheckGeometry import (
    CheckGeometry,
)
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.Formats.Fusion.GeometryCodec.Frustum.FrustumBody import FrustumBody
from convert.adapters.Fusion.Native.Circular.Spans.CheckSpanCount import CheckSpanCount


# journal aliases must resolve before geometry and ownership can be compared
def ReadSpanState(
    Context: ExtrudeContext, History: JournalModel, Solid: FrustumBody
) -> GeometryState:
    Table = MakeLiveTable(History, IntegerValue(Context.Extrude.Fields["endModelHS"]))
    Positions = {
        SlotValue: Index for Index, SlotValue in enumerate(sorted(Table.LiveSlots))
    }
    Mapping = tuple(Positions.get(Stable, -1) for Stable in Table.SlotMap)
    Records = tuple(Table.Entities[SlotValue] for SlotValue in sorted(Table.LiveSlots))
    if any(Value is None for Value in Records):
        raise ValueError("Native circular span has an absent live record")
    for Value in CastValue(tuple[KJournalEntity, ...], Records):
        for TagValue, Target in MakeEntityNode(Value).Tokens:
            if (
                TagValue == 12
                and type(Target) is int
                and Target >= 0
                and (Target >= len(Mapping) or Mapping[Target] < 0)
            ):
                raise ValueError(
                    "Native circular span references an absent live entity"
                )
    Entities = tuple(
        RemapEntity(Value, Mapping)
        for Value in CastValue(tuple[KJournalEntity, ...], Records)
    )
    State = GeometryState(
        ReplaceData(History.Header, RootCount=2, Flags=2, Scale=10.0),
        History.Stamp,
        Entities,
    )
    CheckGeometry(State)
    CheckSpanCount(State, False, Solid)

    return State
