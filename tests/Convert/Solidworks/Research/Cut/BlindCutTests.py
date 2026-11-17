from __future__ import annotations

from math import isclose as IsClose
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.Cut.BlindCutInput import MakePocketInput
from tests.Convert.Solidworks.Research.FreshPartRunner import RunFreshPart
from tests.Convert.Solidworks.Research.PartArtifacts import SavePartOutput


# the decoded graph distinguishes owned driving parameters from metadata that merely names them
def AssertPocket(Report: dict[str, object], ScopeWord: int) -> None:
    Pocket = CastValue(dict[str, object], Report["blind_pocket"])
    Profile = CastValue(dict[str, object], Pocket["cut_profile"])
    Parameter = CastValue(dict[str, object], Pocket["depth_parameter"])
    Keyword = CastValue(dict[str, object], Pocket["keyword"])
    assert Pocket["feature_names"] == [
        "Sketch1",
        "Boss-Extrude1",
        "PocketSketch",
        "BlindPocket",
    ]
    assert Pocket["distinct_feature_ids"] and Pocket["owned_profiles"]
    assert Pocket["distinct_plane_wrappers"]
    assert Profile["counts"] == [2, 0, 1] and Profile["closed"]
    assert Profile["frame"] == Report["profile_model_to_sketch"]
    assert Profile["center_m"] == [0.0097, -0.0073]
    assert IsClose(CastValue(float, Profile["radius_m"]), 0.00641, rel_tol=1e-12)
    assert IsClose(CastValue(float, Profile["parameter_m"]), 0.00641, rel_tol=1e-12)
    assert Profile["fixed_center"] and Profile["radial_link"]
    assert Pocket["operations"] == [-1, 1] and Pocket["cut_flags"] == 0x400201CA
    assert Pocket["end"] == {
        "f08": 1,
        "f88": 0,
        "f8c": 1,
        "f0c": 0,
        "f10": 0,
        "f158": 0,
    }
    assert Pocket["inactive_ends_absent"]
    assert Parameter["name"] == "D1" and Parameter["value_m"] == 0.00483
    assert Parameter["distinct_from_boss"]
    assert Parameter["classes"] == [
        "moDisplayDistanceDim_c",
        "moFeatureDimHandle_c",
        "ParallelPlaneDistanceDim_c",
        "moLengthParameter_c",
    ]
    assert Keyword["tag"] == "Extrusion" and Keyword["name"] == "BlindPocket"
    assert Keyword["type"] is None and Keyword["dimension"] == "D1"
    assert Keyword["profile_id"] == CastValue(list[int], Pocket["profile_ids"])[1]
    assert IsClose(
        CastValue(float, Keyword["depth_in_document_units"]), 4.83, rel_tol=1e-12
    )
    assert Pocket["scope_word"] == ScopeWord and Pocket["constructor_body_state"]
    assert Pocket["body_scope_qualified"] is False


# unchanged nonresolving streams isolate the authored scope difference from other document state
def AssertScopePair(
    Original: dict[str, dict[str, object]], Sibling: dict[str, dict[str, object]]
) -> None:
    assert Original.keys() == Sibling.keys()
    for NameValue in Original:
        Before, After = Original[NameValue], Sibling[NameValue]
        assert Before["bytes"] == After["bytes"]
        if NameValue == "Contents/Config-0-ResolvedFeatures":
            assert Before["sha256"] != After["sha256"]
            assert Before["map_count"] == After["map_count"]
        else:
            assert Before["sha256"] == After["sha256"]


# process isolation and linked stream round trips catch donor reads and hidden map ownership changes
def TestBlindPocket() -> None:
    Original = None
    for ArtifactName, ScopeValue, ScopeWord in (
        ("BlindPocketAllBodies", "all_bodies", 0),
        ("BlindPocketEmptyFeatureScope", "empty_feature_scope", 1),
    ):
        Request = MakePocketInput(ScopeValue)
        Report = RunFreshPart(Request)
        AssertPocket(Report, ScopeWord)
        Streams = CastValue(dict[str, dict[str, object]], Report["streams"])
        assert len(Streams) == 8
        assert all(
            StreamRow["passed"] and StreamRow["tail"] == 0
            for StreamRow in Streams.values()
        ), Streams
        Linked = Streams["Contents/Config-0-ResolvedFeatures"]
        assert Linked["seeded_map_count"] == Linked["map_base"] == Report["map_count"]
        assert Report["configuration_progress"] is True
        assert Report["denied_reads"] == [] and Report["module_reads"]
        assert Report["vendor_acceptance"] == "unverified"
        if Original is None:
            Original = Streams
        else:
            AssertScopePair(Original, Streams)
        SavePartOutput(ArtifactName, Request, Report)
