from convert.adapters.solidworks.Archive.Construction.PlanarMates.MateContext import (
    MateContext,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.PlanarMateIn import (
    PlanarMateIn,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# the first perpendicular graph must retain one actual repeated child and exclude unqualified continuation or additional occurrences
def CheckPerpScope(
    Context: MateContext,
    InputValue: PlanarMateIn,
    Occurrences: tuple[ArchiveNode, ...],
) -> None:
    if InputValue.KindValue != "perpendicular":
        return
    First, Second = (Value.ChildValue for Value in InputValue.Selections)
    if (
        len(Occurrences) != 2
        or Context.PreviousValues
        or First.ModelValue is not Second.ModelValue
        or First.HeaderValue is not Second.HeaderValue
        or First.ConfigValue is not Second.ConfigValue
    ):
        raise ValueError(
            "perpendicular scope requires one mate and two occurrences of one actual child"
        )
