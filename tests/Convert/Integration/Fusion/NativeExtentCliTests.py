import pytest as Pytest
from tests.Convert.Integration.Fusion.SpanCliCase import SpanCliCase
from tests.Convert.Integration.Fusion.ReadSpanCases import ReadSpanCases
from hashlib import sha256 as HashBytes
import json as JsonLib
from math import isclose as IsClose
import os as OsLayer
from pathlib import Path as FilePath
import subprocess as ProcessLayer
import sys as System
from tempfile import TemporaryDirectory


# measured native controls must pass through the public executable without a cad runtime
@Pytest.mark.parametrize("Sample", ReadSpanCases())
def CheckSpanCli(Sample: SpanCliCase) -> None:
    RootPath = FilePath(__file__).resolve().parents[4]
    Environment = dict(OsLayer.environ)
    Environment["PYTHONPATH"] = OsLayer.pathsep.join(
        (str(RootPath / "src"), str(RootPath / "Cli"))
    )
    with TemporaryDirectory() as WorkName:
        assert Sample.Source.is_relative_to(
            RootPath / "re/Fusion/Reconstruction/CircularSpans/Controls"
        )
        assert HashBytes(Sample.Source.read_bytes()).hexdigest() == Sample.Digest
        Output = FilePath(WorkName) / (Sample.CaseName + ".json")
        Result = ProcessLayer.run(
            [
                System.executable,
                "-m",
                "KitCli",
                "decode",
                str(Sample.Source),
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
        assert (
            Result.returncode == 0
        ), f"{Sample.Source.name}: {Result.stdout} {Result.stderr}"
        Record = JsonLib.loads(Output.read_text())
        assert Record["partial"] is False and Record["layer"] == "neutral"
        Document = Record["document"]
        Bodies = Document["bodies"]["$tuple"]
        assert len(Bodies) == 1
        Topology = Bodies[0]["topology"]
        assert Topology["solid_count"] == 1 and Topology["valid"] is True
        assert IsClose(Topology["volume"], Sample.Volume, rel_tol=1e-9)
        assert IsClose(Topology["surface_area"], Sample.AreaValue, rel_tol=1e-9)
        for RoleName, ExpectedBounds in (
            ("minimum", Sample.Minimum),
            ("maximum", Sample.Maximum),
        ):
            Bounds = Topology["bounding_box"][RoleName]
            assert all(
                IsClose(Bounds[AxisName], Amount, rel_tol=1e-9, abs_tol=1e-9)
                for AxisName, Amount in zip(
                    ("x", "y", "z"), ExpectedBounds, strict=True
                )
            )
        Features = Document["feature_timeline"]["$tuple"]
        assert len(Features) == Sample.TimelineCount == 2
        Definition = Features[-1]["definition"]
        assert Definition["$type"] == "DistanceExtrude"
        assert Definition["SideMode"] == Sample.SideMode
        assert set(Features[-1]["parameter_ids"]["$tuple"]) == {
            Value["id"] for Value in Document["parameters"]["$tuple"]
        }
        assert Document["brep"] is not None and not Document["diagnostics"]["$tuple"]
