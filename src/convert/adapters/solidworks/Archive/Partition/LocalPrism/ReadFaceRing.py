from math import fsum as SumFloats

from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismFaceLoop import (
    PrismFaceLoop,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismVectors import (
    KPrismResidual,
    KPrismVector,
    PrismVector,
)
from convert.Geometry.Parasolid import BrepTopology
from convert.Geometry.Revolve.SweepVector import CrossVector, DotVector, OffsetVector
from interchange.brep.Surfaces.BrepSurfaces import PlaneSurface
from interchange.brep.Topology.BrepTopology import BrepCoedge

# each finite face ring keeps geometric order independent of its neutral entity identifiers
KPrismRing = tuple[KPrismVector, ...]


# the local terminal fin anchors the vertex reached after following its oriented edge
def PrismFinEnd(TopologyValue: BrepTopology, UseValue: BrepCoedge) -> str:
    EdgeValue = TopologyValue.edges[UseValue.edge_id]
    return EdgeValue.start_vertex_id if UseValue.reversed else EdgeValue.end_vertex_id


# planar trims must agree with the actual carried plane and its outward sense
def ReadFaceRing(
    BoundaryValue: PrismFaceLoop,
    PlaneValue: PlaneSurface,
    TopologyValue: BrepTopology,
) -> KPrismRing:
    PointsValue = tuple(
        TopologyValue.vertex_by_id[PrismFinEnd(TopologyValue, UseValue)].point
        for UseValue in BoundaryValue.UsesValue
    )
    NormalValue = PlaneValue.normal
    if any(
        not abs(
            DotVector(OffsetVector(PointValue, PlaneValue.origin, -1.0), NormalValue)
        )
        <= KPrismResidual
        for PointValue in PointsValue
    ):
        raise ValueError("local prism trim leaves its supporting plane")
    OriginValue, *Remaining = PointsValue
    TwiceArea = SumFloats(
        DotVector(
            CrossVector(
                OffsetVector(First, OriginValue, -1.0),
                OffsetVector(Second, OriginValue, -1.0),
            ),
            NormalValue,
        )
        for First, Second in zip(Remaining[:-1], Remaining[1:], strict=True)
    )
    if not TwiceArea > 0.0:
        raise ValueError("local prism face normal contradicts its oriented loop")
    return tuple(PrismVector(PointValue) for PointValue in PointsValue)
