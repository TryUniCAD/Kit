from json import dumps as EncodeJson
from pathlib import Path as FilePath
from subprocess import CompletedProcess

from tests.CliResearch.ResearchClient import ResearchCli


# saved observations must traverse the installed command and its real serialization boundary
def RunComparison(
    TmpPath: FilePath, DocumentPath: FilePath, Evidence: dict[str, object]
) -> CompletedProcess[str]:
    EvidencePath = TmpPath / "Observed.json"
    _ = EvidencePath.write_text(EncodeJson(Evidence), encoding="utf-8")
    return ResearchCli(
        TmpPath,
        "api",
        "compare",
        "fusion",
        "--document",
        str(DocumentPath),
        "--measurement",
        str(EvidencePath),
        "--output",
        str(TmpPath / "Compared.json"),
    )
