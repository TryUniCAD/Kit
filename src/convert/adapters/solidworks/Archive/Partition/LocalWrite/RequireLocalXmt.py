from convert.adapters.solidworks.Archive.Partition.LocalWrite.CheckLocalXmt import (
    CheckLocalXmt,
)
from convert.adapters.solidworks.Archive.Partition.LocalWrite.LocalXmtProfile import (
    KLocalLimit,
    KLocalShapes,
)
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# direct node inputs must prove a complete bare graph before any attribute attachment
def RequireLocalXmt(NodeValues: tuple[XmtNode, ...]) -> tuple[XmtNode, ...]:
    if type(NodeValues) is not tuple or not 0 < len(NodeValues) <= KLocalLimit:
        raise ValueError("local kernel node count is outside the resident domain")
    NodesValue: dict[int, XmtNode] = {}
    for IndexValue, NodeValue in enumerate(NodeValues, 1):
        if (
            type(NodeValue) is not XmtNode
            or type(NodeValue.IndexValue) is not int
            or NodeValue.IndexValue != IndexValue
            or type(NodeValue.KindValue) is not int
            or NodeValue.KindValue not in KLocalShapes
        ):
            raise ValueError(
                "local kernel nodes require canonical indices and qualified classes"
            )
        NodesValue[IndexValue] = XmtNode(
            IndexValue, NodeValue.KindValue, dict(NodeValue.FieldsValue)
        )
    CheckLocalXmt(NodesValue)
    return tuple(NodesValue.values())
