from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.ReadAttrHeads import ReadAttrHeads
from convert.adapters.solidworks.Archive.Partition.WalkXmtChain import WalkXmtChain
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# native name lookup requires registered definitions and reciprocal per owner and per type chains
def CheckXmtAttrs(NodesValue: Mapping[int, XmtNode], BodyValue: XmtNode) -> None:
    WorldValue = RequireXmt(NodesValue, 1, 101)
    Definitions = WalkXmtChain(
        NodesValue, WorldValue.Integer("attrib_def"), 80, PreviousField=None
    )
    if set(Definitions) != {
        NodeValue.IndexValue
        for NodeValue in NodesValue.values()
        if NodeValue.KindValue == 80
    }:
        raise ValueError("native attribute registry omits a definition")
    DefinitionNames: set[str] = set()
    for IndexValue in Definitions:
        Definition = NodesValue[IndexValue]
        NameValue = RequireXmt(NodesValue, Definition.Integer("identifier"), 79).String(
            "string"
        )
        if NameValue in DefinitionNames:
            raise ValueError("native attribute name has multiple active definitions")
        DefinitionNames.add(NameValue)
    HeadsValue = ReadAttrHeads(NodesValue, Definitions)
    ListValue = RequireXmt(NodesValue, BodyValue.Integer("attribute_chains"), 70)
    BlockValue = RequireXmt(NodesValue, ListValue.Integer("list_block"), 74)
    EntriesValue = BlockValue.Indexes("entries")
    CountValue = BlockValue.Integer("n_entries")
    if (
        ListValue.Integer("owner") != BodyValue.IndexValue
        or ListValue.Integer("finger_block") != BlockValue.IndexValue
        or CountValue != ListValue.Integer("list_length")
        or CountValue != len(HeadsValue)
        or ListValue.Integer("block_length") != len(EntriesValue)
        or set(EntriesValue[:CountValue]) != set(HeadsValue.values())
        or any(EntriesValue[CountValue:])
    ):
        raise ValueError("native per body attribute index is incomplete")
