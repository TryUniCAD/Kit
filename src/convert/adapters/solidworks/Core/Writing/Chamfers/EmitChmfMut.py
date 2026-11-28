from pathlib import Path as FilePath

from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.GetDocumentCaps import GetDocumentCaps
from convert.adapters.base.TransferContract import CapTransfer, TransferMode
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WriteResult import WriteResult
from convert.adapters.solidworks.Core.Preparation.Chamfers.IsDistChmf import IsDistChmf
from convert.adapters.solidworks.Core.Preparation.Chamfers.PrepChmfPart import (
    PrepChmfPart,
)
from convert.adapters.solidworks.Core.Writing.Chamfers.EmitPairMut import EmitPairMut
from convert.adapters.solidworks.Core.Writing.Chamfers.VerifyAngleMeas import (
    VerifyAngleMeas,
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
from interchange.document.Models.DocumentModel import CadDocument


# both measured chamfer modes use their own native authority before output
def EmitChmfMut(
    DocumentValue: CadDocument,
    TargetValue: KTargetType,
    OptionsValue: WriteOptions | None,
) -> WriteResult:
    if IsDistChmf(DocumentValue):
        return EmitPairMut(DocumentValue, TargetValue, OptionsValue)
    WrittenAt, Receipt, Settings = ReadMeasInput(OptionsValue)
    OutputPath = (
        FilePath(TargetValue).expanduser().resolve()
        if isinstance(TargetValue, (str, FilePath))
        else None
    )
    if OutputPath is not None:
        CheckMeasPath(OutputPath, Settings)
    Candidate = PrepChmfPart(
        DocumentValue, OutputPath or TargetValue, WrittenAt, Settings
    )
    Evidence = VerifyAngleMeas(Receipt, Candidate, WrittenAt)
    Transfers = tuple(
        CapTransfer(Value, TransferMode.KNative)
        for Value in sorted(GetDocumentCaps(DocumentValue))
    )
    return PublishMeasMut(
        TargetValue, OutputPath, Settings, Candidate.BytesValue, Evidence, Transfers
    )
