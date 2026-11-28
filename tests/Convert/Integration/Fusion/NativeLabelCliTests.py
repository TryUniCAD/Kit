from tests.Convert.Integration.Fusion.MakeBadLabel import MakeBadLabel
import os as OsLayer
from pathlib import Path as FilePath
import subprocess as ProcessLayer
import sys as System
from tempfile import TemporaryDirectory


# the public decoder must refuse a structurally encoded archive with a cap label on its sketch sheet
def CheckBadLabel() -> None:
    RootPath = FilePath(__file__).resolve().parents[4]
    Environment = dict(OsLayer.environ)
    Environment["PYTHONPATH"] = OsLayer.pathsep.join(
        (str(RootPath / "src"), str(RootPath / "Cli"))
    )
    Source = (
        RootPath
        / "re/Fusion/Reconstruction/CircularSpans/Controls/Original/DiscFlip.f3d"
    )
    with TemporaryDirectory() as WorkName:
        Target = FilePath(WorkName) / "misplaced.f3d"
        MakeBadLabel(Source, Target)
        Result = ProcessLayer.run(
            [
                System.executable,
                "-m",
                "KitCli",
                "decode",
                str(Target),
                "--output",
                str(FilePath(WorkName) / "output.json"),
            ],
            cwd=RootPath,
            env=Environment,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        assert Result.returncode != 0
        assert "labels do not cover the physical solid" in Result.stdout + Result.stderr
