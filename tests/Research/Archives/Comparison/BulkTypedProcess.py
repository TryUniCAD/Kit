from json import dumps as EncodeJson, loads as ParseJson
from pathlib import Path as FilePath
from typing import cast as CastValue

from interchange.document.Models.DocumentModel import CadDocument
from tests.Research.Archives.Comparison.BulkProcess import RunBulk
from tests.Research.Archives.Comparison.SemanticComparisonTests import WriteDocument


# typed output and modifying definitions must cross codec and process boundaries with explicit evidence
def RunTypedBatch(
    TmpPath: FilePath, First: CadDocument, Second: CadDocument, ExitCode: int
) -> dict[str, object]:
    FirstPath = TmpPath / "Solidworks.json"
    SecondPath = TmpPath / "Fusion.json"
    WriteDocument(FirstPath, First)
    WriteDocument(SecondPath, Second)
    Before = (FirstPath.read_bytes(), SecondPath.read_bytes())
    Manifest = TmpPath / "Pairs.json"
    ManifestText = EncodeJson(
        {
            "version": 1,
            "pairs": [
                {"id": "typed", "left": FirstPath.name, "right": SecondPath.name}
            ],
        }
    )
    assert Manifest.write_text(ManifestText, encoding="utf-8") == len(ManifestText)
    Output = TmpPath / "Output"
    Result = RunBulk(["--manifest", str(Manifest), "--output", str(Output)])
    assert Result.returncode == ExitCode, Result.stderr + Result.stdout
    assert (FirstPath.read_bytes(), SecondPath.read_bytes()) == Before
    Summary = ParseJson((Output / "summary.json").read_text(encoding="utf-8"))
    assert Summary["pair_count"] == 1
    return CastValue(
        dict[str, object],
        ParseJson(
            (Output / Summary["pairs"][0]["report"]["path"]).read_text(encoding="utf-8")
        ),
    )
