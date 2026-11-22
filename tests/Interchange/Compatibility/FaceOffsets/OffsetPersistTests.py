from dataclasses import replace as CopyData
from pathlib import Path as FilePath
from tempfile import TemporaryDirectory
import pytest as Pytest


from interchange.document.Models.DocumentError import DocumentError
from interchange.document.Models.DocumentFilter import FilterDocument
from tests.Interchange.Compatibility.FaceOffsets.BuildOffsetDoc import BuildOffsetDoc


# filtered inspection views must refuse persistence before creating or overwriting any destination
def CheckViewWrite() -> None:
    Filtered = FilterDocument(BuildOffsetDoc(), IncludeBrep=False)
    with TemporaryDirectory() as WorkName:
        Existing = FilePath(WorkName) / "existing.json"
        _ = Existing.write_bytes(b"preserve existing bytes")
        with Pytest.raises(DocumentError, match="inspection-only histories"):
            _ = Filtered.write_json(Existing)
        assert Existing.read_bytes() == b"preserve existing bytes"
        Missing = FilePath(WorkName) / "missing" / "offset.json"
        with Pytest.raises(DocumentError, match="inspection-only histories"):
            _ = Filtered.write_json(Missing)
        assert not Missing.parent.exists()
    with Pytest.raises(DocumentError, match="requires resolved face topology"):
        _ = Filtered.to_json()
    with Pytest.raises(DocumentError, match="requires resolved face topology"):
        _ = Filtered.to_dict()


# encoding failure must leave an existing document and an absent output directory untouched
def CheckBadUnicode() -> None:
    Document = BuildOffsetDoc()
    Document = CopyData(
        Document,
        feature_timeline=Document.feature_timeline[:-1],
        bodies=(
            CopyData(
                Document.bodies[0], final_feature_id=Document.feature_timeline[-2].id
            ),
        ),
        parameters=Document.parameters[:-1],
        selections=(),
        metadata={},
    )
    Document = CopyData(Document, source=CopyData(Document.source, path=chr(0xD800)))
    with TemporaryDirectory() as WorkName:
        Existing = FilePath(WorkName) / "existing.json"
        _ = Existing.write_bytes(b"preserve existing bytes")
        with Pytest.raises(UnicodeEncodeError):
            _ = Document.write_json(Existing)
        assert Existing.read_bytes() == b"preserve existing bytes"
        Missing = FilePath(WorkName) / "missing" / "offset.json"
        with Pytest.raises(UnicodeEncodeError):
            _ = Document.write_json(Missing)
        assert not Missing.parent.exists()
