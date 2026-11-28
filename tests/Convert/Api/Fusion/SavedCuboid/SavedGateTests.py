from dataclasses import replace as ReplaceData
from pathlib import Path as FilePath

from pytest import mark as MarkTests, raises as RaisesError

from convert import open_document as OpenDocument, write_document as WriteDocument
from convert.adapters import AdapterNotFoundError
from interchange import CadDocument
from tests.Convert.Api.Fusion.SavedCuboid.SavedCases import KSavedCases
from tests.Convert.Api.Fusion.SavedCuboid.SavedSource import SavedSource


# reader qualification must not silently promote unmeasured native state into public writable support
@MarkTests.parametrize("StripFlag", (False, True))
def TestSavedGate(TmpPath: FilePath, StripFlag: bool) -> None:
    Original = OpenDocument(SavedSource(KSavedCases[1]))
    Document = CadDocument.from_json(Original.to_json())
    if StripFlag:
        Document = ReplaceData(
            Document,
            metadata={"fusion.native_state": Document.metadata["fusion.native_state"]},
        )
    Target = TmpPath / "Preserved.f3d"
    _ = Target.write_bytes(b"preserved saved cuboid destination")
    with RaisesError((ValueError, AdapterNotFoundError)):
        _ = WriteDocument(
            Document,
            Target,
            destination_format="f3d",
            allow_carrier=False,
            overwrite=True,
        )
    assert Target.read_bytes() == b"preserved saved cuboid destination"
    assert tuple(TmpPath.iterdir()) == (Target,)
