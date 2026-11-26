import json as JsonLib
import os as OsLayer
from pathlib import Path as FilePath
import subprocess as ProcessLayer
import sys as System
from tempfile import TemporaryDirectory


# public interchange loading cannot accept a cut detached from its actual prior body producer
def CheckCutLinkCli() -> None:
    RootPath = FilePath(__file__).resolve().parents[4]
    Environment = dict(OsLayer.environ)
    Environment["PYTHONPATH"] = OsLayer.pathsep.join(
        (str(RootPath / "src"), str(RootPath / "Cli"))
    )
    Source = (
        RootPath / "re/Fusion/Reconstruction/BoundaryCuts/Controls/RequestedCorner.f3d"
    )
    with TemporaryDirectory() as WorkName:
        Output = FilePath(WorkName) / "decoded.json"
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
        Document = JsonLib.loads(Output.read_text())["document"]
        Features = Document["feature_timeline"]["$tuple"]
        Features[-1]["input_feature_ids"]["$tuple"] = [Features[2]["id"]]
        Target = FilePath(WorkName) / "detached.json"
        _ = Target.write_text(JsonLib.dumps(Document))
        Result = ProcessLayer.run(
            [
                System.executable,
                "-m",
                "KitCli",
                "decode",
                str(Target),
                "--from",
                "interchange.json",
                "--output",
                str(FilePath(WorkName) / "invalid.json"),
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
            "no unique prior producer for target body" in Result.stdout + Result.stderr
        )
