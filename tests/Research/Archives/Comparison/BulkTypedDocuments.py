from dataclasses import replace as ChangeRecord

from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.FeatureBody import DesignBody
from interchange.Records.RecordTopology import TopologyCounts
from tests.Research.Archives.Comparison.SemanticDocuments import MakeDocument


# distinct body observations prevent fixture symmetry from selecting arbitrary body counterparts
def MakeOutputDoc(Prefix: str, Changed: bool = False) -> CadDocument:
    Document = MakeDocument(Prefix)
    Stock = Document.feature_timeline[-1]
    Bodies = tuple(
        DesignBody(
            Prefix + "body" + str(Index),
            "authored body",
            Stock.id,
            topology=TopologyCounts(volume=Volume),
        )
        for Index, Volume in enumerate((11.0, 23.0))
    )
    Stock = ChangeRecord(Stock, OutputBodyIds=(Bodies[int(Changed)].id,))
    return ChangeRecord(
        Document,
        bodies=Bodies,
        feature_timeline=(*Document.feature_timeline[:-1], Stock),
    )
