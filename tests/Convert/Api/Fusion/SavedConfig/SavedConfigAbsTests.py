from json import loads as LoadJson
from pathlib import Path as FilePath
from typing import cast as CastValue

from tests.Convert.Api.Fusion.SavedConfig.ReadConfigRoles import ReadConfigRoles
from tests.Convert.Api.Fusion.SavedCuboid.RunParamStage import RunParamStage
from tests.Convert.Api.Fusion.SavedCuboid.RunSnapBuild import RunSnapBuild


# an archive without configuration members must project deliberate absence at the preparation boundary
def TestAbsentConf(TmpPath: FilePath) -> None:
    Payload = RunSnapBuild(TmpPath, "Cuboid without configuration", 15.9)
    assert ReadConfigRoles(Payload) == ()
    Source = TmpPath / "Cuboid.f3d"
    Request = TmpPath / "Prepared.json"
    Prepare = RunParamStage(
        "PrepareRequest.py", Source, Request, ResearchFolder="SavedConfigEnvelope"
    )
    assert Prepare.returncode == 0, Prepare.stderr
    Result = CastValue(dict[str, object], LoadJson(Request.read_text(encoding="utf-8")))
    assert Result["configuration_parts"] == []
