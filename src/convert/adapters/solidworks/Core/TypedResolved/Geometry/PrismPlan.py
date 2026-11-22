from collections.abc import Mapping
from dataclasses import dataclass as DataClass
from interchange.geometry.Models.GeometryCurves import LineGeometry
from interchange.geometry.Models.Transform import Transform


# analytic geometry needs only validated authored contour placement and live depth with traceable native owners
@DataClass(frozen=True, slots=True)
class PrismPlan:
    FrameValue: Transform
    LinesValue: tuple[LineGeometry, ...]
    DepthValue: float
    EvidenceValue: Mapping[str, object]
    ReversedBlind: bool = False
