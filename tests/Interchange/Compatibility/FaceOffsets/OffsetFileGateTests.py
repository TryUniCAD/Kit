from pathlib import Path as FilePath
from tempfile import TemporaryDirectory
import pytest as Pytest

from convert.api.ApiOpen import OpenDocument
from interchange.document.Models.DocumentError import DocumentError
from tests.Interchange.Compatibility.FaceOffsets.BuildOffsetDoc import BuildOffsetDoc


# public file persistence must refuse real decoded inspection histories without mutating an existing document
@Pytest.mark.parametrize("SourceName", ("Corner", "Circle", "Offset"))
def CheckFileGate(SourceName: str) -> None:
    RootPath = FilePath(__file__).resolve().parents[4]
    if SourceName == "Offset":
        Document = BuildOffsetDoc()
    else:
        Relative = (
            "BoundaryCuts/Controls/RequestedCorner.f3d"
            if SourceName == "Corner"
            else "CircularSpans/Controls/Original/DiscFlip.f3d"
        )
        Document = OpenDocument(RootPath / "re/Fusion/Reconstruction" / Relative)
    assert Document.to_json()
    with TemporaryDirectory() as WorkName:
        Target = FilePath(WorkName) / "existing.json"
        _ = Target.write_bytes(b"preserve existing bytes")
        with Pytest.raises(DocumentError, match="inspection-only histories"):
            _ = Document.write_json(Target)
        assert Target.read_bytes() == b"preserve existing bytes"
