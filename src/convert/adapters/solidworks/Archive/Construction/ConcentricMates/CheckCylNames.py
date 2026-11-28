from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyInput import (
    AssemblyInput,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.OccurrenceIn import (
    OccurrenceIn,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Xml.ReadOccName import (
    ReadOccName,
)
from convert.adapters.solidworks.Archive.Construction.ConcentricMates.CylMateIn import (
    CylMateIn,
)
from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleText import (
    ReadStyleText,
)


# actual name and numeric occurrence identities must survive through binary and xml assembly owners
def CheckCylNames(
    InputValue: AssemblyInput,
    Occurrences: tuple[OccurrenceIn, OccurrenceIn],
    IntentValue: CylMateIn,
) -> None:
    SystemValue = InputValue.SystemValue
    if not ReadStyleText(IntentValue.NameValue, "concentric mate name"):
        raise ValueError("concentric mate name must not be empty")
    NamesValue = (
        *(RowValue[1] for RowValue in SystemValue.FolderNames + SystemValue.PlaneNames),
        SystemValue.CabinetName,
        SystemValue.OriginName,
        SystemValue.MateGroupName,
        *(Value.NameValue for Value in Occurrences),
        IntentValue.NameValue,
    )
    Numbers = tuple(ReadOccName(Value.NameValue)[1] for Value in Occurrences)
    if len(set(NamesValue)) != len(NamesValue) or len(set(Numbers)) != len(Occurrences):
        raise ValueError("concentric names and occurrence numbers must be distinct")
