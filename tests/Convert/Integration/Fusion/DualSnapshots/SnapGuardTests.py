from pytest import mark as TestMark, raises as RaisesError

from tests.Convert.Integration.Fusion.DualSide.ReadDualCases import ReadDualCases
from tests.Convert.Integration.Fusion.DualSnapshots.CheckSavedSnap import CheckSavedSnap
from tests.Convert.Integration.Fusion.DualSnapshots.MakeBadSnap import MakeBadSnap


# real serialized counterexamples must refuse before a snapshot can qualify public feature admission
@TestMark.parametrize("ModeName", ("identity", "feature", "sketch", "body", "geometry"))
def CheckSnapGuards(ModeName: str) -> None:
    Sample = next(Value for Value in ReadDualCases() if Value.Identity == "baseline")
    Payload = MakeBadSnap(Sample.Source.read_bytes(), ModeName)
    with RaisesError(ValueError, match="Dual snapshot"):
        CheckSavedSnap(Payload)
