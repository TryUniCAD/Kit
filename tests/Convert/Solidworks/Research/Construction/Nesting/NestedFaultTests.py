from json import dumps as DumpJson
from subprocess import run as RunProcess
from sys import executable as PythonExec
from tests.Convert.Solidworks.Research.ArchiveProcess import KRepoRoot
from tests.Convert.Solidworks.Research.Construction.Nesting.NestedFaultCase import (
    NestedFaultCase,
)


# unsupported recursive inputs must fail at a real guarded construction boundary without emitting a partial native bundle
def TestNestedFault() -> None:
    for FaultValue in (
        "cycle",
        "missing",
        "duplicate",
        "unreachable",
        "foreign",
        "name",
        "frame",
    ):
        Outcome = RunProcess(
            (
                PythonExec,
                "-I",
                "-B",
                str(KRepoRoot / "re/tooling/sw2026/SdkNestedAssemblyProcess.py"),
                str(KRepoRoot),
            ),
            cwd=KRepoRoot,
            input=DumpJson(NestedFaultCase(FaultValue)),
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
        )
        assert Outcome.returncode != 0 and not Outcome.stdout
        assert "ValueError" in Outcome.stderr
        assert "PermissionError" not in Outcome.stderr
