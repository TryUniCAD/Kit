from dataclasses import replace as ReplaceValue

from convert.Geometry.Parasolid import (
    KTerminalFinSchema,
    ParaHeaderData,
    RecordTables,
    ScanPartRecords,
)
from convert.adapters.solidworks.Archive.Partition.CheckXmtGraph import CheckXmtGraph
from convert.adapters.solidworks.Archive.Partition.Current.ReadVertexRows import (
    ReadVertexRows,
)
from convert.adapters.solidworks.Archive.Partition.ReadActiveNodes import (
    ReadActiveNodes,
)


# an active partition may only replace a complete vertex table after proving fin shadow ownership
def ReadVertexTable(DataValue: bytes) -> RecordTables | None:
    HeaderValue = ParaHeaderData(DataValue)
    if HeaderValue is None or HeaderValue.schema != KTerminalFinSchema:
        return None
    Nodes = ReadActiveNodes(DataValue)
    CheckXmtGraph(Nodes)
    BodyData = DataValue[HeaderValue.body_offset :]
    Tables = ScanPartRecords(BodyData, TerminalFinVertices=True)
    if Tables is None or not Tables.terminal_fin_vertices or not Tables.bridges:
        return None
    Vertices, FinSpans = ReadVertexRows(BodyData, Nodes, Tables.points)
    if Vertices.keys() != Tables.vertex_uses.keys():
        return None
    FoundShadow = False
    for IndexValue, TrueVertex in Vertices.items():
        Prior = Tables.vertex_uses[IndexValue]
        if Prior != TrueVertex:
            if Prior.offset >= TrueVertex.offset or not any(
                Start < Prior.offset < EndValue
                for Start, EndValue in FinSpans.get(IndexValue, ())
            ):
                return None
            FoundShadow = True
    return ReplaceValue(Tables, vertex_uses=Vertices) if FoundShadow else None
