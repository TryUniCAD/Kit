from pathlib import Path as FilePath, PureWindowsPath

from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Core.AssemblyPreparation.Nested.NestedAssemblyPlan import (
    NestedAsmPlan,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Nested.ReadNestedAssembly import (
    ReadNestedAsm,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.RequireAsm import RequireAsm
from convert.adapters.solidworks.Core.AssemblyWriting.CheckFreshFiles import (
    CheckFreshFiles,
)
from convert.adapters.solidworks.Core.AssemblyWriting.FinalAsmPath import FinalAsmPath
from convert.adapters.solidworks.Core.AssemblyWriting.Nested.NestFileNames import (
    NestFileNames,
)
from convert.adapters.Staging.StageFileScope import GetStagedFinal
from interchange.document.Models.DocumentModel import CadDocument


# nested assembly preparation must close the real registry stage and every final companion before generation
def PlanNestStage(
    Document: CadDocument, TargetValue: KTargetType, Settings: WriteOptions
) -> tuple[FilePath, FilePath, str, NestedAsmPlan, tuple[PureWindowsPath, ...]]:
    if not isinstance(TargetValue, (str, FilePath)):
        raise TypeError(
            "nested assembly output requires a staged filesystem destination"
        )
    StagePath = FilePath(TargetValue).expanduser().resolve()
    FinalPath, NativePath = FinalAsmPath(StagePath, Settings)
    RequireAsm(
        StagePath != FinalPath and GetStagedFinal(StagePath) == FinalPath,
        "nested assembly publication requires a registry-owned stage",
    )
    PlanValue = ReadNestedAsm(Document)
    RequireAsm(
        Settings.configuration
        in (
            None,
            PlanValue.RootValue.configuration_id,
            PlanValue.RootValue.configuration_name,
        ),
        "requested assembly configuration is unavailable",
    )
    FileValues = NestFileNames(PlanValue, NativePath)
    CheckFreshFiles(FinalPath, tuple(PathValue.name for PathValue in FileValues[:-1]))
    return StagePath, FinalPath, NativePath, PlanValue, FileValues
