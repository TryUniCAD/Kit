from pathlib import Path as FilePath

from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WriteResult import WriteResult
from convert.adapters.solidworks.Core.AssemblyPreparation.Nested.PrepareNestedAssembly import (
    PrepareNestedAssembly,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Nested.ReadNestedAssembly import (
    ReadNestedAssembly,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.RequireAsm import RequireAsm
from convert.adapters.solidworks.Core.AssemblyWriting.CheckAsmOpts import CheckAsmOpts
from convert.adapters.solidworks.Core.AssemblyWriting.CheckFreshFiles import (
    CheckFreshFiles,
)
from convert.adapters.solidworks.Core.AssemblyWriting.FinalAsmPath import FinalAsmPath
from convert.adapters.solidworks.Core.AssemblyWriting.Nested.NestFileNames import (
    NestFileNames,
)
from convert.adapters.solidworks.Core.AssemblyWriting.WriteAsmFiles import WriteAsmFiles
from interchange.document.Models.DocumentModel import CadDocument


# graph preparation and complete final name checks must finish before emitting any staged bundle member
def EmitNestedMut(
    Document: CadDocument,
    TargetValue: KTargetType,
    OptionsValue: WriteOptions | None,
    WrittenAt: int,
) -> WriteResult:
    SettingsValue = CheckAsmOpts(OptionsValue)
    if not isinstance(TargetValue, (str, FilePath)):
        raise TypeError(
            "nested assembly output requires a staged filesystem destination"
        )
    OutputPath = FilePath(TargetValue).expanduser().resolve()
    FinalPath, NativePath = FinalAsmPath(OutputPath, SettingsValue)
    RequireAsm(
        "final_destination" in SettingsValue.values
        and OutputPath.parent != FinalPath.parent,
        "nested assembly emission requires registry path staging",
    )
    PlanValue = ReadNestedAssembly(Document)
    RequireAsm(
        SettingsValue.configuration
        in (
            None,
            PlanValue.RootValue.configuration_id,
            PlanValue.RootValue.configuration_name,
        ),
        "requested assembly configuration is unavailable",
    )
    FileValues = NestFileNames(PlanValue, NativePath)
    CheckFreshFiles(FinalPath, tuple(PathValue.name for PathValue in FileValues[:-1]))
    Candidates = PrepareNestedAssembly(Document, NativePath, WrittenAt)
    RequireAsm(
        tuple(str(PathValue) for PathValue, _ in Candidates)
        == tuple(map(str, FileValues)),
        "generated nested files differ from the validated output plan",
    )
    return WriteAsmFiles(
        OutputPath,
        Candidates[-1][1].BytesValue,
        tuple(
            (PathValue.name, Value.BytesValue) for PathValue, Value in Candidates[:-1]
        ),
        "unmeasured_portable_nested_assembly_profile",
    )
