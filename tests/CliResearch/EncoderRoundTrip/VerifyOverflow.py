from hashlib import sha256 as HashContent
from json import dumps as EncodeJson, loads as DecodeJson
from pathlib import Path as FilePath

from tests.CliResearch.ResearchClient import ResearchCli


# a numeric field must reach the exact sdk measurement gate without disturbing its original candidate binding
def OverflowReceipt(InputsPath: FilePath) -> tuple[bytes, str]:
    Envelope = DecodeJson((InputsPath / "HeldOutEdited.json").read_bytes())
    Receipt = Envelope["receipt"]
    Generated = next(
        Phase
        for Phase in Receipt["phases"]
        if Phase["role"] == "HeldOutEditedGenerated"
    )
    Initial = next(State for State in Generated["states"] if State["role"] == "Initial")
    Initial["depth_m"] = 10**400
    return (
        EncodeJson(Envelope).encode("utf-8"),
        Receipt["builds"][0]["candidate_sha256"],
    )


# an oversized observation must fail through the installed command with a json diagnostic and no output mutation
def VerifyOverflow(
    TmpPath: FilePath, OutputPath: FilePath, InputsPath: FilePath
) -> None:
    Snapshot = {Entry.name: Entry.read_bytes() for Entry in OutputPath.iterdir()}
    Modified, MeasuredSha = OverflowReceipt(InputsPath)
    ReceiptPath = TmpPath / "OverflowReceipt.json"
    _ = ReceiptPath.write_bytes(Modified)
    Result = ResearchCli(
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
    assert Result.returncode == 1, Result.stdout + Result.stderr
    assert not Result.stdout and "Traceback" not in Result.stderr
    Diagnostic = DecodeJson(Result.stderr)
    assert Diagnostic["error_type"] == "ValueError"
    if HashContent(Snapshot["edited.SLDPRT"]).hexdigest() == MeasuredSha:
        assert Diagnostic["error"] == (
            "native measurement requires finite scalar observations"
        )
    else:
        assert "no unique exact native measurement" in Diagnostic["error"]
    assert Snapshot == {
        Entry.name: Entry.read_bytes() for Entry in OutputPath.iterdir()
    }
    assert ReceiptPath.read_bytes() == Modified
