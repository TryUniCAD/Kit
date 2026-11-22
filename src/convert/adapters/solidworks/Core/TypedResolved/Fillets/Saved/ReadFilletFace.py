from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyAttrs import (
    ReadBodyAttrs,
)
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ReadChmfRows import (
    KChmfRoleKey,
)

# the actual stock cap and sketch side attribute layouts carry different ordinal locations
KFilletFaceKeys = {
    40: ("moEndFaceSurfIdRep_c", 6, 4, 0),
    74: ("moFromSktEntSurfIdRep_c", 5, 4, None),
}


# the selected edge stock producer and creation event must agree in the two linked graphs
def ReadFilletFace(
    NodesValue: Mapping[int, XmtNode],
    FaceId: int,
    StockId: int,
    StampValue: int,
) -> KChmfRoleKey:
    FaceValue = RequireXmt(NodesValue, FaceId, 14)
    AttrValue = ReadBodyAttrs(NodesValue, FaceValue)["FACE_ID_2001"]
    Definition = RequireXmt(NodesValue, AttrValue.Integer("definition"), 80)
    Fields = AttrValue.Indexes("fields")
    if (
        Definition.Indexes("fields") != (9, 9, 1, 1)
        or len(Fields) != 4
        or Fields[:2] != (0, 0)
    ):
        raise ValueError("saved fillet stock face has an alternate native identity")
    Identity = RequireXmt(NodesValue, Fields[2], 82).Indexes("values")
    if not Identity or Identity[0] not in KFilletFaceKeys:
        raise ValueError("saved fillet stock face has an alternate producer class")
    ClassName, WidthValue, Ordinal, Contour = KFilletFaceKeys[Identity[0]]
    if len(Identity) != WidthValue or Identity[1:3] != (StockId, StampValue):
        raise ValueError("saved fillet stock face names a different creation event")
    return ClassName, Identity[Ordinal], Contour
