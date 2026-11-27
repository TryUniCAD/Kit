from math import isclose as IsClose
from typing import cast as CastValue

from pytest import mark as MarkTests

from convert.Geometry.Extrude.Circular.DualSide.BuildDualSide import BuildDualSide
from interchange.serialization.JsonCodec import DumpJson, LoadJson
from tests.Convert.Integration.Fusion.DualSide.CheckDualNative import CheckDualNative
from tests.Convert.Integration.Fusion.DualSide.DualCase import DualCase
from tests.Convert.Integration.Fusion.DualSide.ReadDualCases import ReadDualCases


# captured vendor solids verify both analytic measures and complete neutral shell construction
@MarkTests.parametrize(
    "Sample", ReadDualCases(), ids=[Value.Identity for Value in ReadDualCases()]
)
def CheckDualSolid(Sample: DualCase) -> None:
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
    assert not Geometry.validate(frozenset((Sample.Identity,)))
    assert LoadJson(DumpJson(Geometry)) == Geometry
    assert IsClose(
        Volume, CastValue(float, Sample.Reading["volume_cm3"]) * 1000, rel_tol=1e-8
    )
    assert IsClose(
        AreaValue, CastValue(float, Sample.Reading["area_cm2"]) * 100, rel_tol=1e-8
    )
    for Actual, Wanted in zip(
        (Center.x, Center.y, Center.z),
        CastValue(list[float], Sample.Reading["center_cm"]),
        strict=True,
    ):
        assert IsClose(Actual, Wanted * 10, abs_tol=1e-6)
    for Corner, WantedCorner in zip(
        (Bounds.minimum, Bounds.maximum),
        CastValue(list[list[float]], Sample.Reading["bounds_cm"]),
        strict=True,
    ):
        assert all(
            IsClose(Value, Expected * 10, abs_tol=1e-7)
            for Value, Expected in zip(
                (Corner.x, Corner.y, Corner.z), WantedCorner, strict=True
            )
        )
