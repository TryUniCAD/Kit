from __future__ import annotations

from pathlib import Path as FilePath
from subprocess import CompletedProcess, TimeoutExpired, run as RunProcess
from sys import executable as PythonExec
from tempfile import TemporaryDirectory as TempDirectory

from tests.Convert.Solidworks.Research.ArchiveProcess import KRepoRoot
from tests.Convert.Solidworks.Research.ArtifactIO.ArtifactPaths import ArtifactFile
from tests.Convert.Solidworks.Research.Curve.Fields.FieldArguments import (
    FieldArguments,
)
from tests.Convert.Solidworks.Research.Curve.Fields.FieldTimeout import FieldTimeout
from tests.Convert.Solidworks.Research.Curve.SaveReceipt import SaveReceipt


# invocation stays within the interpreter and research program already chosen by the fixture
def InvokeFields(
    StagePath: FilePath, SourceArgs: tuple[str, str], IsLinked: bool, Limit: int
) -> CompletedProcess[str]:
    ScriptPath = KRepoRoot / "re/tooling/sw2026/serial/FieldScan.py"
    Options = ("--link-config",) if IsLinked else ()
    Arguments = (
        PythonExec,
        "-I",
        "-B",
        str(ScriptPath),
        "--inventory-json",
        str(StagePath),
        "--require-proven",
        *Options,
        "--",
        *SourceArgs,
    )
    return RunProcess(
        Arguments,
        cwd=KRepoRoot,
        capture_output=True,
        text=True,
        check=False,
        timeout=Limit,
    )


# the process receives a private report destination and the caller retains the audited result
def RunFieldCli(
    TmpPath: FilePath,
    Pattern: str,
    StreamName: str,
    ReportPath: FilePath,
    IsLinked: bool,
) -> CompletedProcess[str]:
    TargetPath = ArtifactFile(ReportPath.parent, ReportPath.name)
    if TargetPath.exists():
        raise FileExistsError(TargetPath)
    SourceArgs = FieldArguments(TmpPath, Pattern, StreamName)
    Limit = 120
    with TempDirectory(prefix="KitFieldInventory.") as TempName:
        StagePath = FilePath(TempName) / "Report.json"
        try:
            Outcome = InvokeFields(StagePath, SourceArgs, IsLinked, Limit)
        except TimeoutExpired as Failure:
            FieldTimeout(TargetPath, Failure, IsLinked, Limit)
            raise
        if StagePath.is_file():
            Payload = StagePath.read_bytes()
            with TargetPath.open("xb") as OutputFile:
                Written = OutputFile.write(Payload)
                assert Written == len(Payload)
    SaveReceipt(TargetPath, Outcome, IsLinked)
    return Outcome
