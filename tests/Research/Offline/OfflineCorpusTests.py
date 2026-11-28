import json as JsonCodec
import subprocess as Subprocess
import sys as System
from pathlib import Path as FilePath
from typing import cast as CastValue
from os import name as PlatformName

from pytest import mark as MarkValue


# the real corpus runner must preserve ordered decode results across worker counts
@MarkValue.skipif(
    PlatformName != "posix", reason="corpus runner uses POSIX process groups"
)
def CheckCorpus(TmpPath: FilePath) -> None:
    RootPath = FilePath(__file__).resolve().parents[3]
    Manifest = JsonCodec.loads((RootPath / "re/automation/Corpus.json").read_text())
    Assets = [Asset for Asset in Manifest["assets"] if Asset.get("format") == "sldprt"][
        :3
    ]
    assert len(Assets) == 3
    Manifest["assets"] = Assets
    Manifest["source_revision"] = Subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=RootPath, text=True
    ).strip()
    ManifestPath = TmpPath / "Corpus.json"
    _ = ManifestPath.write_text(JsonCodec.dumps(Manifest), encoding="utf-8")
    Outcomes: list[list[tuple[list[int], dict[str, object]]]] = []
    for Workers in ("1", "3"):
        OutputPath = TmpPath / Workers
        Result = Subprocess.run(
            [
                System.executable,
                str(RootPath / "re/automation/OfflineCorpus/RunCorpus.py"),
                "--manifest",
                str(ManifestPath),
                "--output",
                str(OutputPath),
                "--workers",
                Workers,
            ],
            cwd=RootPath,
            capture_output=True,
            text=True,
            check=False,
            timeout=200,
        )
        assert Result.returncode == 0, Result.stderr
        Report = JsonCodec.loads((OutputPath / "Report.json").read_text())
        assert Report["workers"] == int(Workers)
        assert Report["timings"]["elapsed_ns"] > 0
        assert Report["vendor_acceptance"] is False
        assert [AssetRow["source"] for AssetRow in Report["assets"]] == Assets
        assert Report["timings"]["decode_ns"] == sum(
            AssetRow["elapsed_ns"] for AssetRow in Report["assets"]
        )
        Outcomes.append(ReadResults(Report["assets"]))
    assert Outcomes[0] == Outcomes[1]


# compare only decode artifacts and outcomes rather than launch paths or timings
def ReadResults(
    AssetRecords: list[dict[str, object]],
) -> list[tuple[list[int], dict[str, object]]]:
    AssetRows: list[tuple[list[int], dict[str, object]]] = []
    for AssetRow in AssetRecords:
        RunRecords = CastValue(list[dict[str, int]], AssetRow["runs"])
        assert [RunRecord["exit"] for RunRecord in RunRecords] == [0, 0], AssetRow
        assert all(RunRecord["elapsed_ns"] > 0 for RunRecord in RunRecords)
        assert AssetRow["elapsed_ns"] == sum(
            RunRecord["elapsed_ns"] for RunRecord in RunRecords
        )
        Artifacts = {
            ArtifactName: Value
            for ArtifactName, Value in CastValue(
                dict[str, object], AssetRow["artifacts"]
            ).items()
            if ArtifactName.endswith(("/document.json", "/receipt.json", "/cli.json"))
        }
        assert any(
            ArtifactName.endswith("/document.json") for ArtifactName in Artifacts
        )
        assert any(ArtifactName.endswith("/receipt.json") for ArtifactName in Artifacts)
        assert any(ArtifactName.endswith("/cli.json") for ArtifactName in Artifacts)
        AssetRows.append(([RunRecord["exit"] for RunRecord in RunRecords], Artifacts))
    return AssetRows
