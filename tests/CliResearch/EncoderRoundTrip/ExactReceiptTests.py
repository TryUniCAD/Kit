from hashlib import sha256 as HashContent
from json import loads as DecodeJson
from pathlib import Path as FilePath
from subprocess import CompletedProcess, run as RunProcess
from sys import executable as PythonExec

from tests.CliResearch.EncoderRoundTrip.RunEncoder import RunEncoder
from tests.CliResearch.ResearchClient import ResearchCli
from tests.CliResearch.ResearchRoot import ResearchRoot

# the independent measurements bind the same virtual windows directory in every replay
KNativeLocator = r"C:\KitEncoderRoundTrip"


# the checked in authored request lets each runner construct its own source without a native archive fixture
def BuildColdSource(
    TmpPath: FilePath, RootPath: FilePath, InputsPath: FilePath
) -> FilePath:
    ScratchPath = TmpPath / "ColdSource"
    Envelope = DecodeJson((InputsPath / "HeldOutReconstruction.json").read_bytes())
    Result = RunProcess(
        (
            PythonExec,
            "-I",
            "-B",
            str(RootPath / "re/tooling/sw2026/PreparePlainPartEvidence.py"),
            "--neutral",
            str(InputsPath / "Requests/HeldOutReconstruction.json"),
            "--native-locator",
            KNativeLocator + r"\reconstruction.SLDPRT",
            "--written-at",
            str(Envelope["written_at"]),
            "--scratch",
            str(ScratchPath),
        ),
        cwd=TmpPath,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert Result.returncode == 0, Result.stderr
    return ScratchPath / "reconstruction.SLDPRT"


# both receipts must cross the actual installed research launcher and output boundary
def AttachEdited(
    TmpPath: FilePath, OutputPath: FilePath, ReceiptPath: FilePath
) -> CompletedProcess[str]:
    return ResearchCli(
        TmpPath,
        "encoder-round-trip",
        "attach-receipt",
        "--output",
        str(OutputPath),
        "--role",
        "edited",
        "--receipt",
        str(ReceiptPath),
    )


# complete snapshots expose any partial write to a candidate manifest or existing immutable receipt
def ReadOutputs(OutputPath: FilePath) -> dict[str, bytes]:
    return {Entry.name: Entry.read_bytes() for Entry in OutputPath.iterdir()}


# the matching compressor must reproduce measured bytes while every other runtime still exercises the exact gate
def VerifyEnvelope(
    TmpPath: FilePath, OutputPath: FilePath, InputsPath: FilePath
) -> None:
    Snapshot = ReadOutputs(OutputPath)
    Manifest = DecodeJson(Snapshot["manifest.json"])
    CandidateSha = HashContent(Snapshot["edited.SLDPRT"]).hexdigest()
    assert Manifest["candidate_sha256"]["edited"] == CandidateSha
    ExactPath = InputsPath / "HeldOutEdited.json"
    ExactBytes = ExactPath.read_bytes()
    Envelope = DecodeJson(ExactBytes)
    MeasuredSha = Envelope["receipt"]["builds"][0]["candidate_sha256"]
    Runtime = Manifest["runtime"]
    if (
        Runtime["platform"] == "win32"
        and Runtime["machine"] == "AMD64"
        and Runtime["implementation"] == "cpython"
        and Runtime["python"].startswith("3.14.6 ")
        and Runtime["zlib_build"] == Runtime["zlib_runtime"] == "1.3.1.zlib-ng"
    ):
        assert CandidateSha == MeasuredSha
    Result = AttachEdited(TmpPath, OutputPath, ExactPath)
    if CandidateSha == MeasuredSha:
        VerifyBinding(Result, ExactBytes, CandidateSha)
        Snapshot["edited-receipt.json"] = ExactBytes
    else:
        assert Result.returncode == 1, Result.stdout + Result.stderr
        assert "no unique exact native measurement" in Result.stderr
    assert ReadOutputs(OutputPath) == Snapshot
    WrongRole = AttachEdited(
        TmpPath, OutputPath, InputsPath / "HeldOutReconstruction.json"
    )
    assert WrongRole.returncode == 1, WrongRole.stdout + WrongRole.stderr
    assert "no unique exact native measurement" in WrongRole.stderr
    assert ReadOutputs(OutputPath) == Snapshot


# research attachment must identify sdk publication evidence without claiming publication occurred
def VerifyBinding(
    Result: CompletedProcess[str], ExactBytes: bytes, CandidateSha: str
) -> None:
    assert Result.returncode == 0, Result.stdout + Result.stderr
    Binding = DecodeJson(Result.stdout)
    Envelope = DecodeJson(ExactBytes)
    assert Binding["status"] == "receipt_attached"
    assert Binding["role"] == "edited"
    assert Binding["receipt_kind"] == "solidworks_exact_sdk"
    assert Binding["measurement_status"] == "exact_sdk_candidate_bound"
    assert Binding["candidate_sha256"] == CandidateSha
    assert Binding["receipt"]["sha256"] == HashContent(ExactBytes).hexdigest()
    Details = Binding["sdk_publication"]
    assert Details["receipt_option"] == "solidworks_native_measurement"
    assert Details["oracle_case"] == "HeldOutEdited"
    assert Details["oracle_build"] == Envelope["receipt"]["oracle"]["build"]
    assert Details["generated_sha256"] == CandidateSha
    assert Details["native_locator"] == KNativeLocator + r"\edited.SLDPRT"
    assert Details["written_at"] == Envelope["written_at"]
    assert Binding["native_qualification"] == "pending"
    assert Binding["vendor_loadable"] is Binding["application_usable"] is False


# independently measured held out evidence must survive regeneration and attach only to its measured role
def CheckSdkReceipt(TmpPath: FilePath) -> None:
    RootPath = ResearchRoot()
    InputsPath = RootPath / "re/solidworks/measurements/2026/EncoderRoundTrip"
    SourcePath = BuildColdSource(TmpPath, RootPath, InputsPath)
    OutputPath = TmpPath / "RoundTrip"
    Result = RunEncoder(
        TmpPath,
        "solidworks",
        SourcePath,
        OutputPath,
        "12.19",
        LocatorValue=KNativeLocator,
    )
    assert Result.returncode == 0, Result.stdout + Result.stderr
    VerifyEnvelope(TmpPath, OutputPath, InputsPath)
