import json as JsonTools
import sys as SysTools
from importlib import import_module
from pathlib import Path
from typing import Callable, cast as CastValue


# the subprocess invokes the unchanged production collector against caller pinned git objects
def RunContext() -> None:
    SysTools.path.insert(0, SysTools.argv[1])
    ModuleValue = import_module("BuildContext")
    BuildValue = CastValue(Callable[..., str], getattr(ModuleValue, "BuildContext"))
    Arguments = CastValue(
        dict[str, object],
        JsonTools.loads(Path(SysTools.argv[2]).read_text(encoding="utf-8")),
    )
    Content = BuildValue(**Arguments)
    WriteCount = Path(SysTools.argv[3]).write_text(Content, encoding="utf-8")
    assert WriteCount == len(Content)


if __name__ == "__main__":
    RunContext()
