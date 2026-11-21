from math import hypot as Hypot, isclose as IsClose

from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismCarriers import (
    PrismCarriers,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismVectors import (
    KPrismDirectionResidual,
    KPrismResidual,
    PrismDistance,
    PrismVector,
)
from convert.Geometry.Parasolid import BrepTopology
from convert.Geometry.Revolve.SweepVector import DotVector, OffsetVector


# the wire reconstructs straight trims from finite unit carriers and their actual vertices
def CheckPrismTrims(TopologyValue: BrepTopology, CarriersValue: PrismCarriers) -> None:
    for LineValue in CarriersValue.LinesValue:
        EdgeValue = CarriersValue.LineOwners[LineValue.id]
        if not IsClose(
            Hypot(*PrismVector(LineValue.direction)),
            1.0,
            rel_tol=0.0,
            abs_tol=KPrismDirectionResidual,
        ):
            raise ValueError("local prism line direction must be a unit vector")
        for VertexId, ParameterValue in (
            (EdgeValue.start_vertex_id, EdgeValue.start_parameter),
            (EdgeValue.end_vertex_id, EdgeValue.end_parameter),
        ):
            PointValue = OffsetVector(
                LineValue.origin, LineValue.direction, ParameterValue
            )
            if (
                not PrismDistance(
                    PointValue, TopologyValue.vertex_by_id[VertexId].point
                )
                <= KPrismResidual
            ):
                raise ValueError(
                    "local prism line trim does not reach its neutral endpoint"
                )
    for PlaneValue in CarriersValue.PlanesValue:
        Basis = (PlaneValue.normal, PlaneValue.reference_direction)
        if (
            any(
                not IsClose(
                    Hypot(*PrismVector(VectorValue)),
                    1.0,
                    rel_tol=0.0,
                    abs_tol=KPrismDirectionResidual,
                )
                for VectorValue in Basis
            )
            or abs(DotVector(*Basis)) > KPrismDirectionResidual
        ):
            raise ValueError("local prism plane requires an orthonormal frame")
