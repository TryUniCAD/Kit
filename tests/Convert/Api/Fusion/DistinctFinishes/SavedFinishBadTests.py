from pathlib import Path as FilePath

from tests.Convert.Api.Fusion.SavedCuboid.RunParamStage import RunParamStage
from tests.Convert.Api.Fusion.SavedCuboid.SavedCases import KSavedCases
from tests.Convert.Api.Fusion.SavedCuboid.SavedSource import SavedSource


# captured compatibility aliases must not be flattened into a modern appearance request
def TestFinishAlias(TmpPath: FilePath) -> None:
    Request = TmpPath / "Request.json"
    Source = SavedSource(KSavedCases[0])
    Result = RunParamStage(
        "PrepareRequest.py",
        Source,
        Request,
        ResearchFolder="DistinctMaterialAppearances",
    )
    assert Result.returncode == 1 and not Request.exists()
    assert Result.stderr.strip() == (
        "Distinct material appearance request refused: Saved material compatibility aliases "
        "are unsupported (GenericSchema / _Post2015)"
    )
