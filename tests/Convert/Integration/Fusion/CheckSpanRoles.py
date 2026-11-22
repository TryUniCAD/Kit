import json as JsonLib
from pathlib import Path as FilePath

from tests.Convert.Integration.Fusion.SpanCliCase import SpanCliCase


# separate role checks detect swaps between equal valued live taper parameters
def CheckSpanRoles(Output: FilePath, Sample: SpanCliCase) -> None:
    Document = JsonLib.loads(Output.read_text())["document"]
    Feature = Document["feature_timeline"]["$tuple"][-1]
    Definition = Feature["definition"]
    assert Definition["$type"] == "DistanceExtrude"
    assert Definition["side_mode"] == Sample.SideMode
    Parameters = {Value["id"]: Value for Value in Document["parameters"]["$tuple"]}
    assert {
        Value["name"]: Value["attributes"]["native_name"]
        for Value in Parameters.values()
    } == dict(Sample.ParamRoles)
    Expected = {
        "along_parameter_id": "AlongDistance",
        "taper_parameter_id": "TaperAngle",
    }
    if Sample.SideMode == "two_sided":
        Expected.update(
            {
                "against_parameter_id": "AgainstDistance",
                "second_taper_id": "Side2TaperAngle",
            }
        )
    elif Sample.SideMode.startswith("symmetric"):
        Expected["second_taper_id"] = "TaperAngle"
    for RoleName, NativeName in Expected.items():
        Parameter = Parameters[Definition[RoleName]]
        assert Parameter["attributes"]["native_name"] == NativeName
        assert Parameter["owner_id"] == Feature["id"]
    assert all(
        Definition[RoleName] is None
        for RoleName in ("against_parameter_id", "start_offset_id", "second_taper_id")
        if RoleName not in Expected
    )
    assert "fusion.native_state" not in Document["metadata"]
