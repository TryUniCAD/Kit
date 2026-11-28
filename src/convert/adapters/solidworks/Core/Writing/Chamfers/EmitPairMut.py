from pathlib import Path as FilePath

from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WriteResult import WriteResult
from convert.adapters.solidworks.Core.Preparation.Chamfers.PrepChmfPart import (
    PrepChmfPart,
)
from convert.adapters.solidworks.Core.Writing.Chamfers.MatchHeldPair import (
    MatchHeldPair,
)
from convert.adapters.solidworks.Core.Writing.Chamfers.ReadHeldPair import (
    ReadHeldPair,
)
from convert.adapters.solidworks.Core.Writing.Chamfers.VerifyPairMeas import (
    VerifyPairMeas,
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


# distance modes must pass their exact native receipt before file or stream publication
def EmitPairMut(
    DocumentValue: CadDocument,
    TargetValue: KTargetType,
    OptionsValue: WriteOptions | None,
) -> WriteResult:
    WrittenAt, Receipt, Settings = ReadMeasInput(OptionsValue)
    HeldProof = ReadHeldPair(Receipt)
    OutputPath = (
        FilePath(TargetValue).expanduser().resolve()
        if isinstance(TargetValue, (str, FilePath))
        else None
    )
    if OutputPath is not None:
        CheckMeasPath(OutputPath, Settings)
    Candidate = PrepChmfPart(
        DocumentValue,
        OutputPath or TargetValue,
        WrittenAt,
        Settings,
        AllowDistancePair=True,
        PlatformMath=HeldProof is not None,
    )
    Evidence = (
        MatchHeldPair(HeldProof, Candidate)
        if HeldProof is not None
        else VerifyPairMeas(Receipt, Candidate, WrittenAt)
    )
    return PublishMeasMut(
        TargetValue, OutputPath, Settings, Candidate.BytesValue, Evidence
    )
