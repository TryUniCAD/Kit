from json import loads as DecodeJson
from pathlib import Path as FilePath

from tests.CliResearch.ResearchAssets import KSwAsset
from tests.CliResearch.ResearchClient import ResearchCli
from tests.CliResearch.ResearchRoot import ResearchRoot
from tests.CliResearch.OpenLegacy import OpenLegacy


# a historical checkout must keep decoding while the installed launcher reports unavailable verification
def CheckLegacyRoot(TmpPath: FilePath) -> None:
    RootPath = ResearchRoot()
    Target = TmpPath / "LegacyDecoded"
    with OpenLegacy(RootPath, TmpPath) as Legacy:
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
