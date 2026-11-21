from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTime import (
    FeatureTime,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.InitFeatureMut import (
    InitFeatureMut,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.MateContext import (
    MateContext,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.PlanarMateIn import (
    PlanarMateIn,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# the ordinary native distance class reuses the generic feature constructor and actual mate group without assigning its mate id prematurely
def MakeDistBase(Context: MateContext, InputValue: PlanarMateIn) -> ArchiveNode:
    MateValue = ArchiveNode(RuntimeClass("moMateDistanceDim_c", 1), {})
    InitFeatureMut(
        MateValue, InputValue.NameValue, Context.GroupValue, Context.TargetValue
    )
    FieldsValue = MateValue.FieldsValue
    FieldsValue["f35c"] = 0
    FieldsValue.update(FeatureTime(InputValue.CreatedValue))
    FieldsValue.update(
        dict.fromkeys(
            ("f388", "f390", "f394", "f3b8", "has_f3c0", "f438", "f480", "f4f4"), 0
        )
    )
    FieldsValue.update(dict.fromkeys(("f3c0", "f430", "f468", "f470", "f478"), None))
    FieldsValue.update(
        {
            "f370": [],
            "f3b4": 1,
            "f448": [],
            "f488": "",
            "f490": "",
            "f4c0": 1,
            "f4d8": 1,
            "f4dc": 3,
            "f4e0": 3,
        }
    )
    return MateValue
