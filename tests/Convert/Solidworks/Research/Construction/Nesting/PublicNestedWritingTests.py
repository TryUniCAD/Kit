from json import loads as LoadJson
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.ArchiveProcess import KRepoRoot


# each call exercises the real stage and observes the complete nested result in a guarded process
def RunNestWrite(CaseValue: str, Route: str, ModeValue: str) -> dict[str, object]:
    Script = (
        KRepoRoot / "re/tooling/sw2026/nested_publication/ProveAuthenticatedNested.py"
    )
    Outcome = RunProcess(
        (
            PythonExec,
            "-I",
            "-B",
            str(Script),
            "--case",
            CaseValue,
            "--route",
            Route,
            "--mode",
            ModeValue,
        ),
        cwd=KRepoRoot,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert Outcome.returncode == 0 and not Outcome.stderr, Outcome.stderr
    Report = CastValue(dict[str, object], LoadJson(Outcome.stdout))
    assert Report["runtime_input_reads"] == Report["native_processes_started"] == 0
    assert Report["passed"] is True and Report["successful_native_flags"] is False
    return Report


# exact single and repeated measured hierarchies preserve native members on both deferred routes
def TestNestWrite() -> None:
    for CaseValue, FilesValue, StreamsValue in (
        ("SdkNestedDimensionedNative01", 3, 34),
        ("SdkRepeatedDimensionedNative01", 4, 44),
    ):
        Registry = RunNestWrite(CaseValue, "registry", "measured")
        Adapter = RunNestWrite(CaseValue, "adapter", "measured")
        assert Registry == Adapter
        assert Adapter["files"] == FilesValue
        assert Adapter["streams"] == StreamsValue


# a wrong claim or physically unqualified destination must leave no partial bundle
def TestNestRefuse() -> None:
    CaseValue = "SdkRepeatedDimensionedNative01"
    for ModeValue in (
        "no-evidence",
        "wrong-native-report",
        "wrong-epoch",
        "wrong-locator",
        "wrong-pose",
        "foreign-scoped-evidence",
        "unqualified-location",
        "strict-deferred",
        "wrong-config",
        "fixed",
        "collision",
        "stream",
    ):
        Report = RunNestWrite(CaseValue, "adapter", ModeValue)
        assert Report["destination_preserved"] is True
        assert Report["stage_writes"] == 0


# final publication errors retain independently owned sibling data
def TestNestUndo() -> None:
    for ModeValue in ("fault", "peer"):
        Report = RunNestWrite("SdkNestedDimensionedNative01", "registry", ModeValue)
        assert Report["destination_preserved"] is True
        assert Report["stage_writes"] == 3
