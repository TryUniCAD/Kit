from os import getpid as GetProcessId
from sys import argv as KArguments, stdout as KOutput
from time import sleep as WaitSeconds

from convert.Security.PathBoundary import ResolveTemp


# custody regression needs a living descendant that keeps its exited leaders output pipe open
def RunPipeChild() -> None:
    _ = KOutput.write("retained stdout\n")
    _ = KOutput.flush()
    _ = ResolveTemp(KArguments[1]).write_text(str(GetProcessId()), encoding="utf-8")
    WaitSeconds(120)


if __name__ == "__main__":
    RunPipeChild()
