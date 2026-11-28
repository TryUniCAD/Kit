from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath
from typing import cast as CastValue

from tests.Convert.Api.Fusion.SavedCuboid.RunParamStage import RunParamStage
from tests.Convert.Api.Fusion.SavedCuboid.SavedCases import KSavedCases
from tests.Convert.Api.Fusion.SavedCuboid.SavedSource import SavedSource


# a request with two model roles wired to the same driver must fail before archive publication
def TestWrongDriver(TmpPath: FilePath) -> None:
    Source = SavedSource(KSavedCases[0])
    Request = TmpPath / "Request.json"
    Prepare = RunParamStage("PrepareRequest.py", Source, Request)
    assert Prepare.returncode == 0, Prepare.stderr
    Payload = CastValue(
        dict[str, object], LoadJson(Request.read_text(encoding="utf-8"))
    )
    Params = CastValue(dict[str, dict[str, object]], Payload["parameters"])
    Params["width"]["driver_role"] = "depth_driver"
    _ = Request.write_text(DumpJson(Payload), encoding="utf-8")
    Candidate = TmpPath / "Candidate.f3d"
    Generate = RunParamStage("GenerateSavedCuboid.py", Request, Candidate)
    assert Generate.returncode == 1 and not Candidate.exists()
    assert Generate.stderr.strip() == (
        "Saved cuboid generation refused: width model must use the exact independent "
        "width_driver name and value"
    )
