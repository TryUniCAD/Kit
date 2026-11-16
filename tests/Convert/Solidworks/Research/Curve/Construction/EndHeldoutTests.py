from __future__ import annotations

from typing import cast as CastValue

from tests.Convert.Solidworks.Research.ArchiveProcess import KRepoRoot
from tests.Convert.Solidworks.Research.Curve.Construction.HeldoutInput import (
    MakeHeldBody,
)
from tests.Convert.Solidworks.Research.Curve.Fields.WriterFreeze import VerifyFreeze
from tests.Convert.Solidworks.Research.Curve.ReadObject import ReadObject
from tests.Convert.Solidworks.Research.FreshPartRunner import RunFreshPart
from tests.Convert.Solidworks.Research.Frozen.ComparePinned import ComparePinned
from tests.Convert.Solidworks.Research.Frozen.FrozenRoot import FrozenRoot
from tests.Convert.Solidworks.Research.PartArtifacts import SavePartOutput


# frozen writers must predict complete files for source models withheld from field derivation
def TestEndHoldout() -> None:
    with FrozenRoot() as SourceRoot:
        Freeze = VerifyFreeze(SourceRoot)
        Specs = ReadObject(KRepoRoot / "re/tooling/sw2026/EndConditionSpecs.json")
        Cases = [
            Entry
            for Entry in CastValue(list[dict[str, object]], Specs["cases"])
            if Entry["split"] == "heldout"
        ]
        Locked = CastValue(list[dict[str, object]], Freeze["heldout_inputs"])
        assert len(Cases) == len(Locked) == 4
        assert {Entry["name"] for Entry in Cases} == {Entry["name"] for Entry in Locked}
        for CaseValue in Cases:
            Request = MakeHeldBody(CaseValue)
            Report = RunFreshPart(Request)
            Report["frozen_regression"] = ComparePinned(
                Report, Request, SourceRoot, False
            )
            SavePartOutput(CastValue(str, CaseValue["name"]), Request, Report)
            Streams = CastValue(dict[str, dict[str, object]], Report["streams"])
            assert len(Streams) == 8
            assert all(
                StreamRow["passed"] and StreamRow["tail"] == 0
                for StreamRow in Streams.values()
            )
            assert Report["center_fixed"] is True and Report["has_extrusion"] is True
            assert (
                Report["points"] == 2 and Report["arcs"] == 1 and Report["lines"] == 0
            )
            assert Report["end_condition"] == CaseValue["end_condition"]
            assert Report["reverse_direction"] is CaseValue["reverse"]
            assert Report["configuration_progress"] is True
            assert Report["denied_reads"] == [] and Report["module_reads"]
            assert Report["vendor_acceptance"] == "unverified"
        assert VerifyFreeze(SourceRoot) == Freeze
