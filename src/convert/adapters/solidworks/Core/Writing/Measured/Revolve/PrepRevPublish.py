from collections.abc import Mapping
from dataclasses import replace as ReplaceValue
from pathlib import Path as FilePath, PureWindowsPath

from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Core.Preparation.Revolve.PlanRevProfile import (
    PlanRevProfile,
)
from convert.adapters.solidworks.Core.Preparation.Revolve.PrepareRevolve import (
    PrepareRevolve,
)
from convert.adapters.solidworks.Core.Preparation.Revolve.Readback.CheckRevRead import (
    CheckRevRead,
)
from convert.adapters.solidworks.Core.Preparation.Revolve.Readback.IsRevRead import (
    IsRevRead,
)
from convert.adapters.solidworks.Core.Preparation.Revolve.Readback.ReadRevInput import (
    ReadRevInput,
)
from convert.adapters.solidworks.Core.Writing.Measured.Revolve.CheckRevTarget import (
    CheckRevTarget,
)
from convert.adapters.solidworks.Core.Writing.Measured.Revolve.MatchRevMeas import (
    MatchRevMeas,
)
from convert.adapters.solidworks.Core.Writing.Measured.Revolve.ReadRevEvidence import (
    ReadRevEvidence,
)
from convert.adapters.solidworks.Core.Writing.Measured.Revolve.RevCaseFor import (
    RevCaseFor,
)
from interchange.Core.Common import FreezeMapping
from interchange.document.Models.DocumentModel import CadDocument


# all destination intent and measurement checks precede actual native output
def PrepRevPublish(
    DocumentValue: CadDocument, TargetValue: KTargetType, Settings: WriteOptions
) -> tuple[bytes, Mapping[str, object], bool]:
    Evidence = ReadRevEvidence(Settings)
    IsReadback = IsRevRead(DocumentValue)
    InputValue = DocumentValue
    if IsReadback:
        if isinstance(TargetValue, FilePath):
            NameValue = TargetValue.stem
        else:
            FinalValue = Settings.values.get("final_destination")
            if type(FinalValue) is not str:
                raise ValueError(
                    "measured revolve stream requires its exact inspected self locator"
                )
            NameValue = PureWindowsPath(FinalValue).stem
        InputValue = ReadRevInput(DocumentValue, NameValue)
    PlanValue = PlanRevProfile(InputValue)
    if PlanValue is None:
        raise ValueError("measured revolve requires exactly one ordinary feature")
    Locator, Digest = RevCaseFor(Evidence, PlanValue.NameValue)
    CheckRevTarget(TargetValue, Settings, Locator)
    BuildOptions = ReplaceValue(
        Settings,
        values=FreezeMapping({**Settings.values, "final_destination": Locator}),
    )
    Payload = PrepareRevolve(
        InputValue, TargetValue, Evidence.WrittenAt, BuildOptions
    ).BytesValue
    Measurement = MatchRevMeas(Evidence, Payload, Digest)
    if IsReadback:
        CheckRevRead(DocumentValue, Payload)
    return Payload, Measurement, IsReadback
