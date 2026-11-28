from dataclasses import replace as ReplaceValue

from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WriteResult import WriteResult
from convert.adapters.solidworks.Core.AssemblyPreparation.Nested.PrepNestedPlan import (
    PrepNestedPlan,
)
from convert.adapters.solidworks.Core.AssemblyWriting.CheckAsmOpts import CheckAsmOpts
from convert.adapters.solidworks.Core.AssemblyWriting.Nested.Measured.IsNestSite import (
    IsNestSite,
)
from convert.adapters.solidworks.Core.AssemblyWriting.Nested.Measured.MatchNestMeas import (
    MatchNestMeas,
)
from convert.adapters.solidworks.Core.AssemblyWriting.Nested.Measured.ReadNestMeas import (
    ReadNestMeas,
)
from convert.adapters.solidworks.Core.AssemblyWriting.Nested.PlanNestStage import (
    PlanNestStage,
)
from convert.adapters.solidworks.Core.AssemblyWriting.Nested.PublishNestMut import (
    PublishNestMut,
)
from convert.adapters.solidworks.Core.Writing.Measured.PartMeasureOpt import (
    KPartMeasureOpt,
)
from interchange.document.Models.DocumentModel import CadDocument


# a native nested result must close the authenticated bundle and its actual location before any staged open
def EmitNestedMut(
    Document: CadDocument,
    TargetValue: KTargetType,
    OptionsValue: WriteOptions | None,
) -> WriteResult:
    Settings = CheckAsmOpts(OptionsValue, Measured=True)
    StagePath, FinalPath, NativePath, PlanValue, FileValues = PlanNestStage(
        Document, TargetValue, Settings
    )
    Evidence = ReadNestMeas(Settings)
    Candidates = PrepNestedPlan(
        PlanValue, NativePath, Evidence.WrittenAt, PlatformMath=Evidence.PlatformMath
    )
    MatchNestMeas(Evidence, FileValues, Candidates)
    Locator = str(FileValues[-1])
    SameSite = IsNestSite(StagePath, FinalPath, Locator, Settings)
    Profile = (
        "measured_rigid_nested_assembly"
        if SameSite
        else "measured_nested_deferred_delivery"
    )
    Result = PublishNestMut(StagePath, Candidates, Profile)
    return ReplaceValue(
        Result,
        application_usable=SameSite,
        vendor_loadable=SameSite,
        metadata={
            **Result.metadata,
            KPartMeasureOpt: {
                "generated_manifest_sha256": Evidence.ManifestSha,
                "native_result_sha256": Evidence.ReportSha,
            },
            "required_native_destination": Locator,
            "output_scope": "root_and_owned_nested_dependencies",
            "overwrite_supported": False,
        },
    )
