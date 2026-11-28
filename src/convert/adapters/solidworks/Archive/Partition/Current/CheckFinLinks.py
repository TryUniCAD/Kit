from collections.abc import Set as SetValue

from convert.Geometry.Parasolid import RecordTables


# only a closed dimensional fin graph keeps unchecked rows out of edge and vertex order
def CheckFinLinks(
    FinIds: SetValue[int],
    Edges: SetValue[int],
    Vertices: SetValue[int],
    Tables: RecordTables,
) -> None:
    Referenced = (
        {Tables.coedges[IndexValue].references[5] for IndexValue in FinIds}
        | {Tables.coedges[IndexValue].references[8] for IndexValue in FinIds}
        | {Tables.edge_uses[IndexValue].references[0] for IndexValue in Edges}
        | {Tables.vertex_uses[IndexValue].references[1] for IndexValue in Vertices}
    )
    if Referenced - FinIds - {1}:
        raise ValueError("recovered topology uses an unqualified fin dependency")
