from pathlib import Path as FilePath
from subprocess import CompletedProcess as ProcessResult

from tests.Convert.Api.Fusion.SavedCuboid.RunParamStage import RunParamStage


# exercise the normal texture placement command in a fresh process
def RunTexture(
    NameValue: str, InputPath: FilePath, OutputPath: FilePath
) -> ProcessResult[str]:
    return RunParamStage(
        NameValue, InputPath, OutputPath, ResearchFolder="DesignTexturePlacement"
    )
