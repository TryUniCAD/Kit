from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyInput import (
    AssemblyInput,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.OccurrenceIn import (
    OccurrenceIn,
)
from convert.adapters.solidworks.Archive.Construction.AssemblyGroups.GroupMateIn import (
    GroupMateIn,
)


# all native system roles occurrences and ordered mate names occupy one parent namespace and must remain distinct across the complete group
def CheckGroupNames(
    InputValue: AssemblyInput,
    Occurrences: tuple[OccurrenceIn, ...],
    MateValues: tuple[GroupMateIn, ...],
) -> None:
    SystemValue = InputValue.SystemValue
    NamesValue = tuple(
        RowValue[1] for RowValue in SystemValue.FolderNames + SystemValue.PlaneNames
    ) + (
        SystemValue.CabinetName,
        SystemValue.OriginName,
        SystemValue.MateGroupName,
        *(Value.NameValue for Value in Occurrences),
        *(Value.NameValue for Value in MateValues),
    )
    if len(set(NamesValue)) != len(NamesValue):
        raise ValueError("complete planar group names must remain distinct")
