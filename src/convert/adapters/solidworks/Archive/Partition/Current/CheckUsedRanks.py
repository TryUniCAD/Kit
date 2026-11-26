from collections.abc import Set as SetValue

from convert.Geometry.Parasolid import GeomChainLinks, RecordTables
from convert.adapters.solidworks.Archive.Partition.Current.CheckRankRows import (
    CheckRankRows,
)


# projection ranks must depend only on the already qualified consumed row sources
def CheckUsedRanks(
    Tables: RecordTables,
    Edges: SetValue[int],
    Points: SetValue[int],
    Curves: SetValue[int],
    Surfaces: SetValue[int],
) -> None:
    if Tables.edge_uses.keys() - Edges:
        for NextIndex, PrevIndex in ((2, 1), (4, 5)):
            CheckRankRows(
                Edges,
                {
                    IndexValue: (
                        Record.references[NextIndex],
                        Record.references[PrevIndex],
                    )
                    for IndexValue, Record in Tables.edge_uses.items()
                },
            )
    if Tables.points.keys() - Points:
        CheckRankRows(
            Points,
            {
                IndexValue: (Record.references[2], Record.references[3])
                for IndexValue, Record in Tables.points.items()
                if len(Record.references) >= 4
            },
        )
    if Tables.curves.keys() - Curves:
        CheckRankRows(Curves, GeomChainLinks(Tables.curves))
    if Tables.surfaces.keys() - Surfaces:
        CheckRankRows(Surfaces, GeomChainLinks(Tables.surfaces))
