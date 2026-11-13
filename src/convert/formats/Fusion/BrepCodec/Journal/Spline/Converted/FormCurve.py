from convert.formats.Fusion.BrepCodec.Journal.Complex.Authoring.ExactSubtypes import (
    ExactCurve,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Grammar.GrammarValue import (
    ChoiceValue,
    SubtypeNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsCurve import BsCurve


def FormCurve(Curve: BsCurve, Jumps: tuple[tuple[float, ...], ...]) -> SubtypeNode:
    if type(Jumps) is not tuple or len(Jumps) != 3:
        raise ValueError("Converted Form edge needs three discontinuity lists")
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
    Lists = tuple(tuple(float(Value) for Value in Entry) for Entry in Jumps)
    Changed = ChoiceValue(Approximation.ChoiceKey, (*Fields[:7], *Lists, *Fields[10:]))
    return SubtypeNode(Plain.SubtypeName, ((Revision, Changed), *PlainBody[1:]))
