from dataclasses import replace as ReplaceValue

from convert.formats.Fusion.BrepCodec.Journal.Complex.Grammar.GrammarValue import (
    KGrammarValue,
    SubtypeNode,
    SubtypeRef,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Nodes.IntcurveNode import (
    IntcurveNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Nodes.PcurveNode import PcurveNode
from convert.formats.Fusion.BrepCodec.Journal.Complex.Nodes.SplineNode import SplineNode
from convert.formats.Fusion.BrepCodec.Journal.Complex.Nodes.TcoedgeNode import (
    TcoedgeNode,
)
from convert.formats.Fusion.BrepCodec.Journal.JournalEntity import KJournalEntity


def EntitySubtree(Entity: KJournalEntity) -> KGrammarValue:
    if isinstance(Entity, SplineNode):
        return Entity.Surface
    if isinstance(Entity, IntcurveNode):
        return Entity.Curve
    if isinstance(Entity, PcurveNode):
        return Entity.Carrier
    if isinstance(Entity, TcoedgeNode):
        return Entity.Curve
    return None


def SwapSubtree(Entity: KJournalEntity, Value: KGrammarValue) -> KJournalEntity:
    if isinstance(Entity, SplineNode) and isinstance(Value, (SubtypeNode, SubtypeRef)):
        return ReplaceValue(Entity, Surface=Value)
    if isinstance(Entity, IntcurveNode) and isinstance(
        Value, (SubtypeNode, SubtypeRef)
    ):
        return ReplaceValue(Entity, Curve=Value)
    if isinstance(Entity, PcurveNode) and (
        Value is None or isinstance(Value, (SubtypeNode, SubtypeRef))
    ):
        return ReplaceValue(Entity, Carrier=Value)
    if isinstance(Entity, TcoedgeNode):
        return ReplaceValue(Entity, Curve=Value)
    if Value is not None:
        raise ValueError("Fusion entity cannot carry a subtype tree")
    return Entity
