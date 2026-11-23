from itertools import chain as ChainValues
from struct import pack as PackValue

from convert.Geometry.Parasolid import ReadTolerance
from convert.adapters.solidworks.Archive.Partition.LocalPrism.CheckBoxPlanes import (
    CheckBoxPlanes,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.HasBoxCorners import (
    HasBoxCorners,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismVectors import (
    KMillimetersPerMeter,
)
from interchange.brep.Topology.BrepModel import BrepModel


# the measured box writer sources one shared positive length from every face edge and vertex
def ReadBoxTol(ModelValue: BrepModel) -> float:
    if not HasBoxCorners(ModelValue):
        raise ValueError("local tolerances require an axis aligned rectangular solid")
    CheckBoxPlanes(ModelValue)
    Values = {
        Value.tolerance
        for Value in ChainValues(
            ModelValue.faces, ModelValue.edges, ModelValue.vertices
        )
    }
    if len(Values) != 1:
        raise ValueError("local box tolerances must agree across all owners")
    (Millimeters,) = Values
    Meters = Millimeters / KMillimetersPerMeter
    if Meters <= 0.0 or ReadTolerance(PackValue(">d", Meters), 0) is None:
        raise ValueError("local box tolerance must encode a positive finite length")
    return Meters
