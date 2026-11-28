from __future__ import annotations

from json import dumps as DumpJson
from pathlib import Path as FilePath
from subprocess import TimeoutExpired

from tests.Convert.Solidworks.Research.Curve.SaveReceipt import SaveReport


# timeout captures may be bytes despite the process text option
def TimeoutText(TextValue: bytes | str | None) -> str:
    if isinstance(TextValue, bytes):
        return TextValue.decode("utf-8", errors="replace")
    return TextValue or ""


# interrupted commands retain scoped evidence with the same artifact path guarantees
def FieldTimeout(
    ReportPath: FilePath, Failure: TimeoutExpired, IsLinked: bool, Limit: int
) -> None:
    Evidence = {
        "scope": "curve discovery field inventory process timeout",
        "is_writer_output": False,
        "native_acceptance_inherited": False,
        "require_proven": True,
        "linked_configurations": IsLinked,
        "returncode": None,
        "timed_out": True,
        "timeout_seconds": Limit,
    }
    for Suffix, TextValue in (
        (".stdout.log", TimeoutText(Failure.stdout)),
        (".stderr.log", TimeoutText(Failure.stderr)),
        (".scope.json", DumpJson(Evidence, indent=2) + "\n"),
    ):
        SaveReport(ReportPath.with_suffix(Suffix), TextValue)
