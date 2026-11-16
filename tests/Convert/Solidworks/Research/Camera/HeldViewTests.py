from __future__ import annotations

from json import loads as LoadJson
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.ArchiveProcess import KRepoRoot
from tests.Convert.Solidworks.Research.Camera.CameraFreeze import VerifyCamera
from tests.Convert.Solidworks.Research.Camera.MakeViewCase import MakeViewCase
from tests.Convert.Solidworks.Research.Camera.RunCamera import RunCamera
from tests.Convert.Solidworks.Research.Curve.ReadObject import ReadObject
from tests.Convert.Solidworks.Research.PartArtifacts import SavePartOutput


# locked native cases must receive complete neutral predictions before their private observations can be consulted
def TestHeldViews() -> None:
    Freeze = VerifyCamera()
    Specs = ReadObject(KRepoRoot / "re/tooling/sw2026/ViewSourceSpecs.json")
    Cases = CastValue(list[dict[str, object]], Specs["cases"])
    Locked = CastValue(list[dict[str, object]], Freeze["evaluated_heldouts"])
    assert len(Cases) == len(Locked) == 2
    assert {Value["name"] for Value in Cases} == {Value["name"] for Value in Locked}
    for CaseValue in Cases:
        Request = MakeViewCase(CaseValue)
        Outcome = RunCamera(Request)
        assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
        Report = CastValue(dict[str, object], LoadJson(Outcome.stdout))
        SavePartOutput("View" + CastValue(str, CaseValue["name"]), Request, Report)
        Streams = CastValue(dict[str, dict[str, object]], Report["streams"])
        assert len(Streams) == 8
        assert all(
            RowValue["passed"] and RowValue["tail"] == 0
            for RowValue in Streams.values()
        )
        assert Report["denied_reads"] == [] and Report["module_reads"]
        assert (
            Report["heldout_native_payloads_read"]
            is Report["native_acceptance"]
            is False
        )
        assert Report["vendor_acceptance"] == "unverified"
        GraphValue = CastValue(dict[str, object], Report["graph"])
        assert GraphValue["unresolved_references"] == 0
        Fields = CastValue(dict[str, dict[str, object]], Report["view_fields"])
        assert Fields["orientation"]["has_matrix"] == 1
        assert Fields["pan_zoom"]["has_matrix"] == 0
        assert Report["points"] == 2 and Report["arcs"] == 1 and Report["lines"] == 0
    assert VerifyCamera() == Freeze
