from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Construction.PlanarMates.ReadDatumFrame import (
    ReadDatumFrame,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.SignedStamp import (
    SignedStamp,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt
from convert.adapters.solidworks.Assembly.PlanarMates.ReadPlane import ReadVector
from convert.adapters.solidworks.Core.TypedResolved.Geometry.Axes.AxisPick import (
    AxisPick,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.Patterns.ReadTiltRef import (
    ReadTiltRef,
)
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# copied wrapper geometry must agree with the selected underlying datum and not substitute for it
def ReadAxisPick(
    LinkValue: NativeLink,
    HeaderValue: ArchiveNode,
    Features: Mapping[int, ArchiveNode],
    WrapperValue: object,
) -> AxisPick:
    PlaneValue, Component = ReadTiltRef(LinkValue, HeaderValue, Features, WrapperValue)
    Wrapper = RequireNative(WrapperValue, "moPlaneRef_w")
    Fields = Wrapper.FieldsValue
    Reference = RequireNative(Fields.get("f58"), "moCompRefPlane_c")
    Datum = RequireNative(
        PlaneValue.FieldsValue.get("f6f8"), "moDefaultRefPlnData_c"
    ).FieldsValue
    FrameValue, AxisValue = ReadDatumFrame(PlaneValue)
    if (
        Reference.FieldsValue.get("f100") != AxisValue
        or Fields.get("f08") != SignedStamp(FieldInt(HeaderValue.FieldsValue, "f40"))
        or Fields.get("f0c") != 0
        or Fields.get("f100") != Datum.get("f20")
        or ReadVector(Fields.get("fd0")) != FrameValue.OriginValue
        or ReadVector(Fields.get("fe8")) != FrameValue.NormalValue
        or ReadVector(Fields.get("f188")) != (0.0, 0.0, 0.0)
        or any(
            Fields.get(WrapperKey) != Datum.get(DatumKey)
            for WrapperKey, DatumKey in zip(
                ("fb0", "fb8", "fc0", "fc8"), ("b0", "b1", "b2", "b3"), strict=True
            )
        )
    ):
        raise ValueError("cache free origin axis wrapper disagrees with its datum")
    return AxisPick(PlaneValue, Wrapper, Reference, Component, FrameValue)
