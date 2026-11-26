from json import dumps as DumpJson
from sys import argv as ArgValues, stderr as KErrorStream

from convert.Commands.MainEntry import MainEntry as RuntimeEntry
from KitCli.RunResearch import RunResearch
from KitCli.RunDefaults.ApplyDefaults import ApplyDefaults


# research process access belongs to the explicit developer command composition
def MainEntry() -> int:
    try:
        ArgValues[1:] = ApplyDefaults(ArgValues[1:])
    except (OSError, ValueError, TypeError, RuntimeError) as Error:
        print(
            DumpJson({"error": type(Error).__name__, "message": str(Error)}),
            file=KErrorStream,
        )
        return 1
    return RuntimeEntry(ResearchRunner=RunResearch)
