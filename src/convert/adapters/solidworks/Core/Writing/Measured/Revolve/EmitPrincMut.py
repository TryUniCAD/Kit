from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.GetDocumentCaps import GetDocumentCaps
from convert.adapters.base.TransferContract import CapTransfer, TransferMode
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WriteResult import WriteResult
from convert.adapters.solidworks.Core.Preparation.CheckPartOpts import CheckPartOpts
from convert.adapters.solidworks.Core.Preparation.CheckPlainScope import CheckPlainScope
from convert.adapters.solidworks.Core.Preparation.Readback.CheckColdRead import (
    CheckColdRead,
)
from convert.adapters.solidworks.Core.Preparation.Revolve.PlanPublicRevolve import (
    PlanRevolve,
)
from convert.adapters.solidworks.Core.Preparation.Revolve.PrepareRevolve import (
    PrepareRevolve,
)
from convert.adapters.solidworks.Core.Preparation.Revolve.Readback.IsRevRead import (
    IsRevRead,
)
from convert.adapters.solidworks.Core.Writing.Measured.PublishMeasMut import (
    PublishMeasMut,
)
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasInput import ReadMeasInput
from convert.adapters.solidworks.Core.Writing.Measured.Revolve.MatchRevMeas import (
    MatchRevMeas,
)
from convert.adapters.solidworks.Core.Writing.Measured.Revolve.ReadRevReports import (
    ReadRevReports,
)
from convert.adapters.solidworks.Core.Writing.Measured.Revolve.ReadRevTarget import (
    ReadRevTarget,
)
from convert.adapters.solidworks.Core.Writing.Measured.Revolve.RevCaseFor import (
    RevCaseFor,
)
from convert.adapters.solidworks.Core.Writing.Measured.Revolve.RevEvidence import (
    RevEvidence,
)
from convert.adapters.solidworks.Core.Writing.Measured.Revolve.RevWriteInput import (
    RevWriteInput,
)
from interchange.document.Models.DocumentModel import CadDocument


# the physical destination and native receipt qualify only an exact regenerated principal revolve
def EmitPrincMut(
    DocumentValue: CadDocument, TargetValue: KTargetType, OptionsValue: WriteOptions | None
) -> WriteResult:
    WrittenAt, Receipt, Settings = ReadMeasInput(CheckPartOpts(OptionsValue))
    EvidenceValue = RevEvidence(WrittenAt, *ReadRevReports(Receipt))
    IsReadback = IsRevRead(DocumentValue)
    InputValue = RevWriteInput(DocumentValue, TargetValue, Settings) if IsReadback else DocumentValue
    CheckPlainScope(InputValue)
    PlanValue = PlanRevolve(InputValue)
    if PlanValue is None:
        raise ValueError("measured revolve requires exactly one ordinary feature")
    Locator, Digest = RevCaseFor(EvidenceValue, PlanValue.NameValue)
    OutputPath, Settings = ReadRevTarget(TargetValue, Settings, Locator)
    Payload = PrepareRevolve(InputValue, OutputPath or TargetValue, EvidenceValue.WrittenAt, Settings).BytesValue
    Measurement = MatchRevMeas(EvidenceValue, Payload, Digest)
    if IsReadback:
        CheckColdRead(DocumentValue, Payload, IncludeBrep=DocumentValue.brep is not None)
    Transfers = tuple(CapTransfer(Value, TransferMode.KNative) for Value in sorted(GetDocumentCaps(DocumentValue)))
    return PublishMeasMut(TargetValue, OutputPath, Settings, Payload, Measurement, Transfers)
