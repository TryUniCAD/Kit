from dataclasses import replace as ReplaceValue
from pathlib import Path as FilePath

from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WriteResult import WriteResult
from convert.adapters.solidworks.Core.AssemblyPreparation.Model.ReadAsmModel import (
    ReadAsmModel,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.PrepareAssembly import (
    PrepareAssembly,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.RequireAsm import RequireAsm
from convert.adapters.solidworks.Core.AssemblyWriting.CheckAsmOpts import CheckAsmOpts
from convert.adapters.solidworks.Core.AssemblyWriting.CheckFreshAsm import CheckFreshAsm
from convert.adapters.solidworks.Core.AssemblyWriting.FinalAsmPath import FinalAsmPath
from convert.adapters.solidworks.Core.AssemblyWriting.Measured.CheckPairScope import (
    CheckPairScope,
)
from convert.adapters.solidworks.Core.AssemblyWriting.Measured.IsPlanarSite import (
    IsPlanarSite,
)
from convert.adapters.solidworks.Core.AssemblyWriting.Measured.MatchPlanarMeas import (
    MatchPlanarMeas,
)
from convert.adapters.solidworks.Core.AssemblyWriting.Measured.ReadHeldPerp import (
    KHeldPerpSchema,
)
from convert.adapters.solidworks.Core.AssemblyWriting.Measured.ReadPlanarMeas import (
    ReadPlanarMeas,
)
from convert.adapters.solidworks.Core.AssemblyWriting.WriteAsmFiles import WriteAsmFiles
from convert.adapters.Staging.StageFileScope import GetStagedFinal
from interchange.document.Models.DocumentModel import CadDocument


# staged planar output derives both files from the neutral model and checks their exact native evidence before writing
def EmitAsmMut(
    DocumentValue: CadDocument,
    TargetValue: KTargetType,
    OptionsValue: WriteOptions | None,
) -> WriteResult:
    Settings = CheckAsmOpts(OptionsValue, PlanarMeasure=True)
    if not isinstance(TargetValue, (str, FilePath)):
        raise TypeError("assembly output requires a filesystem bundle destination")
    StagePath = FilePath(TargetValue).expanduser().resolve()
    FinalPath, NativePath = FinalAsmPath(StagePath, Settings)
    PerpValue = CheckPairScope(DocumentValue) == "perpendicular"
    RequireAsm(
        StagePath != FinalPath and GetStagedFinal(StagePath) == FinalPath,
        "planar assembly publication requires a registry-owned stage",
    )
    ModelValue = ReadAsmModel(DocumentValue)
    RequireAsm(
        Settings.configuration
        in (None, ModelValue.ConfigValue.id, ModelValue.ConfigValue.name),
        "requested assembly configuration is unavailable",
    )
    CheckFreshAsm(FinalPath, ModelValue.ChildValue.name)
    EpochValue, Receipt = ReadPlanarMeas(Settings, Perpendicular=PerpValue)
    Candidate = PrepareAssembly(
        DocumentValue,
        NativePath,
        EpochValue,
        PublicProfile=True,
        SequentialProjection=PerpValue and Receipt.get("schema") != KHeldPerpSchema,
    )
    Companion = (
        Candidate.ChildValue.PlanValue.NameValue + ".SLDPRT",
        Candidate.ChildValue.BytesValue,
    )
    Members = (Companion, (FinalPath.name, Candidate.BytesValue))
    Evidence = MatchPlanarMeas(Receipt, NativePath, Members)
    SameSite = IsPlanarSite(StagePath, FinalPath, NativePath, Settings)
    Profile = (
        "measured_planar_assembly" if SameSite else "measured_planar_deferred_delivery"
    )
    Result = WriteAsmFiles(StagePath, Candidate.BytesValue, (Companion,), Profile)
    return ReplaceValue(
        Result,
        application_usable=SameSite,
        vendor_loadable=SameSite,
        metadata={
            **Result.metadata,
            **Evidence,
            "output_scope": "one_assembly_and_one_owned_part",
            "overwrite_supported": False,
        },
    )
