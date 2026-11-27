import os as OsLayer
from pathlib import Path as FilePath
import subprocess as ProcessLayer
import sys as System

from tests.Convert.Integration.Fusion.Offsets.ChangeOffset import ChangeOffset


# the public executable must reject corrupted ownership without publishing a decoded report
def CheckStartCli(TmpPath: FilePath) -> None:
    RootPath = FilePath(__file__).resolve().parents[5]
    Source = RootPath / "re/Fusion/OffsetAdmission20261127/Controls/baseline.f3d"
    Target = TmpPath / "Changed.f3d"
    Output = TmpPath / "Decoded.json"
    ChangeOffset(Source, Target, "owner")
    Environment = dict(OsLayer.environ)
    Environment["PYTHONPATH"] = OsLayer.pathsep.join(
        (str(RootPath / "src"), str(RootPath / "Cli"))
    )
    Result = ProcessLayer.run(
        [
            System.executable,
            "-m",
            "KitCli",
            "decode",
            str(Target),
            "--output",
            str(Output),
        ],
        cwd=RootPath,
        env=Environment,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert Result.returncode != 0
    assert (
        "Native extrusion parameter owner is inconsistent"
        in Result.stdout + Result.stderr
    )
    assert "Traceback" not in Result.stdout + Result.stderr
    assert not Output.exists()


# reader support must not turn the conversion command into unqualified publication
def CheckExportCli(TmpPath: FilePath) -> None:
    RootPath = FilePath(__file__).resolve().parents[5]
    Source = RootPath / "re/Fusion/OffsetAdmission20261127/Controls/baseline.f3d"
    Target = TmpPath / "Target.json"
    Environment = dict(OsLayer.environ)
    Environment["PYTHONPATH"] = OsLayer.pathsep.join(
        (str(RootPath / "src"), str(RootPath / "Cli"))
    )
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
    assert (
        "read-only Fusion histories cannot be exported" in Result.stdout + Result.stderr
    )
    assert "Traceback" not in Result.stdout + Result.stderr
    assert not Target.exists()
