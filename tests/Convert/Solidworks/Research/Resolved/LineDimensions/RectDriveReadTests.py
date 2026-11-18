from pathlib import Path as FilePath

from tests.Convert.Solidworks.Research.Construction.RectDimensions.RectDimRequest import (
    RectDimRequest,
)
from tests.Convert.Solidworks.Research.Resolved.LineDimensions.AssertRectRead import (
    AssertRectRead,
)
from tests.Convert.Solidworks.Research.Resolved.LineDimensions.MakeSquareCase import (
    MakeSquareCase,
)
from tests.Convert.Solidworks.Research.Resolved.LineDimensions.MutateRectGraph import (
    MutateRectGraph,
)
from tests.Convert.Solidworks.Research.Resolved.LineDimensions.RunDimBuild import (
    RunDimBuild,
)
from tests.Convert.Solidworks.Research.Resolved.RunPublicRead import RunPublicRead


# complete neutral rectangle builds must retain typed distance endpoints and actual parameter owners through the normal strict sdk process
def TestRectDrivers(TmpPath: FilePath) -> None:
    CasesValue = (
        ("origin", RectDimRequest("typed rectangle drivers", False), 54.0, 18.0),
        ("translated", RectDimRequest("typed translated rectangle", True), 37.0, 29.0),
        ("equal", MakeSquareCase(), 24.675, 24.675),
    )
    for LabelValue, RequestValue, WidthValue, HeightValue in CasesValue:
        SourcePath = RunDimBuild(RequestValue, TmpPath / LabelValue)
        for ModeValue in (None, "stale-keywords", "extended-handles"):
            InputPath = (
                SourcePath
                if ModeValue is None
                else MutateRectGraph(SourcePath, ModeValue)
            )
            AssertRectRead(RunPublicRead(InputPath), WidthValue, HeightValue)
