import os as OsModule
import subprocess as Subprocess
import sys as System
from pathlib import Path as FilePath


# the full census needs bounded reader batches so a single subprocess cannot hide partial progress
def CollectFusion(TargetList: list[FilePath], TempPath: FilePath) -> FilePath:
    RootPath = FilePath(__file__).resolve().parents[3]
    CensusPath = FilePath(
        OsModule.environ.get("KIT_FUSION_CENSUS", str(TempPath / "census.json"))
    )
    CensusRun = Subprocess.run(
        [
            System.executable,
            str(RootPath / "re/automation/FusionCensus.py"),
            "collect",
            "--manifest",
            str(RootPath / "re/automation/Corpus.json"),
            f"--output={CensusPath.absolute()}",
            *(
                f"--summary={TargetPath.absolute() / 'summary.json'}"
                for TargetPath in TargetList
            ),
        ],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert CensusRun.returncode == 0, CensusRun.stderr
    return CensusPath
