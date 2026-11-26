from pathlib import Path as FilePath

from tests.Convert.Api.Fusion.DistinctFinishes.WriteDistinct import WriteDistinct
from tests.Convert.Api.Fusion.SavedCuboid.RunParamStage import RunParamStage
from tests.Convert.Api.Fusion.SavedCuboid.SavedCases import KSavedCases
from tests.Convert.Api.Fusion.SavedCuboid.SavedSource import SavedSource
from tests.Convert.Api.Fusion.SavedMaterials.WriteRichReq import WriteRichReq


# the generation folder holds only the explicit request when replay starts
def PrepareFinReq(Folder: FilePath, Roughness: float) -> FilePath:
    Source = Folder / "Original.f3d"
    _ = Source.write_bytes(SavedSource(KSavedCases[0]).read_bytes())
    Config = Folder / "Config.json"
    Result = RunParamStage(
        "PrepareRequest.py", Source, Config, ResearchFolder="SavedConfigEnvelope"
    )
    assert Result.returncode == 0, Result.stderr
    Material = Folder / "Material.json"
    WriteRichReq(Config, Material, True)
    Replay = Folder / "Replay"
    Replay.mkdir()
    Request = Replay / "Request.json"
    WriteDistinct(Material, Request, Roughness)
    _ = Source.replace(Folder / "Retained.f3d")
    assert not Source.exists() and tuple(Replay.iterdir()) == (Request,)
    return Request
