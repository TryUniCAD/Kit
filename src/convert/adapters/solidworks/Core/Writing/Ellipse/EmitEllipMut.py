from pathlib import Path as FilePath

from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WriteResult import WriteResult
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
    Candidate = PrepareEllipse(
        DocumentValue, OutputPath or TargetValue, WrittenAt, Settings
    )
    Evidence = VerifyEllipMeas(Receipt, Candidate, WrittenAt)
    return PublishMeasMut(
        TargetValue, OutputPath, Settings, Candidate.BytesValue, Evidence
    )
