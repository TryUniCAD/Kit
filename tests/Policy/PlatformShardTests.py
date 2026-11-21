from os import environ as KEnvironment
from pathlib import Path as FilePath
from subprocess import run as RunProcess

from pytest import mark as TestMark

from tests.Policy.Shards.WriteReports import WriteReports


# published artifact corruption must block platform acceptance at the actual reporting process boundary
@TestMark.parametrize(
    "Outcome",
    (
        "passed",
        "missing",
        "duplicate",
        "failed",
        "session",
        "roster",
        "extra",
        "native",
        "rerun",
    ),
)
@TestMark.parametrize("NativePattern", ("", "^tests/Native/"))
def CheckShardGate(TmpPath: FilePath, Outcome: str, NativePattern: str) -> None:
    WriteReports(TmpPath, Outcome)
    Result = RunProcess(
        (
            "bash",
            str(
                FilePath(__file__).resolve().parents[2]
                / ".github/scripts/VerifyShardReports.sh"
            ),
            str(TmpPath),
            "Platform",
            "2" if Outcome == "rerun" else "1",
            NativePattern,
        ),
        env={**KEnvironment, "GITHUB_STEP_SUMMARY": str(TmpPath / "Summary.md")},
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    ExpectedPass = Outcome in ("passed", "rerun") or (
        Outcome == "native" and not NativePattern
    )
    assert (Result.returncode == 0) == ExpectedPass, Result.stdout + Result.stderr
