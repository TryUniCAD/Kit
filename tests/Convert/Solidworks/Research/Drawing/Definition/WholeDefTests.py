from typing import cast as CastValue

from tests.Convert.Solidworks.Research.Drawing.Definition.MakeDefInput import (
    MakeDefInput,
)
from tests.Convert.Solidworks.Research.Drawing.Definition.RunDefCase import RunDefCase


# independently varied paper metadata must preserve complete typed graphs and every surrounding logical stream
def TestWholeDefs() -> None:
    FirstInput = MakeDefInput("SdkWholeAlpha", 4, 9)
    OtherInput = MakeDefInput("SdkWholeBeta", 11, 3)
    ThirdInput = MakeDefInput("SdkWholeGamma", 7, 13)
    FinalInput = MakeDefInput("SdkWholeDelta", 19, 8)
    SheetValue = CastValue(dict[str, object], OtherInput["sheet"])
    SheetValue["custom_property_view"] = "whole unicode Ω " + "w" * 360
    ThirdSheet = CastValue(dict[str, object], ThirdInput["sheet"])
    ThirdSheet["length_unit"] = "in"
    PresentValue = CastValue(dict[str, object], ThirdInput["presentation"])
    UnitsValue = CastValue(dict[str, object], PresentValue["units"])
    UnitsValue.update(length_unit="in", unit_system="ips")
    FinalPresent = CastValue(dict[str, object], FinalInput["presentation"])
    FinalDef = CastValue(dict[str, object], FinalPresent["definition"])
    FinalDef["drafting_standard"] = "moISO_c"
    Reports = tuple(
        RunDefCase(Request)
        for Request in (FirstInput, OtherInput, ThirdInput, FinalInput)
    )
    for Report in Reports:
        assert Report["passed"] and Report["all_logical_streams_identical"]
        assert Report["complete_sdk_readback"] and Report["sdk_read_write_identical"]
        assert Report["complete_research_readback"] and Report["public_reader_passed"]
        assert Report["runtime_input_file_access_attempts"] == 0
        assert Report["native_acceptance"] is False
        assert Report["public_writer_enabled"] is False
    assert len({Report["artifact_sha256"] for Report in Reports}) == 4
    assert CastValue(int, Reports[1]["definition_bytes"]) > CastValue(
        int, Reports[0]["definition_bytes"]
    )
