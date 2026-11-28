from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Construction.Geometry.PlaneFrame import (
    PlaneFrame,
)
from convert.adapters.solidworks.Archive.Construction.OffsetPlane.MakeOffsetData import (
    MakeOffsetData,
)
from convert.adapters.solidworks.Archive.Construction.OffsetPlane.OffsetFrame import (
    OffsetFrame,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.DepthOwner import DepthOwner
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismAtom import (
    CheckPrismAtom,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismRef import (
    CheckPrismRef,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismParam import (
    ReadPrismParam,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.IsLineState import IsLineState
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.OffsetPlanes.ReadOffBase import (
    ReadOffBase,
)
from convert.adapters.solidworks.Core.TypedResolved.ReadDepthOwner import ReadDepthOwner
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# the order and identity of the plane and distance must come from the live handle chain
def ReadOffDrive(
    LinkValue: NativeLink, Display: ArchiveNode, DatumId: int
) -> DepthOwner:
    OwnerValue = ReadDepthOwner(LinkValue, Display, OwnerSlot="f6f8.f98")
    Dimension, Parameter, _ = ReadPrismParam(Display, False)
    Handle = OwnerValue.HandleValue
    CheckPrismRef(Handle)
    if (
        OwnerValue.DepthValue.name != "D1"
        or Dimension is not OwnerValue.Dimension
        or Parameter is not OwnerValue.Parameter
        or Dimension.FieldsValue.get("f50") != DatumId - 1
        or Dimension.FieldsValue.get("refcount") != 1
        or Handle.FieldsValue.get("f58") is not None
        or any(
            Handle.FieldsValue.get(NameValue) is not None
            for NameValue in ("f130", "f138", "f140", "f148")
        )
    ):
        raise ValueError("offset plane lacks its sole local driving distance")
    return OwnerValue


# a cold offset must agree with its linked datum and live distance and actual reversal flag
def ReadOffDatum(
    LinkValue: NativeLink, NodeValue: ArchiveNode, Features: Mapping[int, ArchiveNode]
) -> tuple[ArchiveNode, PlaneFrame, DepthOwner, bool]:
    Fields = NodeValue.FieldsValue
    CheckPrismAtom(NodeValue)
    DataValue = RequireNative(Fields.get("f6f8"), "moFaceRefPlnData_c")
    DataFields = DataValue.FieldsValue
    Reverse = DataFields.get("fa0")
    if (
        type(Reverse) is not int
        or Reverse not in (0, 1)
        or Fields.get("f6dc") != 4
        or Fields.get("f6e8") is not None
        or any(Fields.get(NameValue) != 0 for NameValue in ("f35c", "f6e0", "f6f0"))
        or not IsLineState(Fields.get("f368"))
        or not IsLineState(Fields.get("f388"))
        or Fields.get("f6c0") != dict.fromkeys(("x", "y", "z"), 0.0)
    ):
        raise ValueError("offset plane has an unsupported construction role")
    Wrapper = NativeRecord(DataFields.get("f90"))
    Datum, BaseFrame = ReadOffBase(Wrapper, LinkValue.ConfigValue.RootValue, Features)
    Display = RequireNative(DataFields.get("f98"), "moDisplayDistanceDim_c")
    Driver = ReadOffDrive(LinkValue, Display, NativeNodeId(NodeValue))
    Distance = Driver.DepthValue.native_value
    if Distance is None or Distance < 1e-14:
        raise ValueError("offset plane driving distance is outside the measured domain")
    FrameValue = OffsetFrame(BaseFrame, -Distance if Reverse else Distance)
    if (
        DataFields
        != MakeOffsetData(FrameValue, dict(Wrapper), Display, bool(Reverse)).FieldsValue
    ):
        raise ValueError("offset plane state contradicts the linked distance or frame")
    return Datum, FrameValue, Driver, bool(Reverse)
