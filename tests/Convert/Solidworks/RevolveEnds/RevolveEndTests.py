from math import isclose as IsClose, radians as ToRadians
from typing import cast as CastValue

from pytest import mark as TestMark

from tests.Convert.Solidworks.RevolveEnds.RunRevEnd import RunRevEnd

# the native references independently fix the angular modes and measured volumes
KEndCases = (
    ("EndMidplane", "symmetric_full", False, (), 15654.48707779957),
    ("EndTwo", "two_sided", False, (43.5,), 22585.481356519983),
    ("EndTwoReverse", "two_sided", True, (43.5,), 22585.48135651999),
)


# publication and strict readback must preserve distinct sides around the actual signed axis
@TestMark.parametrize("CaseValue,ModeValue,Reversed,Against,VolumeValue", KEndCases)
def TestRevEndModes(
    CaseValue: str,
    ModeValue: str,
    Reversed: bool,
    Against: tuple[float, ...],
    VolumeValue: float,
) -> None:
    Measured = RunRevEnd("ProveMeasuredRevolveEnds.py", CaseValue, "--queue")
    Angles = [ToRadians(Value) for Value in (98.25, *Against)]
    Drivers = CastValue(dict[str, float], Measured["drivers_radians"])
    assert list(Drivers) == ["D1", "D2"][: len(Angles)]
    assert list(Drivers.values()) == Angles
    Readback = CastValue(dict[str, object], Measured["readback"])
    assert Readback["topology"] == [1, 6, 12, 8]
    assert Readback["reversed"] is Reversed and Readback["mode"] == ModeValue
    assert Readback["effective_axis"] == [0.0, 0.0, 1.0 if Reversed else -1.0]
    ExpectedSpan = (
        [-Angles[0] / 2.0, Angles[0] / 2.0] if not Against else [-Angles[1], Angles[0]]
    )
    assert Readback["angle_span"] == ExpectedSpan
    assert IsClose(CastValue(float, Readback["volume_mm3"]), VolumeValue, rel_tol=5e-7)
    assert Measured["refusals"] == 16
    AssertRevRoutes(Measured)


# alternate physical deflate bytes retain the read scope and require their own native authority
def AssertRevRoutes(ReportValue: dict[str, object]) -> None:
    Expected = {
        "authored registry",
        "authored direct",
        "authored file sink",
        "strict full JSON registry",
        "strict full JSON direct",
        "strict design JSON registry",
        "strict design JSON direct",
    }
    Exact = ReportValue["sha256"] == ReportValue["measured_sha256"]
    assert ReportValue["exact_native_hash"] is Exact
    if Exact:
        assert set(CastValue(list[str], ReportValue["publication_routes"])) == Expected
        assert ReportValue["unmeasured_route_refusals"] == []
        assert ReportValue["strict_json_republications"] == 4
    else:
        assert ReportValue["publication_routes"] == []
        assert (
            set(CastValue(list[str], ReportValue["unmeasured_route_refusals"]))
            == Expected
        )
        assert ReportValue["strict_json_republications"] == 0
