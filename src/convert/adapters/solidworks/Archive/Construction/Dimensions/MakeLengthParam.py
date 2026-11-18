from convert.adapters.solidworks.Archive.Construction.Nodes.InitNodeMut import (
    InitNodeMut,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar


# named length parameters retain unassigned node identity while their authored scalar remains the live driving value
def MakeLengthParam(OwnerValue: ArchiveNode, ValueMetres: float) -> ArchiveNode:
    ValueMetres = RequireScalar(ValueMetres)
    if ValueMetres < 1e-14:
        raise ValueError(
            "ordinary driving length must be positive and at least one e minus fourteen metres"
        )
    Parameter = ArchiveNode(RuntimeClass("moLengthParameter_c", 1), {})
    InitNodeMut(Parameter, "D1")
    Parameter.FieldsValue.update(
        {"owner": OwnerValue, "f0c": 0, "f48": None, "f58": ValueMetres, "f68": 0}
    )
    return Parameter
