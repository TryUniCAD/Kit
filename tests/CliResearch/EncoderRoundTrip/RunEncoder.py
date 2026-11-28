from pathlib import Path as FilePath
from subprocess import CompletedProcess

from tests.CliResearch.ResearchClient import ResearchCli


# compatibility evidence must cross the installed launcher and candidate research process
def RunEncoder(
    TmpPath: FilePath,
    Application: str,
    SourcePath: FilePath,
    OutputPath: FilePath,
    DepthValue: str = "12.5",
    *,
    LocatorValue: str | None = None,
) -> CompletedProcess[str]:
    LocatorArgs = (
        () if LocatorValue is None else ("--native-locator-directory", LocatorValue)
    )
    return ResearchCli(
        TmpPath,
        "encoder-round-trip",
        "run",
        "--application",
        Application,
        "--source",
        str(SourcePath),
        "--output",
        str(OutputPath),
        "--depth-mm",
        DepthValue,
        *LocatorArgs,
    )
