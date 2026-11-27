from typing import cast as CastValue

from pytest import mark as TestMark

from tests.Convert.Solidworks.RevolveEnds.RunRevEnd import RunRevEnd

# each case uses angles and a placement outside the disclosed measurement inputs
KStructureCases = (
    ("EndMidplane", "Right", "symmetric_full", False, (2.125,)),
    ("EndTwo", "Top", "two_sided", False, (2.375, 0.5625)),
    ("EndTwoReverse", "Right", "two_sided", True, (1.125, 1.8125)),
)


# structural reads need actual angular owners even when the output has no measurement
@TestMark.parametrize("CaseValue,PlaneValue,ModeValue,Reversed,Angles", KStructureCases)
def TestRevStruct(
    CaseValue: str,
    PlaneValue: str,
    ModeValue: str,
    Reversed: bool,
    Angles: tuple[float, ...],
) -> None:
    Report = RunRevEnd("ProveRevEndStructure.py", CaseValue)
    assert Report["public_receipt_refusals"] == 2
    assert Report["owner_refusals"] == (
        ["aliased_display", "duplicate_dimension_identity"]
        if len(Angles) == 2
        else ["unexpected_secondary"]
    )
    ShapeView, DesignView = CastValue(list[dict[str, object]], Report["views"])
    assert ShapeView["signed_cap_corners_checked"] is True
    assert DesignView["signed_cap_corners_checked"] is False
    assert ShapeView["mode"] == DesignView["mode"] == ModeValue
    assert ShapeView["reverse"] is DesignView["reverse"] is Reversed
    assert ShapeView["plane"] == DesignView["plane"] == PlaneValue
    assert ShapeView["target_angles"] == DesignView["target_angles"] == list(Angles)
