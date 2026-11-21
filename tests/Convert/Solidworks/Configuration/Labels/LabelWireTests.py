from typing import cast as CastValue

from tests.Convert.Solidworks.Configuration.Labels.RunLabelCase import RunLabelCase

# the signed sentinel and unrelated flag must preserve label framing for the same native layout
KLabelModes = (
    ("clear_condition", [-2, -1, 0, 37, -32768], 5),
    ("other_bit", [-2, -1, 0, 37, -32768], 5),
    ("signed_sentinel", [-1] * 5, 10),
)

# active layers must refuse before a tag can consume bytes or resolve the wrong owner
KLabelRefusals = (
    ("active_layer_alias", 54, "moDrViewLabelData_c.f50 layer object"),
    ("active_zero_selector", 54, "moDrViewLabelData_c.f50 layer object"),
    ("active_layer_truncated", 54, "moDrViewLabelData_c.f50 layer object"),
    ("truncated_selector", 52, "field f18/moDrViewLabelData_c/f48"),
    ("truncated_wide_text", 54, "string payload is truncated"),
    ("truncated_detail_suffix", 599, "field f18/fc8"),
    ("truncated_misc_suffix", 3101, "field f388/fcc"),
    ("trailing_label_data", 3105, "trailing data"),
    ("wrong_archive_version", 0, "requires archive version 19000"),
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
