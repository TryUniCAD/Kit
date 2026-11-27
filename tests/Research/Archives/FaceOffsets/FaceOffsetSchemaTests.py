import json as JsonLib
import os as OsLayer
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExe
from tempfile import TemporaryDirectory

from interchange.Features.Offsets.FaceOffset import FaceOffset
from interchange.serialization.Deserialize import FromData


# native source decoding must transport first class offset operands through the public wire registry
def CheckOffsetWire() -> None:
    RootPath = FilePath(__file__).resolve().parents[4]
    Environment = dict(OsLayer.environ)
    Environment["PYTHONPATH"] = str(RootPath / "src")
    with TemporaryDirectory() as WorkName:
        Target = FilePath(WorkName) / "offsets.json"
        Result = RunProcess(
            [
                PythonExe,
                "re/Fusion/Reconstruction/FaceOffsets/DecodeOffsets.py",
                "re/Fusion/Reconstruction/FaceOffsets/Controls",
                "--output",
                str(Target),
            ],
            cwd=RootPath,
            env=Environment,
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
        )
        assert Result.returncode == 0, Result.stderr
        Samples = JsonLib.loads(Target.read_text())["cases"]
        Modified = [Sample for Sample in Samples if Sample.get("offset_intents")]
        assert len(Modified) == 6
        for Sample in Modified:
            assert Sample["status"] == "inspected"
            assert all(Sample["native_measurement_match"].values())
            Intent = Sample["offset_intents"][0]
            Definition = FromData(Intent["definition"])
            assert isinstance(Definition, FaceOffset)
            assert Definition.FaceSelectionId == Intent["target_reference_id"]
            assert Definition.TargetBodyId and Definition.DistanceParamId
            assert all(Intent["box_rule_matches"].values())
