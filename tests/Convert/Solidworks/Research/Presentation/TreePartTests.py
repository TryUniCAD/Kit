from __future__ import annotations

from json import loads as LoadJson
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.Camera.CameraInput import MakeCamera
from tests.Convert.Solidworks.Research.Camera.RunCamera import RunCamera
from tests.Convert.Solidworks.Research.PartArtifacts import SavePartOutput
from tests.Convert.Solidworks.Research.Presentation.MakeTreeInput import MakeTreeInput


# discovery processes must generate concrete markup nodes through the shared graph without reading heldout observations
def TestTreePart() -> None:
    Request = MakeTreeInput(MakeCamera(7))
    Outcome = RunCamera(Request)
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    Report = CastValue(dict[str, object], LoadJson(Outcome.stdout))
    SavePartOutput("TreeDiscovery", Request, Report)
    Features = CastValue(list[str], Report["features"])
    assert Features.count("moInkMarkupFolder_c") == 1
    assert "moNotesAreaFtrFolder_c" not in Features
    assert len(Features) == 19
    Streams = CastValue(dict[str, dict[str, object]], Report["streams"])
    assert len(Streams) == 8
    assert all(
        RowValue["passed"] and RowValue["tail"] == 0 for RowValue in Streams.values()
    )
    GraphValue = CastValue(dict[str, object], Report["graph"])
    assert GraphValue["unresolved_references"] == 0
    assert Report["denied_reads"] == [] and Report["module_reads"]
    assert (
        Report["heldout_native_payloads_read"] is Report["native_acceptance"] is False
    )


# unsupported folder combinations must fail at the process boundary before producing a native file
def TestBadTree() -> None:
    Request = MakeTreeInput(MakeCamera(7))
    Presentation = CastValue(dict[str, object], Request["presentation"])
    Folders = CastValue(dict[str, str], Presentation["folder_names"])
    Folders["moNotesAreaFtrFolder_c"] = "extra notes"
    Outcome = RunCamera(Request)
    assert Outcome.returncode != 0 and Outcome.stdout == ""
    assert "base part graphs require authored names" in Outcome.stderr
