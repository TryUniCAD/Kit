from json import loads as DecodeJson
from pathlib import Path as FilePath
from subprocess import PIPE as PipeOutput, Popen as OpenProcess, run as RunProcess
from sys import platform as HostPlatform

from pytest import mark as TestMark

from tests.Research.SupervisorClient import KRepoRoot
from tests.Research.Windows.Readback.WarmProgress import KColdCompileSeconds


# independent powershell processes must reuse only assemblies built from identical source bytes
@TestMark.skipif(HostPlatform != "win32", reason="Windows PowerShell assembly boundary")
def CheckCacheReuse(TmpPath: FilePath) -> None:
    SourcePath = TmpPath / "Progress.cs"
    SourceBytes = (
        KRepoRoot / "re/automation/CaptureTools/SolidWorksAuthoring/ReadbackProgress.cs"
    ).read_bytes()
    _ = SourcePath.write_bytes(SourceBytes)
    CachePath = TmpPath / "Cache"
    Command = [
        "powershell.exe",
        "-NoProfile",
        "-NonInteractive",
        "-File",
        str(FilePath(__file__).with_name("ProgressFixture.ps1")),
        "-Source",
        str(SourcePath),
        "-CacheRoot",
        str(CachePath),
        "-CompileOnly",
    ]
    Records = RaceCompile(Command)
    assert sum(Record["compiled"] is True for Record in Records) == 1
    assert sum(Record["compiled"] is False for Record in Records) == 1
    assert Records[0]["assembly"] == Records[1]["assembly"]
    assert len(list(CachePath.glob("*.dll"))) == 1
    CachedPath = FilePath(str(Records[0]["assembly"]))
    CachedTime = CachedPath.stat().st_mtime_ns
    Record = RunCompile(Command, 60)
    assert Record["compiled"] is False
    assert CachedPath.stat().st_mtime_ns == CachedTime
    _ = SourcePath.write_bytes(SourceBytes + b"\n")
    Record = RunCompile(Command, KColdCompileSeconds)
    assert Record["compiled"] is True
    assert Record["assembly"] != Records[0]["assembly"]
    assert len(list(CachePath.glob("*.dll"))) == 2
    CopiedPath = TmpPath / "PreparedProgress.dll"
    PreparedCommand = [*Command[:-1], "-AssemblyPath", str(CopiedPath)]
    Prepared = RunCompile(PreparedCommand, 60)
    assert Prepared["compiled"] is False
    assert CopiedPath.read_bytes() == FilePath(str(Record["assembly"])).read_bytes()
    assert len(list(CachePath.glob("*.dll"))) == 2


# each load must cross a fresh interpreter boundary without leaking a timed out child
def RunCompile(Command: list[str], Timeout: int) -> dict[str, object]:
    Result = RunProcess(
        Command, capture_output=True, text=True, check=False, timeout=Timeout
    )
    assert Result.returncode == 0, Result.stdout + Result.stderr
    Record: dict[str, object] = DecodeJson(Result.stderr.splitlines()[-1])
    return Record


# simultaneous first users must publish one complete assembly and release every child
def RaceCompile(Command: list[str]) -> list[dict[str, object]]:
    Children = [
        OpenProcess(CommandRun, stdout=PipeOutput, stderr=PipeOutput, text=True)
        for CommandRun in (Command, Command)
    ]
    Records: list[dict[str, object]] = []
    try:
        for Child in Children:
            Output, Errors = Child.communicate(timeout=KColdCompileSeconds)
            assert Child.returncode == 0, Output + Errors
            Records.append(DecodeJson(Errors.splitlines()[-1]))
    finally:
        for Child in Children:
            if Child.poll() is None:
                Child.kill()
            _ = Child.communicate()
    return Records
