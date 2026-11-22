from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyAttrs import (
    ReadBodyAttrs,
)
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ReadChmfRows import (
    KChmfRoleKey,
)


# face attributes must use the concrete native identity definition and its integer field
def ReadWarmFaceId(
    NodesValue: Mapping[int, XmtNode], FaceIndex: int
) -> tuple[int, ...]:
    FaceValue = RequireXmt(NodesValue, FaceIndex, 14)
    AttrValue = ReadBodyAttrs(NodesValue, FaceValue)["FACE_ID_2001"]
    DefValue = RequireXmt(NodesValue, AttrValue.Integer("definition"), 80)
    Fields = AttrValue.Indexes("fields")
    if (
        DefValue.Indexes("fields") != (9, 9, 1, 1)
        or len(Fields) != 4
        or Fields[:2] != (0, 0)
    ):
        raise ValueError(
            "saved chamfer faces have an alternate native identity definition"
        )
    return RequireXmt(NodesValue, Fields[2], 82).Indexes("values")


# retained stock caps and sides must derive from the actual stock creation event
def ReadWarmRoles(
    FaceIds: Mapping[int, tuple[int, ...]], StockId: int, EventValue: int
) -> dict[int, KChmfRoleKey]:
    Roles: dict[int, KChmfRoleKey] = {}
    for IndexValue, Values in FaceIds.items():
        if Values[1:4] != (StockId, EventValue, 0):
            raise ValueError("saved chamfer has a foreign stock face")
        match Values:
            case (40, _, _, 0, 0 | 1, 0):
                Roles[IndexValue] = ("moEndFaceSurfIdRep_c", Values[4], 0)
            case (74, _, _, 0, Ordinal) if Ordinal > 0:
                Roles[IndexValue] = ("moFromSktEntSurfIdRep_c", Ordinal, None)
            case _:
                raise ValueError("saved chamfer has an alternate stock face identity")
    if len(Roles) != len(set(Roles.values())) or len(Roles) != 6:
        raise ValueError("saved chamfer has ambiguous restored stock face identities")
    return Roles
