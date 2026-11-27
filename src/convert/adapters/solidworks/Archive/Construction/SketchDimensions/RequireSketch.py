from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt


# generic display reuse must prove the actual sketch owner and indexed point distance instead of accepting a matching class label alone
def RequireSketch(HandleValue: ArchiveNode, TextKind: int) -> ArchiveNode:
    OwnerValue = ArchiveNode.RequireNode(HandleValue.FieldsValue.get("owner"))
    SketchValue = ArchiveNode.RequireNode(HandleValue.FieldsValue.get("ff0"))
    ValueNodes = HandleValue.FieldsValue.get("_values")
    NodesValue = CastValue(tuple[object, ...], ValueNodes)
    IndexValue = FieldInt(HandleValue.FieldsValue, "ff8")
    if (
        HandleValue.ClassValue != RuntimeClass("moSkDimHandleValG2_c", 1)
        or OwnerValue.ClassValue != RuntimeClass("moProfileFeature_c", 1)
        or SketchValue.ClassValue != RuntimeClass("sgSketch", 1)
        or OwnerValue.FieldsValue.get("pd_f80") is not SketchValue
        or FieldInt(OwnerValue.FieldsValue, "f2b0") != 19000
        or type(ValueNodes) is not tuple
        or not 0 <= IndexValue < len(NodesValue)
        or type(CastValue(object, TextKind)) is not int
        or TextKind != 18
    ):
        raise ValueError(
            "sketch display requires a current actual local point distance and native text kind"
        )
    Dimension = ArchiveNode.RequireNode(NodesValue[IndexValue])
    Parameter = ArchiveNode.RequireNode(Dimension.FieldsValue.get("f28"))
    if (
        Dimension.ClassValue != RuntimeClass("sgPntPntDist", 1)
        or Dimension.FieldsValue.get("owner") is not OwnerValue
        or Dimension.FieldsValue.get("_sketch") is not SketchValue
        or FieldInt(Dimension.FieldsValue, "f80") != 1
        or Parameter.ClassValue != RuntimeClass("moLengthParameter_c", 1)
        or Parameter.FieldsValue.get("owner") is not OwnerValue
    ):
        raise ValueError(
            "sketch display lost its actual driving length parameter ownership"
        )
    return OwnerValue
