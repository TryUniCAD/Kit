from __future__ import annotations

from subprocess import CompletedProcess, TimeoutExpired, run as RunProcess
from sys import executable as PythonExec
from pathlib import Path as FilePath
from json import dumps as DumpJson
from tests.Convert.Solidworks.Research.ArchiveProcess import KRepoRoot
from tests.Convert.Solidworks.Research.Curve.SaveReceipt import SaveReceipt


# a fresh interpreter exposes inventory failures through the supported command boundary
def RunFieldCli(
    Pattern: str, StreamName: str, ReportPath: FilePath, IsLinked: bool
) -> CompletedProcess[str]:
    ScriptPath = KRepoRoot / "re/tooling/sw2026/serial/FieldScan.py"
    Arguments = [
        PythonExec,
        str(ScriptPath),
        Pattern,
        StreamName,
        "--inventory-json",
        str(ReportPath),
        "--require-proven",
    ]
    if IsLinked:
        Arguments.append("--link-config")
    try:
        Outcome = RunProcess(
            Arguments,
            cwd=KRepoRoot,
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
        )
    except TimeoutExpired as Failure:
        CapturedOut = Failure.stdout or ""
        CapturedErr = Failure.stderr or ""
        StdoutText = (
            CapturedOut.decode("utf-8", errors="replace")
            if isinstance(CapturedOut, bytes)
            else CapturedOut
        )
        StderrText = (
            CapturedErr.decode("utf-8", errors="replace")
            if isinstance(CapturedErr, bytes)
            else CapturedErr
        )
        for Suffix, TextValue in (
            (".stdout.log", StdoutText),
            (".stderr.log", StderrText),
            (
                ".scope.json",
                DumpJson(
                    {
                        "scope": "curve discovery field inventory process timeout",
                        "is_writer_output": False,
                        "native_acceptance_inherited": False,
                        "require_proven": True,
                        "linked_configurations": IsLinked,
                        "returncode": None,
                        "timed_out": True,
                        "timeout_seconds": 120,
                    },
                    indent=2,
                )
                + "\n",
            ),
        ):
            _ = ReportPath.with_suffix(Suffix).write_text(TextValue, encoding="utf-8")
        raise
    SaveReceipt(ReportPath, Outcome, IsLinked)
    return Outcome
