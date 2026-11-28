from collections import Counter
from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Partition.LocalPrism.CheckPocketLoop import (
    CheckPocketLoop,
    CheckRimSize,
)
from convert.adapters.solidworks.Archive.Partition.LocalWrite.CheckOwnedXmt import (
    CheckOwnedXmt,
)
from convert.adapters.solidworks.Archive.Partition.LocalWrite.CheckXmtLink import (
    CheckXmtLink,
)
from convert.adapters.solidworks.Archive.Partition.LocalWrite.LocalXmtProfile import (
    KLocalShapes,
)
from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Archive.Partition.XmtReferences import XmtReferences


# paired owners and their carrier inventories identify the bounded resident profile
def CheckLocalSize(
    BodyValue: XmtNode, CountsValue: Counter[int], AllowPocket: bool
) -> None:
    FaceCount, EdgeCount, VertexCount = (
        CountsValue[KindValue] for KindValue in (14, 16, 18)
    )
    if (
        CountsValue[12] != 1
        or BodyValue.Integer("body_type") != 1
        or any(
            BodyValue.Integer(NameValue)
            for NameValue in ("owner", "previous", "next", "child")
        )
        or (CountsValue[13], CountsValue[19]) != (2, 2)
        or not FaceCount
        or not EdgeCount
        or not VertexCount
        or (
            CountsValue[17],
            CountsValue[29],
            CountsValue[30],
            CountsValue[50],
        )
        != (2 * EdgeCount, VertexCount, EdgeCount, FaceCount)
        or not AllowPocket
        and CountsValue[15] != FaceCount
    ):
        raise ValueError("local kernel solid ownership or topology counts differ")
    if AllowPocket:
        CheckRimSize(FaceCount, CountsValue[15], EdgeCount, VertexCount)
        if BodyValue.Integer("attribute_chains"):
            raise ValueError(
                "local kernel does not contain one bare rectangular pocket"
            )


# a standalone transmit must contain one closed resident solid before bytes leave the writer
def CheckLocalXmt(
    NodesValue: Mapping[int, XmtNode], *, AllowPocket: bool = False
) -> None:
    BodyValue = RequireXmt(NodesValue, 1, 12)
    CheckLocalSize(
        BodyValue,
        Counter(Value.KindValue for Value in NodesValue.values()),
        AllowPocket,
    )
    for NodeValue in NodesValue.values():
        CheckXmtLink(NodesValue, NodeValue, KLocalShapes[NodeValue.KindValue])
        if 13 <= NodeValue.KindValue <= 50 and NodeValue.Integer("attributes_features"):
            raise ValueError("local kernel boundary attributes are unqualified")
    Pending = {BodyValue.IndexValue}
    Visited: set[int] = set()
    while Pending:
        IndexValue = Pending.pop()
        Visited.add(IndexValue)
        Pending.update(set(XmtReferences(NodesValue[IndexValue])) - Visited)
    if Visited != set(NodesValue):
        raise ValueError("local kernel has records outside its body ownership")
    if AllowPocket:
        CheckPocketLoop(NodesValue)
    CheckOwnedXmt(NodesValue, BodyValue)
