from hashlib import sha256 as HashBytes
import json as JsonLib
import os as OsLayer
from pathlib import Path as FilePath
import subprocess as ProcessLayer
import sys as System
from tempfile import TemporaryDirectory

import pytest as Pytest

from tests.Convert.Integration.Fusion.SignedDepth.CheckSignedRead import CheckSignedRead


# measured reverse depths must retain their expression and geometry through the public command
@Pytest.mark.parametrize("CaseName", ("BossReverseXY", "BossReverseXYHoldout"))
def CheckSignedCli(CaseName: str) -> None:
    RootPath = FilePath(__file__).resolve().parents[5]
    FixtureRoot = RootPath / "re/Fusion/Reconstruction/SignedDepth"
    Manifest = JsonLib.loads((FixtureRoot / "Manifest.json").read_text())
    Sample = next(Value for Value in Manifest["samples"] if Value["id"] == CaseName)
    Source = FixtureRoot / Sample["file"]
    assert Source.resolve().is_relative_to(FixtureRoot.resolve())
    assert HashBytes(Source.read_bytes()).hexdigest() == Sample["sha256"]
    assert Sample["passed"] and all(Sample["checks"].values())
    assert (
        HashBytes(
            (
                RootPath / "re/automation/CaptureTools/Catalogue/Fusion/BuildFusion.py"
            ).read_bytes()
        ).hexdigest()
        == Sample["builder_sha256"]
    )
    Environment = dict(OsLayer.environ)
    Environment["PYTHONPATH"] = OsLayer.pathsep.join(
        (str(RootPath / "src"), str(RootPath / "Cli"))
    )
    with TemporaryDirectory() as WorkName:
        Output = FilePath(WorkName) / "Decoded.json"
        Result = ProcessLayer.run(
            [
                System.executable,
                "-m",
                "KitCli",
                "decode",
                str(Source),
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
        assert Result.returncode == 0, Result.stdout + Result.stderr
        Record = JsonLib.loads(Output.read_text())
        assert Record["partial"] is False and Record["layer"] == "neutral"
        CheckSignedRead(Record["document"], Sample)
