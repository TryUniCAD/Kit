from dataclasses import dataclass as MakeDataClass
from dataclasses import replace as ReplaceValue

from convert.formats.Fusion.BrepCodec.Journal.Complex.Authoring.ExactSubtypes import (
    SplineCurve,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Grammar.GrammarValue import (
    ChoiceValue,
    KGrammarValue,
    SubtypeNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Subtypes.EntitySubtree import (
    EntitySubtree,
    SwapSubtree,
)
from convert.formats.Fusion.BrepCodec.Journal.Geometry.PointNode import PointNode
from convert.formats.Fusion.BrepCodec.Journal.JournalEntity import KJournalEntity
from convert.formats.Fusion.BrepCodec.Journal.Spline.Conversion.JumpCurve import (
    OrderCurve,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Conversion.SwapEntity import (
    IsNear,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.CageResult import (
    CageResult,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.SubtransNode import SubtransNode
from convert.formats.Fusion.BrepCodec.Journal.Spline.SubtypeRef import SubtypeRef
from convert.formats.Fusion.BrepCodec.Journal.Spline.TsplineSurf import TsplineSurf
from convert.formats.Fusion.TSplineCodec.Model.TsplineSurface import TsplineSurface


@MakeDataClass(frozen=True, slots=True)
class StencilSwap:
    Prior: CageResult
    Result: CageResult
    Surface: TsplineSurface


def SwapScope(
    Value: SubtransNode | SubtypeRef, Context: StencilSwap
) -> SubtransNode | SubtypeRef:
    if isinstance(Value, SubtransNode):
        return SubtransNode(Context.Surface, Value.Regions)
    return Value


def SwapSurf(Value: TsplineSurf, Context: StencilSwap) -> TsplineSurf:
    Places = {
        FaceValue.FaceIndex: Index
        for Index, FaceValue in enumerate(Context.Prior.Faces)
    }
    if Value.FaceIndex not in Places:
        raise ValueError("Fusion Form cage swap found an unknown converted face")
    Prior = Context.Prior.Faces[Places[Value.FaceIndex]]
    Result = Context.Result.Faces[Places[Value.FaceIndex]]
    Cache = Value.Cache
    Knots = (Prior.Surface.KnotsU, Prior.Surface.KnotsV)
    if (Cache.KnotsU, Cache.KnotsV) != Knots or not IsNear(
        Cache.Points, Prior.Surface.Points
    ):
        raise ValueError("Fusion Form cage swap found a stale converted surface")
    if tuple(tuple(Values) for Values in Value.Jumps) != Prior.Jumps:
        raise ValueError("Fusion Form cage swap found stale surface discontinuities")
    return ReplaceValue(
        Value,
        Cache=ReplaceValue(Cache, Points=Result.Surface.Points),
        Jumps=Result.Jumps,
        Subtrans=SwapScope(Value.Subtrans, Context),
    )


def SwapExact(Value: SubtypeNode, Context: StencilSwap) -> SubtypeNode:
    Stored = SplineCurve(Value)
    for Index, Prior in enumerate(Context.Prior.Curves):
        Shape = (Prior.Knots, Prior.Multiplicity, Prior.Weights)
        if Shape == (Stored.Knots, Stored.Multiplicity, Stored.Weights) and IsNear(
            Prior.Poles, Stored.Poles
        ):
            if OrderCurve(Stored, Context.Prior.CurveJumps[Index]) != Value:
                raise ValueError("Fusion Form cage swap found another curve form")
            Poles = Context.Result.Curves[Index].Poles
            Lists = Context.Result.CurveJumps[Index]
            return OrderCurve(ReplaceValue(Stored, Poles=Poles), Lists)
    raise ValueError("Fusion Form cage swap found a stale boundary curve")


def SwapTree(Value: KGrammarValue, Context: StencilSwap) -> KGrammarValue:
    if isinstance(Value, TsplineSurf):
        return SwapSurf(Value, Context)
    if isinstance(Value, SubtransNode):
        return SwapScope(Value, Context)
    if isinstance(Value, SubtypeNode):
        if Value.SubtypeName == "exact_int_cur":
            return SwapExact(Value, Context)
        return SubtypeNode(Value.SubtypeName, SwapTree(Value.Body, Context))
    if isinstance(Value, ChoiceValue):
        return ChoiceValue(Value.ChoiceKey, SwapTree(Value.Body, Context))
    if type(Value) is tuple:
        return tuple(SwapTree(Element, Context) for Element in Value)
    return Value


def SwapPlace(Value: PointNode, Context: StencilSwap) -> PointNode:
    for Index, Prior in enumerate(Context.Prior.Points):
        if IsNear((Prior,), (Value.PositionCm,)):
            return ReplaceValue(Value, PositionCm=Context.Result.Points[Index])
    raise ValueError("Fusion Form cage swap found a stale vertex point")


def SwapStencil(Value: KJournalEntity, Context: StencilSwap) -> KJournalEntity:
    if isinstance(Value, PointNode):
        return SwapPlace(Value, Context)
    Subtree = EntitySubtree(Value)
    if Subtree is None:
        return Value
    Changed = SwapTree(Subtree, Context)
    return Value if Changed == Subtree else SwapSubtree(Value, Changed)
