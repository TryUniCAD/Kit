from hashlib import sha256 as HashBytes
from pathlib import Path as FilePath

from pytest import mark as MarkTests

from convert import open_document as OpenDocument
from tests.Convert.Api.Fusion.SavedCameras.ReadCamViews import ReadCamViews
from tests.Convert.Api.Fusion.SavedCuboid.ReadParamSem import ReadParamSem
from tests.Convert.Api.Fusion.SavedCuboid.RunParamStage import RunParamStage
from tests.Convert.Api.Fusion.SavedCuboid.SavedCase import SavedCase
from tests.Convert.Api.Fusion.SavedCuboid.SavedCases import KSavedCases
from tests.Convert.Api.Fusion.SavedCuboid.SavedSource import SavedSource


# persisted camera roles must survive a fresh generation process for populated and empty rosters
@MarkTests.parametrize(
    "CaseValue,ViewCount", ((KSavedCases[0], 4), (KSavedCases[1], 0))
)
def TestSavedCam(TmpPath: FilePath, CaseValue: SavedCase, ViewCount: int) -> None:
    Payload = SavedSource(CaseValue).read_bytes()
    assert HashBytes(Payload).hexdigest() == CaseValue.DigestValue
    Source = TmpPath / "Original.f3d"
    _ = Source.write_bytes(Payload)
    Replay = TmpPath / "Replay"
    Replay.mkdir()
    Request = Replay / "Request.json"
    Prepare = RunParamStage(
        "PrepareRequest.py", Source, Request, ResearchFolder="SavedCameras"
    )
    assert Prepare.returncode == 0, Prepare.stderr
    _ = Source.replace(TmpPath / "Retained.f3d")
    assert not Source.exists() and tuple(Replay.iterdir()) == (Request,)
    Candidate = Replay / "Candidate.f3d"
    Generate = RunParamStage(
        "GenerateSavedCuboid.py", Request, Candidate, ResearchFolder="SavedCameras"
    )
    assert Generate.returncode == 0, Generate.stderr
    Generated = Candidate.read_bytes()
    Views = ReadCamViews(Payload)
    assert len(Views) == ViewCount and ReadCamViews(Generated) == Views
    After = OpenDocument(Generated, source_format="f3d")
    assert ReadParamSem(After) == ReadParamSem(
        OpenDocument(Payload, source_format="f3d")
    )
    assert After.metadata["fusion.read_only"] is True
