from convert.formats.Fusion.BrepCodec.Journal.Complex.Authoring.ExactSubtypes import (
    ExactCurve,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Grammar.GrammarValue import (
    ChoiceValue,
    SubtypeNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsCurve import BsCurve


def JumpCurve(Curve: BsCurve, Jumps: tuple[float, ...]) -> SubtypeNode:
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
        Approximation.ChoiceKey, (*Fields[:9], tuple(Jumps), *Fields[10:])
    )
    return SubtypeNode(Plain.SubtypeName, ((Revision, Changed), *PlainBody[1:]))
