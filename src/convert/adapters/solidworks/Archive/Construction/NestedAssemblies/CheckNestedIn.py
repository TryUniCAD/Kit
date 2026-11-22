from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyInput import (
    AssemblyInput,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.CheckAsmMeta import (
    CheckAsmMeta,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Occurrences.MakePlacement import (
    MakePlacement,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Xml.ReadOccName import (
    ReadOccName,
)
from convert.adapters.solidworks.Archive.Construction.AssemblyTargets.CheckTarget import (
    CheckTarget,
)
from convert.adapters.solidworks.Archive.Construction.AssemblyTargets.TargetAudit import (
    TargetAudit,
)
from convert.adapters.solidworks.Archive.Construction.NestedAssemblies.TargetPlacement import (
    TargetPlacement,
)


# recursive publication must reject incomplete targets naming collisions and unsupported geometry before mutating a fresh parent model
def CheckNestedIn(
    InputValue: AssemblyInput,
    Placements: tuple[TargetPlacement, ...],
    AuditValue: TargetAudit,
) -> None:
    CheckAsmMeta(InputValue)
    if (
        type(Placements) is not tuple
        or not Placements
        or any(type(ItemValue) is not TargetPlacement for ItemValue in Placements)
    ):
        raise ValueError(
            "a populated generated assembly requires explicit target placements"
        )
    SystemValue = InputValue.SystemValue
    NamesValue = tuple(
        RowValue[1] for RowValue in SystemValue.FolderNames + SystemValue.PlaneNames
    ) + (
        SystemValue.CabinetName,
        SystemValue.OriginName,
        SystemValue.MateGroupName,
        *(ItemValue.OccurrenceValue.NameValue for ItemValue in Placements),
    )
    if len(set(NamesValue)) != len(NamesValue):
        raise ValueError(
            "recursive assembly feature and occurrence names must be distinct"
        )
    for ItemValue in Placements:
        CheckTarget(ItemValue.TargetValue, AuditValue)
        _ = MakePlacement(ItemValue.OccurrenceValue.FrameValue)
        _ = ReadOccName(ItemValue.OccurrenceValue.NameValue)
    AuditValue.CheckParent(InputValue.OutputValue.PathName)
