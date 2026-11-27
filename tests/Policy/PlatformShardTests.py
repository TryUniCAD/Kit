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
        "mixed-native",
        "rerun",
        "latest-failed",
    ),
)
@TestMark.parametrize("NativePattern", ("", "^tests/Native/"))
@TestMark.parametrize("PlatformKind", ("generic", "windows"))
def CheckShardGate(
    TmpPath: FilePath, Outcome: str, NativePattern: str, PlatformKind: str
) -> None:
    ReportPrefix = (
        "PlatformReport-windows-2025" if PlatformKind == "windows" else "Platform"
    )
    NativePrefix = (
        "tests/Research/Windows/" if PlatformKind == "windows" else "tests/Native/"
    )
    NativePattern = NativePattern.replace("tests/Native/", NativePrefix)
    WriteReports(TmpPath, Outcome, ReportPrefix, NativePrefix)
    Result = RunProcess(
        (
            "bash",
            str(
                FilePath(__file__).resolve().parents[2]
                / ".github/scripts/VerifyShardReports.sh"
            ),
            str(TmpPath),
            ReportPrefix,
            "2" if Outcome in ("rerun", "latest-failed") else "1",
            NativePattern,
        ),
        env={**KEnvironment, "GITHUB_STEP_SUMMARY": str(TmpPath / "Summary.md")},
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    ExpectedPass = Outcome in ("passed", "rerun") or (
        Outcome in ("native", "mixed-native") and not NativePattern
    )
    assert (Result.returncode == 0) == ExpectedPass, Result.stdout + Result.stderr
