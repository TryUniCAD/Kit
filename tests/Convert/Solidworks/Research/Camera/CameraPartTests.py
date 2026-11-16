from __future__ import annotations

from copy import deepcopy as CopyValue
from json import loads as LoadJson
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.Camera.CameraInput import MakeCamera
from tests.Convert.Solidworks.Research.Camera.RunCamera import RunCamera
from tests.Convert.Solidworks.Research.PartArtifacts import SavePartOutput


# full file boundaries must preserve camera semantics without donor reads or fixed definition lengths
def TestCameraPart() -> None:
    Reports: list[dict[str, object]] = []
    for ViewIndex in (1, 7):
        Request = MakeCamera(ViewIndex)
        Outcome = RunCamera(Request)
        assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
        Report = CastValue(dict[str, object], LoadJson(Outcome.stdout))
        SavePartOutput("CameraDiscovery" + str(ViewIndex), Request, Report)
        Streams = CastValue(dict[str, dict[str, object]], Report["streams"])
        assert len(Streams) == 8
        assert all(
            RowValue["passed"] and RowValue["tail"] == 0
            for RowValue in Streams.values()
        )
        assert Report["denied_reads"] == [] and Report["module_reads"]
        assert Report["vendor_acceptance"] == "unverified"
        assert (
            Report["heldout_native_payloads_read"]
            is Report["native_acceptance"]
            is False
        )
        GraphValue = CastValue(dict[str, object], Report["graph"])
        assert GraphValue["unresolved_references"] == 0
        Fields = CastValue(dict[str, dict[str, object]], Report["view_fields"])
        assert Fields["orientation"]["has_matrix"] == int(ViewIndex != 1)
        assert Fields["pan_zoom"]["has_matrix"] == 0
        assert [Fields["pan_zoom"][KeyValue] for KeyValue in ("f58", "f60", "f68")] == [
            0.003173,
            -0.007191,
            0.005713,
        ]
        assert Fields["pan_zoom"]["f70"] == 37.173
        Reports.append(Report)
    FirstSizes = CastValue(dict[str, int], Reports[0]["sizes"])
    SecondSizes = CastValue(dict[str, int], Reports[1]["sizes"])
    assert (
        SecondSizes["Contents/Definition"] - FirstSizes["Contents/Definition"] == 9 * 8
    )
    assert {
        KeyValue: Value
        for KeyValue, Value in FirstSizes.items()
        if KeyValue != "Contents/Definition"
    } == {
        KeyValue: Value
        for KeyValue, Value in SecondSizes.items()
        if KeyValue != "Contents/Definition"
    }
    assert Reports[0]["blob"] != Reports[1]["blob"]


# invalid presentation must fail at the complete construction boundary before any native file is returned
def TestCameraReject() -> None:
    for FieldName, FieldValue in (
        ("scale2", True),
        ("scale2", 0.0),
        ("translation", [float("nan"), 0.0, 0.0]),
        ("named_view", 0),
        ("perspective", True),
    ):
        Request = CopyValue(MakeCamera(7))
        Presentation = CastValue(dict[str, object], Request["presentation"])
        CameraValue = CastValue(dict[str, object], Presentation["initial_view"])
        CameraValue[FieldName] = FieldValue
        Outcome = RunCamera(Request)
        assert Outcome.returncode != 0
        assert '"blob"' not in Outcome.stdout
        assert "Error" in Outcome.stderr
