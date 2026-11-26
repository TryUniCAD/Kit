from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeLocalRef import (
    MakeLocalRef,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt


# the actual retaining handle points to the local dimension rather than an optional external or cache dimension branch
def MakeHandleMut(OwnerValue: ArchiveNode, Dimension: ArchiveNode) -> ArchiveNode:
    FieldsValue = MakeLocalRef(FieldInt(OwnerValue.FieldsValue, "f2b0"))
    FieldsValue.update(
        {
            "owner": OwnerValue,
            "has_f120": 0,
            "f130": None,
            "f138": None,
            "f140": None,
            "f148": None,
            "f150": 0,
            "fe8": None,
            "f100": None,
            "f154": -1,
            "has_f128": 0,
            "f118": 0,
            "ff0": Dimension,
        }
    )
    HandleValue = ArchiveNode(RuntimeClass("moFeatureDimHandle_c", 1), FieldsValue)
    HandlesValue = (HandleValue,)
    Dimension.FieldsValue.update(
        {"retaining_handles": HandlesValue, "refcount": len(HandlesValue)}
    )
    return HandleValue
