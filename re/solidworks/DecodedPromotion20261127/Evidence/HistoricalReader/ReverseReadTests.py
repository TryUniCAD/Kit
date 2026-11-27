from collections.abc import Mapping
from io import BytesIO
from typing import cast as CastValue

from pytest import mark as TestMark, raises as RaisesError

from convert.api import open_document as OpenDocument
from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter
from convert.adapters.base.WriteOptions import WriteOptions
from tests.Convert.Integration.Solidworks.Reverse.CheckSignedBody import CheckSignedBody
from interchange.Features.FeatureExtrude import ExtrudeFeature
from tests.Convert.Integration.Solidworks.Reverse.LoadReverse import LoadReverse


# real closed archives must preserve the signed solid and its actual driving parameter owner
@TestMark.parametrize(
    "CaseName",
    (
        "discoveryTriangleForward",
        "discoveryTriangleReverse",
        "holdoutStepForward",
        "holdoutStepReverse",
        "holdoutQuadForward",
        "holdoutQuadReverse",
    ),
)
def CheckReverse(CaseName: str) -> None:
    Sample = LoadReverse(CaseName)
    Document = OpenDocument(Sample.SourcePath, strict=True)
    Feature = next(
        Value for Value in Document.feature_timeline if Value.name == "Boss-Extrude1"
    )
    Definition = Feature.definition
    assert isinstance(Definition, ExtrudeFeature)
    assert Definition.reversed is Sample.IsReversed
    assert Definition.length is not None
    assert Definition.length.value == Sample.DepthMm
    (Driver,) = Document.parameters
    assert Driver.value == Definition.length and Driver.owner_id == Feature.id
    assert Feature.parameter_ids == (Driver.id,)
    OwnerValue = CastValue(
        Mapping[str, object], Driver.attributes["typed_archive_owner"]
    )
    assert OwnerValue["slot"] == "f818.f18"
    assert OwnerValue["value_field"] == "f58"
    CheckSignedBody(Document, Sample)
    if Definition.reversed:
        Target = BytesIO(b"preserved")
        with RaisesError(ValueError, match="offline native measurement receipt"):
            SldprtWriter().write(
                Document,
                Target,
                WriteOptions(
                    values={
                        "final_destination": rf"C:\KitReverseResearch\{CaseName}.SLDPRT"
                    }
                ),
            )
        assert Target.getvalue() == b"preserved" and Target.tell() == 0
