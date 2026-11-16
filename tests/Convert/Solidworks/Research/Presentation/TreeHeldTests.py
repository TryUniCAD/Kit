from __future__ import annotations

from json import loads as LoadJson
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.ArchiveProcess import KRepoRoot
from tests.Convert.Solidworks.Research.Camera.RunCamera import RunCamera
from tests.Convert.Solidworks.Research.Curve.ReadObject import ReadObject
from tests.Convert.Solidworks.Research.PartArtifacts import SavePartOutput
from tests.Convert.Solidworks.Research.Presentation.MakeTreeCase import MakeTreeCase
from tests.Convert.Solidworks.Research.Presentation.VerifyTree import VerifyTree


# unseen folder predictions must emit complete files from public inputs before any private observations are opened
def TestTreeHold() -> None:
    Freeze = VerifyTree()
    Specs = ReadObject(KRepoRoot / "re/tooling/sw2026/TreeSourceSpecs.json")
    Cases = CastValue(list[dict[str, object]], Specs["cases"])
    Locked = CastValue(list[dict[str, object]], Freeze["evaluated_heldouts"])
    assert len(Cases) == len(Locked) == 2
    assert {Value["name"] for Value in Cases} == {Value["name"] for Value in Locked}
    for CaseValue in Cases:
        Request = MakeTreeCase(CaseValue)
        Outcome = RunCamera(Request)
        assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
        Report = CastValue(dict[str, object], LoadJson(Outcome.stdout))
        Report["frozen_generator_revision"] = Freeze["writer_revision"]
        Report["private_reference_observations_read"] = False
        SavePartOutput("Tree" + CastValue(str, CaseValue["name"]), Request, Report)
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
        GraphValue = CastValue(dict[str, object], Report["graph"])
        assert GraphValue["unresolved_references"] == 0
        Features = CastValue(list[str], Report["features"])
        assert Features.count("moInkMarkupFolder_c") == 1
        assert "moNotesAreaFtrFolder_c" not in Features and len(Features) == 19
    assert VerifyTree() == Freeze
