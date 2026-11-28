from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt


# the radial display must use its actual local sketch and value group before selecting its native dimension subtype
def RequireRadial(HandleValue: ArchiveNode, TextKind: int) -> ArchiveNode:
    FieldsValue = HandleValue.FieldsValue
    OwnerValue = ArchiveNode.RequireNode(FieldsValue.get("owner"))
    SketchValue = ArchiveNode.RequireNode(FieldsValue.get("ff0"))
    GroupValue = FieldsValue.get("_values")
    Values = CastValue(tuple[object, ...], GroupValue)
    if (
        HandleValue.ClassValue != RuntimeClass("moSkDimHandleRadial_c", 1)
        or OwnerValue.ClassValue != RuntimeClass("moProfileFeature_c", 1)
        or SketchValue.ClassValue != RuntimeClass("sgSketch", 1)
        or OwnerValue.FieldsValue.get("pd_f80") is not SketchValue
        or FieldInt(OwnerValue.FieldsValue, "f2b0") != 19000
        or type(GroupValue) is not tuple
        or len(Values) != 1
        or FieldInt(FieldsValue, "ff8") != 0
    ):
        raise ValueError("radial display requires the sole local circle value group")
    Dimension = ArchiveNode.RequireNode(Values[0])
    Parameter = ArchiveNode.RequireNode(Dimension.FieldsValue.get("f28"))
    ExpectedKind = {3: 20, 15: 17}.get(FieldInt(Dimension.FieldsValue, "f80"))
    if (
        Dimension.ClassValue != RuntimeClass("sgCircleDim", 1)
        or Dimension.FieldsValue.get("_sketch") is not SketchValue
        or Dimension.FieldsValue.get("owner") is not OwnerValue
        or Parameter.ClassValue != RuntimeClass("moLengthParameter_c", 1)
        or Parameter.FieldsValue.get("owner") is not OwnerValue
        or type(CastValue(object, TextKind)) is not int
        or TextKind != ExpectedKind
    ):
        raise ValueError(
            "radial display lost its driving parameter or native text subtype"
        )
    return OwnerValue
