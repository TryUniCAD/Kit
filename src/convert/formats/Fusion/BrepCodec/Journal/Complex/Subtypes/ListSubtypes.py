from convert.formats.Fusion.BrepCodec.Journal.Complex.Grammar.GrammarValue import (
    ChoiceValue,
    KGrammarValue,
    KSubtypeValue,
    SubtypeNode,
    SubtypeRef,
)


def ListSubtypes(Value: KGrammarValue) -> tuple[KSubtypeValue, ...]:
    if isinstance(Value, SubtypeNode):
        return (Value, *ListSubtypes(Value.Body))
    if isinstance(Value, SubtypeRef):
        return (Value,)
    if isinstance(Value, ChoiceValue):
        return ListSubtypes(Value.Body)
    if type(Value) is tuple:
        return tuple(Found for Element in Value for Found in ListSubtypes(Element))
    return ()


def MapSubtypes(Value: KGrammarValue, Mapping: dict[int, int]) -> KGrammarValue:
    if isinstance(Value, SubtypeNode):
        return SubtypeNode(Value.SubtypeName, MapSubtypes(Value.Body, Mapping))
    if isinstance(Value, SubtypeRef):
        if Value.Index not in Mapping:
            raise ValueError("Fusion subtype reference precedes every definition")
        return SubtypeRef(Value.Family, Mapping[Value.Index])
    if isinstance(Value, ChoiceValue):
        return ChoiceValue(Value.ChoiceKey, MapSubtypes(Value.Body, Mapping))
    if type(Value) is tuple:
        return tuple(MapSubtypes(Element, Mapping) for Element in Value)
    return Value
