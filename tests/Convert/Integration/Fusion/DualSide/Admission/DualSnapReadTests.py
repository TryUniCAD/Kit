from pathlib import Path

from pytest import mark as MarkTests, raises as RaisesError

from convert import open_document as OpenDocument
from tests.Convert.Integration.Fusion.DualSide.ReadDualCases import ReadDualCases
from tests.Convert.Integration.Fusion.DualSnapshots.MakeBadSnap import MakeBadSnap


# equal solid geometry cannot authorize a saved snapshot with incorrect identity or source sheets
@MarkTests.parametrize(
    "ModeName", ("identity", "feature", "sketch", "body", "geometry")
)
def CheckSnapBad(TmpPath: Path, ModeName: str) -> None:
    Sample = next(Value for Value in ReadDualCases() if Value.Identity == "baseline")
    Target = TmpPath / "Corrupt.f3d"
    _ = Target.write_bytes(MakeBadSnap(Sample.Source.read_bytes(), ModeName))
    with RaisesError(ValueError):
        _ = OpenDocument(Target, strict=True)
