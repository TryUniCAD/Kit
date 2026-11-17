from tests.Convert.Solidworks.Research.Drawing.MakeFrontInput import MakeFrontInput
from tests.Convert.Solidworks.Research.Drawing.RunSheetCase import RunSheetCase


# independent linked parts exercise archive continuation and real view references together
def TestFrontSheets() -> None:
    First = RunSheetCase(
        "front", MakeFrontInput("SdkFrontAlpha", 0.0227, 0.0159, 0.0053)
    )
    Other = RunSheetCase(
        "front", MakeFrontInput("SdkFrontBeta", 0.0314, 0.0098, 0.0086)
    )
    for Report in (First, Other):
        assert Report["passed"] and Report["public_reader_passed"]
        assert Report["logical_streams_identical"]
        assert Report["runtime_input_file_access_attempts"] == 0
        assert Report["native_acceptance"] is False
        assert Report["public_writer_enabled"] is False
    assert First["artifact_sha256"] != Other["artifact_sha256"]
