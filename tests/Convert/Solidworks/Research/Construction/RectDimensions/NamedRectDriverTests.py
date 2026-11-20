from json import dumps as DumpJson, loads as LoadJson
from subprocess import run as RunProcess
from sys import executable as PythonExec

from tests.Convert.Solidworks.Research.ArchiveProcess import KRepoRoot
from tests.Convert.Solidworks.Research.Construction.RectDimensions.RectDimRequest import (
    RectDimRequest,
)


# native archive and keywords must preserve the same three separately owned driving labels in a guarded process
def TestRectDrivers() -> None:
    RequestValue = RectDimRequest("sdk named rectangle", False)
    RequestValue["driver_names"] = ["PanelWidth", "PanelHeight", "SolidDepth"]
    Outcome = RunProcess(
        [
            PythonExec,
            "-I",
            "-B",
            str(KRepoRoot / "re/tooling/sw2026/ProbeNamedRectangleDrivers.py"),
            str(KRepoRoot),
        ],
        input=DumpJson(RequestValue),
        text=True,
        capture_output=True,
        check=False,
        timeout=60,
    )
    assert Outcome.returncode == 0, Outcome.stderr
    Receipt = LoadJson(Outcome.stdout)
    assert Receipt["passed"] and Receipt["runtime_input_reads"] == 0
