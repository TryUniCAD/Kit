from hashlib import sha256 as HashBytes
import json as JsonLib
from math import isclose as IsClose
import os as OsLayer
from pathlib import Path as FilePath
import subprocess as ProcessLayer
import sys as System
from tempfile import TemporaryDirectory
import pytest as Pytest
from tests.Convert.Integration.Fusion.ReadCutCases import ReadCutCases
from tests.Convert.Integration.Fusion.CutCliCase import CutCliCase
from tests.Convert.Integration.Fusion.CheckCutWire import CheckCutWire


# native cut controls must cross the public executable boundary without partial fallback or a cad runtime
@Pytest.mark.parametrize("Sample", ReadCutCases())
def CheckCutCli(Sample: CutCliCase) -> None:
    RootPath = FilePath(__file__).resolve().parents[4]
    Environment = dict(OsLayer.environ)
    Environment["PYTHONPATH"] = OsLayer.pathsep.join(
        (str(RootPath / "src"), str(RootPath / "Cli"))
    )
    assert HashBytes(Sample.Source.read_bytes()).hexdigest() == Sample.Digest
    with TemporaryDirectory() as WorkName:
        Output = FilePath(WorkName) / "document.json"
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
        assert Result.returncode == 0, Result.stdout + Result.stderr
        Record = JsonLib.loads(Output.read_text())
        assert Record["partial"] is False and Record["layer"] == "neutral"
        Document = Record["document"]
        Bodies = Document["bodies"]["$tuple"]
        assert len(Bodies) == 1
        Topology = Bodies[0]["topology"]
        assert Topology["valid"] is True and Topology["solid_count"] == 1
        assert (
            Topology["face_count"],
            Topology["edge_count"],
            Topology["vertex_count"],
        ) == (Sample.FaceCount, Sample.EdgeCount, Sample.VertexCount)
        assert IsClose(Topology["volume"], Sample.Volume, rel_tol=1e-9)
        assert IsClose(Topology["surface_area"], Sample.AreaValue, rel_tol=1e-9)
        for RoleName, Expected in (
            ("minimum", Sample.Minimum),
            ("maximum", Sample.Maximum),
        ):
            assert all(
                IsClose(
                    Topology["bounding_box"][RoleName][AxisName],
                    Amount,
                    rel_tol=1e-9,
                    abs_tol=1e-9,
                )
                for AxisName, Amount in zip(("x", "y", "z"), Expected, strict=True)
            )
        assert Document["brep"] is not None and not Document["diagnostics"]["$tuple"]
        CheckCutWire(Output, Sample)
