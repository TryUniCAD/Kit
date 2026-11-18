# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path as FilePath
from typing import cast as CastValue

from convert.Formats.Fusion.DocumentRead import ReadFusionDoc
from interchange.geometry.Models.GeometryCurves import LineGeometry
from tests.Research.Archives.Comparison.SemanticComparisonTests import (
    ReadReport,
    RunComparison,
    WriteInputs,
)


# native direction variants preserve physical lines while retaining ordered loop and extrusion differences
def TestNativeMatch(TmpPath: FilePath) -> None:
    RootPath = FilePath(__file__).resolve().parents[4]
    CapturePath = RootPath / "re/automation/PairedCaptures/P03/fusion-8d53584027ff"
    Documents = tuple(
        ReadFusionDoc(CapturePath / f"P03-fusion-{VariantName}.f3d")
        for VariantName in ("baseline-a", "direction-negative")
    )
    Report = ReadReport(RunComparison(WriteInputs(TmpPath, *Documents)), "different", 2)
    Comparison = CastValue(dict[str, object], Report["comparison"])
    assert not Comparison["ambiguous"]
    assert Comparison["search_limited"] is False
    References = CastValue(list[dict[str, object]], Comparison["reference_differences"])
    assert len(References) == 8
    assert {
        (Value["role"], Value["left_target"], Value["left_count"], Value["right_count"])
        for Value in References
    } == {
        (
            f"/closed_profile_entity_ids/0/{Index}",
            Target,
            SideIndex == 0,
            SideIndex == 1,
        )
        for SideIndex, Document in enumerate(Documents)
        for Index, Target in enumerate(
            Document.sketches[0].closed_profile_entity_ids[0]
        )
    }
    assert all(
        Value["left"] == Documents[0].sketches[0].id
        and Value["right"] == Documents[1].sketches[0].id
        and Value["left_target"] == Value["right_target"]
        and Value["reason"] == "target_multiplicity"
        for Value in References
    )
    Matches = CastValue(list[dict[str, object]], Comparison["matches"])
    Lines = tuple(
        {
            Entity.id: Entity.geometry
            for SketchValue in Document.sketches
            for Entity in SketchValue.entities
            if isinstance(Entity.geometry, LineGeometry)
        }
        for Document in Documents
    )
    LineMatches = tuple(Match for Match in Matches if Match["left"] in Lines[0])
    assert len(LineMatches) == len(Lines[0]) == len(Lines[1]) == 4
    for Match in LineMatches:
        assert not Match["differences"]
        assert (
            Lines[0][CastValue(str, Match["left"])]
            == Lines[1][CastValue(str, Match["right"])]
        )
    Changed = tuple(Match for Match in Matches if Match["differences"])
    assert len(Changed) == 2
    assert {Match["left"] for Match in Changed} == {
        next(Value.id for Value in Documents[0].parameters if Value.name == "depth_mm"),
        Documents[0].bodies[0].id,
    }
    Differences = tuple(
        Value
        for Match in Changed
        for Value in CastValue(list[dict[str, object]], Match["differences"])
    )
    assert {
        Value["pointer"]: (
            CastValue(dict[str, object], Value["left"])["value"],
            CastValue(dict[str, object], Value["right"])["value"],
        )
        for Value in Differences
    } == {
        "/value/value": (10.0, -10.0),
        "/expression/source": ("10 mm", "-( 10 mm )"),
        "/topology/bounding_box/minimum/z": (0.0, -10.0),
        "/topology/bounding_box/maximum/z": (10.0, 0.0),
    }
    Sources = CastValue(dict[str, dict[str, object]], Report["sources"])
    assert (
        sum(
            len(CastValue(list[object], Source["unresolved"]))
            for Source in Sources.values()
        )
        == 70
    )
    assert all(
        any(
            Value["path"] == "/brep"
            and Value["reason"] == "domain_requires_independent_comparison"
            for Value in CastValue(list[dict[str, object]], Source["unresolved"])
        )
        for Source in Sources.values()
    )
