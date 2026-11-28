from dataclasses import replace as CopyData
from io import BytesIO
from pathlib import Path as FilePath
from tempfile import TemporaryDirectory
import pytest as Pytest

from convert.api.ApiOpen import OpenDocument
from convert.api.ApiWrite import WriteDocument
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.json.Adapter import JsonAdapter
from interchange.document.Models.DocumentModel import CadDocument
from interchange.document.Models.DocumentError import DocumentError
from interchange.Features.Distance.DistanceCut import DistanceCut
from tests.Convert.Integration.Fusion.NestReadOnly import NestReadOnly


# a decoded neutral cut retains topology while a changed live distance makes evaluation mandatory before export
@Pytest.mark.parametrize("Validated", (True, False))
@Pytest.mark.parametrize("Nested", (True, False))
def CheckCutExport(Validated: bool, Nested: bool) -> None:
    RootPath = FilePath(__file__).resolve().parents[5]
    Document = OpenDocument(
        RootPath / "re/Fusion/Reconstruction/BoundaryCuts/Controls/RequestedCorner.f3d"
    )
    Definition = Document.feature_timeline[-1].definition
    assert isinstance(Definition, DistanceCut)
    ParamId = Definition.Extrusion.AlongParameterId
    Parameters = tuple(
        (
            CopyData(Value, value=CopyData(Value.value, value=1.0))
            if Value.id == ParamId
            else Value
        )
        for Value in Document.parameters
    )
    Document = CopyData(Document, parameters=Parameters, metadata={})
    Document = CadDocument.from_json(Document.to_json())
    if Nested:
        Document = NestReadOnly(Document)
    Stream = BytesIO()
    with Pytest.raises(
        ValueError, match="distance cut .*no qualified geometry evaluator"
    ):
        _ = WriteDocument(
            Document, Stream, DestFormat="interchange.json", ValidateData=Validated
        )
    assert Stream.getvalue() == b""
    with Pytest.raises(
        ValueError, match="distance cut .*no qualified geometry evaluator"
    ):
        _ = JsonAdapter().Write(Document, Stream, WriteOptions(validate=Validated))
    assert Stream.getvalue() == b""
    with TemporaryDirectory() as WorkName:
        Target = FilePath(WorkName) / "existing.json"
        _ = Target.write_bytes(b"preserve existing bytes")
        with Pytest.raises(DocumentError, match="inspection-only histories"):
            _ = Document.write_json(Target)
        assert Target.read_bytes() == b"preserve existing bytes"
