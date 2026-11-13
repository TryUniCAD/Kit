from convert.formats.Fusion.BrepCodec.Journal.Complex.Authoring.ExactSubtypes import (
    ExactCurve,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Grammar.GrammarValue import (
    ChoiceValue,
    SubtypeNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsCurve import BsCurve


def OrderCurve(Curve: BsCurve, Lists: tuple[tuple[float, ...], ...]) -> SubtypeNode:
    if len(Lists) != 3:
        raise ValueError("Fusion exact curve needs three discontinuity lists")
    Plain = ExactCurve(Curve)
    PlainBody = Plain.Body
    if not isinstance(PlainBody, tuple) or not isinstance(PlainBody[0], tuple):
        raise ValueError("Fusion exact curve has an unexpected body")
    Revision, Approximation = PlainBody[0]
    if not isinstance(Approximation, ChoiceValue) or not isinstance(
        Approximation.Body, tuple
    ):
        raise ValueError("Fusion exact curve has an unexpected approximation")
    Fields = Approximation.Body
    Changed = ChoiceValue(
        Approximation.ChoiceKey,
        (*Fields[:7], *(tuple(Values) for Values in Lists), *Fields[10:]),
    )
    return SubtypeNode(Plain.SubtypeName, ((Revision, Changed), *PlainBody[1:]))


def JumpCurve(Curve: BsCurve, Jumps: tuple[float, ...]) -> SubtypeNode:
    return OrderCurve(Curve, ((), (), tuple(Jumps)))
