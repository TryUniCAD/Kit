from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyInput import (
    AssemblyInput,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.CheckAsmMeta import (
    CheckAsmMeta,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.OccurrenceIn import (
    OccurrenceIn,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Occurrences.MakePlacement import (
    MakePlacement,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Xml.ReadOccName import (
    ReadOccName,
)
from convert.adapters.solidworks.Archive.Construction.AssemblyGroups.CheckGroupChild import (
    CheckGroupChild,
)
from convert.adapters.solidworks.Archive.Construction.AssemblyGroups.CheckGroupGeom import (
    CheckGroupGeom,
)
from convert.adapters.solidworks.Archive.Construction.AssemblyGroups.CheckGroupNames import (
    CheckGroupNames,
)
from convert.adapters.solidworks.Archive.Construction.AssemblyGroups.GroupMateIn import (
    GroupMateIn,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)


# complete group admission must validate every actual component endpoint and relationship before allocating any model object or emitting partial output
def CheckGroupIn(
    ChildValue: PartCandidate,
    InputValue: AssemblyInput,
    Occurrences: tuple[OccurrenceIn, ...],
    MateValues: tuple[GroupMateIn, ...],
    FixedIndex: int,
) -> None:
    CheckAsmMeta(InputValue)
    CheckGroupChild(ChildValue, InputValue)
    if (
        type(Occurrences) is not tuple
        or len(Occurrences) < 2
        or any(type(Value) is not OccurrenceIn for Value in Occurrences)
    ):
        raise ValueError(
            "planar groups require at least two actual named rigid occurrences"
        )
    if (
        type(MateValues) is not tuple
        or not MateValues
        or any(type(Value) is not GroupMateIn for Value in MateValues)
    ):
        raise ValueError(
            "planar groups require a complete explicit ordered mate sequence"
        )
    if type(FixedIndex) is not int or not 0 <= FixedIndex < len(Occurrences):
        raise ValueError("planar groups require one actual fixed occurrence index")
    CheckGroupNames(InputValue, Occurrences, MateValues)
    for Value in Occurrences:
        _ = MakePlacement(Value.FrameValue)
        _ = ReadOccName(Value.NameValue)
    for MateValue in MateValues:
        if any(
            Value.OccurrenceIndex >= len(Occurrences) for Value in MateValue.EndValues
        ):
            raise ValueError("a planar mate endpoint selects an absent occurrence")
        CheckGroupGeom(Occurrences, MateValue)
