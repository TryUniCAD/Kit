from pathlib import Path as FilePath
from typing import cast as CastValue
from pytest import mark as MarkTests, raises as RaisesError
from convert import open_document as OpenDocument
from convert.adapters.Fusion.State.DecodeState import DecodeState
from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from interchange import CadDocument
from tests.Convert.Api.Fusion.SavedCuboid.SavedCases import KSavedCases
from tests.Convert.Api.Fusion.SavedCuboid.SavedSource import SavedSource
from tests.Convert.Api.Fusion.SavedCuboid.MoveSavedPoint import MoveSavedPoint


# saved caption movement must survive strict reading and json with its sketch geometry intact
@MarkTests.parametrize(
    ("AxisName", "PointName", "CoordinateName", "Accepts"),
    (
        ("x", "textPosition", "x", True),
        ("y", "textPosition", "y", True),
        ("x", "textPosition", "y", False),
        ("x", "textPosition", "z", False),
        ("x", "DimEndPoint", "x", False),
    ),
)
def TestDimCaption(
    TmpPath: FilePath,
    AxisName: str,
    PointName: str,
    CoordinateName: str,
    Accepts: bool,
) -> None:
    Source = SavedSource(KSavedCases[0]).read_bytes()
    Model = ReadDocument(Source)
    Changed = MoveSavedPoint(Model, AxisName, PointName, CoordinateName)
    assert Changed != Model
    Payload = EmitParsed(Changed)
    if not Accepts:
        with RaisesError(
            ValueError, match="saved geometry or parameter values disagree"
        ):
            _ = OpenDocument(Payload, source_format="f3d", strict=True)
        return
    Original = OpenDocument(Source, source_format="f3d", strict=True)
    Document = OpenDocument(Payload, source_format="f3d", strict=True)
    assert Document.sketches == Original.sketches
    assert Document.parameters == Original.parameters
    assert Document.bodies == Original.bodies
    assert Document.feature_timeline == Original.feature_timeline
    assert Document.metadata["fusion.read_only"] is True
    Target = TmpPath / "PersistedCaption.json"
    _ = Target.write_text(Document.to_json(), encoding="utf-8")
    Reloaded = CadDocument.from_json(Target.read_text(encoding="utf-8"))
    assert Reloaded == Document
    Contract = CastValue(dict[str, object], Reloaded.metadata["fusion.native_state"])
    assert DecodeState(Contract["model"]) == Changed
