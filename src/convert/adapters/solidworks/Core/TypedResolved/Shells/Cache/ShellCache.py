from dataclasses import dataclass as DataClass

from interchange import TopologySummary
from interchange.brep.Topology.BrepModel import BrepModel


# retained shell geometry and its measured summary share the active partition
@DataClass(frozen=True, slots=True)
class ShellCache:
    NameValue: str
    BodyValue: BrepModel
    SummaryValue: TopologySummary
    CentreValue: tuple[float, float, float]
    DigestValue: str
