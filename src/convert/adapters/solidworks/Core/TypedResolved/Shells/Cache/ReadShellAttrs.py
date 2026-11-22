from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# only attached body attributes can corroborate its parent atom and model owner
def ReadShellAttrs(
    Nodes: Mapping[int, XmtNode], BodyValue: XmtNode
) -> dict[str, tuple[int, ...]]:
    Attributes: dict[str, tuple[int, ...]] = {}
    SeenValues: set[int] = set()
    Previous, Current = 0, BodyValue.Integer("attributes_features")
    while Current:
        AttrValue = RequireXmt(Nodes, Current, 81)
        Definition = RequireXmt(Nodes, AttrValue.Integer("definition"), 80)
        NameValue = RequireXmt(Nodes, Definition.Integer("identifier"), 79).String(
            "string"
        )
        if (
            Current in SeenValues
            or NameValue in Attributes
            or AttrValue.Integer("owner") != BodyValue.IndexValue
            or AttrValue.Integer("previous") != Previous
        ):
            raise ValueError("SOLIDWORKS shell body attributes have another owner")
        Attributes[NameValue] = AttrValue.Indexes("fields")
        SeenValues.add(Current)
        Previous, Current = Current, AttrValue.Integer("next")
    if SeenValues != {
        Value.IndexValue
        for Value in Nodes.values()
        if Value.KindValue == 81 and Value.Integer("owner") == BodyValue.IndexValue
    }:
        raise ValueError("SOLIDWORKS shell body has detached attributes")
    return Attributes
