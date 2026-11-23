from os import getpid as GetProcessId
from pathlib import Path as FilePath
from sys import argv as KArguments, stdout as KOutput
from time import sleep as WaitSeconds


# custody regression needs a living descendant that keeps its exited leaders output pipe open
def RunPipeChild() -> None:
    _ = KOutput.write("retained stdout\n")
    _ = KOutput.flush()
    _ = FilePath(KArguments[1]).write_text(str(GetProcessId()), encoding="utf-8")
    WaitSeconds(120)


if __name__ == "__main__":
    RunPipeChild()
