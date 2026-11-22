from hashlib import sha256 as HashBytes
import json as JsonLib
from math import isclose as IsClose
import os as OsLayer
from pathlib import Path as FilePath
import subprocess as ProcessLayer
import sys as System
from tempfile import TemporaryDirectory


# measured native controls must pass through the public executable without a cad runtime
def CheckSpanCli() -> None:
    RootPath = FilePath(__file__).resolve().parents[4]
    Manifest = JsonLib.loads(
        (RootPath / "re/Fusion/Reconstruction/CircularSpans/Manifest.json").read_text()
    )
    Environment = dict(OsLayer.environ)
    Environment["PYTHONPATH"] = OsLayer.pathsep.join(
        (str(RootPath / "src"), str(RootPath / "Cli"))
    )
    with TemporaryDirectory() as WorkName:
        for Sample in Manifest["samples"]:
            Source = (RootPath / Sample["file"]).resolve(strict=True)
            assert Source.is_relative_to(
                RootPath / "re/Fusion/Reconstruction/CircularSpans/Controls"
            )
            assert HashBytes(Source.read_bytes()).hexdigest() == Sample["sha256"]
            Output = FilePath(WorkName) / (Sample["group"] + Sample["name"] + ".json")
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
            assert (
                Result.returncode == 0
            ), f"{Source.name}: {Result.stdout} {Result.stderr}"
            Record = JsonLib.loads(Output.read_text())
            assert Record["partial"] is False and Record["layer"] == "neutral"
            Document = Record["document"]
            Bodies = Document["bodies"]["$tuple"]
            Expected = Sample["observed"]["bodies"]
            assert len(Bodies) == len(Expected) == 1
            Topology = Bodies[0]["topology"]
            assert Topology["solid_count"] == 1 and Topology["valid"] is True
            assert IsClose(
                Topology["volume"], Expected[0]["volume_cm3"] * 1000, rel_tol=1e-9
            )
            assert IsClose(
                Topology["surface_area"], Expected[0]["area_cm2"] * 100, rel_tol=1e-9
            )
            for RoleName, ExpectedKey in (("minimum", "min_cm"), ("maximum", "max_cm")):
                Bounds = Topology["bounding_box"][RoleName]
                assert all(
                    IsClose(Bounds[AxisName], Amount * 10, rel_tol=1e-9, abs_tol=1e-9)
                    for AxisName, Amount in zip(
                        ("x", "y", "z"), Expected[0][ExpectedKey], strict=True
                    )
                )
            Features = Document["feature_timeline"]["$tuple"]
            assert len(Features) == len(Sample["observed"]["timeline"]) == 2
            Definition = Features[-1]["definition"]
            assert Definition["$type"] == "DistanceExtrude"
            assert Definition["SideMode"] == Sample["side_mode"]
            assert set(Features[-1]["parameter_ids"]["$tuple"]) == {
                Value["id"] for Value in Document["parameters"]["$tuple"]
            }
            assert (
                Document["brep"] is not None and not Document["diagnostics"]["$tuple"]
            )
