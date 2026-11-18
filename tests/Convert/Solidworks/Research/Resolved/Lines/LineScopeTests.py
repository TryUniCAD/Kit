from pathlib import Path as FilePath

from tests.Convert.Solidworks.Research.Construction.Part.MakePolygonCase import (
    MakePolygonCase,
)
from tests.Convert.Solidworks.Research.Resolved.Lines.AssertLineRead import (
    AssertLineRead,
)
from tests.Convert.Solidworks.Research.Resolved.Lines.MutateLineGraph import (
    MutateLineGraph,
)
from tests.Convert.Solidworks.Research.Resolved.Lines.RunLineBuild import RunLineBuild
from tests.Convert.Solidworks.Research.Resolved.RunPublicRead import RunPublicRead


# malformed joins construction geometry and duplicate markers must never gain typed polygon semantics through public reading
def TestLineScope(TmpPath: FilePath) -> None:
    VerticesValue = ((-11.25, -5.125), (23.75, 2.5), (4.625, 28.125))
    Target = RunLineBuild(
        MakePolygonCase("reader admission", VerticesValue, False), TmpPath / "source"
    )
    for ModeValue in (
        "bad-handle",
        "bad-endpoint",
        "construction",
        "duplicate-id",
        "relation-owner",
    ):
        Document = RunPublicRead(MutateLineGraph(Target, ModeValue))
        assert all(
            Sketch.attributes.get("typed_line_loop") is not True
            for Sketch in Document.sketches
        )
        assert all(
            ":line:" not in Entity.id
            for Sketch in Document.sketches
            for Entity in Sketch.entities
        )
    Extended = RunPublicRead(MutateLineGraph(Target, "extended-encoding"))
    AssertLineRead(Extended, VerticesValue, 12.75)
