from convert.adapters.solidworks.Archive.Construction.Assembly.OccurrenceIn import (
    OccurrenceIn,
)
from convert.adapters.solidworks.Archive.Construction.AssemblyGroups.GroupMateIn import (
    GroupMateIn,
)


# unmeasured mixed or expanded perpendicular groups must fail before an assembly graph or partial bundle can be produced
def CheckPerpGroup(
    Occurrences: tuple[OccurrenceIn, ...], MateValues: tuple[GroupMateIn, ...]
) -> None:
    if any(Value.KindValue == "perpendicular" for Value in MateValues) and (
        len(Occurrences) != 2 or len(MateValues) != 1
    ):
        raise ValueError(
            "perpendicular groups require exactly two occurrences and one mate"
        )
