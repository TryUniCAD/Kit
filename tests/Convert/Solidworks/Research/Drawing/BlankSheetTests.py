from typing import cast as CastValue

from tests.Convert.Solidworks.Research.Drawing.MakeSheetInput import MakeSheetInput
from tests.Convert.Solidworks.Research.Drawing.RunSheetCase import RunSheetCase


# variable metadata exposes fixed payloads while full public decoding checks native ownership
def TestBlankSheets() -> None:
    FirstInput = MakeSheetInput("SdkBlankAlpha", 3, 7)
    OtherInput = MakeSheetInput("SdkBlankBeta", 7, 5)
    SheetValue = CastValue(dict[str, object], OtherInput["sheet"])
    SheetValue["custom_property_view"] = "independent metadata Ω " + "x" * 300
    First = RunSheetCase("blank", FirstInput)
    Other = RunSheetCase("blank", OtherInput)
    for Report in (First, Other):
        assert Report["passed"] and Report["public_reader_passed"]
        assert Report["logical_streams_identical"]
        assert Report["runtime_input_file_access_attempts"] == 0
        assert Report["native_acceptance"] is False
        assert Report["public_write_refusals"] == {
            "inspection": True,
            "linked_layout": False,
        }
    FirstRows = CastValue(list[dict[str, object]], First["sdk_write_observations"])
    OtherRows = CastValue(list[dict[str, object]], Other["sdk_write_observations"])
    assert CastValue(int, OtherRows[0]["body_bytes"]) > CastValue(
        int, FirstRows[0]["body_bytes"]
    )
