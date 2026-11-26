from collections.abc import Mapping

from convert.Geometry.Parasolid import KParaGeometry, ParseCarrier
from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# carrier geometry must be the full typed record of an actually used face or edge
def CheckCarrier(
    BodyData: bytes,
    IndexValue: int,
    GeomValue: KParaGeometry,
    KindValue: int,
    Owners: Mapping[int, int],
    Nodes: Mapping[int, XmtNode],
    Spans: Mapping[int, tuple[int, int]],
) -> None:
    NodeValue = RequireXmt(Nodes, IndexValue - 1, KindValue)
    OwnerKind, FieldName = (16, "curve") if KindValue == 30 else (14, "surface")
    Owner = RequireXmt(Nodes, NodeValue.Integer("owner"), OwnerKind)
    Start, EndValue = Spans[NodeValue.IndexValue]
    Record = BodyData[Start:EndValue]
    if (
        Owners.get(Owner.IndexValue + 1) != IndexValue
        or Owner.Integer(FieldName) != NodeValue.IndexValue
        or GeomValue.attributes.get("carrier_record") != Record
        or BodyData.rfind(Record, Start) != Start
        or ParseCarrier(BodyData, Start) != (IndexValue, GeomValue)
    ):
        raise ValueError("used geometry carrier differs from its typed record boundary")
