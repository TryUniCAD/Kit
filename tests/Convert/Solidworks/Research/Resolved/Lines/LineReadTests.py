from pathlib import Path as FilePath

from tests.Convert.Solidworks.Research.Construction.Part.MakePolygonCase import (
    MakePolygonCase,
)
from tests.Convert.Solidworks.Research.Resolved.Lines.AssertLineRead import (
    AssertLineRead,
)
from tests.Convert.Solidworks.Research.Resolved.Lines.RunLineBuild import RunLineBuild
from tests.Convert.Solidworks.Research.Resolved.RunPublicRead import RunPublicRead


# independent skew concave and clockwise profiles must survive guarded construction and strict public reading
def TestLineRead(TmpPath: FilePath) -> None:
    CasesValue = (
        ("reader skew", ((-17.125, -4.5), (26.75, 1.875), (3.625, 31.25)), False),
        (
            "reader step",
            (
                (-12.5, -8.25),
                (24.125, -8.25),
                (24.125, 26.75),
                (5.5, 26.75),
                (5.5, 7.625),
                (-12.5, 7.625),
            ),
            True,
        ),
        (
            "reader clockwise",
            (
                (-13.5, 1.25),
                (-4.125, 22.75),
                (19.5, 24.125),
                (28.75, -3.625),
                (1.5, -12.875),
            ),
            False,
        ),
    )
    for NameValue, VerticesValue, IsVariant in CasesValue:
        Request = MakePolygonCase(NameValue, VerticesValue, IsVariant)
        Target = RunLineBuild(Request, TmpPath / NameValue)
        Document = RunPublicRead(Target)
        AssertLineRead(Document, VerticesValue, 18.625 if IsVariant else 12.75)
