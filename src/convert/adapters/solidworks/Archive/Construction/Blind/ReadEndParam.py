from convert.adapters.solidworks.Archive.Construction.Blind.EndInput import KEndInput
from convert.adapters.solidworks.Archive.Construction.Blind.ReadEndHandle import (
    ReadEndHandle,
)
from convert.adapters.solidworks.Archive.Construction.Blind.RequireEndNode import (
    RequireEndNode,
)
from convert.adapters.solidworks.Archive.Construction.Blind.SelectEndValue import (
    SelectEndValue,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# end references must bind the expected named live parameter and its independently allocated dimension identity
def ReadEndParam(
    InputValue: KEndInput, DisplayValue: ArchiveNode, OrdinalValue: int
) -> ArchiveNode:
    IsAngular = OrdinalValue in (3, 4)
    DisplayValue = RequireEndNode(
        DisplayValue, "moDisplayAngularDim_c" if IsAngular else "moDisplayDistanceDim_c"
    )
    HandleValue = ReadEndHandle(DisplayValue)
    Dimension = RequireEndNode(
        HandleValue.FieldsValue["ff0"],
        "AngleDim_c" if IsAngular else "ParallelPlaneDistanceDim_c",
    )
    ParamValue = RequireEndNode(
        Dimension.FieldsValue["f28"],
        "moAngleParameter_c" if IsAngular else "moLengthParameter_c",
    )
    NameValue = RequireEndNode(ParamValue.FieldsValue["f18"], "moNodeName_c")
    if NameValue.FieldsValue["f08"] != f"D{OrdinalValue}":
        raise ValueError("blind dimension name does not match its constructor role")
    ExpectedValue = SelectEndValue(InputValue, OrdinalValue)
    NativeValue = ParamValue.FieldsValue["f58"]
    if type(NativeValue) not in (int, float) or NativeValue != ExpectedValue:
        raise ValueError("blind dimension value does not match its neutral input")
    if (
        type(ParamValue.FieldsValue["f68"]) is not int
        or ParamValue.FieldsValue["f68"] != 0
    ):
        raise ValueError("blind dimension cannot use an alternate parameter value")
    NativeId = Dimension.FieldsValue["f50"]
    if type(NativeId) is not int or NativeId < 0:
        raise ValueError("blind dimension requires its assigned persistent identity")
    return Dimension
