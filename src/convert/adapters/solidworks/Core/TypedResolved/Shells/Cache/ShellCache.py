from dataclasses import dataclass as DataClass

from interchange import TopologySummary
from interchange.brep.Topology.BrepModel import BrepModel


# qualified shell geometry retains a native name and payload digest only when saved
@DataClass(frozen=True, slots=True)
class ShellCache:
    NameValue: str | None
    BodyValue: BrepModel
    SummaryValue: TopologySummary
    CentreValue: tuple[float, float, float]
    DigestValue: str | None
