from json import loads as DecodeJson
from os import utime as SetFileTimes
from pathlib import Path as FilePath

from pytest import mark as TestMark

from tests.CliResearch.NativeVerification.DecodeControl import DecodeControl
from tests.CliResearch.ResearchClient import ResearchCli


# real file boundaries must preserve stable inputs and reject linked oversized or nonregular evidence
@TestMark.parametrize(
    "CaseName",
    ("stable", "document_link", "measurement_link", "directory", "oversized"),
)
def CheckFileInputs(TmpPath: FilePath, CaseName: str) -> None:
    DocumentPath = DecodeControl(TmpPath)
    _ = DocumentPath.write_bytes(DocumentPath.read_bytes() + b"\n")
    EvidencePath = TmpPath / "FileEvidence.json"
    _ = EvidencePath.write_bytes(
        FilePath(__file__).with_name("FusionRectangle.json").read_bytes()
    )
    SetFileTimes(EvidencePath, (946684800, 946684800))
    if CaseName in ("document_link", "measurement_link"):
        LinkedPath = TmpPath / "LinkedInput.json"
        LinkedPath.hardlink_to(
            DocumentPath if CaseName == "document_link" else EvidencePath
        )
    if CaseName == "directory":
        EvidencePath.unlink()
        EvidencePath.mkdir()
    if CaseName == "oversized":
        _ = EvidencePath.write_bytes(b" " * (16 * 1024 * 1024 + 1))
    OutputPath = TmpPath / "FileCompared.json"
    Result = ResearchCli(
        TmpPath,
        "api",
        "compare",
        "fusion",
        "--document",
        str(DocumentPath),
        "--measurement",
        str(EvidencePath),
        "--output",
        str(OutputPath),
    )
    assert Result.returncode == (0 if CaseName == "stable" else 1), Result.stderr
    if CaseName == "stable":
        Report = DecodeJson(OutputPath.read_bytes())
        assert Report["status"] == "passed"
        assert Report["scope"] == "offline_measurement_comparison"
        assert Report["native_acceptance"] is False
        return
    assert not OutputPath.exists()
    assert (
        "byte limit" if CaseName == "oversized" else "regular file without links"
    ) in Result.stderr
