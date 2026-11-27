from hashlib import sha256 as HashBytes

from pytest import mark as TestMark, raises as RaisesError

from tests.Convert.Integration.Fusion.DualSide.DualCase import DualCase
from tests.Convert.Integration.Fusion.DualSide.ReadDualCases import ReadDualCases
from tests.Convert.Integration.Fusion.DualSnapshots.CheckSavedSnap import CheckSavedSnap


# every archived native edit and parameter holdout must preserve complete saved snapshot ownership
@TestMark.parametrize("Sample", ReadDualCases())
def CheckSnapSource(Sample: DualCase) -> None:
    Payload = Sample.Source.read_bytes()
    assert HashBytes(Payload).hexdigest() == Sample.Digest
    if Sample.Frame.z_axis.z == 1.0:
        CheckSavedSnap(Payload)
    else:
        with RaisesError(
            ValueError, match="identity placement|one untransformed shell per body"
        ):
            CheckSavedSnap(Payload)
