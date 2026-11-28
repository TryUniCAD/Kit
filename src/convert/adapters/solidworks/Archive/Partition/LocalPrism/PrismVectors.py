from math import hypot as Hypot

from convert.Geometry.Revolve.SweepVector import OffsetVector
from interchange.geometry.Models.VectorSpace import SpaceVector

# the wire format uses meters while the accepted portable solid uses millimeters
KMillimetersPerMeter = 1000

# the admitted geometry needs one residual for analytic edge and plane incidence
KPrismResidual = 1e-9

# the admitted carrier directions must agree with unit frame resolution
KPrismDirectionResidual = 1e-12

# canonical face comparison and native directions require explicit spatial components
KPrismVector = tuple[float, float, float]


# native directions need three floating point components without geometry rescaling
def PrismVector(VectorValue: SpaceVector) -> KPrismVector:
    return (float(VectorValue.x), float(VectorValue.y), float(VectorValue.z))


# native position fields carry meters within the local body terminal layout
def PrismMeters(VectorValue: SpaceVector) -> KPrismVector:
    Scale = KMillimetersPerMeter
    return (VectorValue.x / Scale, VectorValue.y / Scale, VectorValue.z / Scale)


# incidence checks need the spatial distance between independent neutral endpoints
def PrismDistance(First: SpaceVector, Second: SpaceVector) -> float:
    return Hypot(*PrismVector(OffsetVector(First, Second, -1.0)))
