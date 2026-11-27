import json as JsonLib
import os as OsLayer
from pathlib import Path as FilePath
import subprocess as ProcessLayer
import sys as System
from tempfile import TemporaryDirectory

from pytest import mark as TestMark

from tests.Convert.Integration.Solidworks.Reverse.LoadReverse import LoadReverse
from tests.Convert.Integration.Solidworks.Reverse.CheckCliRefuse import CheckCliRefuse


# command publication must expose the same signed geometry and parameter identity as the strict sdk reader
@TestMark.parametrize(
    "CaseName",
    (
        "discoveryTriangleForward",
        "discoveryTriangleReverse",
        "holdoutStepForward",
        "holdoutStepReverse",
        "holdoutQuadForward",
        "holdoutQuadReverse",
    ),
)
def CheckReverseCli(CaseName: str) -> None:
    Sample = LoadReverse(CaseName)
    RootPath = FilePath(__file__).resolve().parents[5]
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
                str(Sample.SourcePath),
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
        Feature = next(
            Value
            for Value in Document["feature_timeline"]["$tuple"]
            if Value["name"] == "Boss-Extrude1"
        )
        assert Feature["definition"]["reversed"] is Sample.IsReversed
        (Driver,) = Document["parameters"]["$tuple"]
        assert Driver["owner_id"] == Feature["id"]
        assert Driver["value"]["value"] == Sample.DepthMm
        assert Driver["attributes"]["typed_archive_owner"]["slot"] == "f818.f18"
        (BodyValue,) = Document["bodies"]["$tuple"]
        Centroid = BodyValue["attributes"]["solidworks.body_centroid_mm"]["$tuple"]
        assert all(
            abs(Value - Expected) < 1e-10
            for Value, Expected in zip(Centroid, Sample.Centroid, strict=True)
        )
        assert BodyValue["topology"]["shell_count"] == 1
        assert abs(BodyValue["topology"]["volume"] - Sample.VolumeMm) < 1e-8
        if Sample.IsReversed:
            CheckCliRefuse(
                Sample.SourcePath,
                FilePath(WorkName) / Sample.SourcePath.name,
                RootPath,
                Environment,
            )
