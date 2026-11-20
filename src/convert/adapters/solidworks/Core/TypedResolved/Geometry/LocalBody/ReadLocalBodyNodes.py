from convert.Geometry.Parasolid import KTerminalFinSchema, ParaHeaderData
from convert.adapters.solidworks.Archive.Partition.ReadXmtNodeMut import ReadXmtNodeMut
from convert.adapters.solidworks.Archive.Partition.XmtCursor import XmtCursor
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode

# the local profile admits linear and planar topology with mapped body attributes
KLocalNodeKinds = frozenset(
    (12, 13, 14, 15, 16, 17, 18, 19, 29, 30, 50, 70, 74, 79, 80, 81, 82, 83, 84, 98)
)


# local topology must come from complete serialized records with their actual indices
def ReadLocalNodes(DataValue: bytes) -> tuple[dict[int, XmtNode], dict[int, int]]:
    HeaderValue = ParaHeaderData(DataValue)
    if (
        HeaderValue is None
        or HeaderValue.schema != KTerminalFinSchema
        or HeaderValue.description
        != ": TRANSMIT FILE created by modeller version 3701250"
    ):
        raise ValueError("local body transmit profile is unqualified")
    CursorValue = XmtCursor(DataValue[HeaderValue.body_offset :])
    NodesValue: dict[int, XmtNode] = {}
    OffsetsValue: dict[int, int] = {}
    while True:
        OffsetValue = CursorValue.OffsetValue
        KindValue = CursorValue.ReadKind()
        if KindValue == 1:
            break
        if KindValue not in KLocalNodeKinds or len(NodesValue) >= 4096:
            raise ValueError("local body has an unqualified node inventory")
        NodeValue = ReadXmtNodeMut(CursorValue, KindValue)
        IndexValue = NodeValue.IndexValue
        if IndexValue in NodesValue or (
            not NodesValue and (KindValue, IndexValue) != (12, 1)
        ):
            raise ValueError("local body has an ambiguous node identity")
        NodesValue[IndexValue] = NodeValue
        OffsetsValue[IndexValue] = OffsetValue
    CursorValue.FinishRead()
    return NodesValue, OffsetsValue
