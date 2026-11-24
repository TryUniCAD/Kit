import os as OsLayer
from pathlib import Path as FilePath
import subprocess as ProcessLayer
import sys as System
from tempfile import TemporaryDirectory

import pytest as Pytest


# newly readable reverse depths must not bypass remaining conversion qualification requirements
@Pytest.mark.parametrize(
    "CaseName",
    ("BossReverseXY", "BossReverseXYHoldout", "CircleReverse", "CircleReverseHoldout"),
)
def CheckSignedGate(CaseName: str) -> None:
    RootPath = FilePath(__file__).resolve().parents[5]
    Source = RootPath / "re/Fusion/Reconstruction/SignedDepth" / (CaseName + ".f3d")
    Environment = dict(OsLayer.environ)
    Environment["PYTHONPATH"] = OsLayer.pathsep.join(
        (str(RootPath / "src"), str(RootPath / "Cli"))
    )
    with TemporaryDirectory() as WorkName:
        Target = FilePath(WorkName) / "Target.FCStd"
        Result = ProcessLayer.run(
            [System.executable, "-m", "KitCli", "convert", str(Source), str(Target)],
            cwd=RootPath,
            env=Environment,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        assert Result.returncode != 0
        assert "UnqualifiedGeometry records are not conversion-ready" in Result.stderr
        assert "wrapped millimeter literal" not in Result.stderr
        assert "Traceback" not in Result.stderr
        assert not Target.exists()
