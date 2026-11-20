from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Nodes.CheckIdSeed import (
    CheckIdSeed,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# node and dimension identities share the document allocator while archive map slots remain independent
class PersistentIds:

    # explicit reservations preserve the target allocator boundary without deriving identifiers from saved documents
    def __init__(self, NextValue: int = 0, Reserved: tuple[int, ...] = ()) -> None:
        CheckIdSeed(NextValue, Reserved)
        self.CounterValue = NextValue
        self.ReservedSet = frozenset(Reserved)
        self.Allocations: dict[tuple[ArchiveNode, str], int] = {}

    # caller publication needs the actual next identifier after every modeled allocation
    @property
    def NextValue(self) -> int:
        NumberValue = self.CounterValue
        while NumberValue in self.ReservedSet:
            NumberValue += 1
        if NumberValue >= 0x7FFFFFFF:
            raise ValueError("persistent id space exhausted")
        return NumberValue

    # repeated allocation must retain the same actual node identity and reject externally replaced ids
    def AllocateMut(self, NodeValue: ArchiveNode, FieldName: str = "f08") -> int:
        if not isinstance(
            CastValue(object, NodeValue), ArchiveNode
        ) or FieldName not in ("f08", "f50"):
            raise TypeError(
                "persistent ids require a typed node and classified identity field"
            )
        KeyValue = (NodeValue, FieldName)
        if KeyValue in self.Allocations:
            NumberValue = self.Allocations[KeyValue]
            if NodeValue.FieldsValue.get(FieldName) != NumberValue:
                raise ValueError(
                    "allocated persistent id changed outside its allocator"
                )
            return NumberValue
        if NodeValue.FieldsValue.get(FieldName, -1) != -1:
            raise ValueError("fresh nodes cannot supply an existing persistent id")
        NumberValue = self.NextValue
        self.CounterValue = NumberValue + 1
        self.Allocations[KeyValue] = NumberValue
        NodeValue.FieldsValue[FieldName] = NumberValue
        return NumberValue
