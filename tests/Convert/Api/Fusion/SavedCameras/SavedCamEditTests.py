from pathlib import Path as FilePath
from typing import cast as CastValue

from tests.Convert.Api.Fusion.SavedCameras.EditCamRequest import EditCamRequest
from tests.Convert.Api.Fusion.SavedCameras.ReadCamViews import ReadCamViews
from tests.Convert.Api.Fusion.SavedCuboid.RunParamStage import RunParamStage
from tests.Convert.Api.Fusion.SavedCuboid.SavedCases import KSavedCases
from tests.Convert.Api.Fusion.SavedCuboid.SavedSource import SavedSource


# a fresh writer must preserve ordered camera ownership and apply the requested position change
def TestCamEdit(TmpPath: FilePath) -> None:
    Payload = SavedSource(KSavedCases[0]).read_bytes()
    Source = TmpPath / "Original.f3d"
    _ = Source.write_bytes(Payload)
    Replay = TmpPath / "Replay"
    Replay.mkdir()
    Request = Replay / "Request.json"
    Prepare = RunParamStage(
        "PrepareRequest.py", Source, Request, ResearchFolder="SavedCameras"
    )
    assert Prepare.returncode == 0, Prepare.stderr
    EditCamRequest(Request)
    _ = Source.replace(TmpPath / "Retained.f3d")
    assert not Source.exists() and tuple(Replay.iterdir()) == (Request,)
    Candidate = Replay / "Candidate.f3d"
    Generate = RunParamStage(
        "GenerateSavedCuboid.py", Request, Candidate, ResearchFolder="SavedCameras"
    )
    assert Generate.returncode == 0, Generate.stderr
    Before = ReadCamViews(Payload)
    After = ReadCamViews(Candidate.read_bytes())
    assert len(Before) == 4 and After[1:] == tuple(reversed(Before[:-1]))
    ViewName, Modify, Fields = Before[-1]
    Expected = dict(Fields)
    Position = CastValue(tuple[str, str, str], Expected["position"])
    Expected["position"] = ((float.fromhex(Position[0]) + 0.25).hex(), *Position[1:])
    assert After[0] == (ViewName, Modify, tuple(Expected.items()))
