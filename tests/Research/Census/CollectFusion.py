import os as OsModule
from shutil import copyfileobj as CopyStream
import subprocess as Subprocess
import sys as System
from pathlib import Path as FilePath


# the full census needs bounded reader batches so a single subprocess cannot hide partial progress
def CollectFusion(TargetList: list[FilePath], TempPath: FilePath) -> FilePath:
    RootPath = FilePath(__file__).resolve().parents[3]
    CensusPath = TempPath / "census.json"
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
    ExportPath = OsModule.environ.get("KIT_FUSION_CENSUS")
    if ExportPath and FilePath(ExportPath).absolute() != CensusPath.absolute():
        with CensusPath.open("rb") as Source, FilePath(ExportPath).open("xb") as Target:
            CopyStream(Source, Target)
    return CensusPath
