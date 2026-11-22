from collections.abc import Mapping
from dataclasses import replace as ReplaceValue
from os import name as OsName
from pathlib import Path as FilePath, PureWindowsPath

from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Core.Preparation.Revolve.PlanThinWrite import (
    PlanThinWrite,
)
from convert.adapters.solidworks.Core.Preparation.Revolve.PrepareRevolve import (
    PrepareRevolve,
)
from convert.adapters.solidworks.Core.Preparation.Revolve.Readback.CheckRevRead import (
    CheckRevRead,
)
from convert.adapters.solidworks.Core.Preparation.Revolve.Readback.IsThinRead import (
    IsThinRead,
)
from convert.adapters.solidworks.Core.Preparation.Revolve.Readback.ReadRevInput import (
    ReadRevInput,
)
from convert.adapters.solidworks.Core.Writing.Measured.Revolve.CheckRevTarget import (
    CheckRevTarget,
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


# all destination intent and measurement checks precede actual native output
def PrepThinPublish(
    DocumentValue: CadDocument, TargetValue: KTargetType, Settings: WriteOptions
) -> tuple[bytes, Mapping[str, object], bool]:
    WrittenAt, ReportId, Report, JobValue = ReadThinReports(Settings)
    IsReadback = IsThinRead(DocumentValue)
    InputValue = DocumentValue
    if IsReadback:
        FinalValue = Settings.values.get("final_destination")
        if isinstance(TargetValue, FilePath):
            NameValue = TargetValue.stem
        elif type(FinalValue) is str:
            NameValue = PureWindowsPath(FinalValue).stem
        else:
            raise ValueError(
                "measured thin revolve stream requires its inspected self locator"
            )
        InputValue = ReadRevInput(DocumentValue, NameValue, IsThin=True)
    PlanValue = PlanThinWrite(InputValue)
    Locator, Digest, CaseValue = ThinCaseFor(Report, JobValue, PlanValue.NameValue)
    if isinstance(TargetValue, FilePath) and OsName != "nt":
        raise ValueError(
            "measured thin revolve filesystem output requires its inspected Windows path"
        )
    CheckRevTarget(TargetValue, Settings, Locator)
    BuildOptions = ReplaceValue(
        Settings,
        values=FreezeMapping({**Settings.values, "final_destination": Locator}),
    )
    Payload = PrepareRevolve(
        InputValue, TargetValue, WrittenAt, BuildOptions
    ).BytesValue
    Measurement = MatchThinMeas(Payload, Digest, ReportId, CaseValue)
    if IsReadback:
        CheckRevRead(DocumentValue, Payload)
    return Payload, Measurement, IsReadback
