from io import BytesIO
from tempfile import TemporaryDirectory
from pathlib import Path as FilePath
import pytest as Pytest
from convert.api.ApiOpen import OpenDocument
from convert.api.ApiWrite import WriteDocument
from convert.adapters.registry.RegistryErrors import AdapterNotFoundError
from tests.Convert.Integration.Fusion.NestReadOnly import NestReadOnly
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.json.Adapter import JsonAdapter


# public and direct writer boundaries must refuse native inspection graphs before touching destinations
@Pytest.mark.parametrize(
    "SourceName",
    (
        "BoundaryCuts/Controls/RequestedCorner.f3d",
        "CircularSpans/Controls/Original/DiscFlip.f3d",
        "CircularSpans/Controls/Original/DiscSymmetric.f3d",
    ),
)
@Pytest.mark.parametrize("Validated", (True, False))
@Pytest.mark.parametrize("Nested", (True, False))
def CheckReadExport(SourceName: str, Validated: bool, Nested: bool) -> None:
    RootPath = FilePath(__file__).resolve().parents[4]
    Document = OpenDocument(RootPath / "re/Fusion/Reconstruction" / SourceName)
    if Nested:
        Document = NestReadOnly(Document)
        assert "fusion.read_only" not in Document.metadata
    IsCut = SourceName.startswith("BoundaryCuts/")
    RejectType = ValueError if IsCut else AdapterNotFoundError
    RejectText = (
        "no qualified geometry evaluator"
        if IsCut
        else "fusion.f3d does not support the destination"
    )
    ExportText = (
        "no qualified geometry evaluator"
        if IsCut
        else "read-only Fusion histories cannot be exported"
    )
    Unsupported = BytesIO()
    with Pytest.raises(RejectType, match=RejectText):
        _ = WriteDocument(Document, Unsupported, DestFormat="fusion.f3d")
    assert Unsupported.getvalue() == b""
    with TemporaryDirectory() as WorkName:
        Target = FilePath(WorkName) / "unqualified.json"
        with Pytest.raises(ValueError, match=ExportText):
            _ = WriteDocument(
                Document, Target, DestFormat="interchange.json", ValidateData=Validated
            )
        assert not Target.exists()
        Stream = BytesIO()
        with Pytest.raises(ValueError, match=ExportText):
            _ = JsonAdapter().Write(Document, Stream, WriteOptions(validate=Validated))
        assert Stream.getvalue() == b""
