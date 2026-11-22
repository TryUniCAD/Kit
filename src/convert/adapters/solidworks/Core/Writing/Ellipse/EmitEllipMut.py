from pathlib import Path as FilePath

from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.TransferContract import CapTransfer, TransferMode
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WriteResult import WriteResult
from convert.adapters.solidworks.Container.Format import KPartFormatId
from convert.adapters.solidworks.Core.Preparation.Ellipse.IsColdEllip import IsColdEllip
from convert.adapters.solidworks.Core.Preparation.Ellipse.PrepareEllipse import (
    PrepareEllipse,
)
from convert.adapters.solidworks.Core.Writing.Ellipse.CheckEllipPath import (
    CheckEllipPath,
)
from convert.adapters.solidworks.Core.Writing.Ellipse.VerifyEllipMeas import (
    VerifyEllipMeas,
)
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasInput import (
    ReadMeasInput,
)
from convert.adapters.Staging.WriteWholeMut import WriteWholeMut
from interchange.document.Models.DocumentModel import CadDocument


# the scoped ellipse route verifies its full candidate before creating an output or writing to a stream
def EmitEllipMut(
    DocumentValue: CadDocument,
    TargetValue: KTargetType,
    OptionsValue: WriteOptions | None,
) -> WriteResult:
    WrittenAt, Receipt, Settings = ReadMeasInput(OptionsValue)
    OutputPath = (
        FilePath(TargetValue).expanduser().resolve()
        if isinstance(TargetValue, (str, FilePath))
        else None
    )
    if OutputPath is not None:
        CheckEllipPath(OutputPath, Settings)
    Candidate = PrepareEllipse(
        DocumentValue, OutputPath or TargetValue, WrittenAt, Settings
    )
    Evidence = VerifyEllipMeas(Receipt, Candidate, WrittenAt)
    Payload = Candidate.BytesValue
    if OutputPath is None:
        WriteWholeMut(TargetValue, Payload)
    else:
        with OutputPath.open("wb" if Settings.overwrite else "xb") as OutputFile:
            if OutputFile.write(Payload) != len(Payload):
                raise OSError("short measured ellipse write")
    return WriteResult(
        OutputPath,
        KPartFormatId,
        len(Payload),
        metadata=Evidence,
        transfers=(
            tuple(
                CapTransfer(Value, TransferMode.KNative)
                for Value in sorted(DocumentValue.capabilities)
            )
            if IsColdEllip(DocumentValue)
            else ()
        ),
        vendor_loadable=True,
        application_usable=True,
    )
