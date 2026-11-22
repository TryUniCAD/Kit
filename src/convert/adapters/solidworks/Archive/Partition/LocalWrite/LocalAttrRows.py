from struct import iter_unpack as UnpackWords

from convert.adapters.solidworks.Archive.Partition.LocalWrite.LocalBodyOwner import (
    LocalBodyOwner,
)
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# four live attribute values and one empty recipe form the complete body owner chain
def LocalAttrRows(
    BodyValue: XmtNode,
    OwnerValue: LocalBodyOwner,
    DefinitionIndex: int,
    FirstIndex: int,
) -> tuple[tuple[XmtNode, ...], tuple[int, ...]]:
    NameUnits = tuple(
        WordValue
        for (WordValue,) in UnpackWords(
            "<H", OwnerValue.FeatureName.encode("utf-16-le")
        )
    )
    Values = (
        (82, (OwnerValue.AtomId,)),
        (82, (OwnerValue.FeatureId,)),
        (98, NameUnits),
        (82, (OwnerValue.BodyStamp,)),
    )
    Indices = tuple(FirstIndex + 2 * Offset for Offset in range(len(Values) + 1))
    Highest = BodyValue.Integer("highest_node_id")
    Result: list[XmtNode] = []
    for Offset, IndexValue in enumerate(Indices):
        SlotPair = (0, 0)
        if Offset < len(Values):
            KindValue, _ = Values[Offset]
            SlotPair = (IndexValue + 1, 0) if KindValue == 98 else (0, IndexValue + 1)
        Result.append(
            XmtNode(
                IndexValue,
                81,
                {
                    "node_id": Highest + Offset + 1,
                    "definition": DefinitionIndex + 2 * Offset,
                    "owner": BodyValue.IndexValue,
                    "next": Indices[Offset - 1] if Offset > 0 else 0,
                    "previous": Indices[Offset + 1] if Offset + 1 < len(Indices) else 0,
                    "next_of_type": 0,
                    "previous_of_type": 0,
                    "fields": SlotPair,
                },
            )
        )
        if Offset < len(Values):
            KindValue, Contents = Values[Offset]
            Result.append(XmtNode(IndexValue + 1, KindValue, {"values": Contents}))
    return tuple(Result), Indices
