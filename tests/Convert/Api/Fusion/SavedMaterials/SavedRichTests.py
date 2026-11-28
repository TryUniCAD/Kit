from json import loads as LoadJson
from pathlib import Path as FilePath

from pytest import mark as MarkTests

from convert import open_document as OpenDocument
from tests.Convert.Api.Fusion.SavedCuboid.RunParamStage import RunParamStage
from tests.Convert.Api.Fusion.SavedCuboid.SavedCases import KSavedCases
from tests.Convert.Api.Fusion.SavedCuboid.SavedSource import SavedSource
from tests.Convert.Api.Fusion.SavedMaterials.CheckRichTrial import CheckRichTrial
from tests.Convert.Api.Fusion.SavedMaterials.ReadBodyMatSpec import ReadBodyMatSpec
from tests.Convert.Api.Fusion.SavedMaterials.WriteRichReq import WriteRichReq


# persisted authored material changes must regenerate without access to the staged original path
@MarkTests.parametrize("IsMetal", (False, True))
def TestRichMat(TmpPath: FilePath, IsMetal: bool) -> None:
    Source = TmpPath / "Original.f3d"
    _ = Source.write_bytes(SavedSource(KSavedCases[0 if IsMetal else 1]).read_bytes())
    BasePath = TmpPath / "Config.json"
    Prepare = RunParamStage(
        "PrepareRequest.py", Source, BasePath, ResearchFolder="SavedConfigEnvelope"
    )
    assert Prepare.returncode == 0, Prepare.stderr
    Replay = TmpPath / "Replay"
    Replay.mkdir()
    Request = Replay / "Request.json"
    WriteRichReq(BasePath, Request, IsMetal)
    _ = Source.replace(TmpPath / "Retained.f3d")
    assert not Source.exists() and tuple(Replay.iterdir()) == (Request,)
    Candidate = Replay / "Candidate.f3d"
    Generate = RunParamStage(
        "GenerateSavedCuboid.py",
        Request,
        Candidate,
        ResearchFolder="SavedMaterialProperties",
    )
    assert Generate.returncode == 0, Generate.stderr
    Payload = Candidate.read_bytes()
    Material, HasDefault = ReadBodyMatSpec(Payload)
    CheckRichTrial(Material, IsMetal)
    assert HasDefault is IsMetal
    assert (
        OpenDocument(Payload, source_format="f3d").metadata["fusion.read_only"] is True
    )
    Readback = Replay / "Readback.json"
    Project = RunParamStage(
        "PrepareRequest.py",
        Candidate,
        Readback,
        ResearchFolder="SavedMaterialProperties",
    )
    assert Project.returncode == 0, Project.stderr
    assert LoadJson(Readback.read_text(encoding="utf-8")) == LoadJson(
        Request.read_text(encoding="utf-8")
    )
