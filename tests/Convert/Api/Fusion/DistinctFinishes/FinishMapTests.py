from pathlib import Path as FilePath

from tests.Convert.Api.Fusion.DistinctFinishes.PrepareFinReq import PrepareFinReq
from tests.Convert.Api.Fusion.SavedCuboid.RunParamStage import RunParamStage
from tests.Convert.Api.Fusion.SavedMaterials.CheckMapIntake import CheckMapIntake


# preparing distinct appearances must refuse a design mapping even without graphics
def TestFinishMap(TmpPath: FilePath) -> None:
    Request = PrepareFinReq(TmpPath, 0.65)
    Candidate = Request.with_name("Candidate.f3d")
    Generate = RunParamStage(
        "GenerateSavedCuboid.py",
        Request,
        Candidate,
        ResearchFolder="DistinctMaterialAppearances",
    )
    assert Generate.returncode == 0, Generate.stderr
    CheckMapIntake(
        Candidate,
        "DistinctMaterialAppearances",
        "Distinct material appearance request refused",
    )
