from pathlib import Path as FilePath
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.Construction.RectangleAnchors.CornerRequest import (
    CornerRequest,
)
from tests.Convert.Solidworks.Research.Resolved.Origin.AssertOrigin import (
    AssertOrigin,
)
from tests.Convert.Solidworks.Research.Resolved.Origin.MutateOrigin import (
    MutateOrigin,
)
from tests.Convert.Solidworks.Research.Resolved.Origin.RunOriginBuild import (
    RunOriginBuild,
)
from tests.Convert.Solidworks.Research.Resolved.RunPublicRead import RunPublicRead


# independent neutral rectangles must retain their actual fixed datum under ordinary extended stale and cached archive encodings
def TestOriginRead(TmpPath: FilePath) -> None:
    CasesValue = (
        ("origin alpha", 31.75, 18.125, 9.625),
        ("origin beta", 14.375, 27.625, 6.875),
        ("origin gamma", 21.875, 11.0625, 8.375),
    )
    for NameValue, LengthValue, WidthValue, DepthValue in CasesValue:
        SourcePath = RunOriginBuild(
            CornerRequest(NameValue, LengthValue, WidthValue, DepthValue),
            TmpPath / NameValue,
        )
        for ModeValue in (None, "extended-handles", "stale-keywords", "retired-region"):
            InputPath = (
                SourcePath if ModeValue is None else MutateOrigin(SourcePath, ModeValue)
            )
            DocumentValue = RunPublicRead(InputPath)
            AssertOrigin(DocumentValue, LengthValue, WidthValue)
            (SketchValue,) = DocumentValue.sketches
            if ModeValue == "retired-region":
                assert (
                    len(
                        CastValue(
                            tuple[object, ...],
                            SketchValue.attributes["native_retired_line_rows"],
                        )
                    )
                    == 1
                )
                assert (
                    len(
                        CastValue(
                            tuple[object, ...],
                            SketchValue.attributes["native_line_regions"],
                        )
                    )
                    == 1
                )
