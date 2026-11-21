from sys import executable as KPythonPath, platform as KPlatform, stderr as KErrorStream
from typing import NoReturn

from convert.Commands.CliOptions import CliOptions


# research execution must use the selected checkout sdk and preserve downstream process outcomes
def RunResearch(Options: CliOptions) -> NoReturn:
    from subprocess import Popen as StartProcess

    from KitCli.ExitResearch import ExitResearch
    from KitCli.ResearchArgs import ResearchArgs
    from KitCli.ResearchScript import ResearchScript
    from KitCli.ResearchSignals import ResearchSignals
    from KitCli.WaitResearchMut import WaitResearchMut

    RootPath, ScriptPath = ResearchScript(Options)
    Arguments, LegacyReader = ResearchArgs(Options, RootPath, ScriptPath)
    with ResearchSignals() as (ChildProcesses, PendingSignals):
        with StartProcess(
            [KPythonPath, str(ScriptPath), *Arguments],
            start_new_session=KPlatform != "win32",
        ) as ChildProcess:
            ChildProcesses.append(ChildProcess)
            ReturnCode = WaitResearchMut(ChildProcess, PendingSignals)
    if LegacyReader and ReturnCode in (0, 3):
        print(
            "kit: decoding artifacts were preserved; native verification was not performed because the selected checkout lacks the verification capability; update that trusted checkout to enable verification",
            file=KErrorStream,
        )
        if ReturnCode == 0:
            ReturnCode = 4
    ExitResearch(ReturnCode)
