from dataclasses import replace as ReplaceData
from typing import cast as CastValue

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


# native alias resolution must precede carrier and closed topology comparisons
def ReadDualState(History: JournalModel, StateId: int) -> GeometryState:
    Table = MakeLiveTable(History, StateId)
    Positions = {Stable: Index for Index, Stable in enumerate(sorted(Table.LiveSlots))}
    Mapping = tuple(Positions.get(Stable, -1) for Stable in Table.SlotMap)
    Records = tuple(Table.Entities[Stable] for Stable in sorted(Table.LiveSlots))
    if any(Value is None for Value in Records):
        raise ValueError("Native drafted solid has an absent live entity")
    State = GeometryState(
        ReplaceData(History.Header, RootCount=2, Flags=2, Scale=10.0),
        History.Stamp,
        tuple(
            RemapEntity(Value, Mapping)
            for Value in CastValue(tuple[KJournalEntity, ...], Records)
        ),
    )
    CheckGeometry(State)
    return State
