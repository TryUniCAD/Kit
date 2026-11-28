from convert.adapters.solidworks.Core.TypedResolved.DepthOwner import DepthOwner
from convert.adapters.solidworks.Core.TypedResolved.ExtrudeOwner import ExtrudeOwner
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismParam import (
    ReadPrismParam,
)
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.LineDriver import (
    LineDriver,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.ReadDepthOwner import ReadDepthOwner
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# the separate dormant dimension must belong to the exact cold boss instead of a sketch or active equation driver
def ReadEqDormant(
    LinkValue: NativeLink,
    BossValue: ExtrudeOwner,
    SketchDrivers: tuple[LineDriver, ...],
) -> DepthOwner:
    Active = BossValue.RequireDepth()
    Display = RequireNative(BossValue.EndValue.FieldsValue.get("f20"))
    Dormant = ReadDepthOwner(LinkValue, Display, "f20")
    Dimension, Parameter, MetresValue = ReadPrismParam(Display, False)
    ConfigNodes = {
        id(Entry.EntryValue) for Entry in LinkValue.ConfigValue.MapValue.EntriesValue
    }
    ResolvedNodes = {
        id(Entry.EntryValue) for Entry in LinkValue.ResolvedValue.MapValue.EntriesValue
    }
    Owners = (Display, Dormant.HandleValue, Dimension, Parameter)
    if (
        Dormant.DepthValue.name != "D2"
        or Dormant.Dimension is not Dimension
        or Dormant.Parameter is not Parameter
        or Dormant.DepthValue.native_value != MetresValue
        or any(
            id(NodeValue) in ConfigNodes or id(NodeValue) not in ResolvedNodes
            for NodeValue in Owners
        )
        or Display is Active.DisplayValue
        or Dormant.HandleValue is Active.HandleValue
        or Dimension is Active.Dimension
        or Parameter is Active.Parameter
        or Dimension.FieldsValue["f50"] == Active.Dimension.FieldsValue["f50"]
        or any(
            Parameter is Driver.ParamValue
            or Dimension.FieldsValue["f50"] == Driver.NodeValue.FieldsValue["f50"]
            for Driver in SketchDrivers
        )
    ):
        raise ValueError(
            "named width depth requires a separate owned dormant dimension"
        )
    return Dormant
