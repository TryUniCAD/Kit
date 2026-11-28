from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyFaces import (
    ReadBodyFaces,
)


# a retained fillet must bind the closed active shell and its driving curved surface
def CheckLiveRound(
    NodesValue: Mapping[int, XmtNode], BodyValue: XmtNode, RadiusValue: float
) -> None:
    FaceIds = ReadBodyFaces(NodesValue, BodyValue, FaceCount=7)
    SurfaceIds = tuple(
        NodesValue[IndexValue].Integer("surface") for IndexValue in FaceIds
    )
    PlaneIds = {
        NodeValue.IndexValue
        for NodeValue in NodesValue.values()
        if NodeValue.KindValue == 50
    }
    CylinderIds = tuple(
        NodeValue.IndexValue
        for NodeValue in NodesValue.values()
        if NodeValue.KindValue == 51
    )
    if (
        len(PlaneIds) != 6
        or len(CylinderIds) != 1
        or set(SurfaceIds) != PlaneIds.union(CylinderIds)
        or set(FaceIds)
        != {
            NodeValue.IndexValue
            for NodeValue in NodesValue.values()
            if NodeValue.KindValue == 14
        }
        or RequireXmt(NodesValue, CylinderIds[0], 51).FieldsValue.get("radius")
        != RadiusValue
        or any(
            sum(NodeValue.KindValue == KindValue for NodeValue in NodesValue.values())
            != CountValue
            for KindValue, CountValue in ((16, 15), (18, 10))
        )
    ):
        raise ValueError("SOLIDWORKS live fillet topology or radius differs")
