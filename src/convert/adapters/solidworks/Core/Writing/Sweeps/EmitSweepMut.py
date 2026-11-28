from pathlib import Path as FilePath

from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.GetDocumentCaps import GetDocumentCaps
from convert.adapters.base.TransferContract import CapTransfer, TransferMode
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WriteResult import WriteResult
from convert.adapters.solidworks.Core.Preparation.Sweeps.PrepSweepPart import (
    PrepSweepPart,
)
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.Cold.ColdSwSource import (
    IsColdSwSource,
)
from convert.adapters.solidworks.Core.Writing.Measured.CheckMeasPath import (
    CheckMeasPath,
)
from convert.adapters.solidworks.Core.Writing.Measured.PublishMeasMut import (
    PublishMeasMut,
)
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasInput import (
    ReadMeasInput,
)
from convert.adapters.solidworks.Core.Writing.Sweeps.CheckSwRead import CheckSwRead
from convert.adapters.solidworks.Core.Writing.Sweeps.VerifySweepMeas import (
    VerifySweepMeas,
)
from interchange.document.Models.DocumentModel import CadDocument


# both normal sweep destinations must wait for exact offline measurement of the regenerated part
def EmitSweepMut(
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
        CheckMeasPath(OutputPath, Settings)
    Candidate = PrepSweepPart(
        DocumentValue, OutputPath or TargetValue, WrittenAt, Settings
    )
    Evidence = VerifySweepMeas(Receipt, Candidate, WrittenAt)
    Transfers: tuple[CapTransfer, ...] = ()
    if IsColdSwSource(DocumentValue.source):
        CheckSwRead(DocumentValue, Candidate.BytesValue)
        Transfers = tuple(
            CapTransfer(Value, TransferMode.KNative)
            for Value in sorted(GetDocumentCaps(DocumentValue))
        )
    return PublishMeasMut(
        TargetValue, OutputPath, Settings, Candidate.BytesValue, Evidence, Transfers
    )
