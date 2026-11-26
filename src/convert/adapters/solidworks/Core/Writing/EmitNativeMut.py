from pathlib import Path as FilePath

from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.TransferContract import CapTransfer, TransferMode
from convert.adapters.Staging.WriteWholeMut import WriteWholeMut
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WriteResult import WriteResult
from convert.adapters.solidworks.Container.Format import KPartFormatId
from convert.adapters.solidworks.Core.Preparation.CheckPartOpts import CheckPartOpts
from convert.adapters.solidworks.Core.Preparation.PrepareNative import PrepareNative
from convert.adapters.solidworks.Core.Preparation.Readback.IsColdRead import IsColdRead
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
    if OutputPath is not None:
        with OutputPath.open("wb" if SettingsValue.overwrite else "xb") as OutputFile:
            if OutputFile.write(Payload) != len(Payload):
                raise OSError("short native part write")
    else:
        WriteWholeMut(TargetValue, Payload)
    return WriteResult(
        OutputPath,
        KPartFormatId,
        len(Payload),
        metadata=Evidence,
        transfers=(
            tuple(
                CapTransfer(CapabilityValue, TransferMode.KNative)
                for CapabilityValue in sorted(DocumentValue.capabilities)
            )
            if IsColdRead(DocumentValue)
            else ()
        ),
        vendor_loadable=True,
        application_usable=True,
    )
