from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.BodyTree import BodyTree
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.CheckLocalBodyGraph import (
    CheckLocalGraph,
)


# the binding inventory must cover the complete typed solid independently of its name
def ReadLocalTree(NodesValue: Mapping[int, XmtNode]) -> BodyTree:
    CheckLocalGraph(NodesValue, AllowStoredAttrs=True)
    KindsValue = {
        KindValue: tuple(
            IndexValue
            for IndexValue, NodeValue in NodesValue.items()
            if NodeValue.KindValue == KindValue
        )
        for KindValue in (14, 15, 17, 16, 18, 50, 30, 29)
    }
    return BodyTree(
        1,
        KindsValue[14],
        KindsValue[15],
        KindsValue[17],
        KindsValue[16],
        KindsValue[18],
        KindsValue[50],
        KindsValue[30],
        KindsValue[29],
    )
