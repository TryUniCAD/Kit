from pathlib import Path as FilePath

from pytest import approx as NearValue, mark as MarkTests

from convert import open_document as OpenDocument
from convert.adapters.Fusion.Bridge.CheckContract import CheckContract
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from interchange import CadDocument
from tests.Convert.Api.Fusion.SavedCuboid.RunSnapBuild import RunSnapBuild


# native snapshot construction must preserve requested document metadata and live feature bindings
@MarkTests.parametrize("Height", (15.9, 24.7))
def TestGenSnapshot(TmpPath: FilePath, Height: float) -> None:
    Title = "Independent snapshot cuboid"
    Payload = RunSnapBuild(TmpPath, Title, Height)
    Model = ReadDocument(Payload)
    Document = OpenDocument(Payload, source_format="f3d")
    (Config,) = Document.configurations
    assert Config.name == Title
    assert dict(Model.Asset.Properties)["documentName"] == Title
    assert len(Model.Snapshots) == 1 and Model.Graphics is None
    assert Document.metadata["fusion.read_only"] is True
    assert CheckContract(Document.metadata["fusion.native_state"], "model", 2) == Model
    assert [Feature.name for Feature in Document.feature_timeline] == [
        "Plate Profile",
        "Pad",
    ]
    assert {Param.name: Param.value.value for Param in Document.parameters}[
        "padHeight"
    ] == NearValue(Height)
    assert Document.bodies[0].topology.volume == NearValue(21.3 * 33.2 * Height)
    Target = TmpPath / "Persisted.json"
    _ = Target.write_text(Document.to_json(), encoding="utf-8")
    assert CadDocument.from_json(Target.read_text(encoding="utf-8")) == Document
