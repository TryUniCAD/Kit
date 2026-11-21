from hashlib import sha256 as DigestBytes
from json import loads as DecodeJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonPath

from pytest import mark as TestMark

from convert.Formats.Fusion.DocumentCodec.EmitBodyPart import EmitBodyPart
from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.Formats.Fusion.DocumentCodec.ReadBodyPart import ReadBodyPart
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from tests.CliResearch.NativeVerification.RunComparison import RunComparison
from tests.CliResearch.ResearchRoot import ResearchRoot


# real vendor saves must cross the public decoder and measurement comparison commands without an installed cad runtime
@TestMark.parametrize(
    "CaseName",
    (
        "Width",
        "Height",
        "Depth",
        "Taper",
        "AngleNegative",
        "AnglePositive",
        "AngleSmall",
        "AngleSteep",
        "DraftNegative",
        "DraftPositive",
        "DraftSmall",
        "DraftSteep",
    ),
)
def CheckSavedPrism(TmpPath: FilePath, CaseName: str) -> None:
    RootPath = ResearchRoot()
    FixturePath = RootPath / "re/Fusion/Reconstruction/NativeEditedPrisms"
    CaseValue = DecodeJson((FixturePath / "Measurements.json").read_bytes())["cases"][
        CaseName
    ]
    SourcePath = FixturePath / CaseValue["file"]
    SourceBytes = SourcePath.read_bytes()
    assert DigestBytes(SourceBytes).hexdigest() == CaseValue["sha256"]
    DocumentPath = TmpPath / "Decoded.json"
    Result = RunProcess(
        (
            PythonPath,
            "-m",
            "KitCli",
            "decode",
            str(SourcePath),
            "--output",
            str(DocumentPath),
        ),
        capture_output=True,
        text=True,
        check=False,
        timeout=300,
    )
    assert Result.returncode == 0, Result.stderr or Result.stdout
    Compared = RunComparison(TmpPath, DocumentPath, CaseValue["measurement"])
    assert Compared.returncode == 0, Compared.stderr or Compared.stdout
    Report = DecodeJson((TmpPath / "Compared.json").read_bytes())
    assert Report["status"] == "passed" and Report["full_semantics_verified"] is True
    assert Report["native_acceptance"] is False
    assert Report["scope"] == "offline_measurement_comparison"
    NativeModel = ReadDocument(SourceBytes)
    BodyValue = NativeModel.Bodies[0]
    Emitted = EmitBodyPart(BodyValue)
    assert Emitted.Payload.startswith(b"ASM BinaryFile4")
    assert ReadBodyPart(Emitted) == BodyValue
    assert ReadDocument(EmitParsed(NativeModel)) == NativeModel
