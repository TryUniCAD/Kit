from hashlib import sha256 as HashBytes

from pytest import mark as TestMark, raises as RaisesError

from interchange.geometry.Models.Transform import Transform
from tests.Convert.Integration.Fusion.DualFrameSnapshots.CheckFramedSnap import (
    CheckFramedSnap,
)
from tests.Convert.Integration.Fusion.DualSide.DualCase import DualCase
from tests.Convert.Integration.Fusion.DualSide.ReadDualCases import ReadDualCases


# discovery and frozen holdout sources require explicit qualified placement while the old default still refuses
@TestMark.parametrize(
    "Sample", tuple(Value for Value in ReadDualCases() if Value.Frame != Transform())
)
def CheckFrameSnaps(Sample: DualCase) -> None:
    Payload = Sample.Source.read_bytes()
    assert HashBytes(Payload).hexdigest() == Sample.Digest
    CheckFramedSnap(Payload, Sample.Frame)
    with RaisesError(ValueError, match="identity placement"):
        CheckFramedSnap(Payload)
