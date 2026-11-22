from dataclasses import replace as ReplaceValue

from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.GetDocumentCaps import GetDocumentCaps
from convert.adapters.base.TransferContract import CapTransfer, TransferMode
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WriteResult import WriteResult
from convert.adapters.solidworks.Core.Preparation.CheckPartOpts import CheckPartOpts
from convert.adapters.solidworks.Core.Preparation.Revolve.PlanThinPart import (
    PlanThinWrite,
)
from convert.adapters.solidworks.Core.Preparation.Revolve.PrepareRevolve import (
    PrepareRevolve,
)
from convert.adapters.solidworks.Core.Writing.Measured.PublishMeasMut import (
    PublishMeasMut,
)
from convert.adapters.solidworks.Core.Writing.Measured.Thin.CheckThinPath import (
    CheckThinPath,
)
from convert.adapters.solidworks.Core.Writing.Measured.Thin.MatchThinMeas import (
    MatchThinMeas,
)
from convert.adapters.solidworks.Core.Writing.Measured.Thin.ReadThinReports import (
    ReadThinReports,
)
from convert.adapters.solidworks.Core.Writing.Measured.Thin.ThinCaseFor import (
    ThinCaseFor,
)
from interchange.Core.Common import FreezeMapping
from interchange.document.Models.DocumentModel import CadDocument


# public output requires the authored thin model and its exact independently inspected complete archive
def EmitThinMut(
    DocumentValue: CadDocument,
    TargetValue: KTargetType,
    OptionsValue: WriteOptions | None,
) -> WriteResult:
    PlanValue = PlanThinWrite(DocumentValue)
    Settings = CheckPartOpts(OptionsValue)
    WrittenAt, ReportId, Report, JobValue = ReadThinReports(Settings)
    Locator, Digest, CaseValue = ThinCaseFor(Report, JobValue, PlanValue.NameValue)
    OutputPath = CheckThinPath(TargetValue, Settings, Locator)
    BuildOptions = ReplaceValue(
        Settings,
        values=FreezeMapping({**Settings.values, "final_destination": Locator}),
    )
    Payload = PrepareRevolve(
        DocumentValue, OutputPath or TargetValue, WrittenAt, BuildOptions
    ).BytesValue
    Evidence = MatchThinMeas(Payload, Digest, ReportId, CaseValue)
    Transfers = tuple(
        CapTransfer(Value, TransferMode.KNative)
        for Value in sorted(GetDocumentCaps(DocumentValue))
    )
    return PublishMeasMut(
        TargetValue, OutputPath, Settings, Payload, Evidence, Transfers
    )
