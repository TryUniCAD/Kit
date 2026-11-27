from dataclasses import replace as ReplaceValue
from pathlib import Path as FilePath

from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WriteResult import WriteResult
from convert.adapters.solidworks.Core.AssemblyPreparation.Nested.PrepNestedPlan import (
    PrepNestedPlan,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Readback.IsNestedRead import (
    IsNestedRead,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.RequireAsm import RequireAsm
from convert.adapters.solidworks.Core.AssemblyWriting.CheckAsmOpts import CheckAsmOpts
from convert.adapters.solidworks.Core.AssemblyWriting.CheckFreshFiles import (
    CheckFreshFiles,
)
from convert.adapters.solidworks.Core.AssemblyWriting.FinalAsmPath import FinalAsmPath
from convert.adapters.solidworks.Core.AssemblyWriting.Measured.MatchAsmMeas import (
    MatchAsmMeas,
)
from convert.adapters.solidworks.Core.AssemblyWriting.Measured.ReadAsmMeas import (
    ReadAsmMeas,
)
from convert.adapters.solidworks.Core.AssemblyWriting.Nested.NestFileNames import (
    NestFileNames,
)
from convert.adapters.solidworks.Core.AssemblyWriting.Nested.PlanNestedDoc import (
    PlanNestedDoc,
)
from convert.adapters.solidworks.Core.AssemblyWriting.Readback.CheckBundleRead import (
    CheckBundleRead,
)
from convert.adapters.solidworks.Core.AssemblyWriting.Readback.ReadbackTransfers import (
    ReadbackTrans,
)
from convert.adapters.solidworks.Core.AssemblyWriting.WriteAsmFiles import WriteAsmFiles
from interchange.document.Models.DocumentModel import CadDocument


# graph preparation and exact native verification must finish before the first staged member write
def EmitNestedMut(
    Document: CadDocument,
    TargetValue: KTargetType,
    OptionsValue: WriteOptions | None,
) -> WriteResult:
    SettingsValue = CheckAsmOpts(OptionsValue)
    WrittenAt, Receipt = ReadAsmMeas(SettingsValue)
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
    PlanValue = PlanNestedDoc(Document)
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
    Candidates = PrepNestedPlan(PlanValue, NativePath, WrittenAt)
    RequireAsm(
        tuple(str(PathValue) for PathValue, _ in Candidates)
        == tuple(map(str, FileValues)),
        "generated nested files differ from the validated output plan",
    )
    Reopened = IsNestedRead(Document)
    Evidence = MatchAsmMeas(Receipt, PlanValue, Candidates, Reopened=Reopened)
    if Reopened:
        CheckBundleRead(
            Document, tuple((PathValue, Target.BytesValue) for PathValue, Target in Candidates)
        )
    Transfers = ReadbackTrans(Document) if Reopened else ()
    ResultValue = WriteAsmFiles(
        OutputPath,
        Candidates[-1][1].BytesValue,
        tuple(
            (PathValue.name, Value.BytesValue) for PathValue, Value in Candidates[:-1]
        ),
    )
    return ReplaceValue(
        ResultValue,
        metadata={**ResultValue.metadata, **Evidence},
        transfers=Transfers,
        application_usable=True,
        vendor_loadable=True,
    )
