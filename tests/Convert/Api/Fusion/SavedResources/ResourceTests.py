from dataclasses import replace as ReplaceData
from pathlib import Path as FilePath

from pytest import raises as RaisesError

from convert import open_document as OpenDocument, write_document as WriteDocument
from convert.adapters import AdapterNotFoundError
from convert.adapters.Fusion.Bridge.CheckContract import CheckContract
from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from interchange import CadDocument
from tests.Convert.Api.Fusion.SavedResources.ResourceDoc import ResourceDoc
from tests.Convert.Api.Fusion.SavedResources.ResTree import MakeResTree


# the strict public round trip must preserve nested material resources and their ordered binary contents
def TestResState(TmpPath: FilePath) -> None:
    Expected = ResourceDoc(MakeResTree())
    Payload = EmitParsed(Expected)
    assert ReadDocument(Payload) == Expected
    InputPath = TmpPath / "Resources.f3d"
    _ = InputPath.write_bytes(Payload)
    Document = OpenDocument(InputPath, source_format="f3d")
    assert Document.metadata["fusion.read_only"] is True
    Persisted = TmpPath / "Document.json"
    _ = Persisted.write_text(Document.to_json(), encoding="utf-8")
    Loaded = CadDocument.from_json(Persisted.read_text(encoding="utf-8"))
    assert Loaded == Document
    assert (
        CheckContract(Loaded.metadata["fusion.native_state"], "model", Version=2)
        == Expected
    )
    VerifyResGate(Loaded, TmpPath)


# the native contract with resources must remain read only after eliminating the descriptive flag
def VerifyResGate(Document: CadDocument, TmpPath: FilePath) -> None:
    Unflagged = ReplaceData(
        Document,
        metadata={"fusion.native_state": Document.metadata["fusion.native_state"]},
    )
    Target = TmpPath / "Preserved.f3d"
    Sentinel = b"existing conversion destination"
    _ = Target.write_bytes(Sentinel)
    for Candidate, ErrorType, Diagnostic in (
        (
            Document,
            AdapterNotFoundError,
            r"fusion\.f3d does not support the destination",
        ),
        (Unflagged, ValueError, "Fusion native-state projection is read-only"),
    ):
        with RaisesError(ErrorType, match=Diagnostic):
            _ = WriteDocument(
                Candidate,
                Target,
                destination_format="f3d",
                allow_carrier=False,
                overwrite=True,
            )
        assert Target.read_bytes() == Sentinel
