from io import BytesIO as ByteStream
from json import loads as LoadJson
from os import environ as SystemEnv
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as KPythonPath
from zipfile import ZipFile as ZipArchive

from convert import open_document as OpenDocument


# saved cuboid display ordering must survive json without changing unrelated archive members
def TestDisplayWire(TmpPath: FilePath) -> None:
    Repository = FilePath(__file__).resolve().parents[5]
    StudyFolder = Repository / "re/Fusion/SavedCuboidRoundTrip"
    SourcePath = StudyFolder / "Corpus/BaselineRestored.f3d"
    OutputPath = TmpPath / "Evidence"
    Result = RunProcess(
        (
            KPythonPath,
            "-B",
            str(StudyFolder / "BuildDisplayOrderContrast.py"),
            "--source",
            str(SourcePath),
            "--output",
            str(OutputPath),
        ),
        cwd=TmpPath,
        env={**SystemEnv, "PYTHONPATH": str(Repository / "src")},
        capture_output=True,
        text=True,
        check=False,
        timeout=90,
    )
    assert Result.returncode == 0, Result.stderr
    Observed = LoadJson((OutputPath / "SourceComparison.json").read_bytes())
    assert Observed["source_order_matches_display"] is True
    assert Observed["source_order_matches_canonical"] is False
    Before = (OutputPath / "Canonical.f3d").read_bytes()
    After = (OutputPath / "DisplayOrdered.f3d").read_bytes()
    VerifyMembers(Before, After)
    assert OpenDocument(After, source_format="f3d").metadata["fusion.read_only"] is True


# archive comparison independently confirms the contrast changes only the history member
def VerifyMembers(Before: bytes, After: bytes) -> None:
    with (
        ZipArchive(ByteStream(Before)) as Original,
        ZipArchive(ByteStream(After)) as Changed,
    ):
        assert Original.namelist() == Changed.namelist()
        ChangedNames = [
            MemberName
            for MemberName in Original.namelist()
            if Original.read(MemberName) != Changed.read(MemberName)
        ]
        assert len(ChangedNames) == 1 and ChangedNames[0].endswith(".smbh")
