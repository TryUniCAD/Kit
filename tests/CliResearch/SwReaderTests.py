from pathlib import Path as FilePath
from json import dumps as EncodeJson, loads as DecodeJson

from tests.CliResearch.CheckReceipt import CheckReceipt
from tests.CliResearch.DirectReader import DirectReader
from tests.CliResearch.ResearchAssets import KSwAsset
from tests.CliResearch.ResearchClient import ResearchCli
from tests.CliResearch.ResearchRoot import ResearchRoot


# the reserved part exercises pinned batch paths with embedded spaces
KHoldoutAsset = (
    "re/solidworks/examples/Single Turbo Dual Overhead Cam V8 - KDP - 2024/"
    "CUBIERTA.SLDPRT"
)


# solidworks dispatch must preserve reader receipts and refuse overwriting existing artifacts
def CheckSwReceipts(TmpPath: FilePath) -> None:
    Direct = TmpPath / "Direct"
    Bridged = TmpPath / "Bridged"
    Arguments = ("--asset", KSwAsset)
    Reference = DirectReader(
        TmpPath, "SolidworksReader.py", *Arguments, "--output", str(Direct)
    )
    Result = ResearchCli(TmpPath, "solidworks", *Arguments, "--output", str(Bridged))
    assert Reference.returncode == 0 and Result.returncode == 4, (
        Reference.stderr,
        Result.stderr,
    )
    assert {Value.name for Value in Direct.iterdir()} == {
        "document.json",
        "receipt.json",
    }
    assert {Value.name for Value in Bridged.iterdir()} == {
        "document.json",
        "receipt.json",
        "NativeVerification.json",
    }
    NativeReport = DecodeJson((Bridged / "NativeVerification.json").read_bytes())
    assert NativeReport["status"] == "api_unavailable"
    assert NativeReport["action"]
    assert NativeReport["portable_complete"] is False
    assert NativeReport["conversion_qualified"] is False
    assert NativeReport["full_semantics_verified"] is False
    assert "constraint_operands" in NativeReport["semantic_gaps"]
    for FileName in ("document.json", "receipt.json"):
        assert (Direct / FileName).read_bytes() == (Bridged / FileName).read_bytes()
    CheckReceipt(Bridged)
    Before = {Value.name: Value.read_bytes() for Value in Bridged.iterdir()}
    Repeated = ResearchCli(TmpPath, "solidworks", *Arguments, "--output", str(Bridged))
    assert Repeated.returncode == 1
    assert {Value.name: Value.read_bytes() for Value in Bridged.iterdir()} == Before


# callers need ordered batch evidence with the same bytes as singleton decoding
def CheckSwBatch(TmpPath: FilePath) -> None:
    Batch = TmpPath / "Batch"
    Arguments = ("--batch", "--asset", KHoldoutAsset, "--asset", KSwAsset)
    Result = ResearchCli(TmpPath, "solidworks", *Arguments, "--output", str(Batch))
    assert Result.returncode == 4, Result.stderr
    Summary = DecodeJson((Batch / "summary.json").read_bytes())
    assert DecodeJson(Result.stdout)["assets"] == Summary["assets"]
    assert [Entry["path"] for Entry in Summary["assets"]] == [KHoldoutAsset, KSwAsset]
    assert DecodeJson((Batch / "NativeVerification.json").read_bytes())["status"] == (
        "api_unavailable"
    )
    for Index, Entry in enumerate(Summary["assets"]):
        Single = TmpPath / f"Single{Index}"
        Reply = DirectReader(
            TmpPath,
            "SolidworksReader.py",
            "--asset",
            Entry["path"],
            "--output",
            str(Single),
        )
        assert Reply.returncode == 0, Reply.stderr
        assert DecodeJson(Reply.stdout)["fingerprint"] == Entry["fingerprint"]
        for Name in ("document.json", "receipt.json"):
            assert (Batch / Entry["directory"] / Name).read_bytes() == (
                Single / Name
            ).read_bytes()


# a failed second pin must never expose the first staged document
def CheckSwBatchPinFailure(TmpPath: FilePath) -> None:
    Manifest = DecodeJson((ResearchRoot() / "re/automation/Corpus.json").read_bytes())
    for Asset in Manifest["assets"]:
        if Asset["path"] == KSwAsset:
            Asset["sha256"] = "0" * 64
    ManifestPath = TmpPath / "Manifest.json"
    ManifestPath.write_text(EncodeJson(Manifest), encoding="utf-8")
    Batch = TmpPath / "Batch"
    Result = ResearchCli(
        TmpPath,
        "solidworks",
        "--batch",
        "--asset",
        KHoldoutAsset,
        "--asset",
        KSwAsset,
        "--manifest",
        str(ManifestPath),
        "--output",
        str(Batch),
    )
    assert Result.returncode == 1, Result.stderr
    assert "asset bytes differ from the pinned digest/prefix" in Result.stderr
    assert not Batch.exists()
    assert not list(TmpPath.glob(".reader-*"))
