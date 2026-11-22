import os as OsLayer
from pathlib import Path as FilePath
import subprocess as ProcessLayer
import sys as System
from tempfile import TemporaryDirectory


# native face appearances must be retained or explicitly refused instead of silently becoming body wide color
def CheckColorCli() -> None:
    RootPath = FilePath(__file__).resolve().parents[4]
    Environment = dict(OsLayer.environ)
    Environment["PYTHONPATH"] = OsLayer.pathsep.join(
        (str(RootPath / "src"), str(RootPath / "Cli"))
    )
    Source = (
        RootPath
        / "re/Fusion/Reconstruction/BoundaryCuts/Controls/ReviewGuards/FaceAppearance.f3d"
    )
    with TemporaryDirectory() as WorkName:
        Result = ProcessLayer.run(
            [
                System.executable,
                "-m",
                "KitCli",
                "decode",
                str(Source),
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
        assert any(
            Message in Result.stdout + Result.stderr
            for Message in (
                "faceVisualMaterialByAttrTagID",
                "Unsupported Fusion journal attribute family",
            )
        )
