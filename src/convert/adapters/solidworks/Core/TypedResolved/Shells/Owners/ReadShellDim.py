from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Scalars.ReadScalar import ReadScalar
from convert.adapters.solidworks.Core.TypedResolved.DepthOwner import DepthOwner
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckTreeAlias import (
    CheckTreeAlias,
)
from convert.adapters.solidworks.Core.TypedResolved.ReadDepthOwner import ReadDepthOwner
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# the shell thickness comes from a live radius dimension within the linear display owner
def ReadShellDim(LinkValue: NativeLink, ShellNode: ArchiveNode) -> DepthOwner:
    Display = RequireNative(ShellNode.FieldsValue.get("f818"), "moDisplayDistanceDim_c")
    OwnerValue = ReadDepthOwner(LinkValue, Display, RadiusSlot=True)
    Parameter, Dimension = OwnerValue.Parameter, OwnerValue.Dimension
    ParamFields, DimFields = Parameter.FieldsValue, Dimension.FieldsValue
    if (
        OwnerValue.DepthValue.name != "D1"
        or any(ParamFields.get(NameValue) != 0 for NameValue in ("f0c", "f2c"))
        or ParamFields.get("f20") != ""
        or ParamFields.get("f48") is not None
        or any(
            DimFields.get(NameValue) != 0
            for NameValue in ("f30", "f54", "f5c", "f68", "has_f78")
        )
        or any(DimFields.get(NameValue) is not None for NameValue in ("f48", "f60"))
    ):
        raise ValueError("SOLIDWORKS shell thickness has alternate parameter ownership")
    Cache = NativeRecord(Display.FieldsValue.get("f5b0"))
    DataValue = Cache.get("data")
    if (
        Display.FieldsValue.get("n850") != 1
        or Cache.get("elem") != 8
        or Cache.get("n") != 1
        or type(DataValue) is not bytes
        or len(DataValue) != 8
        or ReadScalar(DataValue, 0, "f64")[0] != OwnerValue.DepthValue.native_value
    ):
        raise ValueError(
            "SOLIDWORKS shell thickness differs from its linked display value"
        )
    CheckTreeAlias(LinkValue, (Display, OwnerValue.HandleValue, Dimension, Parameter))
    return OwnerValue
