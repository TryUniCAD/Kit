from convert.adapters.solidworks.Core.TypedResolved.ExtrudeOwner import ExtrudeOwner
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismParam import (
    ReadPrismParam,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckTreeAlias import (
    CheckTreeAlias,
)
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# independently editable stock depths require the actual display handle and parameter chain
def CheckColdDepth(LinkValue: NativeLink, OwnerValue: ExtrudeOwner) -> None:
    DepthValue = OwnerValue.RequireDepth()
    Dimension, Parameter, LengthValue = ReadPrismParam(DepthValue.DisplayValue, False)
    if (
        DepthValue.DepthValue.name != "D1"
        or OwnerValue.EndValue.FieldsValue.get("f18") is not DepthValue.DisplayValue
        or DepthValue.DisplayValue.FieldsValue.get("n850") != 1
        or (Dimension, Parameter, LengthValue)
        != (
            DepthValue.Dimension,
            DepthValue.Parameter,
            DepthValue.DepthValue.native_value,
        )
    ):
        raise ValueError("blind stock lacks its actual typed D1")
    NameValue = RequireNative(Parameter.FieldsValue.get("f18"), "moNodeName_c")
    CheckTreeAlias(
        LinkValue,
        (
            DepthValue.DisplayValue,
            DepthValue.HandleValue,
            Dimension,
            Parameter,
            NameValue,
        ),
    )
