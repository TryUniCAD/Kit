from json import loads as LoadJson
from pathlib import Path as FilePath

from pytest import mark as MarkTests

from convert import open_document as OpenDocument
from convert.Formats.Fusion.MaterialCodec.Models.ColorValue import ColorValue
from tests.Convert.Api.Fusion.DistinctFinishes.PrepareFinReq import PrepareFinReq
from tests.Convert.Api.Fusion.DistinctFinishes.ReadFinishPair import ReadFinishPair
from tests.Convert.Api.Fusion.SavedCuboid.RunParamStage import RunParamStage


# a fresh process must regenerate both independent finishes from the single persisted request
@MarkTests.parametrize("Roughness", (0.65, 0.72))
def TestDualFinish(TmpPath: FilePath, Roughness: float) -> None:
    Request = PrepareFinReq(TmpPath, Roughness)
    Replay = Request.parent
    Candidate = Replay / "Candidate.f3d"
    Generate = RunParamStage(
        "GenerateSavedCuboid.py",
        Request,
        Candidate,
        ResearchFolder="DistinctMaterialAppearances",
    )
    assert Generate.returncode == 0, Generate.stderr
    Payload = Candidate.read_bytes()
    Physical, BodyFace = ReadFinishPair(Payload)
    assert Physical.Finish.Metallic and Physical.Finish.Roughness == 0.35
    assert Physical.Color == ColorValue(0.75, 0.125, 0.375, 1.0)
    Values = {Entry.FieldName: Entry.Value for Entry in BodyFace.Properties}
    assert (
        BodyFace.SchemaName == "PrismOpaqueSchema"
        and Values["surface_roughness"] == Roughness
    )
    Document = OpenDocument(Payload, source_format="f3d")
    assert Document.materials[0].ColorValue == (0.25, 0.5, 0.75, 1.0)
    assert Document.metadata["fusion.read_only"] is True
    Readback = Replay / "Readback.json"
    Project = RunParamStage(
        "PrepareRequest.py",
        Candidate,
        Readback,
        ResearchFolder="DistinctMaterialAppearances",
    )
    assert Project.returncode == 0, Project.stderr
    assert LoadJson(Readback.read_text(encoding="utf-8")) == LoadJson(
        Request.read_text(encoding="utf-8")
    )
