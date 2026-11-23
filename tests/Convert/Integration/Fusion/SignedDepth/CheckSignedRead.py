from math import isclose as IsClose
from typing import Any as AnyValue


# native measurements must constrain the decoded feature graph as well as successful command execution
def CheckSignedRead(Document: dict[str, AnyValue], Sample: dict[str, AnyValue]) -> None:
    assert not Document["diagnostics"]["$tuple"]
    Features = Document["feature_timeline"]["$tuple"]
    assert len(Features) == 2
    assert Features[-1]["definition"]["$type"] == "DistanceExtrude"
    Depth = next(
        Value
        for Value in Document["parameters"]["$tuple"]
        if Value["name"] == "depth_mm"
    )
    NativeDepth = next(
        Value for Value in Sample["native"]["parameters"] if Value["name"] == "depth_mm"
    )
    assert Depth["expression"]["source"] == NativeDepth["expression"]
    assert Depth["owner_id"] == Features[-1]["id"]
    assert Features[-1]["definition"]["along_parameter_id"] == Depth["id"]
    assert IsClose(
        Depth["value"]["value"], NativeDepth["value_internal"] * 10, rel_tol=1e-9
    )
    Bodies = Document["bodies"]["$tuple"]
    assert len(Bodies) == Sample["native"]["body_count"] == 1
    Topology = Bodies[0]["topology"]
    assert Topology["valid"] and Topology["solid_count"] == 1
    assert IsClose(Topology["volume"], Sample["native"]["volume_mm3"], rel_tol=1e-9)
    for RoleName, Expected in zip(
        ("minimum", "maximum"),
        Sample["native"]["bodies"][0]["bounding_box_mm"],
        strict=True,
    ):
        for AxisName, Amount in zip(("x", "y", "z"), Expected, strict=True):
            assert IsClose(
                Topology["bounding_box"][RoleName][AxisName],
                Amount,
                rel_tol=1e-9,
                abs_tol=1e-9,
            )
