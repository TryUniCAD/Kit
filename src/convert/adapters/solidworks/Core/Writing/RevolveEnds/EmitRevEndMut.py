from dataclasses import replace as ReplaceValue

from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.GetDocumentCaps import GetDocumentCaps
from convert.adapters.base.TransferContract import CapTransfer, TransferMode
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WriteResult import WriteResult
from convert.adapters.solidworks.Core.Preparation.CheckPartOpts import CheckPartOpts
from convert.adapters.solidworks.Core.Preparation.Revolve.PrepareRevolve import (
    PrepareRevolve,
)
from convert.adapters.solidworks.Core.Writing.Measured.PublishMeasMut import (
    PublishMeasMut,
)
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasInput import (
    ReadMeasInput,
)
from convert.adapters.solidworks.Core.Writing.RevolveEnds.MatchRevEndMeas import (
    MatchRevEndMeas,
)
from convert.adapters.solidworks.Core.Writing.RevolveEnds.PlanRevEnd import PlanRevEnd
from convert.adapters.solidworks.Core.Writing.RevolveEnds.ReadEndReports import (
    ReadEndReports,
)
from convert.adapters.solidworks.Core.Writing.RevolveEnds.RevEndTarget import (
    RevEndTarget,
)
from convert.adapters.solidworks.Core.Writing.RevolveEnds.GetRevEndCase import (
    GetRevEndCase,
)
from interchange.Core.Common import FreezeMapping
from interchange.document.Models.DocumentModel import CadDocument


# publication checks the original authored model and native receipt before touching the requested sink
def EmitRevEndMut(
    DocumentValue: CadDocument,
    TargetValue: KTargetType,
    OptionsValue: WriteOptions | None,
) -> WriteResult:
    WrittenAt, Receipt, Settings = ReadMeasInput(CheckPartOpts(OptionsValue))
    Reports = ReadEndReports(Receipt)
    PlanValue = PlanRevEnd(DocumentValue)
    CaseValue = GetRevEndCase(Reports, PlanValue.NameValue, PlanValue.SideMode)
    OutputPath = RevEndTarget(TargetValue, Settings, CaseValue.LocatorValue)
    BuildOptions = ReplaceValue(
        Settings,
        values=FreezeMapping(
            {**Settings.values, "final_destination": CaseValue.LocatorValue}
        ),
    )
    Payload = PrepareRevolve(
        DocumentValue, OutputPath or TargetValue, WrittenAt, BuildOptions
    ).BytesValue
    Evidence = MatchRevEndMeas(CaseValue, Payload, Reports.NativeSha)
    Transfers = tuple(
        CapTransfer(CapValue, TransferMode.KNative)
        for CapValue in sorted(GetDocumentCaps(DocumentValue))
    )
    return PublishMeasMut(
        TargetValue, OutputPath, Settings, Payload, Evidence, Transfers
    )
