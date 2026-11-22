from pathlib import Path as FilePath
from time import time as ReadTime

from convert.adapters.base.ContractTypes import IsBinaryTarget, KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WriteResult import WriteResult
from convert.adapters.solidworks.Container.Format import KPartFormatId
from convert.adapters.solidworks.Core.Preparation.CheckPartOpts import CheckPartOpts
from convert.adapters.solidworks.Core.Preparation.PrepareNative import PrepareNative
from interchange.document.Models.DocumentModel import CadDocument


# preparing and writing native bytes establishes a candidate whose usability requires measurement
def EmitNativeMut(
    DocumentValue: CadDocument,
    TargetValue: KTargetType,
    OptionsValue: WriteOptions | None,
) -> WriteResult:
    SettingsValue = CheckPartOpts(OptionsValue)
    OutputPath = (
        FilePath(TargetValue).expanduser().resolve()
        if isinstance(TargetValue, (str, FilePath))
        else None
    )
    Candidate = PrepareNative(
        DocumentValue, OutputPath or TargetValue, int(ReadTime()), SettingsValue
    )
    Payload = Candidate.BytesValue
    CountValue: int | None
    if OutputPath is not None:
        with OutputPath.open("wb" if SettingsValue.overwrite else "xb") as OutputFile:
            CountValue = OutputFile.write(Payload)
    elif IsBinaryTarget(TargetValue):
        CountValue = TargetValue.write(Payload)
    else:
        raise TypeError("native part output requires a path or binary stream")
    if CountValue is not None and CountValue != len(Payload):
        raise OSError("short native part write")
    return WriteResult(OutputPath, KPartFormatId, len(Payload))
