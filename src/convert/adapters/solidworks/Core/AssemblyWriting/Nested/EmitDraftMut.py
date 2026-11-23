from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WriteResult import WriteResult
from convert.adapters.solidworks.Core.AssemblyPreparation.Nested.PrepNestedPlan import (
    PrepNestedPlan,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.RequireAsm import RequireAsm
from convert.adapters.solidworks.Core.AssemblyWriting.CheckAsmOpts import CheckAsmOpts
from convert.adapters.solidworks.Core.AssemblyWriting.Nested.PlanNestStage import (
    PlanNestStage,
)
from convert.adapters.solidworks.Core.AssemblyWriting.Nested.PublishNestMut import (
    PublishNestMut,
)
from interchange.document.Models.DocumentModel import CadDocument


# the isolated research registry needs a complete staged output without native qualification
def EmitDraftMut(
    Document: CadDocument,
    TargetValue: KTargetType,
    OptionsValue: WriteOptions | None,
    WrittenAt: int,
) -> WriteResult:
    Settings = CheckAsmOpts(OptionsValue)
    StagePath, _, NativePath, PlanValue, FileValues = PlanNestStage(
        Document, TargetValue, Settings
    )
    Candidates = PrepNestedPlan(PlanValue, NativePath, WrittenAt)
    RequireAsm(
        tuple(str(PathValue) for PathValue, _ in Candidates)
        == tuple(map(str, FileValues)),
        "generated nested files differ from the validated output plan",
    )
    return PublishNestMut(
        StagePath, Candidates, "unmeasured_portable_nested_assembly_profile"
    )
