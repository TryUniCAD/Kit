from collections import Counter
from collections.abc import Mapping
from pathlib import Path as FilePath
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.Construction.RectDimensions.RectDimRequest import (
    RectDimRequest,
)
from tests.Convert.Solidworks.Research.Resolved.LineDimensions.MutateRectGraph import (
    MutateRectGraph,
)
from tests.Convert.Solidworks.Research.Resolved.LineDimensions.RunDimBuild import (
    RunDimBuild,
)
from tests.Convert.Solidworks.Research.Resolved.RunPublicRead import RunPublicRead


# the public sketch must preserve sparse endpoint identity and authored axes without adding retired geometry or stale drivers
def TestStockSlots(TmpPath: FilePath) -> None:
    SourcePath = RunDimBuild(
        RectDimRequest("axis only sparse stock", True), TmpPath / "source"
    )
    (SourceSketch,) = RunPublicRead(SourcePath).sketches
    Document = RunPublicRead(MutateRectGraph(SourcePath, "stock-sparse"))
    (SketchValue,) = Document.sketches
    assert not Document.validate() and SketchValue.attributes["typed_line_loop"] is True
    assert SketchValue.parameter_ids == ()
    assert all(Param.owner_id != SketchValue.id for Param in Document.parameters)
    assert tuple(Entity.geometry for Entity in SketchValue.entities) == tuple(
        Entity.geometry for Entity in SourceSketch.entities
    )
    assert Counter(Constraint.kind for Constraint in SketchValue.constraints) == {
        "horizontal": 2,
        "vertical": 2,
    }
    assert {
        Constraint.references[0].entity_id for Constraint in SketchValue.constraints
    } == {Entity.id for Entity in SketchValue.entities}
    ActiveRows = CastValue(
        tuple[Mapping[str, object], ...], SketchValue.attributes["native_point_rows"]
    )
    RetiredRows = CastValue(
        tuple[Mapping[str, object], ...],
        SketchValue.attributes["native_retired_point_rows"],
    )
    assert tuple(PointRow["array_index"] for PointRow in ActiveRows) == (0, 2, 3, 4)
    assert tuple(PointRow["array_index"] for PointRow in RetiredRows) == (1,)
    for ModeValue in ("stock-retired-mark", "stock-retired-endpoint"):
        (Rejected,) = RunPublicRead(MutateRectGraph(SourcePath, ModeValue)).sketches
        assert Rejected.attributes.get("typed_line_loop") is not True
