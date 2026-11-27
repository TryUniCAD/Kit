from convert.adapters.solidworks.Core.AssemblyPreparation.Model.CheckAsmOcc import (
    CheckAsmOcc,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Model.ReadAsmConfig import (
    ReadAsmConfig,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Model.ReadAsmOrder import (
    ReadAsmOrder,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.RequireAsm import RequireAsm
from interchange.assembly.ComponentDefinition import ComponentDef
from interchange.assembly.ComponentInstance import ComponentInst
from interchange.document.Models.DocumentModel import AssemblyData, CadDocument


# direct occurrence order and the single fixed anchor must be settled before any native wrapper allocation
def ReadAsmOccs(
    GraphValue: AssemblyData,
    RootValue: ComponentDef,
    ChildValue: ComponentDef,
    ChildDocument: CadDocument,
) -> tuple[tuple[ComponentInst, ...], int]:
    RequireAsm(
        len(GraphValue.instances) in (2, 3),
        "only two or three direct occurrences are admitted",
    )
    ChildConfig = ReadAsmConfig(ChildDocument)
    Occurrences = tuple(sorted(GraphValue.instances, key=ReadAsmOrder))
    RequireAsm(
        tuple(Value.order for Value in Occurrences) == tuple(range(len(Occurrences))),
        "direct occurrence order must be explicit and unique",
    )
    for Value in Occurrences:
        CheckAsmOcc(Value, RootValue, ChildValue, ChildConfig)
    FixedValues = tuple(Index for Index, Value in enumerate(Occurrences) if Value.fixed)
    RequireAsm(len(FixedValues) == 1, "one exact fixed occurrence is required")
    return Occurrences, FixedValues[0]
