from pathlib import Path as FilePath

from tests.Convert.Api.Fusion.SavedCuboid.RunParamStage import RunParamStage
from tests.Convert.Api.Fusion.SavedCuboid.SavedCases import KSavedCases
from tests.Convert.Api.Fusion.SavedCuboid.SavedSource import SavedSource
from tests.Convert.Api.Fusion.SavedMaterials.CheckMapIntake import CheckMapIntake
from tests.Convert.Api.Fusion.SavedMaterials.WriteRichReq import WriteRichReq


# authored material preparation must preserve the boundary when only design mapping is present
def TestMatMapping(TmpPath: FilePath) -> None:
    Config = TmpPath / "Config.json"
    Prepare = RunParamStage(
        "PrepareRequest.py",
        SavedSource(KSavedCases[0]),
        Config,
        ResearchFolder="SavedConfigEnvelope",
    )
    assert Prepare.returncode == 0, Prepare.stderr
    Request = TmpPath / "Material.json"
    WriteRichReq(Config, Request, True)
    Candidate = TmpPath / "Candidate.f3d"
    Generate = RunParamStage(
        "GenerateSavedCuboid.py",
        Request,
        Candidate,
        ResearchFolder="SavedMaterialProperties",
    )
    assert Generate.returncode == 0, Generate.stderr
    CheckMapIntake(
        Candidate, "SavedMaterialProperties", "Saved cuboid material request refused"
    )
