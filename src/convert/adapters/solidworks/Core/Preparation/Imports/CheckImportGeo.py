from convert.adapters.solidworks.Archive.Partition.LocalCylinder.ReadCylShape import (
    ReadCylShape,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.CheckBoxPlanes import (
    CheckBoxPlanes,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.HasBoxCorners import (
    HasBoxCorners,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.MakeLocalPrism import (
    MakeLocalPrism,
)
from convert.adapters.solidworks.Core.Preparation.Imports.CheckLPrism import CheckLPrism
from interchange.brep.Topology.BrepModel import BrepModel


# each measured planar profile uses its own typed ownership and the shared closed trim validation
def IsOwnedPrism(ModelValue: BrepModel) -> bool:
    if HasBoxCorners(ModelValue):
        _ = MakeLocalPrism(ModelValue)
        CheckBoxPlanes(ModelValue)
        return False
    if (
        len(ModelValue.faces),
        len(ModelValue.edges),
        len(ModelValue.vertices),
    ) == (8, 18, 12):
        _ = MakeLocalPrism(ModelValue)
        CheckBoxPlanes(ModelValue)
        CheckLPrism(ModelValue)
        return True
    _ = ReadCylShape(ModelValue)
    return False
