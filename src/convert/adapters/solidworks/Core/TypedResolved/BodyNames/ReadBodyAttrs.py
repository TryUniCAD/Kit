from collections.abc import Mapping
from types import MappingProxyType

from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.WalkXmtChain import WalkXmtChain
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# body labels must come from the actual owner list and never a global string search
def ReadBodyAttrs(
    NodesValue: Mapping[int, XmtNode], BodyValue: XmtNode
) -> Mapping[str, XmtNode]:
    Indexes = WalkXmtChain(
        NodesValue,
        BodyValue.Integer("attributes_features"),
        81,
        OwnerField="owner",
        OwnerValue=BodyValue.IndexValue,
    )
    if set(Indexes) != {
        NodeValue.IndexValue
        for NodeValue in NodesValue.values()
        if NodeValue.KindValue == 81
        and NodeValue.Integer("owner") == BodyValue.IndexValue
    }:
        raise ValueError("native body owner list omits an attribute")
    NamesValue: dict[str, XmtNode] = {}
    for IndexValue in Indexes:
        Attribute = NodesValue[IndexValue]
        Definition = RequireXmt(NodesValue, Attribute.Integer("definition"), 80)
        Identifier = RequireXmt(NodesValue, Definition.Integer("identifier"), 79)
        NameValue = Identifier.String("string")
        if NameValue in NamesValue:
            raise ValueError("native body name definition has multiple attributes")
        NamesValue[NameValue] = Attribute
    return MappingProxyType(NamesValue)
