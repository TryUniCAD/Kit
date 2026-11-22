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
        with Pytest.raises(DocumentError, match="requires resolved face topology"):
            _ = Filtered.write_json(Existing)
        assert Existing.read_bytes() == b"preserve existing bytes"
        Missing = FilePath(WorkName) / "missing" / "offset.json"
        with Pytest.raises(DocumentError, match="requires resolved face topology"):
            _ = Filtered.write_json(Missing)
        assert not Missing.parent.exists()
    with Pytest.raises(DocumentError, match="requires resolved face topology"):
        _ = Filtered.to_json()
    with Pytest.raises(DocumentError, match="requires resolved face topology"):
        _ = Filtered.to_dict()
