from collections.abc import Mapping
from types import MappingProxyType

from convert.adapters.solidworks.Archive.Partition.ReadAttrHeads import ReadAttrHeads
from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.WalkXmtChain import WalkXmtChain
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode

# populated local slots can contain only the witnessed integer and unicode records
KLocalSlotKinds = MappingProxyType({1: 82, 10: 98})


# the body needs one registered type head and one typed slot layout per attribute
def CheckOwnedXmt(NodesValue: Mapping[int, XmtNode], BodyValue: XmtNode) -> None:
    if not BodyValue.Integer("attribute_chains"):
        if any(NodeValue.KindValue >= 70 for NodeValue in NodesValue.values()):
            raise ValueError("bare local kernel contains owned attributes")
        return
    ListValue = RequireXmt(NodesValue, BodyValue.Integer("attribute_chains"), 70)
    BlockValue = RequireXmt(NodesValue, ListValue.Integer("list_block"), 74)
    DefinitionIds = tuple(
        IndexValue
        for IndexValue, NodeValue in NodesValue.items()
        if NodeValue.KindValue == 80
    )
    NamesValue = {
        NodesValue[NodesValue[IndexValue].Integer("identifier")].String("string")
        for IndexValue in DefinitionIds
    }
    HeadsValue = ReadAttrHeads(NodesValue, DefinitionIds)
    AttributeIds = WalkXmtChain(
        NodesValue,
        BodyValue.Integer("attributes_features"),
        81,
        OwnerField="owner",
        OwnerValue=1,
    )
    EntriesValue = BlockValue.Indexes("entries")
    CountValue = BlockValue.Integer("n_entries")
    if (
        "" in NamesValue
        or len(NamesValue) != len(DefinitionIds)
        or len(DefinitionIds) != len(HeadsValue)
        or not 0 < CountValue == len(HeadsValue) == ListValue.Integer("list_length")
        or ListValue.Integer("block_length") != len(EntriesValue)
        or ListValue.Integer("list_type") != 4
        or ListValue.Integer("finger_block") != BlockValue.IndexValue
        or ListValue.Integer("owner") != BodyValue.IndexValue
        or ListValue.Integer("previous")
        or ListValue.Integer("next")
        or BlockValue.Integer("next_block")
        or set(EntriesValue[:CountValue]) != set(HeadsValue.values())
        or any(EntriesValue[CountValue:])
        or set(AttributeIds)
        != {
            IndexValue
            for IndexValue, NodeValue in NodesValue.items()
            if NodeValue.KindValue == 81
        }
    ):
        raise ValueError("local attribute array counts or body ownership differ")
    for IndexValue in AttributeIds:
        AttributeValue = NodesValue[IndexValue]
        DefinitionValue = NodesValue[AttributeValue.Integer("definition")]
        SlotCodes = DefinitionValue.Indexes("fields")
        SlotValues = AttributeValue.Indexes("fields")
        if not SlotCodes or len(SlotCodes) != len(SlotValues):
            raise ValueError("local attribute slot count differs from its definition")
        for CodeValue, SlotIndex in zip(SlotCodes, SlotValues, strict=True):
            if SlotIndex:
                SlotValue = NodesValue[SlotIndex]
                if SlotValue.KindValue != KLocalSlotKinds.get(CodeValue):
                    raise ValueError(
                        "local attribute slot kind differs from its definition"
                    )
                MemberCount = len(SlotValue.Indexes("values"))
                if not MemberCount or SlotValue.KindValue == 82 and MemberCount != 1:
                    raise ValueError("local attribute value count is unqualified")
