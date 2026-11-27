import os as OsLayer
from pathlib import Path as FilePath
import subprocess as ProcessLayer
import sys as System
from tempfile import TemporaryDirectory
from tests.Convert.Integration.Fusion.MakeOffsetPlane import MakeOffsetPlane


# matching loops and normals cannot qualify a native carrier saved on a different plane
def CheckPlaneCli() -> None:
    RootPath = FilePath(__file__).resolve().parents[4]
    Environment = dict(OsLayer.environ)
    Environment["PYTHONPATH"] = OsLayer.pathsep.join(
        (str(RootPath / "src"), str(RootPath / "Cli"))
    )
    Source = (
        RootPath / "re/Fusion/Reconstruction/BoundaryCuts/Controls/RequestedCorner.f3d"
    )
    with TemporaryDirectory() as WorkName:
        Target = FilePath(WorkName) / "offset.f3d"
        MakeOffsetPlane(Source, Target)
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
        assert "boundary leaves its declared plane" in Result.stdout + Result.stderr
