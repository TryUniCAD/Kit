from pathlib import Path as FilePath
from time import time as ReadTime

from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WriteResult import WriteResult
from convert.adapters.registry import AdapterRegistry
from convert.adapters.solidworks.Container.Format import KAsmFormatId
from convert.adapters.solidworks.Core.AssemblyWriting.CheckAsmOpts import CheckAsmOpts
from convert.adapters.solidworks.Core.AssemblyWriting.Nested.MakeNestWriter import (
    MakeNestWriter,
)
from interchange.document.Models.DocumentModel import CadDocument


# an explicit internal call owns one isolated registry and its normal checked path transaction
def WriteNestedAsm(
    Document: CadDocument,
    TargetValue: KTargetType,
    OptionsValue: WriteOptions | None = None,
    *,
    WrittenAt: int | None = None,
) -> WriteResult:
    if not isinstance(TargetValue, (str, FilePath)):
        raise TypeError(
            "nested assembly output requires a filesystem bundle destination"
        )
    SettingsValue = CheckAsmOpts(OptionsValue)
    TargetPath = FilePath(TargetValue).expanduser()
    if TargetPath.is_symlink():
        raise FileExistsError(TargetPath)
    RegistryValue = AdapterRegistry()
    RegistryValue.RegisterWriter(
        MakeNestWriter(int(ReadTime()) if WrittenAt is None else WrittenAt)
    )
    return RegistryValue.WriteDocument(
        Document, TargetPath, FormatId=KAsmFormatId, OptionsData=SettingsValue
    )
