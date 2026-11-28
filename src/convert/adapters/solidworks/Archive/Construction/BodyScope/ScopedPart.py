from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Construction.BodyScope.StockBodyGraph import (
    StockBodyGraph,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)


# complete selected stock construction must keep the original owner graph available beside its emitted part
@DataClass(frozen=True, slots=True)
class ScopedPart:
    PartValue: PartCandidate
    ScopeValue: StockBodyGraph
