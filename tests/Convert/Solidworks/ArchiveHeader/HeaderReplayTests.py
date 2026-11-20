from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec

# repository resolution lets the codec process run in its own output directory
KRepoRoot = FilePath(__file__).resolve().parents[4]


# the existing native control gives this comparison a fixed input identity
KFixturePath = KRepoRoot / "re/solidworks/v2026/corpus/ladder/L1_boss.SLDPRT"


# redaction produced the tracked identity used by this compatibility process
KFixtureHash = "55e5a9840cc78a1d4b3ac4b8de3f37540695494e4d7a0edfb3cd3a2a876e2ac6"


# separate stream roots must replay completely from the same immutable native control
def TestHeadReplay(TmpPath: FilePath) -> None:
    ScriptPath = KRepoRoot / "re/tooling/sw2026/CheckStandaloneHeaders.py"
    ReportPath = TmpPath / "HeaderReplay.json"
    Outcome = RunProcess(
        [
            PythonExec,
            "-I",
            "-B",
            str(ScriptPath),
            str(KFixturePath),
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
    assert Report["source_sha256"] == KFixtureHash
    assert Report["container_version"] == 4 and Report["archive_version"] == 19000
    assert set(Report["streams"]) == {"Header2", "Contents/Config-0-ModelHeader"}
    for StreamValue in Report["streams"].values():
        assert StreamValue["root_index"] == 2
        assert StreamValue["byte_count"] > 0 and len(StreamValue["sha256"]) == 64
    assert list(TmpPath.iterdir()) == [ReportPath]
