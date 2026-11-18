from pathlib import Path as FilePath

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


# malformed driver ownership must preserve legacy reading without falsely qualifying a complete typed dimension graph
def TestRectScope(TmpPath: FilePath) -> None:
    SourcePath = RunDimBuild(
        RectDimRequest("typed rectangle rejection", False), TmpPath / "source"
    )
    for ModeValue in (
        "wrong-handle-class",
        "wrong-value-index",
        "wrong-sketch",
        "missing-axis",
        "wrong-axis",
        "alternate-value",
        "reference-count",
    ):
        DocumentValue = RunPublicRead(MutateRectGraph(SourcePath, ModeValue))
        assert all(
            SketchValue.attributes.get("typed_line_dimensions") is not True
            for SketchValue in DocumentValue.sketches
        )
