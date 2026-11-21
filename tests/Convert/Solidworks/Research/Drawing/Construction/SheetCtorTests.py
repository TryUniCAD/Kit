from typing import cast as CastValue

from tests.Convert.Solidworks.Research.Drawing.Construction.MakeCtorInput import (
    MakeCtorInput,
)
from tests.Convert.Solidworks.Research.Drawing.Construction.RunCtorCase import (
    RunCtorCase,
)


# complete generated files must preserve new support identities clocks aliases and authored paper settings
def TestSheetCtor() -> None:
    FirstInput = MakeCtorInput("SdkCtorAlpha", 9, 14)
    OtherInput = MakeCtorInput("SdkCtorBeta", 11, 3)
    ThirdInput = MakeCtorInput("SdkCtorGamma", 21, 5)
    FinalInput = MakeCtorInput("SdkCtorDelta", 8, 23)
    OtherSheet = CastValue(dict[str, object], OtherInput["sheet"])
    OtherSheet["custom_property_view"] = "new supports Ω " + "s" * 360
    ThirdSheet = CastValue(dict[str, object], ThirdInput["sheet"])
    ThirdSheet["length_unit"] = "in"
    Presentation = CastValue(dict[str, object], ThirdInput["presentation"])
    UnitsValue = CastValue(dict[str, object], Presentation["units"])
    UnitsValue.update(length_unit="in", unit_system="ips")
    FinalPresent = CastValue(dict[str, object], FinalInput["presentation"])
    FinalDef = CastValue(dict[str, object], FinalPresent["definition"])
    FinalDef["drafting_standard"] = "moISO_c"
    Reports = tuple(
        RunCtorCase(Request)
        for Request in (FirstInput, OtherInput, ThirdInput, FinalInput)
    )
    for Report in Reports:
        assert Report["passed"] and Report["all_logical_streams_identical"]
        assert (
            Report["sdk_complete_read_write_identical"]
            and Report["public_reader_passed"]
        )
        assert Report["real_aliases_preserved"] and Report["component_copy_preserved"]
        assert (
            Report["preallocation_plane_handle_preserved"]
            and Report["scale_operation_order_preserved"]
        )
        assert Report["runtime_input_file_access_attempts"] == 0
        assert Report["sdk_sheet_constructor"] is True
        assert Report["complete_sdk_only_drawing_factory"] is False
        assert (
            Report["native_acceptance"] is False
            and Report["public_writer_enabled"] is False
        )
    assert len({Report["artifact_sha256"] for Report in Reports}) == 4
