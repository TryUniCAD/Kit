from convert.Formats.Fusion.BrepCodec.Journal.Planar.LiveTable import LiveTable
from convert.Formats.Fusion.BrepCodec.Journal.Writing.MakeEntityNode import (
    MakeEntityNode,
)


# live typed geometry cannot retain references into removed historical slots
def CheckCutLive(Table: LiveTable) -> None:
    for Reference in Table.LiveSlots:
        Entity = Table.Entities[Reference]
        if Entity is None:
            raise ValueError("Native cut has an absent live entity")
        for TagValue, Target in MakeEntityNode(Entity).Tokens:
            if (
                TagValue == 12
                and type(Target) is int
                and Target >= 0
                and (
                    Target >= len(Table.SlotMap)
                    or Table.SlotMap[Target] not in Table.LiveSlots
                )
            ):
                raise ValueError("Native cut references a removed historical entity")
