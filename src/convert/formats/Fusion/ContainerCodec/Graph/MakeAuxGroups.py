from __future__ import annotations

from typing import TYPE_CHECKING

from convert.formats.Fusion.EntityCodec.Model.EntityGroup import EntityGroup
from convert.formats.Fusion.EntityCodec.Model.NamedValue import NamedValue
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue

if TYPE_CHECKING:
    from convert.formats.Fusion.ContainerCodec.Graph.SegmentCatalog import (
        SegmentCatalog,
    )


def MakeAuxGroups(
    Catalog: SegmentCatalog, ClassName: str, Fields: dict[str, KEntityValue]
) -> tuple[EntityGroup, ...]:
    Current = Catalog.ByName[ClassName].Value.ClassGuid.upper()
    Groups: list[EntityGroup] = []
    Consumed: set[str] = set()
    Visited: set[str] = set()
    while Current and Current != Catalog.Profile.RootGuid.upper():
        if Current in Visited or Current not in Catalog.ByGuid:
            raise ValueError("Invalid Fusion auxiliary class ancestry")
        Visited.add(Current)
        Schema = Catalog.ByGuid[Current].Value
        Names = tuple(Member.FieldName for Member in Schema.Members if Member.IsSaved)
        if not set(Names).issubset(Fields):
            raise ValueError("Missing Fusion auxiliary entity fields")
        Consumed.update(Names)
        Groups.append(
            EntityGroup(
                Schema.ClassGuid,
                tuple(NamedValue(NameValue, Fields[NameValue]) for NameValue in Names),
            )
        )
        Current = Schema.BaseGuid.upper()
    if set(Fields) != Consumed:
        raise ValueError("Unknown Fusion auxiliary entity fields")
    return tuple(Groups)
