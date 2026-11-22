from pathlib import Path as FilePath

from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.GetDocumentCaps import GetDocumentCaps
from convert.adapters.base.TransferContract import CapTransfer, TransferMode
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WriteResult import WriteResult
from convert.adapters.solidworks.Core.Preparation.Ellipse.IsEllipRead import IsEllipRead
from convert.adapters.solidworks.Core.Preparation.Ellipse.PrepEllipRead import (
    PrepEllipRead,
)
from convert.adapters.solidworks.Core.Preparation.Ellipse.PrepareEllipse import (
    PrepareEllipse,
)
from convert.adapters.solidworks.Core.Writing.Measured.CheckMeasPath import (
    CheckMeasPath,
)
from convert.adapters.solidworks.Core.Writing.Ellipse.VerifyEllipMeas import (
    VerifyEllipMeas,
)
from convert.adapters.solidworks.Core.Writing.Measured.PublishMeasMut import (
    PublishMeasMut,
)
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasInput import (
    ReadMeasInput,
)
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
        CheckMeasPath(OutputPath, Settings)
    ReadbackValue = IsEllipRead(DocumentValue)
    Draft = PrepEllipRead if ReadbackValue else PrepareEllipse
    Candidate = Draft(DocumentValue, OutputPath or TargetValue, WrittenAt, Settings)
    Evidence = VerifyEllipMeas(Receipt, Candidate, WrittenAt, RequireAuth=ReadbackValue)
    Transfers: tuple[CapTransfer, ...] = (
        tuple(
            CapTransfer(Value, TransferMode.KNative)
            for Value in sorted(GetDocumentCaps(DocumentValue))
        )
        if ReadbackValue
        else ()
    )
    return PublishMeasMut(
        TargetValue, OutputPath, Settings, Candidate.BytesValue, Evidence, Transfers
    )
