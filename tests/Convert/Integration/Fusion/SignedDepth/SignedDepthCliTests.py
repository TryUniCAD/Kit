from hashlib import sha256 as HashBytes
import json as JsonLib
from math import isclose as IsClose
import os as OsLayer
from pathlib import Path as FilePath
import subprocess as ProcessLayer
import sys as System
from tempfile import TemporaryDirectory

import pytest as Pytest


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
        Document = Record["document"]
        assert not Document["diagnostics"]["$tuple"]
        Features = Document["feature_timeline"]["$tuple"]
        assert len(Features) == 2
        assert Features[-1]["definition"]["$type"] == "DistanceExtrude"
        Depth = next(
            Value
            for Value in Document["parameters"]["$tuple"]
            if Value["name"] == "depth_mm"
        )
        NativeDepth = next(
            Value
            for Value in Sample["native"]["parameters"]
            if Value["name"] == "depth_mm"
        )
        assert Depth["expression"]["source"] == NativeDepth["expression"]
        assert Depth["owner_id"] == Features[-1]["id"]
        assert Features[-1]["definition"]["along_parameter_id"] == Depth["id"]
        assert IsClose(
            Depth["value"]["value"], NativeDepth["value_internal"] * 10, rel_tol=1e-9
        )
        Bodies = Document["bodies"]["$tuple"]
        assert len(Bodies) == Sample["native"]["body_count"] == 1
        Topology = Bodies[0]["topology"]
        assert Topology["valid"] and Topology["solid_count"] == 1
        assert IsClose(Topology["volume"], Sample["native"]["volume_mm3"], rel_tol=1e-9)
        for RoleName, Expected in zip(
            ("minimum", "maximum"),
            Sample["native"]["bodies"][0]["bounding_box_mm"],
            strict=True,
        ):
            for AxisName, Amount in zip(("x", "y", "z"), Expected, strict=True):
                assert IsClose(
                    Topology["bounding_box"][RoleName][AxisName],
                    Amount,
                    rel_tol=1e-9,
                    abs_tol=1e-9,
                )
