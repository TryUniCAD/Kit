from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.GetDocumentCaps import GetDocumentCaps
from convert.adapters.base.TransferContract import CapTransfer, TransferMode
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WriteResult import WriteResult
from convert.adapters.solidworks.Core.Preparation.Circle.PrepareCircle import (
    PrepareCircle,
)
from convert.adapters.solidworks.Core.Writing.Circle.CircOutput import CircOutput
from convert.adapters.solidworks.Core.Writing.Circle.MatchCircAuth import MatchCircAuth
from convert.adapters.solidworks.Core.Writing.Circle.ReadCircAuth import ReadCircAuth
from convert.adapters.solidworks.Core.Writing.Measured.PublishMeasMut import (
    PublishMeasMut,
)
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasInput import (
    ReadMeasInput,
)
from interchange.document.Models.DocumentModel import CadDocument


# regeneration from the owned circle plan precedes all native publication attestation
def EmitCircMut(
    DocumentValue: CadDocument,
    TargetValue: KTargetType,
    OptionsValue: WriteOptions | None,
) -> WriteResult:
    WrittenAt, Receipt, Settings = ReadMeasInput(OptionsValue)
    Schema, ReportSha, Report = ReadCircAuth(Receipt)
    OutputPath, BuildOptions = CircOutput(TargetValue, Settings)
    Candidate = PrepareCircle(
        DocumentValue,
        OutputPath or TargetValue,
        WrittenAt,
        BuildOptions,
        Measured=True,
    )
    Payload = Candidate.BytesValue
    Evidence = MatchCircAuth(
        Schema, ReportSha, Report, Candidate.PlanValue.NameValue, Payload
    )
    Transfers = tuple(
        CapTransfer(Value, TransferMode.KNative)
        for Value in sorted(GetDocumentCaps(DocumentValue))
    )
    return PublishMeasMut(
        TargetValue, OutputPath, BuildOptions, Payload, Evidence, Transfers
    )
