from sys import executable as KPythonPath, stderr as KErrorStream
from typing import NoReturn

from convert.Commands.CliOptions import CliOptions


# research execution must use the selected checkout sdk and preserve downstream process outcomes
def RunResearch(Options: CliOptions) -> NoReturn:
    from KitCli.ExitResearch import ExitResearch
    from KitCli.ResearchArgs import ResearchArgs
    from KitCli.ResearchScript import ResearchScript
    from KitCli.ResearchSignals import ResearchSignals
    from KitCli.StartResearch import StartResearch
    from KitCli.WaitResearchMut import WaitResearchMut

    RootPath, ScriptPath = ResearchScript(Options)
    Arguments, LegacyReader = ResearchArgs(Options, RootPath, ScriptPath)
    OwnWindows = Options.ResearchTool == "supervisor"
    with ResearchSignals(OwnWindows) as (
        ChildProcesses,
        PendingSignals,
    ):
        with StartResearch(
            [KPythonPath, str(ScriptPath), *Arguments], OwnWindows
        ) as ChildProcess:
            ChildProcesses.append(ChildProcess)
            ReturnCode = WaitResearchMut(ChildProcess, PendingSignals)
    if Options.Offline:
        print(
            "kit: offline decoding only; native verification pending; vendor acceptance not established",
            file=KErrorStream,
        )
    if LegacyReader and ReturnCode in (0, 3):
        print(
            "kit: decoding artifacts were preserved; native verification was not performed because the selected checkout lacks the verification capability; update that trusted checkout to enable verification",
            file=KErrorStream,
        )
        if ReturnCode == 0:
            ReturnCode = 4
    ExitResearch(ReturnCode)
