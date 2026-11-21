from typing import cast as CastValue

from tests.Convert.Solidworks.Configuration.Labels.RunLabelCase import RunLabelCase

# full label comparisons need distinct physical owners and independently checked field digests
KLabelControls = (
    (
        "ladder",
        [12607, 16177],
        69,
        69,
        "d7512b4a779284181f37f6cb849b9b193a5dd0626200d0c78faf8f28191fa3fb",
    ),
    (
        "concave",
        [11056, 14626],
        54,
        15,
        "4ad85ef3909e0de77ab8d69c8f41cbda1701b280461c17f385ed266f460b7238",
    ),
)


# read the complete label family at its real caller boundary without allocating object slots
def TestPartLabels() -> None:
    for CaseName, Interval, Counter, HeaderIndex, FieldDigest in KLabelControls:
        ReportValue = RunLabelCase(CaseName)
        assert ReportValue["root_interval"] == Interval
        assert ReportValue["part"] == ["moPart_c", 1, 2]
        assert ReportValue["header_alias"] == ["moExtObject_c", 1, HeaderIndex]
        assert ReportValue["anchor_slots"] == [1, 2, 3]
        assert ReportValue["map_base"] == 4
        assert ReportValue["map_counter"] == Counter
        assert ReportValue["selectors"] == [-1] * 5
        assert ReportValue["field_sha256"] == FieldDigest
        Layouts = CastValue(dict[str, int], ReportValue["schema_calls"])
        assert Layouts == {
            "moLabelDefs_c": 1,
            "moDrViewLabelData_c": 5,
            "moDetailLabelData_c": 1,
            "moSectionLabelData_c": 1,
            "moAuxLabelData_c": 1,
            "moOrthoLabelData_c": 1,
            "moMiscLabelData_c": 1,
            "utCharFormat_c": 31,
            "utLineWidth_c.Serialize0": 10,
        }
