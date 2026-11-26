from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# carrier inventories must agree with the actual face edge and vertex owners
def CheckLocalGeom(
    NodesValue: Mapping[int, XmtNode], KindsValue: Mapping[int, set[int]]
) -> None:
    for OwnerKind, OwnerField, MemberKind in (
        (14, "surface", 50),
        (16, "curve", 30),
        (18, "point", 29),
    ):
        CarrierIds: set[int] = set()
        for IndexValue in KindsValue[OwnerKind]:
            MemberIndex = NodesValue[IndexValue].Integer(OwnerField)
            if (
                RequireXmt(NodesValue, MemberIndex, MemberKind).Integer("owner")
                != IndexValue
            ):
                raise ValueError("local geometry has a foreign topological owner")
            CarrierIds.add(MemberIndex)
        if CarrierIds != KindsValue.get(MemberKind):
            raise ValueError("local body geometry inventory differs")
