from __future__ import annotations

from hashlib import sha256 as HashBytes
from os import getenv as ReadEnv
from pathlib import Path as FilePath
from typing import cast as CastValue
from pytest import mark as MarkTests
from tests.convert.solidworks.research.Curve.AssertFixtures import AssertFixtures
from tests.convert.solidworks.research.Curve.CorpusPaths import KCurveCorpus
from tests.convert.solidworks.research.Curve.ReadManifest import ReadManifest
from tests.convert.solidworks.research.Curve.ReadObject import ReadObject
from tests.convert.solidworks.research.Curve.Fields.AssertDigest import AssertDigest
from tests.convert.solidworks.research.Curve.Fields.AssertFieldCode import (
    AssertFieldCode,
)
from tests.convert.solidworks.research.Curve.Fields.RunFieldCli import RunFieldCli


# incomplete real inputs must retain explicit failures instead of successful empty field graphs
@MarkTests.parametrize(
    "FailureKind", ("EmptyPattern", "MissingStream", "TruncatedFixture")
)
def TestFieldFail(TmpPath: FilePath, FailureKind: str) -> None:
    Entries = AssertFixtures(ReadManifest())
    StreamName = "Contents/Config-0"
    Pattern = str(KCurveCorpus / "*.SLDPRT")
    Expected = {FileName: Entry["sha256"] for FileName, Entry in Entries.items()}
    if FailureKind == "EmptyPattern":
        Pattern = str(TmpPath / "Unmatched" / "*.SLDPRT")
        Expected = {}
    elif FailureKind == "MissingStream":
        StreamName = "Contents/FieldInventoryMissing"
        assert all(
            Stream["name"] != StreamName
            for Entry in Entries.values()
            for Stream in CastValue(list[dict[str, object]], Entry["streams"])
        )
    else:
        assert FailureKind == "TruncatedFixture"
        SourcePath = KCurveCorpus / "ControlRectangle.SLDPRT"
        Truncated = SourcePath.read_bytes()[:64]
        assert len(Truncated) == 64 < SourcePath.stat().st_size
        InputPath = TmpPath / "Truncated.SLDPRT"
        with InputPath.open("xb") as OutputFile:
            assert OutputFile.write(Truncated) == 64
        Pattern = str(InputPath)
        Expected = {InputPath.name: HashBytes(Truncated).hexdigest()}
    OutputDir = (
        FilePath(ReadEnv("SwResearchOutput") or str(TmpPath))
        / "SourceParser/Curve/Fields/Failures"
    )
    OutputDir.mkdir(parents=True, exist_ok=True)
    ReportPath = OutputDir / f"{FailureKind}.json"
    Outcome = RunFieldCli(Pattern, StreamName, ReportPath, False)
    assert Outcome.returncode == 1, Outcome.stdout + Outcome.stderr
    Report = ReadObject(ReportPath)
    assert Report["schema"] == "kit.sw2026.field-inventory.v1"
    assert Report["version"] == 19000
    assert Report["passed"] is False
    assert Report["require_proven"] is True
    assert Report["linked_configurations"] is False
    assert Report["writer_output"] is Report["raw_payloads_emitted"] is False
    assert Report["values_truncated"] is Report["byte_roundtrip_performed"] is False
    assert Report["native_acceptance"] == "unmeasured"
    AssertFieldCode(Report)
    Files = CastValue(list[dict[str, object]], Report["files"])
    Names = [CastValue(str, FileData["name"]) for FileData in Files]
    assert len(Files) == len(set(Names)) == Report["file_count"] == len(Expected)
    assert set(Names) == set(Expected)
    if FailureKind == "EmptyPattern":
        assert Report["error"] == "no input files matched"
    for FileData in Files:
        FileName = CastValue(str, FileData["name"])
        FileEntry = FilePath(CastValue(str, FileData["path"]))
        ExpectedPath = (
            FilePath(Pattern)
            if FailureKind == "TruncatedFixture"
            else KCurveCorpus / FileName
        )
        assert FileEntry.resolve() == ExpectedPath.resolve()
        assert AssertDigest(FileData["sha256"]) == Expected[FileName]
        assert FileData["bytes"] == FileEntry.stat().st_size
        assert FileData["passed"] is False and FileData["stage"] == "container"
        assert CastValue(dict[str, object], FileData["stream"])["name"] == StreamName
        assert FileData.get("proven_schemas") is not True
        assert "document" not in FileData and "nodes" not in FileData
        ErrorData = CastValue(dict[str, object], FileData["error"])
        assert set(ErrorData) == {"type", "message_sha256", "message_policy"}
        assert isinstance(ErrorData["type"], str) and ErrorData["type"]
        AssertDigest(ErrorData["message_sha256"])
        assert ErrorData["message_policy"] == (
            "hashed to avoid dumping opaque payloads through codec exceptions"
        )
