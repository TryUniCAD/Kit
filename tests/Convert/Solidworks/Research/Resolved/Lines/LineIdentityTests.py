from collections.abc import Mapping
from pathlib import Path as FilePath
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.Construction.Part.MakePolygonCase import (
    MakePolygonCase,
)
from tests.Convert.Solidworks.Research.Resolved.Lines.MutateLineGraph import (
    MutateLineGraph,
)
from tests.Convert.Solidworks.Research.Resolved.Lines.RunLineBuild import RunLineBuild
from tests.Convert.Solidworks.Research.Resolved.RunPublicRead import RunPublicRead


# stored row order creation identities and permanent markers must stay distinct across actual archive public reads
def TestLineIds(TmpPath: FilePath) -> None:
    VerticesValue = (
        (-16.5, -8.75),
        (29.125, -8.75),
        (29.125, 23.25),
        (7.5, 23.25),
        (7.5, 4.625),
        (-16.5, 4.625),
    )
    Target = RunLineBuild(
        MakePolygonCase("reader identities", VerticesValue, True), TmpPath / "source"
    )
    Reordered = RunPublicRead(MutateLineGraph(Target, "reordered-lines"))
    (SketchValue,) = Reordered.sketches
    PrefixValue = f"sldprt:sketch:{SketchValue.attributes['native_object_id']}:line:"
    assert tuple(Entity.id for Entity in SketchValue.entities) == tuple(
        PrefixValue + str(Index) for Index in (3, 1, 6, 2, 5, 4)
    )
    assert SketchValue.closed_profile_entity_ids == (
        tuple(PrefixValue + str(Index) for Index in (3, 4, 5, 6, 1, 2)),
    )
    Renumbered = RunPublicRead(MutateLineGraph(Target, "sparse-identities"))
    (SketchValue,) = Renumbered.sketches
    assert tuple(Entity.id for Entity in SketchValue.entities) == tuple(
        PrefixValue + str(17 + 7 * Index) for Index in range(6)
    )
    assert SketchValue.closed_profile_entity_ids == (
        tuple(Entity.id for Entity in SketchValue.entities),
    )
    for Index, Entity in enumerate(SketchValue.entities):
        Fields = CastValue(Mapping[str, object], Entity.attributes["native_fields"])
        assert Fields["f08"] == 17 + 7 * Index
        assert Fields["f0c"] == 101 + 2 * Index
    Points = CastValue(
        tuple[Mapping[str, object], ...], SketchValue.attributes["native_point_rows"]
    )
    assert tuple(Point["native_creation_id"] for Point in Points) == tuple(
        301 + 3 * Index for Index in range(6)
    )
