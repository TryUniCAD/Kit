from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue

# repository resolution lets the codec process run in its own output directory
KRepoRoot = FilePath(__file__).resolve().parents[4]


# both controls must prove stream identity through the same isolated command
def RunHeadReplay(
    TmpPath: FilePath, SourceName: str, SourceHash: str
) -> tuple[str, str]:
    SourcePath = KRepoRoot / SourceName
    ScriptPath = KRepoRoot / "re/tooling/sw2026/CheckStandaloneHeaders.py"
    ReportPath = TmpPath / "HeaderReplay.json"
    Outcome = RunProcess(
        [
            PythonExec,
            "-I",
            "-B",
            str(ScriptPath),
            str(SourcePath),
            "--report",
            str(ReportPath),
        ],
        cwd=TmpPath,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    Report = LoadJson(ReportPath.read_text(encoding="utf-8"))
    assert Report["source_sha256"] == SourceHash
    assert Report["container_version"] == 4 and Report["archive_version"] == 19000
    assert set(Report["streams"]) == {"Header2", "Contents/Config-0-ModelHeader"}
    for StreamValue in Report["streams"].values():
        assert StreamValue["root_index"] == 2
        assert StreamValue["byte_count"] > 0 and len(StreamValue["sha256"]) == 64
    assert list(TmpPath.iterdir()) == [ReportPath]
    return (
        CastValue(str, Report["streams"]["Header2"]["sha256"]),
        CastValue(str, Report["streams"]["Contents/Config-0-ModelHeader"]["sha256"]),
    )
