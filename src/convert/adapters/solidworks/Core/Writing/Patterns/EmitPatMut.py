from pathlib import Path as FilePath

from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.GetDocumentCaps import GetDocumentCaps
from convert.adapters.base.TransferContract import CapTransfer, TransferMode
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WriteResult import WriteResult
from convert.adapters.solidworks.Core.Preparation.Patterns.PrepPatPart import (
    PrepPatPart,
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
from convert.adapters.solidworks.Core.Writing.Patterns.MatchPatMeas import MatchPatMeas
from convert.adapters.solidworks.Core.Writing.Patterns.ReadPatMeas import ReadPatMeas
from convert.adapters.solidworks.Core.Writing.Patterns.ReadPatOptions import (
    ReadPatOptions,
)
from convert.Security.PathBoundary import ResolveWithin
from interchange.document.Models.DocumentModel import CadDocument


# publication requires the exact generated archive and its clean native lifecycle before touching the user sink
def EmitPatMut(
    DocumentValue: CadDocument,
    TargetValue: KTargetType,
    OptionsValue: WriteOptions | None,
) -> WriteResult:
    OtherOptions, Presentation = ReadPatOptions(OptionsValue)
    WrittenAt, Receipt, Settings = ReadMeasInput(OtherOptions)
    FilesValue, ResultValue, ResultSha = ReadPatMeas(Receipt)
    OutputPath = None
    if isinstance(TargetValue, (str, FilePath)):
        Requested = FilePath(TargetValue).expanduser().absolute()
        OutputPath = ResolveWithin(Requested.name, Requested.parent)
        CheckMeasPath(OutputPath, Settings)
    Candidate = PrepPatPart(
        DocumentValue,
        OutputPath or TargetValue,
        WrittenAt,
        Settings,
        PresentValue=Presentation,
    )
    Payload = Candidate.BytesValue
    Evidence = MatchPatMeas(FilesValue, ResultValue, ResultSha, Payload)
    Transfers = tuple(
        CapTransfer(Value, TransferMode.KNative)
        for Value in sorted(GetDocumentCaps(DocumentValue))
    )
    return PublishMeasMut(
        TargetValue, OutputPath, Settings, Payload, Evidence, Transfers
    )
