from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue

from convert import open_document as OpenDocument
from tests.Convert.Solidworks.Research.ArchiveProcess import KRepoRoot
from tests.Convert.Solidworks.Research.Construction.Nesting.MakeNestedCase import (
    MakeNestedCase,
)


# each public nested route must stage the complete owned hierarchy in a guarded process
def CheckNestWrite(
    Request: dict[str, object], Folder: FilePath, Route: str, ModeValue: str
) -> dict[str, object]:
    Folder.mkdir()
    Script = (
        KRepoRoot / "re/tooling/sw2026/nested_publication/MeasurePublicNestedWriting.py"
    )
    Outcome = RunProcess(
        (PythonExec, "-I", "-B", str(Script), "--worker", str(Folder.resolve())),
        input=DumpJson({"request": Request, "route": Route, "mode": ModeValue}),
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
def TestNestWrite(TmpPath: FilePath) -> None:
    Request = MakeNestedCase(True, r"C:\KitSdkNested")
    Registry = CheckNestWrite(Request, TmpPath / "registry", "registry", "fresh")
    Adapter = CheckNestWrite(Request, TmpPath / "adapter", "adapter", "fresh")
    assert Registry == Adapter
    assert Adapter["vendor_loadable"] is Adapter["application_usable"] is True
    Files = CastValue(dict[str, object], Adapter["files"])
    assert set(Files) == {
        "SdkFrame.SLDASM",
        "SdkModule.SLDASM",
        "SdkNestedPlate.SLDPRT",
        "SdkGaugePlate.SLDPRT",
    }
    Readback = OpenDocument(TmpPath / "registry" / "SdkFrame.SLDASM")
    Assembly = Readback.assembly
    assert Assembly is not None
    Definitions = {Value.name: Value for Value in Assembly.definitions}
    assert set(Definitions) == {
        "SdkFrame",
        "SdkModule",
        "SdkNestedPlate",
        "SdkGaugePlate",
    }
    assert tuple(
        Value.order for Value in Assembly.GetChildren(Definitions["SdkFrame"].id)
    ) == (0, 1, 2)
    assert tuple(
        Value.order for Value in Assembly.GetChildren(Definitions["SdkModule"].id)
    ) == (0, 1)
    Failure = CheckNestWrite(Request, TmpPath / "fixed", "adapter", "fixed")
    assert Failure["refused"] == "AdapterNotFoundError"
    assert Failure["output_unchanged"] is True
