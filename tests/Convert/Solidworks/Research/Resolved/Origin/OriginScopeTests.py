from pathlib import Path as FilePath

from tests.Convert.Solidworks.Research.Construction.RectangleAnchors.CornerRequest import (
    CornerRequest,
)
from tests.Convert.Solidworks.Research.Resolved.Origin.MutateOrigin import (
    MutateOrigin,
)
from tests.Convert.Solidworks.Research.Resolved.Origin.RunOriginBuild import (
    RunOriginBuild,
)
from tests.Convert.Solidworks.Research.Resolved.RunPublicRead import RunPublicRead


# malformed external ownership and cached membership must preserve legacy reading without a false typed origin claim
def TestOriginScope(TmpPath: FilePath) -> None:
    SourcePath = RunOriginBuild(
        CornerRequest("origin rejection", 28.375, 17.625, 8.125), TmpPath / "source"
    )
    for ModeValue in (
        "external-index",
        "local-index",
        "point-kind",
        "reference-count",
        "missing-origin",
        "foreign-owner",
        "point-mark",
        "selected-index",
        "reference-mode",
        "backup-position",
        "extra-relation",
        "retired-referenced",
        "wrong-region",
        "origin-suppressed",
        "origin-drive-mode",
    ):
        DocumentValue = RunPublicRead(MutateOrigin(SourcePath, ModeValue))
        assert all(
            SketchValue.attributes.get("typed_origin_coincidence") is not True
            and SketchValue.attributes.get("typed_line_loop") is not True
            for SketchValue in DocumentValue.sketches
        )
