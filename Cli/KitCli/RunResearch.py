from sys import executable as KPythonPath, platform as KPlatform
from typing import NoReturn

from convert.Commands.CliOptions import CliOptions
from convert.Commands.ResearchTools import KResearchScripts


# research execution must use the selected checkout sdk and preserve downstream process outcomes
def RunResearch(Options: CliOptions) -> NoReturn:
    from subprocess import Popen as StartProcess

    from KitCli.ExitResearch import ExitResearch
    from KitCli.ResearchSignals import ResearchSignals
    from KitCli.WaitResearchMut import WaitResearchMut

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
    if Options.ResearchTool == "supervisor" and KPlatform == "win32":
        raise ValueError("The PR94 research supervisor requires Linux or macOS")
    Arguments = list(Options.ToolArgs)
    if Options.Command == "run":
        Arguments = [*Arguments, "--batch-format", Options.ResearchTool]
    elif Options.ResearchTool in ("solidworks", "fusion", "corpus"):
        if any(
            Value.split("=", 1)[0] in ("--r", "--ro", "--roo", "--root")
            for Value in Arguments
        ):
            raise ValueError("Set research --root once, before the tool name")
        Arguments = ["--root", str(RootPath), *Arguments]
        if Options.ResearchTool in ("solidworks", "fusion"):
            Arguments.append("--native-verify")
    with ResearchSignals() as (ChildProcesses, PendingSignals):
        with StartProcess(
            [KPythonPath, str(ScriptPath), *Arguments],
            start_new_session=KPlatform != "win32",
        ) as ChildProcess:
            ChildProcesses.append(ChildProcess)
            ReturnCode = WaitResearchMut(ChildProcess, PendingSignals)
    ExitResearch(ReturnCode)
