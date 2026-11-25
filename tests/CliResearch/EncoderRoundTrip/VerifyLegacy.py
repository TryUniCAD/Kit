from hashlib import sha256 as HashContent
from json import loads as DecodeJson
from pathlib import Path as FilePath

from tests.CliResearch.EncoderRoundTrip.MakeLegacy import MakeLegacy
from tests.CliResearch.ResearchClient import ResearchCli


# authentic legacy receipt custody must survive repeated installed command attachment without the original native source
def VerifyLegacy(
    TmpPath: FilePath,
    OutputPath: FilePath,
    ReceiptPath: FilePath,
    SourcePath: FilePath,
) -> None:
    Original = {Entry.name: Entry.read_bytes() for Entry in OutputPath.iterdir()}
    ReceiptBytes = ReceiptPath.read_bytes()
    CandidateSha = HashContent(Original["edited.SLDPRT"]).hexdigest()
    MeasuredSha = DecodeJson(ReceiptBytes)["receipt"]["builds"][0]["candidate_sha256"]
    Runtime = DecodeJson(Original["manifest.json"])["runtime"]
    if (
        Runtime["platform"] == "win32"
        and Runtime["machine"] == "AMD64"
        and Runtime["implementation"] == "cpython"
        and Runtime["python"].startswith("3.14.6 ")
        and Runtime["zlib_build"] == Runtime["zlib_runtime"] == "1.3.1.zlib-ng"
    ):
        assert CandidateSha == MeasuredSha
    assert not SourcePath.exists()
    LegacyPath = TmpPath / "LegacyCustody"
    Snapshot = MakeLegacy(Original, LegacyPath)
    Bindings: list[dict[str, object]] = []
    for _ in range(2):
        Result = ResearchCli(
            TmpPath,
            "encoder-round-trip",
            "attach-receipt",
            "--output",
            str(LegacyPath),
            "--role",
            "edited",
            "--receipt",
            str(ReceiptPath),
        )
        if CandidateSha == MeasuredSha:
            assert Result.returncode == 0, Result.stdout + Result.stderr
            Binding = DecodeJson(Result.stdout)
            assert (
                Binding["status"],
                Binding["role"],
                Binding["receipt_kind"],
                Binding["native_qualification"],
                Binding["vendor_loadable"],
                Binding["application_usable"],
            ) == (
                "receipt_attached",
                "edited",
                "solidworks_exact_sdk",
                "pending",
                False,
                False,
            )
            assert (Binding["candidate_sha256"], Binding["receipt"]["sha256"]) == (
                CandidateSha,
                HashContent(ReceiptBytes).hexdigest(),
            )
            Snapshot["edited-receipt.json"] = ReceiptBytes
            Bindings.append(Binding)
        else:
            assert Result.returncode == 1, Result.stdout + Result.stderr
            assert (
                DecodeJson(Result.stderr)["error"]
                == "regenerated SOLIDWORKS part has no unique exact native measurement"
            )
        assert {
            Entry.name: Entry.read_bytes() for Entry in LegacyPath.iterdir()
        } == Snapshot
    if CandidateSha == MeasuredSha:
        assert Bindings[0] == Bindings[1]
    assert {
        Entry.name: Entry.read_bytes() for Entry in OutputPath.iterdir()
    } == Original
    assert not SourcePath.exists()
    assert ReceiptPath.read_bytes() == ReceiptBytes
