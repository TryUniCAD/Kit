from collections.abc import Mapping
from struct import pack as PackValue

from convert.adapters.solidworks.Archive.Partition.ReadXmtVector import ReadXmtVector
from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Core.Partition.Current.Attributed.ReadEdgePoints import (
    ReadEdgePoints,
)


# a free trim may qualify only through its geometrically identical owned edge
def CheckOwnedTrim(Nodes: Mapping[int, XmtNode], TrimValue: XmtNode) -> int:
    LineValue = RequireXmt(Nodes, TrimValue.Integer("basis_curve"), 30)
    Owner = RequireXmt(Nodes, LineValue.Integer("geometric_owner"), 141)
    EdgeValue = RequireXmt(Nodes, LineValue.Integer("owner"), 16)
    First, LastValue = (
        TrimValue.FieldsValue[NameValue] for NameValue in ("parm_1", "parm_2")
    )
    if (
        Owner.Integer("owner") != TrimValue.IndexValue
        or Owner.Integer("shared_geometry") != LineValue.IndexValue
        or Owner.Integer("next") != Owner.IndexValue
        or Owner.Integer("previous") != Owner.IndexValue
        or TrimValue.Integer("geometric_owner")
        or TrimValue.Integer("attributes_features")
        or LineValue.String("sense") != "+"
        or TrimValue.String("sense") != "+"
        or type(First) is not float
        or type(LastValue) is not float
        or First >= LastValue
    ):
        raise ValueError("attributed active trim has an unsupported owner or interval")
    Origin = ReadXmtVector(LineValue, "pvec")
    Direction = ReadXmtVector(LineValue, "direction")
    Endpoints = (
        ReadXmtVector(TrimValue, "point_1"),
        ReadXmtVector(TrimValue, "point_2"),
    )
    for Param, EndValue in zip((First, LastValue), Endpoints, strict=True):
        Mapped = tuple(
            OriginCoord + Param * DirectionCoord
            for OriginCoord, DirectionCoord in zip(Origin, Direction, strict=True)
        )
        if PackValue(">ddd", *Mapped) != PackValue(">ddd", *EndValue):
            raise ValueError("attributed active trim interval differs from its line")
    if set(Endpoints) != set(ReadEdgePoints(Nodes, EdgeValue)):
        raise ValueError("attributed active trim endpoints differ from its edge")
    return Owner.IndexValue
