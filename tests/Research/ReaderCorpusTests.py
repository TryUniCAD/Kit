import json as JsonCodec
import subprocess as Subprocess
import sys as System
import tempfile as TempFiles
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path as FilePath

from tests.Research.ReaderClient import ReaderClient


# the solidworks reader must account for the complete declared inventory beyond the ordinary control
def CheckReadCorpus() -> None:
    RootPath = FilePath(__file__).resolve().parents[2]
    Manifest = JsonCodec.loads((RootPath / "re/automation/Corpus.json").read_text())
    AssetList = [
        Asset for Asset in Manifest["assets"] if Asset.get("format") == "sldprt"
    ]
    assert len(AssetList) == 58
    with TempFiles.TemporaryDirectory() as TempPath:
        Client = ReaderClient(FilePath(TempPath))
        with ThreadPoolExecutor(max_workers=4) as WorkerPool:
            Results = list(
                WorkerPool.map(Client.ReadAsset, [Asset["path"] for Asset in AssetList])
            )
        for Asset, (AssetPath, ResultInfo) in zip(AssetList, Results, strict=True):
            assert AssetPath == Asset["path"]
            assert ResultInfo.returncode == 0, (AssetPath, ResultInfo.stderr)
            OutputPath = FilePath(JsonCodec.loads(ResultInfo.stdout)["output"])
            Receipt = JsonCodec.loads((OutputPath / "receipt.json").read_text())
            assert Receipt["source"] == Asset
            assert Receipt["semantic_qualification"] == "unverified"
            assert Receipt["unresolved"]
            assert Receipt["portable_complete"] is False
        print(
            JsonCodec.dumps(
                {"reader_corpus": {"decoded": len(Results), "rejected": 0}},
                sort_keys=True,
            )
        )


# discovery measurements must exercise the same saved file boundaries as the original hosted census
def CheckDiscCensus(TmpPath: FilePath) -> None:
    RootPath = FilePath(__file__).resolve().parents[2]
    CensusPath = RootPath / "re/automation/SolidworksCensus.py"
    ReportPath = TmpPath / "Discovery.json"
    for FlagValue in (
        "--output",
        "--check-equations",
        "--check-cut-terminations",
        "--check-directions",
        "--check-rectangle-edges",
        "--check-support-evidence",
        "--check-resolved-lengths",
    ):
        ResultInfo = Subprocess.run(
            [System.executable, str(CensusPath), FlagValue, str(ReportPath)],
            cwd=RootPath,
            capture_output=True,
            text=True,
            check=False,
            timeout=240,
        )
        assert ResultInfo.returncode == 0, (
            FlagValue,
            ResultInfo.stdout,
            ResultInfo.stderr,
        )
