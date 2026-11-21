from math import isfinite as IsFinite, tau as FullTurn

from convert.Geometry.Parasolid import BrepTopology
from convert.Geometry.Revolve.SweepVector import OffsetVector
from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismVectors import (
    KMillimetersPerMeter,
    PrismMeters,
    PrismVector,
)
from interchange.brep.Curves.BrepCurves import CircleCurve
from interchange.brep.Topology.BrepTopology import BrepEdge
from interchange.geometry.Models.VectorSpace import SpaceVector


# a vertex free transmit can omit only the seam point reconstructed from the authored circle
def CheckCylTrim(
    TopologyValue: BrepTopology, EdgeValue: BrepEdge, CircleValue: CircleCurve
) -> None:
    if EdgeValue.start_vertex_id != EdgeValue.end_vertex_id or (
        EdgeValue.start_parameter,
        EdgeValue.end_parameter,
    ) != (0.0, FullTurn):
        raise ValueError(
            "local cylinder requires one full circle trim with a shared seam"
        )
    RadiusValue = CircleValue.radius
    CentreValue = CircleValue.center
    RadialValue = CircleValue.reference_direction
    SeamPoint = TopologyValue.vertex_by_id[EdgeValue.start_vertex_id].point
    Expected = OffsetVector(CentreValue, RadialValue, RadiusValue)
    NativeCentre = SpaceVector(*PrismMeters(CentreValue))
    NativeRadius = RadiusValue / KMillimetersPerMeter
    if (
        PrismVector(SeamPoint) != PrismVector(Expected)
        or PrismVector(Expected) == PrismVector(CentreValue)
        or not 0.0 < NativeRadius <= 1000000.0
        or any(
            not IsFinite(Component) or abs(Component) > 1000000.0
            for Component in PrismVector(NativeCentre)
        )
        or OffsetVector(NativeCentre, RadialValue, NativeRadius) == NativeCentre
    ):
        raise ValueError("local cylinder seam is noncanonical or unrepresentable")
