from hashlib import sha256 as DigestBytes
from json import dumps as EncodeJson, loads as ParseJson
from pathlib import Path as FilePath

from tests.Research.Archives.Comparison.BulkProcess import RunBulk
from tests.Research.Archives.Comparison.SemanticComparisonTests import (
    KTolerances,
    WriteDocument,
)
from tests.Research.Archives.Comparison.SemanticDocuments import MakeDocument


# explicit pairing bridges independently named exports while retaining declared physical unit contracts
def CheckUnitPairs(TmpPath: FilePath) -> None:
    WriteDocument(TmpPath / "Solidworks.json", MakeDocument("source"))
    WriteDocument(TmpPath / "Fusion.json", MakeDocument("target", "in"))
    Manifest = TmpPath / "Pairs.json"
    _ = Manifest.write_text(
        EncodeJson(
            {
                "version": 1,
                "pairs": [
                    {
                        "id": "../rectangle",
                        "left": "Solidworks.json",
                        "right": "Fusion.json",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    Tolerances = TmpPath / "Tolerances.json"
    _ = Tolerances.write_text(EncodeJson(KTolerances), encoding="utf-8")
    Output = TmpPath / "Output"
    Result = RunBulk(
        [
            "--manifest",
            str(Manifest),
            "--right-unit",
            "in",
            "--tolerances",
            str(Tolerances),
            "--output",
            str(Output),
        ]
    )
    assert Result.returncode == 0, Result.stderr + Result.stdout
    Summary = ParseJson((Output / "summary.json").read_text(encoding="utf-8"))
    assert Summary["outcomes"] == {"equal_observed_graph": 1}
    assert Summary["pairing"] == "manifest"
    assert Summary["manifest_sha256"] == DigestBytes(Manifest.read_bytes()).hexdigest()
    Artifact = Summary["pairs"][0]["report"]
    assert Artifact["path"] == "reports/0000.json"
    assert (
        Artifact["sha256"]
        == DigestBytes((Output / Artifact["path"]).read_bytes()).hexdigest()
    )
    assert not (TmpPath / "rectangle.json").exists()


# duplicate pair labels would make bulk evidence attribution unsafe even with valid documents
def CheckDuplicate(TmpPath: FilePath) -> None:
    Manifest = TmpPath / "Pairs.json"
    Entry = {"id": "same", "left": "First.json", "right": "Second.json"}
    _ = Manifest.write_text(
        EncodeJson({"version": 1, "pairs": [Entry, Entry]}), encoding="utf-8"
    )
    Output = TmpPath / "Output"
    Result = RunBulk(["--manifest", str(Manifest), "--output", str(Output)])
    assert Result.returncode == 1
    assert "unique" in Result.stderr
    assert not Output.exists()
