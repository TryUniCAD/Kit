from pathlib import Path as FilePath
from time import time as ReadTime

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
from convert.adapters.solidworks.Core.AssemblyWriting.CheckFreshAsm import (
    CheckFreshAsm,
)
from convert.adapters.solidworks.Core.AssemblyWriting.FinalAsmPath import FinalAsmPath
from convert.adapters.solidworks.Core.AssemblyWriting.QualifyPerpAsm import (
    QualifyPerpAsm,
)
from convert.adapters.solidworks.Core.AssemblyWriting.WriteAsmBundle import (
    WriteAsmBundle,
)
from interchange.document.Models.DocumentModel import CadDocument


# public assembly emission must finish exact admission mapping and conflict checks before writing either member of its owned pair
def EmitAsmMut(
    DocumentValue: CadDocument,
    TargetValue: KTargetType,
    OptionsValue: WriteOptions | None,
) -> WriteResult:
    SettingsValue = CheckAsmOpts(OptionsValue)
    if not isinstance(TargetValue, (str, FilePath)):
        raise TypeError("assembly output requires a filesystem bundle destination")
    OutputPath = FilePath(TargetValue).expanduser().resolve()
    FinalPath, NativePath = FinalAsmPath(OutputPath, SettingsValue)
    ModelValue = ReadAsmModel(DocumentValue)
    RequireAsm(
        SettingsValue.configuration
        in (None, ModelValue.ConfigValue.id, ModelValue.ConfigValue.name),
        "requested assembly configuration is unavailable",
    )
    CheckFreshAsm(FinalPath, ModelValue.ChildValue.name)
    Candidate = PrepareAssembly(DocumentValue, NativePath, int(ReadTime()))
    return QualifyPerpAsm(DocumentValue, WriteAsmBundle(Candidate, OutputPath))
