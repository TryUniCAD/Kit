from __future__ import annotations

from pathlib import Path as FilePath
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.Frozen.MatchImports import MatchImports
from tests.Convert.Solidworks.Research.Frozen.RunPinned import RunPinned
from tests.Convert.Solidworks.Research.PartArtifacts import SavePartOutput
from tests.Convert.Solidworks.Research.Presentation.Frame.CheckFrame import CheckFrame
from tests.Convert.Solidworks.Research.Presentation.MakeTreeCase import MakeTreeCase


# retained predictions bind corrected profile bytes to their independent neutral requests and frozen imports
def CheckFrameOut(
    CaseValue: dict[str, object], SourceRoot: FilePath, Revision: str
) -> None:
    Request = MakeTreeCase(CaseValue)
    Report = RunPinned(Request, SourceRoot, True)
    MatchImports(Report, SourceRoot)
    AxisValue = {"top": "y", "right": "x"}[CastValue(str, CaseValue["plane"])]
    CheckFrame(AxisValue, Report["profile_model_to_sketch"])
    Features = CastValue(list[str], Report["features"])
    assert len(Features) == 19 and Features.count("moInkMarkupFolder_c") == 1
    assert "moNotesAreaFtrFolder_c" not in Features
    assert Report["points"] == 2 and Report["arcs"] == 1 and Report["lines"] == 0
    GraphValue = CastValue(dict[str, object], Report["graph"])
    assert GraphValue["unresolved_references"] == 0
    assert (
        Report["heldout_native_payloads_read"] is Report["native_acceptance"] is False
    )
    assert Report["vendor_acceptance"] == "unverified"
    Report["frozen_generator_revision"] = Revision
    Report["private_reference_observations_read"] = False
    SavePartOutput("Frame" + CastValue(str, CaseValue["name"]), Request, Report)
