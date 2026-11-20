from json import loads as DecodeJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess

from tests.CliResearch.ResearchAssets import KSwAsset
from tests.CliResearch.ResearchClient import ResearchCli
from tests.CliResearch.ResearchRoot import ResearchRoot


# a historical checkout must keep decoding while the installed launcher reports unavailable verification
def CheckLegacyRoot(TmpPath: FilePath) -> None:
    RootPath = ResearchRoot()
    Legacy = TmpPath / "LegacyCheckout"
    Result = RunProcess(
        [
            "git",
            "-C",
            str(RootPath),
            "worktree",
            "add",
            "--detach",
            str(Legacy),
            "520f0f5a9a96d3bcc0364c97b1add413ccac86ab",
        ],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert Result.returncode == 0, Result.stderr
    Target = TmpPath / "LegacyDecoded"
    Reply = ResearchCli(
        TmpPath,
        "solidworks",
        "--asset",
        KSwAsset,
        "--output",
        str(Target),
        Checkout=Legacy,
    )
    assert Reply.returncode == 4, Reply.stderr
    assert "verification was not performed" in Reply.stderr
    assert (Target / "document.json").is_file()
    Receipt = DecodeJson((Target / "receipt.json").read_bytes())
    assert Receipt["portable_complete"] is False
    assert Receipt["native_acceptance"] == "not_established"
    assert not (Target / "NativeVerification.json").exists()
