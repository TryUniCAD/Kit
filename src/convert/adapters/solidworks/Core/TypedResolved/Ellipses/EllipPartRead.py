from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Construction.Ellipse.EllipsePlan import (
    EllipsePlan,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.ExtrudeOwner import ExtrudeOwner
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from interchange.geometry.Models.GeometryConics import EllipseGeometry

# the three typed geometric stations avoid an ambiguous inverse reconstruction from public semiaxes
KEllipseStations = "native_ellipse_stations_m"


# source conic facts and its linked profile and driver remain one witnessed model
@DataClass(frozen=True, slots=True)
class EllipPartRead:
    LinkValue: NativeLink
    BossValue: ExtrudeOwner
    SketchValue: ArchiveNode
    HandleValue: ArchiveNode
    GeometryValue: EllipseGeometry
    SegmentId: int
    PointIds: tuple[int, ...]
    PlanValue: EllipsePlan
