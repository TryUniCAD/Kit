from convert.adapters.solidworks.Core.AssemblyPreparation.Nested.NestedAssemblyPlan import (
    NestedAsmPlan,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Nested.ReadNestedAssembly import (
    ReadNestedAsm,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Readback.ColdNestedPlan import (
    ColdNestedPlan,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Readback.IsNestedRead import (
    IsNestedRead,
)
from interchange.document.Models.DocumentModel import CadDocument


# only the exact native reader origin may invoke the verified reopened projection
def PlanNestedDoc(Document: CadDocument) -> NestedAsmPlan:
    return (
        ColdNestedPlan(Document) if IsNestedRead(Document) else ReadNestedAsm(Document)
    )
