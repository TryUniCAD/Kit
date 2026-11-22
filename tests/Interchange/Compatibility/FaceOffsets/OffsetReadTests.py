import json as JsonLib
from io import BytesIO
from collections.abc import MutableMapping
from pathlib import Path as FilePath
from tempfile import TemporaryDirectory
import pytest as Pytest

from convert.api.ApiOpen import OpenDocument
from interchange.document.Models.DocumentError import DocumentError
from tests.Interchange.Compatibility.FaceOffsets.BuildOffsetDoc import BuildOffsetDoc


# filtered public reads retain validated feature history without pretending the omitted geometry was absent in the source
@Pytest.mark.parametrize("ConfigName", (None, "default"))
def CheckOffsetView(ConfigName: str | None) -> None:
    Document = BuildOffsetDoc()
    with TemporaryDirectory() as WorkName:
        Source = FilePath(WorkName) / "offset.json"
        _ = Source.write_text(Document.to_json(), encoding="utf-8")
        Filtered = OpenDocument(
            Source,
            SourceFormat="interchange.json",
            IncludeBrep=False,
            Configuration=ConfigName,
        )
    assert Filtered.brep is None
    assert Filtered.feature_timeline == Document.feature_timeline
    assert Filtered.metadata["kit.omitted_brep"] is True
    assert not isinstance(Filtered.metadata, MutableMapping)
    Filtered.assert_valid()


# raw json must reject absent malformed or falsely declared filtered topology before returning a document
@Pytest.mark.parametrize("Failure", ("missing", "wrong-type", "forged"))
@Pytest.mark.parametrize("ConfigName", (None, "default"))
def CheckOffsetJson(Failure: str, ConfigName: str | None) -> None:
    WireValue = JsonLib.loads(BuildOffsetDoc().to_json())
    WireValue["brep"] = "missing" if Failure == "wrong-type" else None
    if Failure == "forged":
        WireValue["metadata"]["kit.omitted_brep"] = True
    Expected = (
        "B-rep must be a BrepModel"
        if Failure == "wrong-type"
        else "requires resolved face topology"
    )
    with Pytest.raises(DocumentError, match=Expected):
        _ = OpenDocument(
            BytesIO(JsonLib.dumps(WireValue).encode("utf-8")),
            SourceFormat="interchange.json",
            Configuration=ConfigName,
        )
