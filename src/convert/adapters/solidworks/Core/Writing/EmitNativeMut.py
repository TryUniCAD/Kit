from pathlib import Path as FilePath

from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.TransferContract import CapTransfer, TransferMode
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WriteResult import WriteResult
from convert.adapters.solidworks.Core.Preparation.CheckPartOpts import CheckPartOpts
from convert.adapters.solidworks.Core.Preparation.PrepareNative import PrepareNative
from convert.adapters.solidworks.Core.Preparation.Readback.IsColdRead import IsColdRead
from convert.adapters.solidworks.Core.Writing.Measured.MatchPartMeas import (
    MatchPartMeas,
)
from convert.adapters.solidworks.Core.Writing.Measured.ReadPartMeas import ReadPartMeas
from convert.adapters.solidworks.Core.Writing.Measured.PublishMeasMut import (
    PublishMeasMut,
)
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
    return PublishMeasMut(
        TargetValue,
        OutputPath,
        SettingsValue,
        Payload,
        Evidence,
        (
            tuple(
                CapTransfer(CapabilityValue, TransferMode.KNative)
                for CapabilityValue in sorted(DocumentValue.capabilities)
            )
            if IsColdRead(DocumentValue)
            else ()
        ),
    )
