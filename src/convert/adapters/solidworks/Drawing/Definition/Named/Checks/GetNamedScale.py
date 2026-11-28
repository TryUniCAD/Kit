from math import isclose as IsClose, isfinite as IsFinite

from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Drawing.Definition.Projection.ConceptFields import (
    NeedConceptMap,
    NeedDrawNumber,
)


# explicit ratios must stay finite and independent of the drawing sheet scale or inherited view modes
def GetNamedScale(ViewValue: ArchiveNode) -> float:
    FieldsValue = ViewValue.FieldsValue
    Numerator = NeedDrawNumber(FieldsValue["f780"])
    Denominator = NeedDrawNumber(FieldsValue["f788"])
    if min(Numerator, Denominator) <= 0:
        raise BodyUnsupported(
            "named drawing Definition requires positive explicit scale terms"
        )
    ScaleValue = Numerator / Denominator
    FrameValue = NeedConceptMap(FieldsValue["f5e0"])
    FlagsValue = int(NeedDrawNumber(FieldsValue["f610"]))
    if (
        not IsFinite(ScaleValue)
        or ScaleValue <= 0
        or not IsFinite(1.0 / ScaleValue)
        or not IsClose(
            NeedDrawNumber(FrameValue["f70"]), ScaleValue, rel_tol=1e-12, abs_tol=0.0
        )
        or FlagsValue & 8 != 8
        or FlagsValue & 201326592 != 0
    ):
        raise BodyUnsupported(
            "named drawing Definition has an unqualified explicit scale frame"
        )
    return ScaleValue
