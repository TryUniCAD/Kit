import os as OsLayer
from pathlib import Path as FilePath
import subprocess as ProcessLayer
import sys as System
from tempfile import TemporaryDirectory


# known cut definitions must reach qualification without permitting an unqualified native conversion
def CheckCutConvert() -> None:
    RootPath = FilePath(__file__).resolve().parents[4]
    Environment = dict(OsLayer.environ)
    Environment["PYTHONPATH"] = OsLayer.pathsep.join(
        (str(RootPath / "src"), str(RootPath / "Cli"))
    )
    Source = (
        RootPath / "re/Fusion/Reconstruction/BoundaryCuts/Controls/RequestedCorner.f3d"
    )
    with TemporaryDirectory() as WorkName:
        Target = FilePath(WorkName) / "unqualified.json"
        Result = ProcessLayer.run(
            [
                System.executable,
                "-m",
                "KitCli",
                "convert",
                str(Source),
                str(Target),
                "--to",
                "interchange.json",
            ],
            cwd=RootPath,
            env=Environment,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        assert Result.returncode != 0 and not Target.exists()
        assert any(
            Message in Result.stdout + Result.stderr
            for Message in ("UnqualifiedGeometry", "RetainedMetadata")
        )
        assert "IncompleteFeature" not in Result.stdout + Result.stderr
        assert "Traceback" not in Result.stdout + Result.stderr
