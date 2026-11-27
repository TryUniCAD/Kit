from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeValueFields import (
    MakeValueFields,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# zero draft angles need their actual native angle subtype after the shared dimension constructor owns the parameter and plane state
def MakeAngleValue(OwnerValue: ArchiveNode, Parameter: ArchiveNode) -> ArchiveNode:
    FieldsValue = MakeValueFields(OwnerValue, Parameter)
    FieldsValue["ff8"] = 1
    return ArchiveNode(RuntimeClass("AngleDim_c", 1), FieldsValue)
