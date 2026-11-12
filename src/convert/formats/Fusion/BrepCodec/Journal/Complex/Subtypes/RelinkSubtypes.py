from itertools import accumulate as Accumulate

from convert.formats.Fusion.BrepCodec.Journal.Complex.Grammar.GrammarValue import (
    ChoiceValue,
    KGrammarValue,
    SubtypeNode,
    SubtypeRef,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Subtypes.EntitySubtree import (
    EntitySubtree,
    SwapSubtree,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Subtypes.ListSubtypes import (
    ListSubtypes,
)
from convert.formats.Fusion.BrepCodec.Journal.JournalEntity import KJournalEntity


def RelinkValueMut(
    Value: KGrammarValue,
    Sources: tuple[SubtypeNode, ...],
    Mapping: dict[int, int],
    Cursors: list[int],
) -> KGrammarValue:
    if isinstance(Value, SubtypeNode):
        Original = Cursors[0]
        Cursors[0] += 1
        _ = Mapping.setdefault(Original, Cursors[1])
        Cursors[1] += 1
        return SubtypeNode(
            Value.SubtypeName, RelinkValueMut(Value.Body, Sources, Mapping, Cursors)
        )
    if isinstance(Value, SubtypeRef):
        if Value.Index in Mapping:
            return SubtypeRef(Value.Family, Mapping[Value.Index])
        if not 0 <= Value.Index < len(Sources):
            raise ValueError("Fusion subtype reference precedes every definition")
        Inline = [Value.Index, Cursors[1]]
        Result = RelinkValueMut(Sources[Value.Index], Sources, Mapping, Inline)
        Cursors[1] = Inline[1]
        return Result
    if isinstance(Value, ChoiceValue):
        return ChoiceValue(
            Value.ChoiceKey, RelinkValueMut(Value.Body, Sources, Mapping, Cursors)
        )
    if type(Value) is tuple:
        return tuple(
            RelinkValueMut(Element, Sources, Mapping, Cursors) for Element in Value
        )
    return Value


def RelinkSubtypes(
    Entities: tuple[KJournalEntity, ...], Chosen: tuple[int, ...]
) -> tuple[KJournalEntity, ...]:
    if Chosen == tuple(range(len(Entities))):
        return Entities
    Trees = tuple(ListSubtypes(EntitySubtree(Entity)) for Entity in Entities)
    Sources = tuple(
        Found
        for Subtrees in Trees
        for Found in Subtrees
        if isinstance(Found, SubtypeNode)
    )
    Starts = (
        0,
        *Accumulate(
            sum(isinstance(Found, SubtypeNode) for Found in Subtrees)
            for Subtrees in Trees
        ),
    )
    Mapping: dict[int, int] = {}
    Cursors = [0, 0]
    Results: list[KJournalEntity] = []
    for Index in Chosen:
        Cursors[0] = Starts[Index]
        Subtree = EntitySubtree(Entities[Index])
        Linked = RelinkValueMut(Subtree, Sources, Mapping, Cursors)
        Results.append(SwapSubtree(Entities[Index], Linked))
    return tuple(Results)
