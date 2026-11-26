from pathlib import Path as FilePath

from convert import open_document as OpenDocument
from tests.Convert.Api.Fusion.DistinctFinishes.PrepareFinReq import PrepareFinReq
from tests.Convert.Api.Fusion.SavedCuboid.RunParamStage import RunParamStage


# a single assigned appearance remains distinct from the separate two finish request contract
def TestSharedFin(TmpPath: FilePath) -> None:
    _ = PrepareFinReq(TmpPath, 0.65)
    Candidate = TmpPath / "Single.f3d"
    Generate = RunParamStage(
        "GenerateSavedCuboid.py",
        TmpPath / "Material.json",
        Candidate,
        ResearchFolder="SavedMaterialProperties",
    )
    assert Generate.returncode == 0, Generate.stderr
    assert OpenDocument(Candidate).metadata["fusion.read_only"] is True
    Request = TmpPath / "Distinct.json"
    Project = RunParamStage(
        "PrepareRequest.py",
        Candidate,
        Request,
        ResearchFolder="DistinctMaterialAppearances",
    )
    assert Project.returncode == 1 and not Request.exists()
    assert Project.stderr.strip() == (
        "Distinct material appearance request refused: Body and physical aspect appearance must be distinct assets"
    )
