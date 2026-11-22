from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# only attached entity attributes can corroborate physical ownership across saved marks
def ReadShellAttrs(
    Nodes: Mapping[int, XmtNode], EntityValue: XmtNode
) -> dict[str, XmtNode]:
    Attributes: dict[str, XmtNode] = {}
    SeenValues: set[int] = set()
    Previous, Current = 0, EntityValue.Integer("attributes_features")
    while Current:
        AttrValue = RequireXmt(Nodes, Current, 81)
        Definition = RequireXmt(Nodes, AttrValue.Integer("definition"), 80)
        NameValue = RequireXmt(Nodes, Definition.Integer("identifier"), 79).String(
            "string"
        )
        if (
            Current in SeenValues
            or NameValue in Attributes
            or AttrValue.Integer("owner") != EntityValue.IndexValue
            or AttrValue.Integer("previous") != Previous
        ):
            raise ValueError("SOLIDWORKS shell attributes have another owner")
        Attributes[NameValue] = AttrValue
        SeenValues.add(Current)
        Previous, Current = Current, AttrValue.Integer("next")
    if SeenValues != {
        Value.IndexValue
        for Value in Nodes.values()
        if Value.KindValue == 81 and Value.Integer("owner") == EntityValue.IndexValue
    }:
        raise ValueError("SOLIDWORKS shell entity has detached attributes")
    return Attributes
