from convert.formats.Fusion.BrepCodec.Journal.Complex.Grammar.GrammarValue import (
    ChoiceValue,
    KGrammarValue,
    KSubtypeValue,
    SubtypeNode,
    SubtypeRef,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsCurve import BsCurve
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsSurface import BsSurface
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.CheckBsCurve import (
    CheckBsCurve,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.CheckBsSurface import (
    CheckBsSurface,
)

KEmptyRange = (1.0, 0.0)

KNullSurface = ChoiceValue("null_surface", ())


def ExactSurface(Surface: BsSurface) -> SubtypeNode:
    CheckBsSurface(Surface)
    Approximation = ChoiceValue(0, (Surface, 0.0, (), (), (), (), (), (), None))
    return SubtypeNode(
        "exact_spl_sur", (23100, Approximation, KEmptyRange, KEmptyRange, 0)
    )


def ExactCurve(Curve: BsCurve) -> SubtypeNode:
    CheckBsCurve(Curve, 3)
    Approximation = ChoiceValue(
        0,
        (
            Curve,
            0.0,
            KNullSurface,
            KNullSurface,
            None,
            None,
            (None, None),
            (),
            (),
            (),
            0,
        ),
    )
    return SubtypeNode("exact_int_cur", ((23100, Approximation), KEmptyRange, 0, 0))


def ParamCurve(Curve: BsCurve, SurfaceIndex: int) -> SubtypeNode:
    CheckBsCurve(Curve, 2)
    if type(SurfaceIndex) is not int or SurfaceIndex < 0:
        raise ValueError("Fusion pcurve surface reference must be a table index")
    Carrier = ChoiceValue(
        "spline",
        (False, SubtypeRef("surface", SurfaceIndex), (None, None, None, None)),
    )
    return SubtypeNode("exp_par_cur", (Curve, 0.0, Carrier))


def NeedMember(Value: KGrammarValue, Index: int) -> KGrammarValue:
    if type(Value) is not tuple or not 0 <= Index < len(Value):
        raise ValueError("Fusion subtype body lacks its B-spline approximation")
    return Value[Index]


def ApproxBody(Value: KGrammarValue) -> KGrammarValue:
    if not isinstance(Value, ChoiceValue) or Value.ChoiceKey != 0:
        raise ValueError("Fusion subtype approximation has an unsupported form")
    return NeedMember(Value.Body, 0)


def SplineSurface(Value: KSubtypeValue) -> BsSurface:
    if isinstance(Value, SubtypeNode) and Value.SubtypeName == "exact_spl_sur":
        Surface = ApproxBody(NeedMember(Value.Body, 1))
        if isinstance(Surface, BsSurface):
            return Surface
    raise ValueError("Fusion surface is not an exact B-spline surface")


def SplineCurve(Value: KSubtypeValue) -> BsCurve:
    if isinstance(Value, SubtypeNode) and Value.SubtypeName == "exact_int_cur":
        Curve = ApproxBody(NeedMember(NeedMember(Value.Body, 0), 1))
        if isinstance(Curve, BsCurve):
            return Curve
    raise ValueError("Fusion curve is not an exact B-spline curve")


def PcurveSpline(Value: KSubtypeValue) -> BsCurve:
    if isinstance(Value, SubtypeNode) and Value.SubtypeName == "exp_par_cur":
        Curve = NeedMember(Value.Body, 0)
        if isinstance(Curve, BsCurve):
            return Curve
    raise ValueError("Fusion pcurve is not an explicit parameter-space B-spline")
