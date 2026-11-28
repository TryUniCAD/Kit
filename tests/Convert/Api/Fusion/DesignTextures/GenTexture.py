from pathlib import Path as FilePath

from tests.Convert.Api.Fusion.DesignTextures.RunTexture import RunTexture


# generation must pass through the public research command and report success
def GenTexture(Request: FilePath, Candidate: FilePath) -> None:
    Result = RunTexture("GenerateSavedCuboid.py", Request, Candidate)
    assert Result.returncode == 0, Result.stderr
