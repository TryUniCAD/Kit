from collections.abc import Mapping
from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from interchange.geometry.Models.GeometryCurves import CircleGeometry
from interchange.geometry.Models.Transform import Transform


# analytic circle geometry retains actual profile placement signed ends and source ownership evidence
@DataClass(frozen=True, slots=True)
class CircleGeomPlan:
    FrameValue: Transform
    CircleValue: CircleGeometry
    LowerValue: float
    UpperValue: float
    EvidenceValue: Mapping[str, object]
    BossValue: ArchiveNode
