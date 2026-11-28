from pathlib import Path as FilePath

from pytest import mark as MarkTests

from tests.Convert.Api.Fusion.SavedCuboid.RunParamStage import RunParamStage
from tests.Convert.Api.Fusion.SavedCuboid.SavedCase import SavedCase
from tests.Convert.Api.Fusion.SavedCuboid.SavedCases import KSavedCases
from tests.Convert.Api.Fusion.SavedCuboid.SavedSource import SavedSource


# both saved appearance families carry a legacy alias that the authored writer cannot express
@MarkTests.parametrize("CaseValue", (KSavedCases[0], KSavedCases[1]))
def TestMatAlias(TmpPath: FilePath, CaseValue: SavedCase) -> None:
    Request = TmpPath / "Request.json"
    Result = RunParamStage(
        "PrepareRequest.py",
        SavedSource(CaseValue),
        Request,
        ResearchFolder="SavedMaterialProperties",
    )
    assert Result.returncode == 1 and not Request.exists()
    assert Result.stderr.strip() == (
        "Saved cuboid material request refused: Saved material compatibility aliases are unsupported "
        "(GenericSchema / _Post2015)"
    )
