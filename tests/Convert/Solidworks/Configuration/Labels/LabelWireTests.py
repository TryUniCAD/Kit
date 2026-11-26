from typing import cast as CastValue

from tests.Convert.Solidworks.Configuration.Labels.RunLabelCase import RunLabelCase
from tests.Convert.Solidworks.Configuration.Labels.WireLabelCases import (
    KLabelModes,
    KLabelRefusals,
)


# compare complete label reads across condition modes and refuse incomplete or unproved owners
def TestLabelWire() -> None:
    ReportValue = RunLabelCase("wire")
    assert ReportValue["conditional_layer_admitted"] is False
    Positives = CastValue(list[dict[str, object]], ReportValue["positives"])
    for Result, (CaseName, Selectors, BranchCount) in zip(
        Positives, KLabelModes, strict=True
    ):
        assert Result["case"] == CaseName
        assert Result["selectors"] == Selectors
        assert Result["branch_calls"] == BranchCount
        FirstLabel = CastValue(dict[str, object], Result["first_label"])
        assert FirstLabel["f88"] == "View 1 Ω"
        assert FirstLabel["f90"] == ["A", "Côté 1"]
        assert FirstLabel["f30"] == {"f06": -30, "f00": 0.125}
        assert FirstLabel["fcc"] == 0xD137ABEA
    Refusals = CastValue(list[dict[str, object]], ReportValue["refusals"])
    for Refusal, (CaseName, Offset, Diagnostic) in zip(
        Refusals, KLabelRefusals, strict=True
    ):
        assert Refusal["case"] == CaseName
        assert Refusal["offset"] == Offset
        assert Diagnostic in CastValue(str, Refusal["diagnostic"])
