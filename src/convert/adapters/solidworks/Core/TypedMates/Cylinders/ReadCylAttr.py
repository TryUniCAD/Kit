from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.WalkXmtChain import WalkXmtChain
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# legitimate repeated automation attributes must not hide a missing or ambiguous selected identity owner
def ReadCylAttr(
    NodesValue: Mapping[int, XmtNode], OwnerValue: XmtNode, NameValue: str
) -> XmtNode:
    Indexes = WalkXmtChain(
        NodesValue,
        OwnerValue.Integer("attributes_features"),
        81,
        OwnerField="owner",
        OwnerValue=OwnerValue.IndexValue,
    )
    if set(Indexes) != {
        Value.IndexValue
        for Value in NodesValue.values()
        if Value.KindValue == 81 and Value.Integer("owner") == OwnerValue.IndexValue
    }:
        raise ValueError("concentric kernel owner omits an attribute")
    Matches: list[XmtNode] = []
    for IndexValue in Indexes:
        Attribute = RequireXmt(NodesValue, IndexValue, 81)
        Definition = RequireXmt(NodesValue, Attribute.Integer("definition"), 80)
        Identifier = RequireXmt(NodesValue, Definition.Integer("identifier"), 79)
        if Identifier.String("string") == NameValue:
            Matches.append(Attribute)
    if len(Matches) != 1:
        raise ValueError("concentric kernel identity attribute is absent or ambiguous")
    return Matches[0]
