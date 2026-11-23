import sys as System
from pathlib import Path as FilePath

from convert.Commands.CliOptions import CliOptions
from convert.Commands.ResearchTools import KResearchScripts
from KitCli.CanWindowsStop import CanWindowsStop


# trusted checkout validation keeps research execution inside the selected source tree
def ResearchScript(Options: CliOptions) -> tuple[FilePath, FilePath]:
    if Options.ResearchRoot is None:
        raise ValueError("Research requires --root pointing to a trusted PR94 checkout")
    RootPath = Options.ResearchRoot.expanduser().resolve()
    ScriptName = (
        "InferenceGrid/RunFeatureCatalogue.py"
        if Options.Command == "run"
        else KResearchScripts.get(Options.ResearchTool)
    )
    if ScriptName is None:
        raise ValueError("Unknown research tool")
    ScriptPath = RootPath / "re" / "automation" / ScriptName
    if (
        not (RootPath / ".git").exists()
        or not (RootPath / "src" / "convert").is_dir()
        or not ScriptPath.is_file()
    ):
        raise ValueError(
            "Selected checkout does not contain the requested PR94 research tool"
        )
    if not ScriptPath.resolve().is_relative_to(RootPath):
        raise ValueError("Research script must remain inside the selected checkout")
    if (
        System.platform == "win32"
        and Options.ResearchTool == "supervisor"
        and not CanWindowsStop(ScriptPath)
    ):
        raise ValueError(
            "Selected supervisor lacks Windows console shutdown protocol 1; "
            + "update the selected --root research checkout before running it"
        )
    return RootPath, ScriptPath
