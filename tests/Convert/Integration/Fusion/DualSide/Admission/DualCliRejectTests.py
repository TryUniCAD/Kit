from os import pathsep as PathSeparator
from pathlib import Path

from pytest import mark as MarkTests, MonkeyPatch as PatchScope

from tests.Convert.Commands.CliProcess import CliProcess
from tests.Convert.Integration.Fusion.DualSide.ReadDualCases import ReadDualCases
from tests.Convert.Integration.Fusion.DualSnapshots.MakeBadSnap import MakeBadSnap


# ordinary cli decoding cannot silently fall back when saved snapshot semantics are corrupt
@MarkTests.parametrize(
    "ModeName", ("identity", "feature", "sketch", "body", "geometry")
)
def CheckDualCliBad(TmpPath: Path, MonkeyPatch: PatchScope, ModeName: str) -> None:
    Sample = next(Value for Value in ReadDualCases() if Value.Identity == "baseline")
    RootPath = Path(__file__).resolve().parents[6]
    MonkeyPatch.setenv(
        "PYTHONPATH", PathSeparator.join((str(RootPath / "src"), str(RootPath / "Cli")))
    )
    Source = TmpPath / "Corrupt.f3d"
    _ = Source.write_bytes(MakeBadSnap(Sample.Source.read_bytes(), ModeName))
    Target = TmpPath / "Rejected.json"
    Result = CliProcess(TmpPath, "decode", str(Source), "--output", str(Target))
    assert Result.returncode != 0 and "Traceback" not in Result.stderr
    assert not Target.exists()
