from json import dumps as EncodeJson, loads as DecodeJson
from pathlib import Path as FilePath
from shutil import copytree as CopyTree

from tests.CliResearch.EncoderRoundTrip.RebindWriter import RebindWriter
from tests.CliResearch.ResearchClient import ResearchCli


# unmeasured protocol ingress must validate both persisted roles before considering native receipt evidence
def CheckFusionBind(OutputPath: FilePath, Snapshot: dict[str, bytes]) -> None:
    TmpPath = OutputPath.parent
    Manifest = DecodeJson(Snapshot["manifest.json"])
    ReceiptPath = TmpPath / "UnmeasuredBinding.json"
    Envelope = {
        "schema": 1,
        "application": "fusion",
        "role": "reconstruction",
        "run_fingerprint": "0" * 64,
        "source_sha256": Manifest["source_sha256"],
        "candidate_sha256": Manifest["candidate_sha256"]["reconstruction"],
        "sdk_revision": Manifest["sdk_revision"],
    }
    assert Envelope["run_fingerprint"] != Manifest["run_fingerprint"]
    ReceiptBytes = EncodeJson(Envelope).encode("utf-8")
    _ = ReceiptPath.write_bytes(ReceiptBytes)
    ReboundPath = TmpPath / "ReboundFusionWriter"
    _ = CopyTree(OutputPath, ReboundPath)
    RebindWriter(ReboundPath, Snapshot["reconstruction-writer-input.json"])
    for RunPath, FailureText in (
        (OutputPath, "receipt run_fingerprint does not bind this round-trip role"),
        (
            ReboundPath,
            "round-trip role edited writer input does not reproduce its native candidate",
        ),
    ):
        Before = {Entry.name: Entry.read_bytes() for Entry in RunPath.iterdir()}
        Result = ResearchCli(
            TmpPath,
            "encoder-round-trip",
            "attach-receipt",
            "--output",
            str(RunPath),
            "--role",
            "reconstruction",
            "--receipt",
            str(ReceiptPath),
        )
        assert Result.returncode == 1, Result.stdout + Result.stderr
        assert DecodeJson(Result.stderr)["error"] == FailureText
        assert not (RunPath / "reconstruction-receipt.json").exists()
        assert {Entry.name: Entry.read_bytes() for Entry in RunPath.iterdir()} == Before
    assert ReceiptPath.read_bytes() == ReceiptBytes
