from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.ArchiveProcess import KRepoRoot
from tests.Convert.Solidworks.Research.Construction.Nesting.MakeNestedCase import (
    MakeNestedCase,
)


# each public nested route must stage the complete owned hierarchy in a guarded process
def CheckPublicNested(
    Request: dict[str, object], Area: FilePath, Route: str, Mode: str
) -> dict[str, object]:
    Area.mkdir()
    Script = (
        KRepoRoot / "re/tooling/sw2026/nested_publication/MeasurePublicNestedWriting.py"
    )
    Outcome = RunProcess(
        (PythonExec, "-I", "-B", str(Script), "--worker", str(Area.resolve())),
        input=DumpJson({"request": Request, "route": Route, "mode": Mode}),
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert Outcome.returncode == 0 and not Outcome.stderr, Outcome.stderr
    Report = CastValue(dict[str, object], LoadJson(Outcome.stdout))
    assert Report["runtime_input_file_reads"] == 0
    return Report


# both actual public adapters must transfer the same native bundle and refuse an unsupported placement without publishing
def TestPublicNestedWriting(TmpPath: FilePath) -> None:
    Request = MakeNestedCase(True, r"C:\KitSdkNested")
    Registry = CheckPublicNested(Request, TmpPath / "registry", "registry", "fresh")
    Adapter = CheckPublicNested(Request, TmpPath / "adapter", "adapter", "fresh")
    assert Registry == Adapter
    assert Adapter["vendor_loadable"] is Adapter["application_usable"] is True
    Files = CastValue(dict[str, object], Adapter["files"])
    assert set(Files) == {
        "SdkFrame.SLDASM",
        "SdkModule.SLDASM",
        "SdkNestedPlate.SLDPRT",
        "SdkGaugePlate.SLDPRT",
    }
    Failure = CheckPublicNested(Request, TmpPath / "fixed", "adapter", "fixed")
    assert Failure["refused"] == "AdapterNotFoundError"
    assert Failure["output_unchanged"] is True
