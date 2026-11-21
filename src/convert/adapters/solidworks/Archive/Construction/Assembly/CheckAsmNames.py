from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyInput import (
    AssemblyInput,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyMateIn import (
    AssemblyMateIn,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.OccurrenceIn import (
    OccurrenceIn,
)


# native system occurrence and mate feature names share one parent namespace and cannot silently alias otherwise distinct generated objects
def CheckAsmNames(
    InputValue: AssemblyInput,
    Occurrences: tuple[OccurrenceIn, OccurrenceIn],
    MateValue: AssemblyMateIn,
) -> None:
    SystemValue = InputValue.SystemValue
    NamesValue = tuple(
        RowValue[1] for RowValue in SystemValue.FolderNames + SystemValue.PlaneNames
    ) + (
        SystemValue.CabinetName,
        SystemValue.OriginName,
        SystemValue.MateGroupName,
        MateValue.NameValue,
        *(NodeValue.NameValue for NodeValue in Occurrences),
    )
    if len(set(NamesValue)) != len(NamesValue):
        raise ValueError("assembly features require distinct authored names")
