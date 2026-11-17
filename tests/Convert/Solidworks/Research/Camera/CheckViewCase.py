from __future__ import annotations

from json import loads as LoadJson
from pathlib import Path as FilePath
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.Camera.MakeViewCase import MakeViewCase
from tests.Convert.Solidworks.Research.Camera.RunCamera import RunCamera
from tests.Convert.Solidworks.Research.Frozen.ComparePinned import ComparePinned
from tests.Convert.Solidworks.Research.PartArtifacts import SavePartOutput


# each camera regression pairs exact historical bytes with the independently checked current transform
def CheckViewCase(CaseValue: dict[str, object], SourceRoot: FilePath) -> None:
    Request = MakeViewCase(CaseValue)
    Outcome = RunCamera(Request)
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    Report = CastValue(dict[str, object], LoadJson(Outcome.stdout))
    Report["frozen_regression"] = ComparePinned(Report, Request, SourceRoot, True)
    SavePartOutput("View" + CastValue(str, CaseValue["name"]), Request, Report)
    Streams = CastValue(dict[str, dict[str, object]], Report["streams"])
    assert len(Streams) == 8
    assert all(
        RowValue["passed"] and RowValue["tail"] == 0 for RowValue in Streams.values()
    )
    assert Report["denied_reads"] == [] and Report["module_reads"]
    assert (
        Report["heldout_native_payloads_read"] is Report["native_acceptance"] is False
    )
    assert Report["vendor_acceptance"] == "unverified"
    GraphValue = CastValue(dict[str, object], Report["graph"])
    assert GraphValue["unresolved_references"] == 0
    Fields = CastValue(dict[str, dict[str, object]], Report["view_fields"])
    assert Fields["orientation"]["has_matrix"] == 1
    assert Fields["pan_zoom"]["has_matrix"] == 0
    assert Report["points"] == 2 and Report["arcs"] == 1 and Report["lines"] == 0
