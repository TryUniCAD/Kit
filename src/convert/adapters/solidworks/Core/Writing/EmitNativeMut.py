from pathlib import Path as FilePath

from convert.adapters.base.ContractTypes import IsBinaryTarget, KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WriteResult import WriteResult
from convert.adapters.solidworks.Container.Format import KPartFormatId
from convert.adapters.solidworks.Core.Preparation.CheckPartOpts import CheckPartOpts
from convert.adapters.solidworks.Core.Preparation.PrepareNative import PrepareNative
from convert.adapters.solidworks.Core.Writing.Measured.MatchPartMeas import (
    MatchPartMeas,
)
from convert.adapters.solidworks.Core.Writing.Measured.ReadPartMeas import ReadPartMeas
from interchange.document.Models.DocumentModel import CadDocument


# publication verifies the complete regenerated archive before touching either kind of output target
def EmitNativeMut(
    DocumentValue: CadDocument,
    TargetValue: KTargetType,
    OptionsValue: WriteOptions | None,
) -> WriteResult:
    SettingsValue = CheckPartOpts(OptionsValue)
    WrittenAt, Receipt = ReadPartMeas(SettingsValue)
    OutputPath = (
        FilePath(TargetValue).expanduser().resolve()
        if isinstance(TargetValue, (str, FilePath))
        else None
    )
    Candidate = PrepareNative(
        DocumentValue, OutputPath or TargetValue, WrittenAt, SettingsValue
    )
    Payload = Candidate.BytesValue
    Evidence = MatchPartMeas(Receipt, Payload)
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
    return WriteResult(
        OutputPath,
        KPartFormatId,
        len(Payload),
        metadata=Evidence,
        vendor_loadable=True,
        application_usable=True,
    )
