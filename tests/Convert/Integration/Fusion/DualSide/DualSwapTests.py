from math import isclose as IsClose

from convert.Geometry.Extrude.Circular.DualSide.BuildDualSide import BuildDualSide
from tests.Convert.Integration.Fusion.DualSide.CheckDualNative import CheckDualNative
from tests.Convert.Integration.Fusion.DualSide.ReadDualCases import ReadDualCases


# equal volume swapped sides must still preserve their distinct axial centroids
def CheckDualSwap() -> None:
    Samples = tuple(
        Value for Value in ReadDualCases() if Value.Identity in ("baseline", "swapped")
    )
    assert len(Samples) == 2
    Volumes: list[float] = []
    Centers: list[float] = []
    for Sample in Samples:
        Geometry, Volume, AreaValue, Center, Bounds = BuildDualSide(
            Sample.Identity,
            Sample.Frame,
            Sample.Profile,
            Sample.FirstMm,
            Sample.SecondMm,
            Sample.FirstTaper,
            Sample.SecondTaper,
        )
        CheckDualNative(Sample, Geometry)
        Volumes.append(Volume)
        Centers.append(Center.z)
        assert AreaValue > 0 and Bounds.maximum.z > Bounds.minimum.z
    assert IsClose(Volumes[0], Volumes[1], rel_tol=1e-12)
    assert IsClose(Centers[0], -Centers[1], abs_tol=1e-9)
    assert abs(Centers[0] - Centers[1]) > 1.0
